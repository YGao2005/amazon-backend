from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class ExpirationStatus(str, Enum):
    FRESH = "fresh"
    EXPIRING_SOON = "expiring_soon"  # Within 3 days
    EXPIRED = "expired"
    UNKNOWN = "unknown"

class ExpirationAlert(BaseModel):
    ingredient_id: str = Field(..., description="ID of the ingredient")
    ingredient_name: str = Field(..., description="Name of the ingredient")
    expiration_date: date = Field(..., description="Expiration date")
    days_until_expiration: int = Field(..., description="Days until expiration (negative if expired)")
    status: ExpirationStatus = Field(..., description="Current expiration status")
    quantity: float = Field(..., description="Quantity of the ingredient")
    unit: str = Field(..., description="Unit of measurement")
    location: Optional[str] = Field(None, description="Storage location")

class ExpirationSummary(BaseModel):
    total_ingredients: int = Field(..., description="Total number of ingredients")
    fresh_count: int = Field(..., description="Number of fresh ingredients")
    expiring_soon_count: int = Field(..., description="Number of ingredients expiring soon")
    expired_count: int = Field(..., description="Number of expired ingredients")
    unknown_count: int = Field(..., description="Number of ingredients with unknown expiration")
    alerts: List[ExpirationAlert] = Field(..., description="List of expiration alerts")

class ExpirationSettings(BaseModel):
    warning_days: int = Field(default=3, description="Days before expiration to show warning")
    enable_notifications: bool = Field(default=True, description="Whether to enable expiration notifications")
    auto_suggest_recipes: bool = Field(default=True, description="Auto-suggest recipes for expiring ingredients")

class WasteLog(BaseModel):
    id: str = Field(..., description="Unique identifier for waste log entry")
    ingredient_name: str = Field(..., description="Name of the wasted ingredient")
    quantity: float = Field(..., description="Quantity wasted")
    unit: str = Field(..., description="Unit of measurement")
    expiration_date: date = Field(..., description="Original expiration date")
    waste_date: datetime = Field(default_factory=datetime.utcnow, description="Date when ingredient was wasted")
    reason: Optional[str] = Field(None, description="Reason for waste")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost of wasted ingredient")

class WasteStats(BaseModel):
    total_items_wasted: int = Field(default=0, description="Total number of items wasted")
    total_estimated_cost: float = Field(default=0.0, description="Total estimated cost of waste")
    most_wasted_ingredient: Optional[str] = Field(None, description="Most frequently wasted ingredient")
    waste_by_category: dict = Field(default_factory=dict, description="Waste statistics by ingredient category")
    monthly_waste_trend: List[dict] = Field(default_factory=list, description="Monthly waste trend data")

class RecipeRecommendation(BaseModel):
    recipe_id: str = Field(..., description="ID of recommended recipe")
    recipe_title: str = Field(..., description="Title of recommended recipe")
    expiring_ingredients_used: List[str] = Field(..., description="List of expiring ingredients that would be used")
    urgency_score: float = Field(..., description="Urgency score based on expiration dates")
    prep_time_minutes: Optional[int] = Field(None, description="Recipe preparation time")