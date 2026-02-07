import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
from typing import List

from src.core.config import settings
from src.models.product import Product
from src.models.order import Order

groq_client = Groq(api_key=settings.GROQ_API_KEY)
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


class AIService:

    CHAT_MODEL = "llama-3.3-70b-versatile"

    @staticmethod
    def generate_product_embedding(product: Product) -> np.ndarray:
        text = f"""
        {product.name}
        {product.description or ""}
        Categoria: {product.category.value}
        Preço: R$ {product.price}
        """.strip()

        embedding = embedding_model.encode(text)

        return embedding

    @staticmethod
    def search_similar_products(db: Session, query: str, limit: int = 5) -> List[dict]:
        """Busca semântica: vetoriza query → compara com produtos → retorna mais similares."""
        query_embedding = embedding_model.encode(query)

        products = db.query(Product).filter(Product.is_active == True).all()

        if not products:
            return []

        similarities = []

        for product in products:
            product_embedding = AIService.generate_product_embedding(product)

            similarity = cosine_similarity(
                query_embedding.reshape(1, -1), product_embedding.reshape(1, -1)
            )[0][0]

            similarities.append({"product": product, "similarity": float(similarity)})

        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return similarities[:limit]

    @staticmethod
    def get_personalized_recommendations(
        db: Session, user_id: int, limit: int = 5
    ) -> List[Product]:
        """Recomenda produtos da categoria mais comprada pelo usuário."""
        orders = db.query(Order).filter(Order.user_id == user_id).all()

        if not orders:
            return (
                db.query(Product)
                .filter(Product.is_active == True)
                .order_by(Product.id.desc())
                .limit(limit)
                .all()
            )

        purchased_ids = set()
        categories = []

        for order in orders:
            for item in order.items:
                if item.product_id:
                    purchased_ids.add(item.product_id)
                    if item.product:
                        categories.append(item.product.category)

        if categories:
            favorite_category = max(set(categories), key=categories.count)

            recommendations = (
                db.query(Product)
                .filter(
                    Product.is_active == True,
                    Product.category == favorite_category,
                    ~Product.id.in_(purchased_ids),
                )
                .limit(limit)
                .all()
            )

            return recommendations

        return []

    @staticmethod
    def chat_about_products(db: Session, user_message: str, user_id: int = None) -> str:
        """Chat com RAG: busca produtos relevantes → injeta como contexto → LLM responde."""
        relevant_products = AIService.search_similar_products(db, user_message, limit=3)

        context = "Produtos disponíveis:\n\n"

        for i, item in enumerate(relevant_products, 1):
            product = item["product"]
            context += f"{i}. {product.name}\n"
            context += f"   Categoria: {product.category.value}\n"
            context += f"   Preço: R$ {product.price}\n"
            if product.description:
                context += f"   Descrição: {product.description}\n"
            context += f"   Estoque: {product.stock} unidades\n\n"

        response = groq_client.chat.completions.create(
            model=AIService.CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """Você é um assistente de vendas de um e-commerce brasileiro.
                    Seja prestativo, amigável e objetivo.
                    Recomende produtos baseado APENAS no catálogo fornecido.
                    Sempre mencione preço em reais (R$) e características.
                    Se não houver produtos relevantes, seja honesto.""",
                },
                {
                    "role": "user",
                    "content": f"Contexto:\n{context}\n\nPergunta: {user_message}",
                },
            ],
            temperature=0.7,
            max_tokens=500,
        )

        return response.choices[0].message.content
