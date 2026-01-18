"""
User model - represents users table in database.
"""

from sqlalchemy import BooleanClauseList, Column, String, Boolean, null, true
from sqlalchemy.sql.traversals import _flatten_clauseelement
from src.db.base import BaseModel


class User(BaseModel):
    """
    Modelo de usuário no sistema.

    Tabela: users

    Campos herdados de BaseModel:
    - id: int (PK, auto-incrementado)
    - created_at: datetime (automático)
    - updated_at: datetime (automático)

    Campos específicos:
    - email: string único (usado pra login)
    - username: string único (nome de exibição)
    - hashed_password: string (senha com hash bcrypt)
    - is_active: bool (usuário ativo/desativado)
    - is_superuser: bool (admin do sistema)
    """

    __tablename__ = "users"

    email = Column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
        comment="Email do usuário (usado para autenticação).",
    )

    username = Column(
        String, unique=True, index=True, nullable=True, comment="Nome de usuário único."
    )

    hashed_password = Column(String, nullable=False, comment="Senha com bcrypt.")

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Indica se o usuário está ativo no sistema.",
    )

    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indica se o usuário tem privilégios de administrador.",
    )

    def __repr__(self) -> str:
        """
        Representação em string pra debugging.
        """

        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
