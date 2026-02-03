"""
Rotas de produtos - CRUD com soft delete.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Query
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
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: ProductCategory | None = Query(default=None),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    search: str | None = Query(default=None, min_length=1),
) -> List[ProductResponse]:
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
    """Soft delete - preserva histórico de pedidos."""
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
