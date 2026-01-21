"""
Pydantic schemas para a validação de dados relacionados a usuários.
"""

from dataclasses import field
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


# BASE SCHEMAS


class UserBase(BaseModel):
    """
    Schema base com campos em comuns para todos os schemas de usuário.
    """

    email: EmailStr = Field(description="Email válido do usuário.")
    username: str = Field(
        min_length=5, max_length=50, description="Nome de usuário (5-50 caracteres)."
    )


# INPUT SCHEMAS (Request)


class UserCreate(BaseModel):
    """
    Schema para a criação de usuário (POST /auth/register).

    Campos:
    - email: Validando como email válido.
    - username: 5-50 caracteres.
    - password: 8-16 caracteres, somente o hashed será salvo no banco de dados.

    Exemplo:
    {
          "email": "user@example.com",
          "username": "johndoe",
          "password": "senha_segura_123"
    }
    """

    email: EmailStr
    username: str = Field(
        min_length=5,
        max_length=50,
        description="Nome de usuário (mínimo 5 caracteres.)",
    )
    password: str = Field(
        min_length=8, max_length=16, description="Senha (mínimo 8 caracteres)"
    )


class UserLogin(BaseModel):
    """
    Schema para login de usuário (POST /auth/login).

    Campos:
    - email: Email do usuário.
    - password: Senha em texto plano (será verificada contra hash).

    Exemplo:
        {
            "email": "user@example.com",
            "password": "senha_segura_123"
        }
    """

    email: EmailStr = Field(description="Email do usuário.")
    password: str = Field(description="Senha do usuário.")


class UserUpdate(BaseModel):
    """
    Schema para atualização de usuário (PATCH auth/me).

    Todos os campos são opcionais (permite atualização parcial).

    Exemplo:
        {
            "username": "novo_username"
        }
    """

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=5, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=16)


# OUTPUT SCHEMAS (Response)


class UserResponse(UserBase):
    """
    Schema para retornar dados de usuário (response da API).

    NUNCA inclui hashed_password (segurança).

    Campos:
    - id
    - email
    - username
    - is_active
    - is_superuser
    - created_at
    - updated_at

    Exemplo:
        {
            "id": 1,
            "email": "user@example.com",
            "username": "johndoe",
            "is_active": true,
            "is_superuser": false,
            "created_at": "2024-01-18T10:30:00Z",
            "updated_at": "2024-01-18T10:30:00Z"
        }
    """

    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """
    Schema para resposta de autenticação (login bem-sucedido).

    Exemplo:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
    """

    acess_token: str = Field(description="JWT token para autenticação.")
    token_type: str = Field(default="bearer", description="Tipo do token.")
