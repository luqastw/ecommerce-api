"""
User management routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_user
from src.models.user import User
from src.schemas.user import UserResponse


router = APIRouter()


@router.get(
    "/me", response_model=UserResponse, summary="Obter dados do usuário autenticado"
)
def get_current_user_data(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Retorna dados do usuário autenticado.

    Requer:
        - Header: Authorization: Bearer <token>

    Returns:
        UserResponse: Dados do usuário (sem senha)
    """
    return UserResponse.model_validate(current_user)
