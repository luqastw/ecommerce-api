from enum import Enum


class ProductCategory(str, Enum):
    ELETRONICOS = "eletronicos"
    ROUPAS = "roupas"
    LIVROS = "livros"
    ALIMENTOS = "alimentos"
    ESPORTES = "esportes"
    CASA = "casa"
    BELEZA = "beleza"
    BRINQUEDOS = "brinquedos"


class OrderStatus(str, Enum):
    """Fluxo: PENDING → PAID → SHIPPED → DELIVERED (ou PENDING → CANCELLED)."""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
