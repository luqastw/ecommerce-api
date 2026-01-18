"""
Database session management.
Cria engine SQLAlchemy e SessionLocal para interagir com o banco.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency para FastAPI que fornece uma sessão de banco.

    Uso em rotas:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users

    Como funciona:
        1. Cria uma nova sessão
        2. Injeta na função da rota
        3. Após a requisição, fecha a sessão (finally)

    Isso garante que:
        - Cada request tem sua própria sessão
        - Sessões são sempre fechadas (evita memory leaks)
        - Erros não deixam sessões abertas

    Yields:
        Session: Sessão de banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
