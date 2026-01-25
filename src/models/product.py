"""
Product model - represents products table in database.
"""

from sqlalchemy import Column, String, Text, Numeric, Integer, Boolean, Enum as SQLEnum
from src.db.base import BaseModel
from src.models.enums import ProductCategory
