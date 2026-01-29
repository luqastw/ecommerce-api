"""
Cart Service - Business logic for shopping cart operations.

Responsabilidades:
- Buscar/criar carrinho do usuário
- Adicionar produtos ao carrinho (com validação de estoque)
- Atualizar quantidades
- Remover itens
- Limpar carrinho
- Calcular totais
"""

from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException, status
from decimal import Decimal
from typing import Optional

from src.models.cart import Cart, CartItem
from src.models.product import Product
from src.schemas.cart import CartItemCreate, CartItemUpdate


class CartService:
    """
    Service para operações do carrinho de compras.

    Todos os métodos são @staticmethod pois não precisam de instância.
    Isso facilita o uso: CartService.add_item(...) sem criar objeto.
    """

    @staticmethod
    def get_or_create_cart(db: Session, user_id: int) -> Cart:
        """
        Busca o carrinho do usuário ou cria um novo se não existir.

        Regra de negócio:
        - 1 usuário = 1 carrinho (garantido por unique constraint no DB)
        - Se carrinho não existe, cria automaticamente
        - Carrinho persiste entre sessões (não expira)

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário

        Returns:
            Cart: Carrinho do usuário (existente ou recém-criado)

        Exemplo:
            cart = CartService.get_or_create_cart(db, user_id=5)
            # Sempre retorna um carrinho válido
        """

        cart = db.query(Cart).filter(Cart.user_id == user_id).first()

        if cart:
            return cart

        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

        return cart

    @staticmethod
    def add_item(db: Session, user_id: int, item_data: CartItemCreate) -> CartItem:
        """
        Adiciona produto ao carrinho com validações completas.

        Fluxo:
        1. Validar se produto existe e está ativo
        2. Validar se tem estoque suficiente
        3. Buscar/criar carrinho do usuário
        4. Verificar se produto já está no carrinho
        5a. Se já existe → aumentar quantidade (validar estoque novamente)
        5b. Se não existe → criar novo item

        Args:
            db: Sessão do banco
            user_id: ID do usuário
            item_data: Dados do item (product_id, quantity)

        Returns:
            CartItem: Item adicionado/atualizado

        Raises:
            HTTPException 404: Produto não encontrado ou inativo
            HTTPException 400: Estoque insuficiente

        Exemplo:
            item_data = CartItemCreate(product_id=10, quantity=2)
            item = CartService.add_item(db, user_id=5, item_data=item_data)
        """

        product = (
            db.query(Product)
            .filter(Product.id == item_data.product_id, Product.is_active == True)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto de ID {item_data.product_id} não encontrado ou inativo.",
            )

        if product.stock < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estoque insuficiente. Disponível: {product.stock}. Solicitado: {item_data.quantity}",
            )

        cart = CartService.get_or_create_cart(db, user_id)

        existing_item = (
            db.query(CartItem)
            .filter(
                CartItem.cart_id == cart.id, CartItem.product_id == item_data.product_id
            )
            .first()
        )

        if existing_item:
            new_quantity = existing_item.quantity + item_data.quantity

            if product.stock < new_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Estoque insuficiente. Você tem: {existing_item.quantity}. Disponível: {product.stock}.",
                )

            existing_item.quantity = new_quantity
            db.commit()
            db.refresh(existing_item)

            return existing_item

        else:
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price_at_add=product.price,
            )

            db.add(cart_item)
            db.commit()
            db.refresh(cart_item)

            return cart_item

    @staticmethod
    def update_item_quantity(
        db: Session, user_id: int, item_id: int, update_data: CartItemUpdate
    ) -> CartItem:
        """
        Atualiza quantidade de um item do carrinho.

        Validações:
        - Item pertence ao usuário (segurança)
        - Estoque suficiente para nova quantidade

        Args:
            db: Sessão do banco
            user_id: ID do usuário
            item_id: ID do item no carrinho
            update_data: Nova quantidade

        Returns:
            CartItem: Item atualizado

        Raises:
            HTTPException 404: Item não encontrado no carrinho do usuário
            HTTPException 400: Estoque insuficiente
        """

        cart_item = (
            db.query(CartItem)
            .join(Cart)
            .filter(CartItem.id == item_id, Cart.user_id == user_id)
            .first()
        )

        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado no seu carrinho.",
            )

        product = db.query(Product).filter(Product.id == cart_item.product_id).first()

        if product.stock < update_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estoque insuficiente. Disponível: {product.stock}",
            )

        cart_item.quantity = update_data.quantity
        db.commit()
        db.refresh(cart_item)

        return cart_item

    @staticmethod
    def remove_item(db: Session, user_id: int, item_id: int) -> None:
        """
        Remove item do carrinho.

        Args:
            db: Sessão do banco
            user_id: ID do usuário
            item_id: ID do item a remover

        Raises:
            HTTPException 404: Item não encontrado no carrinho do usuário
        """

        cart_item = (
            db.query(CartItem)
            .join(Cart)
            .filter(CartItem.id == item_id, Cart.user_id == user_id)
            .first()
        )

        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado no carrinho.",
            )

        db.delete(cart_item)
        db.commit()

    @staticmethod
    def clear_cart(db: Session, user_id: int) -> None:
        """
        Remove todos os itens do carrinho.

        Útil para:
        - Após finalizar compra
        - Botão "Limpar carrinho" na UI

        Args:
            db: Sessão do banco
            user_id: ID do usuário
        """

        cart = db.query(Cart).filter(Cart.user_id == user_id).first()

        if cart:
            db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
            db.commit()

    @staticmethod
    def get_cart_with_details(db: Session, user_id: int) -> Optional[Cart]:
        """
        Busca carrinho com todos os detalhes usando eager loading.

        Evita problema N+1:
        - SEM joinedload: 1 query para cart + N queries para items + N queries para products
        - COM joinedload: 1 query com JOINs traz tudo de uma vez

        Args:
            db: Sessão do banco
            user_id: ID do usuário

        Returns:
            Cart | None: Carrinho com items e products carregados, ou None
        """

        cart = (
            db.query(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.product))
            .filter(Cart.user_id == user_id)
            .first()
        )

        return cart

    @staticmethod
    def calculate_totals(cart: Cart) -> tuple[int, Decimal]:
        """
        Calcula total de itens e preço total do carrinho.

        Args:
            cart: Carrinho com items carregados (use get_cart_with_details)

        Returns:
            tuple: (total_items, total_price)

        Exemplo:
            cart = CartService.get_cart_with_details(db, user_id)
            total_items, total_price = CartService.calculate_totals(cart)
            # total_items = 5 (2 notebooks + 3 mouses)
            # total_price = Decimal('7150.00')
        """

        if not cart or not cart.items:
            return 0, Decimal("0.00")

        total_items = sum(item.quantity for item in cart.items)

        total_price = sum(
            Decimal(str(item.price_at_add)) * item.quantity for item in cart.items
        )

        return total_items, total_price
