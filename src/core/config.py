"""
Core configuration module.
Carrega variáveis de ambiente e define configurações da aplicação.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Configurações da aplicação usando Pydantic Settings.

    Pydantic Settings automaticamente:
    - Carrega variáveis do arquivo .env
    - Valida tipos de dados
    - Fornece valores padrão
    - Lança erros se variáveis obrigatórias estiverem faltando
    """

    APP_NAME: str = "E-commerce API"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
