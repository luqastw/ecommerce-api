"""
Alembic environment configuration.
"""

import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

root_path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_path))

from src.core.config import settings
from src.db.base import Base

from src.models.user import User
from src.models.product import Product
from src.models.cart import Cart, CartItem

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Modo offline: gera SQL sem conectar no banco.
    Útil para gerar scripts SQL para review ou deploy manual.

    Uso:
        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Modo online: conecta no banco e aplica as migrations.
    Uso normal:
        alembic upgrade head
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
