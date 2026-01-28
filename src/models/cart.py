from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.base import BaseModel


class Cart(BaseModel):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    user = relationship("User", back_populates="cart")
    items = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, user_id={self.user_id}, items={len(self.items)}>"


class CartItem(BaseModel):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(
        Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity = Column(Integer, nullable=False, default=1)
    price_at_add = Column(Numeric(10, 2), nullable=False)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_positive_quantity"),
        CheckConstraint("price_at_add >= 0", name="check_non_negative_price"),
    )
