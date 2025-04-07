from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    picture = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ingredients = relationship("Ingredient", back_populates="user", cascade="all, delete-orphan")
    saved_recipes = relationship("SavedRecipe", back_populates="user", cascade="all, delete-orphan")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    quantity = Column(Float, default=1.0)
    unit = Column(String, default="pieces")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="ingredients")
    
    # Unique constraint for user_id + name combination
    __table_args__ = (
        # UniqueConstraint('user_id', 'name', name='uix_user_ingredient'),
    )


class SavedRecipe(Base):
    __tablename__ = "saved_recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_name = Column(String, index=True)
    ingredients_required = Column(JSON)  # List of ingredients with quantities
    missing_ingredients = Column(JSON, default=[])  # List of missing ingredients
    instructions = Column(JSON)  # List of cooking steps
    difficulty_level = Column(String, nullable=True)
    cooking_time = Column(String, nullable=True)
    servings = Column(Integer, default=2)
    notes = Column(Text, nullable=True)  # User notes about the recipe
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="saved_recipes")
