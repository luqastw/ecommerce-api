"""
E-commerce API - Main application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.api.routes import auth, users

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered e-commerce API with intelligent product recommendations",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])


@app.get(
    "/",
    tags=["Health"],
    summary="Health check.",
    description="Verifica se a API está online.",
)
def health_check():
    """
    Health check endpoint.

    Retorna status da API e versão.
    """

    return {
        "status": "online",
        "message": f"{settings.APP_NAME} is running.",
        "version": settings.VERSION,
    }


@app.on_event("startup")
async def startup_event():
    """
    Executado quando a aplicação inicia.
    Útil para inicializar conexões, verificar DB, etc.
    """
    print(f"🚀 {settings.APP_NAME} v{settings.VERSION} started!")
    print(f"📚 Documentation: http://localhost:8000/docs")
    print(f"🔒 Debug mode: {settings.DEBUG}")
