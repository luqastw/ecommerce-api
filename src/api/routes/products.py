"""
Product routes - CRUD operations for products.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy import Column
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_admin
from src.models.product import Product
from src.models.enums import ProductCategory
from src.models.user import User
from src.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter()


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar produto.",
    description="Cria novo produto. Somente administradores.",
)
def create_product(
    product_data: ProductCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ProductResponse:
    """
    Cria um novo produto.

    Requer:
        - Autenticação (JWT token)
        - Permissão de administrador (is_superuser=True)

    Args:
        product_data: Dados do novo produto
        current_admin: Usuário admin (via dependency)
        db: Sessão do banco

    Returns:
        ProductResponse: Produto criado
    """

    db_product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        category=product_data.category,
        stock=product_data.stock,
        image_url=product_data.image_url,
        is_active=True,
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return ProductResponse.model_validate(db_product)


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="Listar produtos.",
    description="Lista produtos com filtro e paginação. Acesso público.",
)
def list_products(
    db: Session = Depends(get_db),
    limit: int = Query(
        default=10, ge=1, le=100, description="Quantidade de produtos por página."
    ),
    offset: int = Query(default=0, ge=0, description="Número de produtos a pular."),
    category: ProductCategory | None = Query(
        default=None, description="Filtrar por categoria."
    ),
    min_price: float | None = Query(
        default=None, ge=0, description="Filtrar por preço mínimo."
    ),
    max_price: float | None = Query(
        default=None, ge=0, description="Filtrar por preço máximo."
    ),
    search: str | None = Query(
        default=None, min_length=1, description="Buscar por nome do produto."
    ),
) -> List[ProductResponse]:
    """
    Lista produtos com paginação e filtros.

    Acesso público (não requer autenticação).

    Query Parameters:
        - limit: Produtos por página (1-100, default: 10)
        - offset: Produtos a pular (default: 0)
        - category: Filtrar por categoria
        - min_price: Preço mínimo
        - max_price: Preço máximo
        - search: Buscar no nome do produto

    Returns:
        Lista de produtos

    Exemplos:
        GET /products?limit=20&offset=0
        GET /products?category=eletronicos&min_price=1000
        GET /products?search=notebook&limit=5
    """

    query = db.query(Product).filter(Product.is_active == True)

    if category:
        query = query.filter(Product.category == category)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    query = query.order_by(Product.id)

    products = query.offset(offset).limit(limit).all()

    return [ProductResponse.model_validate(p) for p in products]


@router.get(
    "/{product.id}",
    response_model=ProductResponse,
    summary="Obter detalhes de um produto.",
    description="Retorna detalhes de um produto específico. Acesso público.",
)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductResponse:
    """
    Retorna detalhes de um produto específico.

    Acesso público (não requer autenticação).

    Args:
        product_id: ID do produto
        db: Sessão do banco

    Returns:
        ProductResponse: Dados do produto

    Raises:
        HTTPException 404: Produto não encontrado
    """

    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produto com ID {product.id} não encontrado.",
        )

    return ProductResponse.model_validate(product)


@router.patch(
    "/{product.id}",
    response_model=ProductResponse,
    summary="Atualizar produto.",
    description="Atualiza dados de um produto. Somente administradores.",
)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ProductResponse:
    """
    Atualiza dados de um produto.

    Permite atualização parcial (PATCH).

    Requer:
        - Autenticação (JWT token)
        - Permissão de administrador (is_superuser=True)

    Args:
        product_id: ID do produto a atualizar
        product_update: Dados a serem atualizados
        current_admin: Usuário admin (via dependency)
        db: Sessão do banco

    Returns:
        ProductResponse: Produto atualizado

    Raises:
        HTTPException 404: Produto não encontrado
    """

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produto com ID {product_id} não encontrado.",
        )

    update_data = product_update.model_dump(exclude_unset=True)

    if not update_data:
        return ProductResponse.model_validate(product)

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return ProductResponse.model_validate(product)


@router.delete(
    "/{product.id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar produto.",
    description="Desativa um produto (soft delete). Somente administradores.",
)
def delete_product(
    product_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Desativa um produto (soft delete).

    O produto não é deletado do banco, apenas marcado como inativo.
    Isso preserva histórico de pedidos e relatórios.

    Requer:
        - Autenticação (JWT token)
        - Permissão de administrador (is_superuser=True)

    Args:
        product_id: ID do produto a desativar
        current_admin: Usuário admin (via dependency)
        db: Sessão do banco

    Returns:
        204 No Content (sem body)

    Raises:
        HTTPException 404: Produto não encontrado
    """

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produto com ID {product_id} não encontrado.",
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Produto já desativado."
        )

    product.is_active = False
    db.commit()

    return None
