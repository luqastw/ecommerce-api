"""
Initialize database: create all tables.
"""

from src.db.base import Base
from src.db.session import engine
from src.models.user import User


def init_db() -> None:
    """
    Cria todas as tabelas no banco de dados.

    IMPORTANTE: Isto é apenas para desenvolvimento/testes.
    Em produção, use Alembic migrations.
    """

    print("Creating tables in database...")
    Base.metadata.create_all(bind=engine)
    print("All tables created.")


if __name__ == "__main__":
    init_db()
