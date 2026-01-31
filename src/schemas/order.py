"""
Pydantic schemas para validação de dados relacionados a pedidos.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from src.models.enums import OrderStatus


class OrderItemResponse(BaseModel):
    """
    Schema de resposta de um item do pedido.

    Representa um produto comprado com preço e quantidade congelados.

    Exemplo de response:
        {
            "id": 1,
            "order_id": 5,
            "product_id": 10,
            "product_name": "Notebook Dell Inspiron 15",
            "quantity": 2,
            "price": "3500.00",
            "subtotal": "7000.00"
        }
    """

    id: int
    order_id: int
    product_id: Optional[int] = Field(
        None, description="ID do produto (pode ser NULL se ele foi deletado)."
    )
    product_name: str = Field(description="Nome do produto no momento da compra.")
    quantity: int = Field(gt=0, description="Quantidade comprada.")
    price: Decimal = Field(description="Preço unitário pago.")
    subtotal: Decimal = Field(description="quantity . price")

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """
    Schema para criar pedido (checkout).

    NÃO precisa de campos!

    Processo:
    1. Cliente faz POST /orders (body vazio)
    2. Backend busca carrinho do usuário autenticado
    3. Valida estoque de todos os produtos
    4. Cria pedido copiando itens do carrinho
    5. Limpa o carrinho
    6. Retorna o pedido criado

    Por que não enviar itens no body?
    - Carrinho já tem os itens
    - Evita inconsistência (cliente manipular preços)
    - Mais simples e seguro

    Exemplo de request:
        POST /orders
        Body: {}  ← Vazio!
    """

    pass


class OrderResponse(BaseModel):
    """
    Schema de resposta de pedido completo.

    Retorna pedido com todos os itens e informações completas.

    Exemplo de response:
        {
            "id": 1,
            "user_id": 5,
            "total_price": "7000.00",
            "status": "pending",
            "items": [
                {
                    "id": 1,
                    "product_name": "Notebook Dell",
                    "quantity": 2,
                    "price": "3500.00",
                    "subtotal": "7000.00"
                }
            ],
            "created_at": "2024-01-29T10:00:00Z",
            "updated_at": "2024-01-29T10:00:00Z"
        }
    """

    id: int
    user_id: int
    total_price: Decimal = Field(description="Valor total do pedido.")
    status: OrderStatus = Field(description="Status atual do pedido.")
    items: List[OrderItemResponse] = Field(
        default=[], description="Lista de itens comprados."
    )
    created_at: datetime = Field(description="Data do pedido.")
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderSummary(BaseModel):
    """
    Schema resumido de pedido (para listar histórico).

    Versão enxuta sem detalhes dos itens.
    Útil para GET /orders (lista de pedidos).

    Exemplo de response:
        {
            "id": 1,
            "total_price": "7000.00",
            "status": "delivered",
            "items_count": 2,
            "created_at": "2024-01-29T10:00:00Z"
        }
    """

    id: int
    total_price: Decimal
    status: OrderStatus
    items_count: int = Field(description="Quantidade total de itens")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderUpdateStatus(BaseModel):
    """
    Schema para admin atualizar status do pedido.

    Apenas admins podem atualizar status.
    Clientes podem apenas visualizar.

    Transições válidas:
    - pending → paid
    - pending → cancelled
    - paid → shipped
    - shipped → delivered

    Request body:
        {
            "status": "paid"
        }
    """

    status: Optional[OrderStatus] = Field(description="Novo status do pedido.")
