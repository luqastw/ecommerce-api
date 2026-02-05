"""
Testes unitários para src/services/cart_service.py

Testamos:
- Criação de carrinho
- Adicionar itens (validação de estoque)
- Atualizar quantidades
- Remover itens
- Cálculo de totais
"""

import pytest
from decimal import Decimal
from fastapi import HTTPException

from src.services.cart_service import CartService
from src.schemas.cart import CartItemCreate, CartItemUpdate
from src.models.cart import Cart, CartItem
from src.models.product import Product
from src.models.enums import ProductCategory


class TestGetOrCreateCart:
    """Testes para buscar/criar carrinho."""

    def test_create_new_cart(self, db_session, test_user):
        """Deve criar carrinho se não existir."""
        cart = CartService.get_or_create_cart(db_session, test_user.id)

        assert cart is not None
        assert cart.user_id == test_user.id

    def test_return_existing_cart(self, db_session, test_user):
        """Deve retornar carrinho existente."""
        cart1 = CartService.get_or_create_cart(db_session, test_user.id)
        cart2 = CartService.get_or_create_cart(db_session, test_user.id)

        assert cart1.id == cart2.id

    def test_different_users_different_carts(self, db_session, test_user, test_admin):
        """Usuários diferentes devem ter carrinhos diferentes."""
        cart_user = CartService.get_or_create_cart(db_session, test_user.id)
        cart_admin = CartService.get_or_create_cart(db_session, test_admin.id)

        assert cart_user.id != cart_admin.id


class TestAddItem:
    """Testes para adicionar item ao carrinho."""

    def test_add_item_success(self, db_session, test_user, test_product):
        """Deve adicionar item ao carrinho."""
        item_data = CartItemCreate(product_id=test_product.id, quantity=2)

        cart_item = CartService.add_item(db_session, test_user.id, item_data)

        assert cart_item is not None
        assert cart_item.product_id == test_product.id
        assert cart_item.quantity == 2
        assert cart_item.price_at_add == test_product.price

    def test_add_item_creates_cart_if_not_exists(self, db_session, test_user, test_product):
        """Deve criar carrinho automaticamente se não existir."""
        item_data = CartItemCreate(product_id=test_product.id, quantity=1)

        cart_item = CartService.add_item(db_session, test_user.id, item_data)

        cart = db_session.query(Cart).filter(Cart.user_id == test_user.id).first()
        assert cart is not None
        assert cart_item.cart_id == cart.id

    def test_add_existing_item_increases_quantity(self, db_session, test_user, test_product):
        """Adicionar produto existente deve aumentar quantidade."""
        item_data = CartItemCreate(product_id=test_product.id, quantity=2)

        CartService.add_item(db_session, test_user.id, item_data)
        cart_item = CartService.add_item(db_session, test_user.id, item_data)

        assert cart_item.quantity == 4

    def test_add_item_product_not_found(self, db_session, test_user):
        """Deve lançar erro se produto não existir."""
        item_data = CartItemCreate(product_id=99999, quantity=1)

        with pytest.raises(HTTPException) as exc_info:
            CartService.add_item(db_session, test_user.id, item_data)

        assert exc_info.value.status_code == 404

    def test_add_item_product_inactive(self, db_session, test_user, test_product):
        """Deve lançar erro se produto estiver inativo."""
        test_product.is_active = False
        db_session.commit()

        item_data = CartItemCreate(product_id=test_product.id, quantity=1)

        with pytest.raises(HTTPException) as exc_info:
            CartService.add_item(db_session, test_user.id, item_data)

        assert exc_info.value.status_code == 404

    def test_add_item_insufficient_stock(self, db_session, test_user, test_product):
        """Deve lançar erro se estoque for insuficiente."""
        item_data = CartItemCreate(product_id=test_product.id, quantity=100)

        with pytest.raises(HTTPException) as exc_info:
            CartService.add_item(db_session, test_user.id, item_data)

        assert exc_info.value.status_code == 400
        assert "Estoque insuficiente" in str(exc_info.value.detail)

    def test_add_item_insufficient_stock_when_adding_more(self, db_session, test_user, test_product):
        """Deve lançar erro ao adicionar mais do que o estoque permite."""
        test_product.stock = 5
        db_session.commit()

        item_data = CartItemCreate(product_id=test_product.id, quantity=3)
        CartService.add_item(db_session, test_user.id, item_data)

        with pytest.raises(HTTPException) as exc_info:
            CartService.add_item(db_session, test_user.id, item_data)

        assert exc_info.value.status_code == 400


