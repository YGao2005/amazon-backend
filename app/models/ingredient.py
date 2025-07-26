from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class IngredientCategory(str, Enum):
    PRODUCE = "produce"
    DAIRY = "dairy"
    PROTEIN = "protein"
    GRAINS = "grains"
    SPICES = "spices"
    OTHER = "other"

class IngredientBase(BaseModel):
    name: str = Field(..., description="Name of the ingredient")
    category: IngredientCategory = Field(..., description="Category of the ingredient")
    quantity: float = Field(..., description="Quantity of the ingredient")
    unit: str = Field(..., description="Unit of measurement (e.g., 'kg', 'pieces', 'liters')")
    expiration_date: Optional[datetime] = Field(None, description="Expiration date of the ingredient")
    purchase_date: Optional[datetime] = Field(None, description="Date when ingredient was purchased")
    location: Optional[str] = Field(None, description="Storage location (e.g., 'fridge', 'pantry')")
    notes: Optional[str] = Field(None, description="Additional notes about the ingredient")

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[IngredientCategory] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    expiration_date: Optional[datetime] = None
    purchase_date: Optional[datetime] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class Ingredient(IngredientBase):
    id: str = Field(..., description="Unique identifier for the ingredient")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    image_url: Optional[str] = Field(None, description="URL to ingredient image")
    
    class Config:
        from_attributes = True

class IngredientScanRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image data")
    
class IngredientScanResponse(BaseModel):
    ingredients: List[IngredientCreate] = Field(..., description="List of detected ingredients")
    confidence: float = Field(..., description="Confidence score of the detection")