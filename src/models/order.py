"""
Order models - represents orders and order_items tables in database.
"""

from operator import truediv
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Numeric,
    ReleaseSavepointClause,
    String,
    Enum as SQLENum,
    CheckConstraint,
    null,
)
from sqlalchemy.orm import foreign, relationship
from sqlalchemy.sql.roles import ColumnListRole
from src.db.base import BaseModel
from src.models.enums import OrderStatus


class Order(BaseModel):
    """
    Modelo de pedido.

    Tabela: orders

    Campos herdados de BaseModel:
    - id: int (PK, auto-incrementado)
    - created_at: datetime (data do pedido)
    - updated_at: datetime (última atualização)

    Campos específicos:
    - user_id: ID do usuário que fez o pedido (FK)
    - total_price: Valor total do pedido (congelado)
    - status: Status atual do pedido (Enum)

    Relacionamentos:
    - user: Usuário que fez o pedido
    - items: Itens do pedido (OrderItem)

    Por que não referenciar cart?
    - Pedido é snapshot permanente
    - Carrinho é temporário e pode ser modificado
    - Após criar pedido, carrinho é limpo
    """

    __tablename__ = "orders"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID do usuário que fez o pedido.",
    )

    total_price = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Valor total do pedido (congelado no momento da compra).",
    )

    status = Column(
        SQLENum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
        comment="Status atual do pedido.",
    )

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("total_price >= 0", name="check_non_negative_total"),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status}, total={self.total_price})>"


class OrderItem(BaseModel):
    """
    Modelo de item do pedido.

    Tabela: order_items

    Campos herdados de BaseModel:
    - id: int (PK, auto-incrementado)
    - created_at: datetime
    - updated_at: datetime

    Campos específicos:
    - order_id: ID do pedido (FK)
    - product_id: ID do produto (FK)
    - quantity: Quantidade comprada
    - price: Preço unitário no momento da compra (congelado)
    - product_name: Nome do produto (snapshot)

    Por que salvar product_name?
    - Se produto for deletado depois, ainda sabemos o que foi comprado
    - Histórico permanente e completo

    Por que price ao invés de price_at_add?
    - Mais semântico para pedido (é o preço final pago)
    - Vem do cart_item.price_at_add

    Relacionamentos:
    - order: Pedido ao qual pertence
    - product: Produto referenciado (pode ser NULL se deletado)
    """

    __tablename__ = "order_items"

    order_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID do produto (NULL se produto foi deletado).",
    )

    product_name = Column(
        String(200),
        nullable=False,
        comment="Nome do produto no momento da compra (snapshot).",
    )

    quantity = Column(Integer, nullable=False, comment="Quantidade comprada.")

    price = Column(
        Numeric(10, 2), nullable=False, comment="Preço unitário pago (congelado)."
    )

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_positive_quantity_order"),
        CheckConstraint("price >= 0", name="check_non_negative_price_order"),
    )

    def __repr__(self) -> str:
        """Representação em string para debugging."""
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product={self.product_name}, qty={self.quantity})>"
