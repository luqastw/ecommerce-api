"""
SQLAlchemy declarative base and common model functionality.
"""

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class BaseModel(Base):
    """
    Modelo base abstrato com campos comuns para todas as tabelas.

    Fornece automaticamente:
    - id: Chave primária auto-incrementada.
    - created_at: Timestamp de criação (automático).
    - updated_at: Timestamp de última atualização (também automático).

    Uso:
        class User(BaseModel):
            __tablename__ = "users"
            email = Column(String)
    """

    __abstract__ = True

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Identificador único de registro.",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Data e hora da criação do registro.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Data e hora da última atualização do registro.",
    )

    def __repr__(self) -> str:
        """
        Representação em string do objeto.

        Exemplo:
            >> user = User(id=1, email='test1@test.com')
            >> print(user)
            <User(id=1)>
        """

        return f"<{self.__class__.__name__}(id={self.id})>"
