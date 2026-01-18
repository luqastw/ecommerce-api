"""
Security utilities: password hashing, JWT token creation/verification.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash.

    Args:
        plain_password: Senha fornecida pelo usuário (texto plano)
        hashed_password: Hash armazenado no banco de dados

    Returns:
        True se a senha estiver correta, False caso contrário

    Exemplo:
        >>> hashed = get_password_hash("minha_senha")
        >>> verify_password("minha_senha", hashed)
        True
        >>> verify_password("senha_errada", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera um hash bcrypt da senha.

    Args:
        password: Senha em texto plano

    Returns:
        Hash bcrypt da senha

    Nota:
        Nunca armazene senhas em texto plano!
        O hash é unidirecional (não pode ser revertido).

    Exemplo:
        >>> hash1 = get_password_hash("senha123")
        >>> hash2 = get_password_hash("senha123")
        >>> hash1 != hash2  # Hashes diferentes (bcrypt usa salt aleatório)
        True
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria um JWT (JSON Web Token) para autenticação.

    Args:
        data: Dados a serem codificados no token (ex: {"sub": "user_id"})
        expires_delta: Tempo até expiração. Se None, usa padrão de 30 min

    Returns:
        Token JWT codificado como string

    Estrutura do JWT:
        Header: {"alg": "HS256", "typ": "JWT"}
        Payload: {data + "exp": timestamp}
        Signature: HMAC usando SECRET_KEY

    Exemplo:
        >>> from datetime import timedelta
        >>> token = create_access_token({"sub": "123"}, timedelta(hours=1))
        >>> # Token pode ser enviado ao cliente e validado depois
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica e valida um JWT.

    Args:
        token: Token JWT a ser decodificado

    Returns:
        Payload do token se válido, None se inválido/expirado

    Validações automáticas:
        - Assinatura (garante que não foi adulterado)
        - Expiração (verifica timestamp "exp")
        - Formato (estrutura válida do JWT)

    Exemplo:
        >>> token = create_access_token({"sub": "123"})
        >>> payload = decode_access_token(token)
        >>> payload["sub"]
        '123'
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