class TestUpdateItemQuantity:
    """Testes para atualizar quantidade de item."""

    def test_update_quantity_success(self, db_session, test_user, test_product):
        """Deve atualizar quantidade com sucesso."""
        item_data = CartItemCreate(product_id=test_product.id, quantity=2)
        cart_item = CartService.add_item(db_session, test_user.id, item_data)

        update_data = CartItemUpdate(quantity=5)
        updated_item = CartService.update_item_quantity(
            db_session, test_user.id, cart_item.id, update_data
        )

        assert updated_item.quantity == 5

    def test_update_quantity_item_not_found(self, db_session, test_user):
        """Deve lançar erro se item não existir."""
        update_data = CartItemUpdate(quantity=5)

        with pytest.raises(HTTPException) as exc_info:
            CartService.update_item_quantity(
                db_session, test_user.id, 99999, update_data
            )

        assert exc_info.value.status_code == 404

    def test_update_quantity_not_owner(self, db_session, test_user, test_admin, test_product):
        """Deve lançar erro se item não pertencer ao usuário."""
        item_data = CartItemCreate(product_id=test_product.id, quantity=2)
        cart_item = CartService.add_item(db_session, test_user.id, item_data)

        update_data = CartItemUpdate(quantity=5)

        with pytest.raises(HTTPException) as exc_info:
            CartService.update_item_quantity(
                db_session, test_admin.id, cart_item.id, update_data
            )

        assert exc_info.value.status_code == 404

    def test_update_quantity_insufficient_stock(self, db_session, test_user, test_product):
        """Deve lançar erro se estoque for insuficiente."""
        item_data = CartItemCreate(product_id=test_product.id, quantity=2)
        cart_item = CartService.add_item(db_session, test_user.id, item_data)

        update_data = CartItemUpdate(quantity=100)

        with pytest.raises(HTTPException) as exc_info:
            CartService.update_item_quantity(
                db_session, test_user.id, cart_item.id, update_data
            )

        assert exc_info.value.status_code == 400


class TestRemoveItem:
    """Testes para remover item do carrinho."""

    def test_remove_item_success(self, db_session, test_user, test_product):
        """Deve remover item com sucesso."""
        item_data = CartItemCreate(product_id=test_product.id, quantity=2)
        cart_item = CartService.add_item(db_session, test_user.id, item_data)
        item_id = cart_item.id

        CartService.remove_item(db_session, test_user.id, item_id)

        removed_item = db_session.query(CartItem).filter(CartItem.id == item_id).first()
        assert removed_item is None

    def test_remove_item_not_found(self, db_session, test_user):
        """Deve lançar erro se item não existir."""
        with pytest.raises(HTTPException) as exc_info:
            CartService.remove_item(db_session, test_user.id, 99999)

        assert exc_info.value.status_code == 404

    def test_remove_item_not_owner(self, db_session, test_user, test_admin, test_product):
        """Deve lançar erro se item não pertencer ao usuário."""
        item_data = CartItemCreate(product_id=test_product.id, quantity=2)
        cart_item = CartService.add_item(db_session, test_user.id, item_data)

        with pytest.raises(HTTPException) as exc_info:
            CartService.remove_item(db_session, test_admin.id, cart_item.id)

        assert exc_info.value.status_code == 404


class TestClearCart:
    """Testes para limpar carrinho."""

    def test_clear_cart_success(self, db_session, test_user, test_product):
        """Deve limpar todos os itens do carrinho."""
        item_data = CartItemCreate(product_id=test_product.id, quantity=2)
        CartService.add_item(db_session, test_user.id, item_data)

        CartService.clear_cart(db_session, test_user.id)

        cart = db_session.query(Cart).filter(Cart.user_id == test_user.id).first()
        items = db_session.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        assert len(items) == 0

    def test_clear_cart_no_cart(self, db_session, test_user):
        """Deve funcionar mesmo sem carrinho existente."""
        CartService.clear_cart(db_session, test_user.id)


class TestCalculateTotals:
    """Testes para cálculo de totais."""

    def test_calculate_totals_empty_cart(self):
        """Carrinho vazio deve retornar zeros."""
        cart = Cart(user_id=1)
        cart.items = []

        total_items, total_price = CartService.calculate_totals(cart)

        assert total_items == 0
        assert total_price == Decimal("0.00")

    def test_calculate_totals_none_cart(self):
        """Cart None deve retornar zeros."""
        total_items, total_price = CartService.calculate_totals(None)

        assert total_items == 0
        assert total_price == Decimal("0.00")

    def test_calculate_totals_with_items(self, db_session, test_cart_with_items):
        """Deve calcular totais corretamente."""
        cart = CartService.get_cart_with_details(
            db_session, test_cart_with_items.user_id
        )

        total_items, total_price = CartService.calculate_totals(cart)

        assert total_items == 2
        assert total_price == Decimal("7000.00")
