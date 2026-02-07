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
    """Pedido é snapshot permanente. total_price é congelado no momento da compra."""

    __tablename__ = "orders"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    total_price = Column(Numeric(10, 2), nullable=False)

    status = Column(
        SQLENum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
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
    """product_name salvo como snapshot. product_id pode ser NULL (SET NULL on delete)."""

    __tablename__ = "order_items"

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_positive_quantity_order"),
        CheckConstraint("price >= 0", name="check_non_negative_price_order"),
    )

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product={self.product_name}, qty={self.quantity})>"
