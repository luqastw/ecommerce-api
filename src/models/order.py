"""
Order models - represents orders and order_items tables in database.
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Numeric,
    String,
    Enum as SQLENum,
    CheckConstraint,
)

from sqlalchemy.orm import relationship
from src.db.base import BaseModel
from src.models.enums import OrderStatus


class Order(BaseModel):
    """
    Pedido é snapshot permanente - não referencia cart pois carrinho é temporário.
    total_price é congelado no momento da compra.
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
    product_name salvo como snapshot - se produto for deletado, histórico permanece.
    product_id pode ser NULL (SET NULL on delete).
    """

    __tablename__ = "order_items"

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID do pedido.",
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID do produto.",
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
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product={self.product_name}, qty={self.quantity})>"
