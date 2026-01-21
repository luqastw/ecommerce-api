"""
User management routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_user
from src.models.user import User
from src.schemas.user import UserResponse

router = APIRouter()
