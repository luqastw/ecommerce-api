"""
Testes de integração para rotas do carrinho.

Testamos:
- Obter carrinho
- Adicionar itens
- Atualizar quantidades
- Remover itens
- Limpar carrinho
"""

import pytest


class TestGetCart:
    """Testes para GET /cart/."""

    def test_get_cart_empty(self, client, auth_headers):
        """Deve retornar carrinho vazio."""
        response = client.get("/cart/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_items"] == 0
        assert data["total_price"] == "0.00"

    def test_get_cart_with_items(self, client, auth_headers, test_product):
        """Deve retornar carrinho com itens."""
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )

        response = client.get("/cart/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total_items"] == 2
        assert data["items"][0]["product_name"] == test_product.name

    def test_get_cart_unauthorized(self, client):
        """Deve rejeitar requisição sem autenticação."""
        response = client.get("/cart/")

        assert response.status_code == 403


class TestGetCartSummary:
    """Testes para GET /cart/summary."""

    def test_get_cart_summary_empty(self, client, auth_headers):
        """Deve retornar resumo zerado para carrinho vazio."""
        response = client.get("/cart/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 0
        assert data["total_price"] == "0"

    def test_get_cart_summary_with_items(self, client, auth_headers, test_product):
        """Deve retornar resumo correto."""
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 3},
        )

        response = client.get("/cart/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 3


class TestAddItemToCart:
    """Testes para POST /cart/items."""

    def test_add_item_success(self, client, auth_headers, test_product):
        """Deve adicionar item ao carrinho."""
        response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == test_product.id
        assert data["quantity"] == 2
        assert data["product_name"] == test_product.name

    def test_add_item_default_quantity(self, client, auth_headers, test_product):
        """Quantidade padrão deve ser 1."""
        response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id},
        )

        assert response.status_code == 201
        assert response.json()["quantity"] == 1

    def test_add_item_increases_quantity(self, client, auth_headers, test_product):
        """Adicionar produto existente deve aumentar quantidade."""
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )

        response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 3},
        )

        assert response.status_code == 201
        assert response.json()["quantity"] == 5

    def test_add_item_product_not_found(self, client, auth_headers):
        """Deve rejeitar produto inexistente."""
        response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": 99999, "quantity": 1},
        )

        assert response.status_code == 404

    def test_add_item_insufficient_stock(self, client, auth_headers, test_product):
        """Deve rejeitar se estoque for insuficiente."""
        response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 100},
        )

        assert response.status_code == 400
        assert "Estoque insuficiente" in response.json()["detail"]

    def test_add_item_invalid_quantity(self, client, auth_headers, test_product):
        """Deve rejeitar quantidade inválida."""
        response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 0},
        )

        assert response.status_code == 422

    def test_add_item_quantity_exceeds_max(self, client, auth_headers, test_product):
        """Deve rejeitar quantidade acima do máximo."""
        response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 101},
        )

        assert response.status_code == 422

    def test_add_item_unauthorized(self, client, test_product):
        """Deve rejeitar sem autenticação."""
        response = client.post(
            "/cart/items",
            json={"product_id": test_product.id, "quantity": 1},
        )

        assert response.status_code == 403


class TestUpdateCartItem:
    """Testes para PATCH /cart/items/{item_id}."""

    def test_update_item_success(self, client, auth_headers, test_product):
        """Deve atualizar quantidade do item."""
        add_response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )
        item_id = add_response.json()["id"]

        response = client.patch(
            f"/cart/items/{item_id}",
            headers=auth_headers,
            json={"quantity": 5},
        )

        assert response.status_code == 200
        assert response.json()["quantity"] == 5

    def test_update_item_not_found(self, client, auth_headers):
        """Deve retornar 404 se item não existir."""
        response = client.patch(
            "/cart/items/99999",
            headers=auth_headers,
            json={"quantity": 5},
        )

        assert response.status_code == 404

    def test_update_item_insufficient_stock(self, client, auth_headers, test_product):
        """Deve rejeitar se estoque for insuficiente."""
        add_response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )
        item_id = add_response.json()["id"]

        response = client.patch(
            f"/cart/items/{item_id}",
            headers=auth_headers,
            json={"quantity": 100},
        )

        assert response.status_code == 400


class TestRemoveCartItem:
    """Testes para DELETE /cart/items/{item_id}."""

    def test_remove_item_success(self, client, auth_headers, test_product):
        """Deve remover item do carrinho."""
        add_response = client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )
        item_id = add_response.json()["id"]

        response = client.delete(f"/cart/items/{item_id}", headers=auth_headers)

        assert response.status_code == 204

        cart_response = client.get("/cart/", headers=auth_headers)
        assert len(cart_response.json()["items"]) == 0

    def test_remove_item_not_found(self, client, auth_headers):
        """Deve retornar 404 se item não existir."""
        response = client.delete("/cart/items/99999", headers=auth_headers)

        assert response.status_code == 404


class TestClearCart:
    """Testes para DELETE /cart/."""

    def test_clear_cart_success(self, client, auth_headers, test_product):
        """Deve limpar todos os itens do carrinho."""
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_product.id, "quantity": 2},
        )

        response = client.delete("/cart/", headers=auth_headers)

        assert response.status_code == 204

        cart_response = client.get("/cart/", headers=auth_headers)
        assert len(cart_response.json()["items"]) == 0

    def test_clear_cart_already_empty(self, client, auth_headers):
        """Deve funcionar mesmo com carrinho vazio."""
        response = client.delete("/cart/", headers=auth_headers)

        assert response.status_code == 204
