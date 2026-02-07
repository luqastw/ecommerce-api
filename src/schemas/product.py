from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional

from src.models.product import ProductCategory


class ProductBase(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    price: Decimal = Field(gt=0)
    category: ProductCategory


class ProductCreate(ProductBase):
    stock: int = Field(default=0, gt=0)
    image_url: Optional[str] = Field(None, max_length=500)

    @field_validator("price")
    @classmethod
    def validate_price_precision(cls, value: Decimal) -> Decimal:
        """Máximo 2 casas decimais."""
        price_str = str(value)
        if "." in price_str:
            decimal_plates = len(price_str.split(".")[1])

            if decimal_plates > 2:
                raise ValueError("O preço deve ter no máximo 2 casas decimais.")

        return value


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    category: Optional[ProductCategory] = None
    stock: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

    @field_validator("price")
    @classmethod
    def validate_price_precision(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        """Máximo 2 casas decimais."""
        if value is None:
            return value

        price_str = str(value)
        if "." in price_str:
            decimal_plates = len(price_str.split(".")[1])

            if decimal_plates > 2:
                raise ValueError("O preço deve ter no máximo 2 casas decimais.")

        return value


class ProductResponse(ProductBase):
    id: int
    stock: int
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
