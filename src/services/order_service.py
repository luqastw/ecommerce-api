"""
Order Service - Business logic for order management and checkout.

Responsabilidades:
- Criar pedido a partir do carrinho (checkout)
- Validar estoque antes de finalizar compra
- Gerenciar status de pedidos
- Listar histórico de pedidos do usuário
- Validar transições de status
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from fastapi import HTTPException, status
from decimal import Decimal
from typing import List, Optional

from src.models.order import Order, OrderItem
from src.models.cart import Cart, CartItem
from src.models.enums import OrderStatus
from src.services.cart_service import CartService


class OrderService:
    """
    Service para operação de pedidos.

    Todos os métodos são @staticmethod.
    """

    @staticmethod
    def create_order(db: Session, user_id: int) -> Order:
        """
        Cria pedido a partir do carrinho do usuário (checkout).

        Fluxo completo (transação atômica):
        1. Buscar carrinho do usuário
        2. Validar que carrinho não está vazio
        3. Validar estoque de TODOS os produtos
        4. Calcular total do pedido
        5. Criar registro Order
        6. Criar registros OrderItem (cópia dos cart items)
        7. Atualizar estoque dos produtos
        8. Limpar carrinho
        9. Commit (tudo ou nada!)

        Args:
            db: Sessão do banco
            user_id: ID do usuário

        Returns:
            Order: Pedido criado com items carregados

        Raises:
            HTTPException 400: Carrinho vazio
            HTTPException 400: Estoque insuficiente para algum produto

        Exemplo:
            order = OrderService.create_order(db, user_id=5)
            # Carrinho é esvaziado automaticamente
        """

        cart = (
            db.query(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.product))
            .filter(Cart.user_id == user_id)
            .first()
        )

        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Carrinho vazio. Adicione produtos antes de finalizar a compra.",
            )

        for cart_item in cart.items:
            product = cart_item.product

            if not product or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Produto '{cart_item.product.name if product else 'desconhecido'}' não está mais disponível.",
                )

            if product.stock < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Estoque insuficiente para '{product.name}'. "
                        f"Disponível: {product.stock}, "
                        f"no carrinho: {cart_item.quantity}"
                    ),
                )

        total_price = sum(
            Decimal(str(item.price_at_add)) * item.quantity for item in cart.items
        )

        order = Order(
            user_id=user_id, total_price=total_price, status=OrderStatus.PENDING
        )

        db.add(order)
        db.flush()

        order_items = []

        for cart_items in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=cart_item.product.name,
                quantity=cart_item.quantity,
                price=cart_item.price_at_add,
            )
            order_items.append(order_item)

        db.add_all(order_items)

        for cart_item in cart.items:
            product = cart_item.product
            product.stock -= cart_item.quantity

            if product.stock < 0:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao atualizar estoque de '{product.name}'",
                )

        CartService.clear_cart(db, user_id)

        db.commit()
        db.refresh(order)
        order = (
            db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.user_id == user_id)
            .first()
        )

        return order

    @staticmethod
    def get_user_orders(
        db: Session, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Order]:
        """
        Lista pedidos do usuário com paginação.

        Pedidos mais recentes primeiro (ordem decrescente por created_at).

        Args:
            db: Sessão do banco
            user_id: ID do usuário
            limit: Quantidade de pedidos por página
            offset: Pedidos a pular

        Returns:
            Lista de Orders (sem items carregados - use get_order_by_id para detalhes)
        """

        orders = (
            db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(desc(Order.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return orders

    @staticmethod
    def get_order_by_id(db: Session, order_id: int, user_id: int) -> Optional[Order]:
        """
        Busca pedido específico com todos os itens.

        Valida que pedido pertence ao usuário (segurança).

        Args:
            db: Sessão do banco
            order_id: ID do pedido
            user_id: ID do usuário

        Returns:
            Order com items carregados, ou None se não encontrado
        """

        order = (
            db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.user_id == user_id, Order.id == order_id)
            .first()
        )

        return order

    @staticmethod
    def _validade_status_transition(
        current_status: OrderStatus, new_status: OrderStatus
    ) -> bool:
        """
        Valida se a transição de status é permitida.

        Regras de negócio:
        - pending → paid ✅
        - pending → cancelled ✅
        - paid → shipped ✅
        - shipped → delivered ✅
        - delivered → * ❌ (final)
        - cancelled → * ❌ (final)
        - * → pending ❌ (não pode voltar)

        Args:
            current_status: Status atual
            new_status: Novo status desejado

        Returns:
            True se transição é válida, False caso contrário
        """

        if current_status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            return False

        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.PAID, OrderStatus.CANCELLED],
            OrderStatus.PAID: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
        }

        allowed_statuses = valid_transitions.get(current_status, [])
        return new_status in allowed_statuses

    @staticmethod
    def update_order_status(
        db: Session, order_id: int, new_status: OrderStatus
    ) -> Order:
        """
        Atualiza status do pedido (apenas admin).

        Valida transição de status antes de atualizar.

        Args:
            db: Sessão do banco
            order_id: ID do pedido
            new_status: Novo status

        Returns:
            Order atualizado

        Raises:
            HTTPException 404: Pedido não encontrado
            HTTPException 400: Transição de status inválida
        """

        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido {order_id} não encontrado.",
            )

        if not OrderService._validade_status_transition(order.status, new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Transição inválida: {order.status.value} → {new_status.value}. "
                    f"Verifique as regras de transição de status."
                ),
            )

        order.status = new_status
        db.commit()
        db.refresh(order)

        return order
