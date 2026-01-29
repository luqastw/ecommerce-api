"""
Enums used across models.
"""

from enum import Enum


class ProductCategory(str, Enum):
    """
    Categorias de produtos disponíveis.

    Herda de str para ser serializável em JSON.
    """

    ELETRONICOS = "eletronicos"
    ROUPAS = "roupas"
    LIVROS = "livros"
    ALIMENTOS = "alimentos"
    ESPORTES = "esportes"
    CASA = "casa"
    BELEZA = "beleza"
    BRINQUEDOS = "brinquedos"


class OrderStatus(str, Enum):
    """
    Status possíveis de um pedido.

    Fluxo típico:
    PENDING -> PAID -> SHIPPED -> DELIVERED

    Pode também:
    PENDING -> CANCELLED
    """

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
