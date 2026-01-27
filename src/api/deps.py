"""
FastAPI dependencies for dependency injection.
"""

from typing import Generator
from fastapi import status, HTTPException, Depends
from fastapi import security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.models.user import User
from src.core.security import decode_access_token

security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency que fornece uma sessão do banco de dados.

    Uso:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users

    Yields:
        Session: Sessão SQLAlchemy.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency que autentica o usuário via JWT Token.

    Extrai o token do header Authorization, decodifica, busca o usuário no banco e retorna.

    Lança HTTPException 401 se:
    - Token inválido.
    - Token expirado.
    - Usuário não encontrado.
    - Usuário inativo.

    Args:
        credentials: JWT Token extraído do header.
        db: Sessão do banco de dados.

    Returns:
        User: Usuário autenticado.

    Raises:
        HTTPException: 401 se autenticação falhar.

    Uso:
        @app.get("/users/me")
        def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """

    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency que verifica se o usuário autenticado é admin.

    Usa get_current_user para autenticar, depois verifica is_superuser.

    Args:
        current_user: Usuário autenticado (via get_current_user)

    Returns:
        User: Usuário admin

    Raises:
        HTTPException 403: Se usuário não for admin

    Uso:
        @app.post("/products")
        def create_product(current_admin: User = Depends(get_current_admin)):
            # Só admins chegam aqui!
    """

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão. Apenas administradores podem acessar essa função.",
        )

    return current_user
