from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from .recipe import MealType, DifficultyLevel

class DietaryRestriction(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_FREE = "nut_free"
    LOW_CARB = "low_carb"
    KETO = "keto"
    PALEO = "paleo"
    HALAL = "halal"
    KOSHER = "kosher"

class CookingSkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class UserPreferencesBase(BaseModel):
    dietary_restrictions: List[DietaryRestriction] = Field(default=[], description="User's dietary restrictions")
    favorite_cuisines: List[str] = Field(default=[], description="Preferred cuisines")
    disliked_ingredients: List[str] = Field(default=[], description="Ingredients the user dislikes")
    preferred_meal_types: List[MealType] = Field(default=[], description="Preferred meal types")
    max_prep_time: Optional[int] = Field(None, description="Maximum preparation time preference in minutes")
    max_cook_time: Optional[int] = Field(None, description="Maximum cooking time preference in minutes")
    preferred_difficulty: List[DifficultyLevel] = Field(default=[], description="Preferred difficulty levels")
    cooking_skill_level: CookingSkillLevel = Field(default=CookingSkillLevel.BEGINNER, description="User's cooking skill level")
    household_size: int = Field(default=1, description="Number of people in household")
    budget_conscious: bool = Field(default=False, description="Whether user prefers budget-friendly recipes")
    health_conscious: bool = Field(default=False, description="Whether user prefers healthy recipes")
    quick_meals_preference: bool = Field(default=False, description="Whether user prefers quick meals")

class UserPreferencesCreate(UserPreferencesBase):
    pass

class UserPreferencesUpdate(BaseModel):
    dietary_restrictions: Optional[List[DietaryRestriction]] = None
    favorite_cuisines: Optional[List[str]] = None
    disliked_ingredients: Optional[List[str]] = None
    preferred_meal_types: Optional[List[MealType]] = None
    max_prep_time: Optional[int] = None
    max_cook_time: Optional[int] = None
    preferred_difficulty: Optional[List[DifficultyLevel]] = None
    cooking_skill_level: Optional[CookingSkillLevel] = None
    household_size: Optional[int] = None
    budget_conscious: Optional[bool] = None
    health_conscious: Optional[bool] = None
    quick_meals_preference: Optional[bool] = None

class UserPreferences(UserPreferencesBase):
    id: str = Field(..., description="Unique identifier for user preferences")
    user_id: str = Field(default="default_user", description="User identifier (single user system)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        from_attributes = True

class UserStats(BaseModel):
    total_recipes_cooked: int = Field(default=0, description="Total number of recipes cooked")
    favorite_cuisine: Optional[str] = Field(None, description="Most frequently cooked cuisine")
    average_rating: Optional[float] = Field(None, description="Average rating given to recipes")
    total_ingredients_used: int = Field(default=0, description="Total number of different ingredients used")
    cooking_streak_days: int = Field(default=0, description="Current cooking streak in days")
    last_cooked_date: Optional[datetime] = Field(None, description="Last time user cooked a recipe")
    
class UserProfile(BaseModel):
    preferences: UserPreferences
    stats: UserStats