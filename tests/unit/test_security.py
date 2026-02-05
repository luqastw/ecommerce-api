"""
Testes unitários para src/core/security.py

Testamos:
- Hash de senha (criação e verificação)
- JWT (criação e decodificação)
"""

import pytest
from datetime import timedelta

from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    """Testes para hash e verificação de senha."""

    def test_get_password_hash_returns_hash(self):
        """Hash deve retornar string diferente da senha original."""
        password = "minha_senha_123"

        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        """Senha correta deve retornar True."""
        password = "senha_secreta"
        hashed = get_password_hash(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_verify_password_incorrect(self):
        """Senha incorreta deve retornar False."""
        password = "senha_correta"
        hashed = get_password_hash(password)

        result = verify_password("senha_errada", hashed)

        assert result is False

    def test_same_password_different_hashes(self):
        """Mesma senha deve gerar hashes diferentes (bcrypt usa salt)."""
        password = "mesma_senha"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password(self):
        """Senha vazia ainda deve gerar hash válido."""
        password = ""

        hashed = get_password_hash(password)

        assert hashed is not None
        assert verify_password(password, hashed) is True

    def test_long_password(self):
        """Senha longa deve funcionar normalmente."""
        password = "a" * 100

        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_special_characters_password(self):
        """Senha com caracteres especiais deve funcionar."""
        password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"

        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True


class TestJWT:
    """Testes para criação e validação de tokens JWT."""

    def test_create_access_token_returns_string(self):
        """Token deve ser uma string não vazia."""
        data = {"sub": "123"}

        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Token válido deve retornar payload com dados originais."""
        user_id = "456"
        data = {"sub": user_id}

        token = create_access_token(data)
        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == user_id

    def test_decode_invalid_token(self):
        """Token inválido deve retornar None."""
        invalid_token = "token.invalido.aqui"

        payload = decode_access_token(invalid_token)

        assert payload is None

    def test_decode_empty_token(self):
        """Token vazio deve retornar None."""
        payload = decode_access_token("")

        assert payload is None

    def test_decode_malformed_token(self):
        """Token mal formado deve retornar None."""
        payload = decode_access_token("not-a-jwt-token")

        assert payload is None

    def test_token_with_custom_expiration(self):
        """Token com expiração customizada deve funcionar."""
        data = {"sub": "789"}
        expires = timedelta(hours=2)

        token = create_access_token(data, expires_delta=expires)
        payload = decode_access_token(token)

        assert payload is not None
        assert "exp" in payload

    def test_token_preserves_additional_data(self):
        """Token deve preservar dados adicionais no payload."""
        data = {"sub": "123", "role": "admin", "name": "John"}

        token = create_access_token(data)
        payload = decode_access_token(token)

        assert payload["sub"] == "123"
        assert payload["role"] == "admin"
        assert payload["name"] == "John"

    def test_token_has_expiration(self):
        """Token deve ter campo de expiração."""
        data = {"sub": "123"}

        token = create_access_token(data)
        payload = decode_access_token(token)

        assert "exp" in payload
