from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_user
from src.models.user import User
from src.schemas.user import UserResponse, UserUpdate
from src.core.security import get_password_hash


router = APIRouter()


@router.get(
    "/me", response_model=UserResponse, summary="Obter dados do usuário autenticado"
)
def get_current_user_data(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserUpdate, summary="Atualizar perfil do usuário.")
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    update_data = user_update.model_dump(exclude_unset=True)

    if not update_data:
        return UserResponse.model_validate(current_user)

    if "email" in update_data:
        existing_email = (
            db.query(User)
            .filter(User.email == update_data["email"], User.id != current_user.id)
            .first()
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email já em uso."
            )

    if "username" in update_data:
        existing_username = (
            db.query(User)
            .filter(
                User.username == update_data["username"], User.id != current_user.id
            )
            .first()
        )

        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User já em uso."
            )

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.delete(
    "/me", status_code=status.HTTP_204_NO_CONTENT, summary="Desativar conta de usuário."
)
def deactivate_account(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Soft delete - admin pode reativar."""
    current_user.is_active = False
    db.commit()

    return None
