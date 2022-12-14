from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from dependencies.models.base_model import DeclarativeBase

class Manufacturer(DeclarativeBase):
    __tablename__ = "manufacturers"
    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(50), nullable=False, index=True)

    bass_guitars = relationship("BassGuitar", back_populates="manufacturer")