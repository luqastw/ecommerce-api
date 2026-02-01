"""
Cart routes - Shopping cart endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_user
from src.models.user import User
from src.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    CartResponse,
    CartSummary,
)
from src.services.cart_service import CartService

router = APIRouter()


@router.get(
    "/",
    response_model=CartResponse,
    summary="Obter carrinho completo.",
    description="Retorna o carrinho com todos os itens e totais calculados.",
)
def get_cart(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CartResponse:
    """
    Retorna carrinho completo do usuário autenticado.

    Inclui:
    - Lista de itens com detalhes do produto
    - Total de itens (soma das quantidades)
    - Preço total (soma dos subtotais)

    Requer:
        Authorization: Bearer <token>

    Returns:
        CartResponse: Carrinho com items, totais e timestamps

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
                }
            ],
            "total_items": 2,
            "total_price": "7000.00",
            "created_at": "2024-01-20T10:00:00Z",
            "updated_at": "2024-01-20T15:30:00Z"
        }
    """

    cart = CartService.get_cart_with_details(db, current_user.id)

    if not cart:
        cart = CartService.get_or_create_cart(db, current_user.id)
        cart.items = []

    total_items, total_price = CartService.calculate_totals(cart)

    items_response = []
    for item in cart.items:
        items_response.append(
            {
                "id": item.id,
                "cart_id": item.cart_id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "product_image": item.product.image_url,
                "quantity": item.quantity,
                "price_at_add": item.price_at_add,
                "subtotal": item.price_at_add * item.quantity,
                "created_at": item.created_at,
            }
        )

    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        items=items_response,
        total_items=total_items,
        total_price=total_price,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


@router.get(
    "/summary",
    response_model=CartSummary,
    summary="Resumo do carrinho.",
    description="Retorna apenas totais (útil para a badge do carrinho na UI).",
)
def get_cart_summary(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CartSummary:
    """
    Retorna resumo do carrinho (apenas totais).

    Útil para exibir no header do site:
    - "🛒 3 itens - R$ 7.150,00"

    Mais leve que GET /cart pois não retorna lista de itens.

    Returns:
        CartSummary: total_items e total_price
    """

    cart = CartService.get_cart_with_details(db, current_user.id)

    if not cart:
        return CartSummary(total_items=0, total_price=0)

    total_items, total_price = CartService.calculate_totals(cart)

    return CartSummary(total_items=total_items, total_price=total_price)


@router.post(
    "/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar item ao carrinho.",
    description="Adiciona item ao carrinho ou aumenta a quantidade se já existir.",
)
def add_item_to_cart(
    item_data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartItemResponse:
    """
    Adiciona produto ao carrinho.

    Comportamento:
    - Se produto NÃO está no carrinho → cria novo item
    - Se produto JÁ está no carrinho → soma quantidade

    Validações automáticas:
    - Produto existe e está ativo
    - Estoque suficiente
    - Quantidade entre 1-100

    Request body:
        {
            "product_id": 10,
            "quantity": 2
        }

    Returns:
        CartItemResponse: Item adicionado/atualizado com dados do produto

    Raises:
        404: Produto não encontrado ou inativo
        400: Estoque insuficiente ou dados inválidos
    """

    cart_item = CartService.add_item(db, current_user.id, item_data)

    db.refresh(cart_item)

    return CartItemResponse(
        id=cart_item.id,
        cart_id=cart_item.cart_id,
        product_id=cart_item.product_id,
        product_name=cart_item.product.name,
        product_image=cart_item.product.image_url,
        quantity=cart_item.quantity,
        price_at_add=cart_item.price_at_add,
        subtotal=cart_item.price_at_add * cart_item.quantity,
        created_at=cart_item.created_at,
    )


@router.patch(
    "/items/{item_id}",
    response_model=CartItemResponse,
    summary="Atualizar quantidade do item.",
    description="Atualiza a quantidade de um item do carrinho.",
)
def update_cart_item(
    item_id: int,
    update_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartItemResponse:
    """
    Atualiza quantidade de item no carrinho.

    Validações:
    - Item pertence ao usuário autenticado (segurança)
    - Estoque suficiente para nova quantidade
    - Quantidade entre 1-100

    Args:
        item_id: ID do item no carrinho
        update_data: Nova quantidade

    Request body:
        {
            "quantity": 5
        }

    Returns:
        CartItemResponse: Item atualizado

    Raises:
        404: Item não encontrado no carrinho do usuário
        400: Estoque insuficiente
    """

    cart_item = CartService.update_item_quantity(
        db, current_user.id, item_id, update_data
    )

    db.refresh(cart_item)

    return CartItemResponse(
        id=cart_item.id,
        cart_id=cart_item.cart_id,
        product_id=cart_item.product_id,
        product_name=cart_item.product.name,
        product_image=cart_item.product.image_url,
        quantity=cart_item.quantity,
        price_at_add=cart_item.price_at_add,
        subtotal=cart_item.price_at_add * cart_item.quantity,
        created_at=cart_item.created_at,
    )


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover item do carrinho.",
    description="Remove um item específico do carrinho.",
)
def remove_item_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove item do carrinho.

    Validações:
    - Item pertence ao usuário autenticado

    Args:
        item_id: ID do item a remover

    Returns:
        204 No Content (sem body)

    Raises:
        404: Item não encontrado no carrinho do usuário
    """

    CartService.remove_item(db, current_user.id, item_id)

    return None


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Limpar carrinho.",
    description="Remove todos os itens do carrinho.",
)
def clear_cart(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Remove todos os itens do carrinho.

    Útil para:
    - Botão "Limpar carrinho" na UI
    - Após finalizar compra

    O carrinho em si não é deletado, apenas esvaziado.

    Returns:
        204 No Content
    """

    CartService.clear_cart(db, current_user.id)

    return None
