from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DESSERT = "dessert"

class RecipeIngredient(BaseModel):
    name: str = Field(..., description="Name of the ingredient")
    quantity: float = Field(..., description="Quantity needed")
    unit: str = Field(..., description="Unit of measurement")
    optional: bool = Field(default=False, description="Whether ingredient is optional")

class RecipeStep(BaseModel):
    step_number: int = Field(..., description="Step number in the recipe")
    instruction: str = Field(..., description="Instruction for this step")
    duration_minutes: Optional[int] = Field(None, description="Time required for this step")

class NutritionInfo(BaseModel):
    calories: Optional[int] = Field(None, description="Calories per serving")
    protein_g: Optional[float] = Field(None, description="Protein in grams")
    carbs_g: Optional[float] = Field(None, description="Carbohydrates in grams")
    fat_g: Optional[float] = Field(None, description="Fat in grams")
    fiber_g: Optional[float] = Field(None, description="Fiber in grams")

class RecipeBase(BaseModel):
    title: str = Field(..., description="Recipe title")
    description: Optional[str] = Field(None, description="Recipe description")
    ingredients: List[RecipeIngredient] = Field(..., description="List of ingredients")
    steps: List[RecipeStep] = Field(..., description="Cooking steps")
    prep_time_minutes: Optional[int] = Field(None, description="Preparation time in minutes")
    cook_time_minutes: Optional[int] = Field(None, description="Cooking time in minutes")
    servings: int = Field(default=1, description="Number of servings")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM, description="Difficulty level")
    meal_type: List[MealType] = Field(default=[], description="Types of meals this recipe is suitable for")
    cuisine: Optional[str] = Field(None, description="Cuisine type (e.g., 'Italian', 'Asian')")
    tags: List[str] = Field(default=[], description="Recipe tags")
    nutrition: Optional[NutritionInfo] = Field(None, description="Nutritional information")

class RecipeCreate(RecipeBase):
    pass

class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[RecipeIngredient]] = None
    steps: Optional[List[RecipeStep]] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[DifficultyLevel] = None
    meal_type: Optional[List[MealType]] = None
    cuisine: Optional[str] = None
    tags: Optional[List[str]] = None
    nutrition: Optional[NutritionInfo] = None

class Recipe(RecipeBase):
    id: str = Field(..., description="Unique identifier for the recipe")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    image_url: Optional[str] = Field(None, description="URL to recipe image")
    cooked_count: int = Field(default=0, description="Number of times this recipe has been cooked")
    last_cooked: Optional[datetime] = Field(None, description="Last time this recipe was cooked")
    rating: Optional[float] = Field(None, description="User rating (1-5)")
    
    class Config:
        from_attributes = True

class RecipeGenerationRequest(BaseModel):
    available_ingredients: List[str] = Field(..., description="List of available ingredient names")
    meal_type: Optional[MealType] = Field(None, description="Preferred meal type")
    cuisine: Optional[str] = Field(None, description="Preferred cuisine")
    dietary_restrictions: List[str] = Field(default=[], description="Dietary restrictions")
    max_prep_time: Optional[int] = Field(None, description="Maximum preparation time in minutes")
    servings: int = Field(default=2, description="Number of servings needed")

class RecipeGenerationResponse(BaseModel):
    recipe: RecipeCreate = Field(..., description="Generated recipe")
    missing_ingredients: List[str] = Field(..., description="Ingredients not available but needed")
    confidence: float = Field(..., description="Confidence score of the generation")

class MarkCookedRequest(BaseModel):
    rating: Optional[float] = Field(None, description="Rating for the cooked recipe (1-5)")
    notes: Optional[str] = Field(None, description="Notes about cooking experience")