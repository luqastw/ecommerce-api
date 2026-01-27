"""
Pydantic schema para a validação de dados relacionados a produtos.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional

from src.models.product import ProductCategory


class ProductBase(BaseModel):
    """
    Schema base com campos comuns a todos os schemas de produtos.
    """

    name: str = Field(min_length=3, max_length=200, description="Nome do produto.")
    description: Optional[str] = Field(None, description="Descrição do produto.")
    price: Decimal = Field(gt=0, description="Preço do produto.")
    category: ProductCategory = Field(description="Cateegoria do produto.")


class ProductCreate(ProductBase):
    """
    Schema para criação de produto (POST /products).

    Campos adicionais opcionais:
        - stock: Quantidade inicial em estoque (default: 0)
        - image_url: URL da imagem (opcional)

    Exemplo:
        {
            "name": "Notebook Dell Inspiron 15",
            "description": "Notebook com processador Intel Core i5, 8GB RAM, 256GB SSD",
            "price": 3499.90,
            "category": "eletronicos",
            "stock": 10,
            "image_url": "https://exemplo.com/imagem.jpg"
        }
    """

    stock: int = Field(
        default=0, gt=0, description="Quantidade do produto disponível no estoque."
    )
    image_url: Optional[str] = Field(
        None, max_length=500, description="URL com imagem do produto."
    )

    @field_validator("price")
    @classmethod
    def validate_price_precision(cls, value: Decimal) -> Decimal:
        """
        Valida que o preço tem no máximo 2 casas decimais.

        Evita valores como: 10.999 (três casas decimais).
        """

        price_str = str(value)
        if "." in price_str:
            decimal_plates = len(price_str.split(".")[1])

            if decimal_plates > 2:
                raise ValueError("O preço deve ter no máximo 2 casas decimais.")

        return value


class ProductUpdate(BaseModel):
    """
    Schema para atualização de produto (PATCH /products/{id}).

    Todos os campos são opcionais (atualização parcial).

    Exemplo:
        {
            "price": 3299.90,
            "stock": 15
        }
    """

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
        """
        Valida as casas decimais do preço.
        """

        if value is None:
            return value

        price_str = str(value)
        if "." in price_str:
            decimal_plates = len(price_str.split(".")[1])

            if decimal_plates > 2:
                raise ValueError("O preço deve ter no máximo 2 casas decimais.")

        return value


class ProductResponse(ProductBase):
    """
    Schema para retornar dados de produto (response da API).

    Campos adicionais:
        - id
        - stock
        - image_url
        - is_active
        - created_at
        - updated_at

    Exemplo:
        {
            "id": 1,
            "name": "Notebook Dell Inspiron 15",
            "description": "Notebook com processador Intel Core i5...",
            "price": 3499.90,
            "category": "eletronicos",
            "stock": 10,
            "image_url": "https://exemplo.com/imagem.jpg",
            "is_active": true,
            "created_at": "2024-01-20T23:00:00Z",
            "updated_at": "2024-01-20T23:00:00Z"
        }
    """

    id: int
    stock: int
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
