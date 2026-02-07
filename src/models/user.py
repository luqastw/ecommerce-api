from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from src.db.base import BaseModel


class User(BaseModel):
    """is_active: soft delete. is_superuser: admin."""

    __tablename__ = "users"

    email = Column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    username = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password = Column(String, nullable=False)

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    cart = relationship("Cart", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
