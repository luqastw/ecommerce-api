from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    Text,
    Numeric,
    Integer,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from src.db.base import BaseModel
from src.models.enums import ProductCategory


class Product(BaseModel):
    """is_active: soft delete (False = produto "deletado" mas mantido no histórico)."""

    __tablename__ = "products"

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    category = Column(SQLEnum(ProductCategory), nullable=False, index=True)
    stock = Column(Integer, nullable=False, default=0)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"
