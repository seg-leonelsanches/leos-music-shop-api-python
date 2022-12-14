import humps

from typing import Union
from fastapi import APIRouter, Depends, Header, status, HTTPException
from sqlalchemy.orm import joinedload, Session

from dependencies import models, schemas
from dependencies.authentication import jwt_methods
from dependencies.authentication.user_methods import get_customer_user, get_user
from dependencies.database import get_db
from dependencies.misc import deep_dict
from dependencies.segment import analytics_instance

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    responses={404: {"description": "Not found"}}
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_orders(db: Session = Depends(get_db), user: models.User = Depends(get_user)):
    order_query = db.query(models.Order)

    if user.user_type == "customer":
        order_query = order_query.filter(models.Order.customer_id == user.id)

    orders = order_query.all()
    return orders


@router.get("/{id}")
def get_one_order(id: int, db: Session = Depends(get_db), user: models.User = Depends(get_user)):
    order_query = db.query(models.Order) \
        .options(
            joinedload(models.Order.order_bass_guitars) \
            .joinedload(models.OrderBassGuitar.bass_guitar) \
            .joinedload(models.BassGuitar.manufacturer) \
        ) \
        .filter(models.Order.id == id)
    
    if user.user_type == "customer":
        order_query = order_query.filter(models.Order.customer_id == user.id)
    
    order = order_query.one_or_none()

    if order is None:
        raise HTTPException(
            status_code=404, detail=f"Order with Id {id} not found.")

    return order


def _anonymous_order(request: schemas.OrderSchema, db: Session):
    if request.guest_user_data is None:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY, detail=f"Customer data not provided")

    guest_order: models.GuestOrder = models.GuestOrder(
        first_name=request.guest_user_data.first_name,
        last_name=request.guest_user_data.last_name,
        email=request.guest_user_data.email,
        address_first_line=request.guest_user_data.address_first_line,
        address_second_line=request.guest_user_data.address_second_line,
        city=request.guest_user_data.city,
        state=request.guest_user_data.state,
        zip_code=request.guest_user_data.zip_code
    )

    guest_order.guest_order_bass_guitars = []
    for bass_order in request.bass_guitars:
        bass_guitar = db.query(models.BassGuitar) \
            .filter(models.BassGuitar.id == bass_order.bass_guitar_id) \
            .one()

        guest_order.guest_order_bass_guitars.append(
            models.GuestOrderBassGuitar(
                bass_guitar_id=bass_order.bass_guitar_id,
                quantity=bass_order.quantity,
                historical_price=bass_guitar.price
            )
        )

    db.add(guest_order)
    db.commit()
    db.refresh(guest_order)

    guest_order_id = guest_order.id
    
    guest_order = db.query(models.GuestOrder) \
        .options(joinedload(models.GuestOrder.guest_order_bass_guitars) \
            .joinedload(models.GuestOrderBassGuitar.bass_guitar)) \
        .filter(models.GuestOrder.id == guest_order_id) \
        .one_or_none()

    guest_order_dict = deep_dict(guest_order)

    analytics_instance.identify(f"guest-user-{guest_order.email}", {
        'first_name': guest_order.first_name,
        'last_name': guest_order.last_name,
        'email': guest_order.email
    })

    analytics_instance.track(f"guest-order-{guest_order.id}", 
        'Guest Order Placed', 
        humps.camelize(guest_order_dict)
    )

    return guest_order


def _identified_customer_order(request: schemas.OrderSchema, customer: models.Customer, db: Session):
    order: models.Order = models.Order(
        customer_id=customer.customer_id
    )

    order.order_bass_guitars = []
    for bass_order in request.bass_guitars:
        bass_guitar = db.query(models.BassGuitar) \
            .filter(models.BassGuitar.id == bass_order.bass_guitar_id) \
            .one()

        order.order_bass_guitars.append(
            models.OrderBassGuitar(
                bass_guitar_id=bass_order.bass_guitar_id,
                quantity=bass_order.quantity,
                historical_price=bass_guitar.price
            )
        )

    db.add(order)
    db.commit()
    db.refresh(order)

    order_id = order.id

    order = db.query(models.Order) \
        .options(joinedload(models.Order.order_bass_guitars) \
            .joinedload(models.OrderBassGuitar.bass_guitar)) \
        .filter(models.Order.id == order_id) \
        .one_or_none()

    order_dict = deep_dict(order)

    analytics_instance.track(customer.customer_id, 
        'Order Placed', 
        humps.camelize(order_dict)
    )
    
    return order


@router.post("")
def place_new_order(
    request: schemas.OrderSchema,
    db: Session = Depends(get_db),
    authorization: Union[str, None] = Header(default=None)
):
    customer: models.Customer | None = None
    if authorization:
        token: str | None = jwt_methods.validate_jwt_format(authorization)
        if token is None:
            raise HTTPException(status_code=status.HTTP_417_EXPECTATION_FAILED,
                                detail=f"Invalid authentication header")
        customer = get_customer_user(token, db)

    if not customer:
        return _anonymous_order(request, db)

    return _identified_customer_order(request, customer, db)
