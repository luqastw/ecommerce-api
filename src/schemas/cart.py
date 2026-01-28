"""
Pydantic schemas para validação de dados relacionados ao carrinho de compras.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class CartItemBase(BaseModel):
    """
    Schema base para todo item no carrinho.

    Usado como base para outros schemas (herança).
    """

    product_id: int = Field(gt=0, description="ID do produto a adicionar.")

    quantity: int = Field(
        default=1, gt=0, le=100, description="Quantidade do produto (máximo de 100)."
    )


class CartItemCreate(CartItemBase):
    """
    Schema para adicionar item no carrinho (POST /cart/items).

    Cliente envia:
    - product_id: Qual produto
    - quantity: Quantas unidades (opcional, default=1)

    Servidor calcula automaticamente:
    - price_at_add: Pega do produto
    - cart_id: Pega do usuário autenticado

    Exemplo de request:
        {
            "product_id": 10,
            "quantity": 2
        }
    """

    pass


class CartItemUpdate(BaseModel):
    """
    Schema para atualizar quantidade de item (PATCH /cart/items/{id}).

    Permite apenas atualizar a quantidade.
    Não permite trocar o produto (teria que deletar e adicionar outro).

    Exemplo de request:
        {
            "quantity": 5
        }
    """

    quantity: int = Field(gt=0, le=100, description="Nova quantidade do item.")


class CartItemResponse(BaseModel):
    """
    Schema de resposta de um item do carrinho.

    Retorna dados do item + informações do produto.

    Exemplo de response:
        {
            "id": 1,
            "cart_id": 5,
            "product_id": 10,
            "product_name": "Notebook Dell Inspiron 15",
            "product_image": "https://exemplo.com/notebook.jpg",
            "quantity": 2,
            "price_at_add": "3500.00",
            "subtotal": "7000.00",
            "created_at": "2024-01-20T10:30:00Z"
        }
    """

    id: int
    cart_id: int
    product_id: int
    quantity: int
    price_at_add: Decimal
    created_at: datetime

    product_name: str = Field(description="Nome do produto")
    product_image: Optional[str] = Field(None, description="URL da imagem do produto")

    subtotal: Decimal = Field(description="quantity × price_at_add")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("subtotal", mode="before")
    @classmethod
    def calculate_subtotal(cls, v, info):
        """
        Calcula subtotal automaticamente (quantity × price_at_add).

        É executado ANTES da validação do campo.
        Se subtotal não for fornecido, calcula baseado nos outros campos.
        """
        if v is not None:
            return v

        data = info.data
        quantity = data.get("quantity", 1)
        price_at_add = data.get("price_at_add", 0)

        return Decimal(str(quantity)) * Decimal(str(price_at_add))


class CartResponse(BaseModel):
    """
    Schema de resposta do carrinho completo.

    Retorna o carrinho com todos os itens e totais calculados.

    Exemplo de response:
        {
            "id": 1,
            "user_id": 5,
            "items": [
                {
                    "id": 1,
                    "product_id": 10,
                    "product_name": "Notebook Dell",
                    "quantity": 2,
                    "price_at_add": "3500.00",
                    "subtotal": "7000.00"
                },
                {
                    "id": 2,
                    "product_id": 25,
                    "product_name": "Mouse Logitech",
                    "quantity": 1,
                    "price_at_add": "150.00",
                    "subtotal": "150.00"
                }
            ],
            "total_items": 3,
            "total_price": "7150.00",
            "created_at": "2024-01-20T10:00:00Z",
            "updated_at": "2024-01-20T15:30:00Z"
        }
    """

    id: int
    user_id: int
    items: List[CartItemResponse] = Field(
        default=[], description="Lista de itens no carrinho"
    )

    total_items: int = Field(description="Total de itens (soma das quantidades)")
    total_price: Decimal = Field(
        description="Preço total do carrinho (soma dos subtotais)"
    )

    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class CartSummary(BaseModel):
    """
    Schema resumido do carrinho (para exibir no header da UI).

    Retorna apenas os totais, sem detalhes dos itens.
    Útil para mostrar o "badge" do carrinho no front-end.

    Exemplo de response:
        {
            "total_items": 3,
            "total_price": "7150.00"
        }
    """

    total_items: int = Field(description="Total de itens no carrinho")
    total_price: Decimal = Field(description="Valor total do carrinho")
