"""
Order routes - Order management and checkout endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import http
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from src.api.deps import get_db, get_current_user, get_current_admin
from src.models.order import Order, OrderItem
from src.models.user import User
from src.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderSummary,
    OrderUpdateStatus,
    OrderItemResponse,
)
from src.services import order_service
from src.services.order_service import OrderService

router = APIRouter()


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Finaliza compra (checkout).",
    description="Cria pedido através do carrinho do usuário autenticado.",
)
def checkout(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> OrderResponse:
    """
    Finaliza compra criando pedido a partir do carrinho.

    Processo automático:
    1. Valida que carrinho não está vazio
    2. Valida estoque de todos os produtos
    3. Cria pedido com status PENDING
    4. Copia itens do carrinho para o pedido
    5. Atualiza estoque dos produtos
    6. Limpa o carrinho

    Requer:
        Authorization: Bearer <token>

    Request body:
        {} ← Vazio! Usa carrinho do usuário autenticado

    Returns:
        OrderResponse: Pedido criado com todos os itens

    Raises:
        400: Carrinho vazio ou estoque insuficiente
        401: Não autenticado

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
            "created_at": "2024-01-29T15:30:00Z",
            "updated_at": "2024-01-29T15:30:00Z"
        }
    """

    order = OrderService.create_order(db, current_user.id)

    items_response = []
    for item in order.items:
        items_response.append(
            OrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price,
                subtotal=Decimal(str(item.price)) * item.quantity,
            )
        )

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_price=order.total_price,
        status=order.status,
        items=items_response,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get(
    "/",
    response_model=List[OrderSummary],
    summary="Lista pedidos do usuário.",
    description="Retorna historico de pedidos com paginação (resumido, sem detalhes).",
)
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(
        default=10, ge=1, le=100, description="Quantidade de pedidos por página (1-100)"
    ),
    offset: int = Query(
        default=0, ge=0, description="Número de pedidos a pular (paginação)"
    ),
) -> List[OrderSummary]:
    """
    Lista pedidos do usuário autenticado com paginação.

    Retorna versão resumida (sem itens) para não sobrecarregar.
    Para ver detalhes de um pedido específico, use GET /orders/{id}.

    Ordenação: Mais recentes primeiro.

    Query parameters:
        - limit: Pedidos por página (default: 10, max: 100)
        - offset: Pedidos a pular (default: 0)

    Returns:
        Lista de OrderSummary

    Exemplo de response:
        [
            {
                "id": 5,
                "total_price": "7000.00",
                "status": "delivered",
                "items_count": 2,
                "created_at": "2024-01-29T15:30:00Z"
            },
            {
                "id": 3,
                "total_price": "150.00",
                "status": "pending",
                "items_count": 1,
                "created_at": "2024-01-20T10:00:00Z"
            }
        ]
    """

    orders = OrderService.get_user_orders(db, current_user.id, limit, offset)

    summaries = []
    for order in orders:
        items_count = db.query(OrderItem).filter(OrderItem.order_id == order.id).count()

        summaries.append(
            OrderSummary(
                id=order.id,
                total_price=order.total_price,
                status=order.status,
                items_count=items_count,
                created_at=order.created_at,
            )
        )

    return summaries


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Obter detalhes de um pedido.",
    description="Retorna pedido completo com todos os itens.",
)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderResponse:
    """
    Retorna detalhes completos de um pedido específico.

    Validação automática:
    - Pedido pertence ao usuário autenticado

    Args:
        order_id: ID do pedido

    Returns:
        OrderResponse: Pedido com todos os itens

    Raises:
        404: Pedido não encontrado ou não pertence ao usuário
        401: Não autenticado
    """

    order = OrderService.get_order_by_id(db, order_id, current_user.id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido {order_id} não encontrado.",
        )

    items_response = []
    for item in order.items:
        items_response.append(
            OrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price,
                subtotal=Decimal(str(item.price)) * item.quantity,
            )
        )

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_price=order.total_price,
        status=order.status,
        items=items_response,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.patch(
    "/{order_id}/patch",
    response_model=OrderResponse,
    summary="Atualizar status de um pedido (admin).",
    description="Atualiza status de um pedido. Somente administradores.",
)
def update_order_status(
    order_id: int,
    status_update: OrderUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderResponse:
    """
    idas:
        - pending → paid, cancelled
        - paid → shipped, cancelled
        - shipped → delivered
        - delivered → (final, não pode mudar)
        - cancelled → (final, não pode mudar)

    Args:
        order_id: ID do pedido
        status_update: Novo status

    Request body:
        {
            "status": "paid"
        }

    Returns:
        OrderResponse: Pedido atualizado

    Raises:
        404: Pedido não encontrado
        400: Transição de status inválida
        403: Sem permissão (não é admin)
    """

    order = OrderService.update_order_status(db, order_id, status_update.status)

    db.refresh(order)
    order = OrderService.get_order_by_id(db, order_id, order.user_id)

    items_response = []
    for item in order.items:
        items_response.append(
            OrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price,
                subtotal=Decimal(str(item.price)) * item.quantity,
            )
        )

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_price=order.total_price,
        status=order.status,
        items=items_response,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
