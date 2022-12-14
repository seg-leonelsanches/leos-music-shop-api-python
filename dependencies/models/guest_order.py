from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from dependencies.models.base_model import DeclarativeBase
from dependencies.models.base_order import BaseOrder

class GuestOrder(DeclarativeBase, BaseOrder):
    __tablename__ = "guest_orders"
    
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), nullable=False, index=True)
    address_first_line = Column(String(100), nullable=False)
    address_second_line = Column(String(100), nullable=True)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(Integer)

    guest_order_bass_guitars = relationship("GuestOrderBassGuitar", back_populates="guest_order")