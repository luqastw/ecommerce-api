"""
Product model - represents products table in database.
"""

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
    """
    is_active: soft delete (False = produto "deletado" mas mantido no histórico).
    """

    __tablename__ = "products"

    name = Column(String(200), nullable=False, index=True, comment="Nome do produto.")

    description = Column(Text, nullable=True, comment="Descrição do produto.")

    price = Column(Numeric(10, 2), nullable=True, comment="Preço do produto em reais.")

    category = Column(
        SQLEnum(ProductCategory),
        nullable=False,
        index=True,
        comment="Categoria do produto.",
    )

    stock = Column(
        Integer, nullable=False, default=0, comment="Quantidade disponível no estoque."
    )

    image_url = Column(String(500), nullable=True, comment="URL da imagem do produto.")

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Indica se o produto está ativo (disponível para venda).",
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"
