"""
Product model - represents products table in database.
"""

import decimal
from sqlalchemy import Column, String, Text, Numeric, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.sql.roles import ColumnListRole
from src.db.base import BaseModel
from src.models.enums import ProductCategory


class Product(BaseModel):
    """
    Modelo de produto no sistema.

    Tabela: products

    Campos herdados de BaseModel:
        - id: int (PK, auto-increment)
        - created_at: datetime (automático)
        - updated_at: datetime (automático)

    Campos específicos:
        - name: Nome do produto
        - description: Descrição detalhada
        - price: Preço (Decimal para precisão)
        - category: Categoria (Enum)
        - stock: Quantidade em estoque
        - image_url: URL da imagem (opcional)
        - is_active: Produto ativo (soft delete)
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
        """
        Representação em string para debugging.
        """
        return f'<Product(id={self.id}, name={self.name), price={self.price})>'
