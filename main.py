from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import (
    auth, 
    bass_guitars,
    customers, 
    guest_orders, 
    manufacturers, 
    me, 
    orders,
    sign_up,
    test
)

app = FastAPI(
    title="Leo's Music Shop API",
    version="0.0.1",
    description="This is the coolest API for Leo's Music Shop."
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(bass_guitars.router)
app.include_router(customers.router)
app.include_router(guest_orders.router)
app.include_router(manufacturers.router)
app.include_router(me.router)
app.include_router(orders.router)
app.include_router(sign_up.router)
app.include_router(test.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
