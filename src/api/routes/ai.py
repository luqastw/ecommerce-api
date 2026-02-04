from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_user
from src.models.user import User
from src.services.ai_service import AIService
from src.schemas.ai import (
    RecommendationResponse,
    SearchResultItem,
    SearchResponse,
    ChatRequest,
    ChatResponse,
)

router = APIRouter()


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Busca semântica de produtos.",
    description="Encontra produtos por similaridade de significado, sem se limitar a palavras-chave.",
)
def semantic_search(
    q: str = Query(..., min_length=5, max_length=200),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> SearchResponse:
    results = AIService.search_similar_products(db, q, limit)

    items = [
        SearchResultItem(product=item["product"], similarity=item["similarity"])
        for item in results
    ]

    return SearchResponse(query=q, total=len(items), results=items)


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Conversar e perguntar para a IA do sistema.",
    description="Utiliza RAG para buscar por produtos utilizando IA.",
)
def chat_with_ai(body: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    ai_response = AIService.chat_about_products(db, body.message)

    return ChatResponse(user_message=body.message, ai_response=ai_response)


@router.get(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Mostra recomendações de produtos.",
    description="Se baseia nos produtos que o cliente já comprou e mostra recomendações.",
)
def get_recommendations(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    recommendations = AIService.get_personalized_recommendations(
        db, current_user.id, limit
    )

    return RecommendationResponse(recommendations=recommendations)
