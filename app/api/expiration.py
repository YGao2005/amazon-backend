from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from datetime import datetime, date, timedelta

from app.models.expiration import (
    ExpirationSummary, ExpirationAlert, ExpirationStatus,
    ExpirationSettings, WasteLog, WasteStats, RecipeRecommendation
)
from app.models.ingredient import Ingredient
from app.services.firebase.firestore import firebase_service

router = APIRouter(tags=["expiration"])

@router.get("/summary", response_model=ExpirationSummary)
async def get_expiration_summary():
    """Get summary of ingredient expiration status"""
    try:
        # Get all ingredients
        ingredients = await firebase_service.get_collection("ingredients")
        
        total_ingredients = len(ingredients)
        fresh_count = 0
        expiring_soon_count = 0
        expired_count = 0
        unknown_count = 0
        alerts = []
        
        today = date.today()
        warning_threshold = 3  # days
        
        for ingredient_data in ingredients:
            ingredient = Ingredient(**ingredient_data)
            
            if not ingredient.expiration_date:
                unknown_count += 1
                continue
            
            exp_date = ingredient.expiration_date.date() if isinstance(ingredient.expiration_date, datetime) else ingredient.expiration_date
            days_until_expiration = (exp_date - today).days
            
            # Determine status
            if days_until_expiration < 0:
                status = ExpirationStatus.EXPIRED
                expired_count += 1
            elif days_until_expiration <= warning_threshold:
                status = ExpirationStatus.EXPIRING_SOON
                expiring_soon_count += 1
            else:
                status = ExpirationStatus.FRESH
                fresh_count += 1
            
            # Create alert for expiring or expired items
            if status in [ExpirationStatus.EXPIRED, ExpirationStatus.EXPIRING_SOON]:
                alert = ExpirationAlert(
                    ingredient_id=ingredient.id,
                    ingredient_name=ingredient.name,
                    expiration_date=exp_date,
                    days_until_expiration=days_until_expiration,
                    status=status,
                    quantity=ingredient.quantity,
                    unit=ingredient.unit,
                    location=ingredient.location
                )
                alerts.append(alert)
        
        # Sort alerts by urgency (expired first, then by days until expiration)
        alerts.sort(key=lambda x: (x.status != ExpirationStatus.EXPIRED, x.days_until_expiration))
        
        return ExpirationSummary(
            total_ingredients=total_ingredients,
            fresh_count=fresh_count,
            expiring_soon_count=expiring_soon_count,
            expired_count=expired_count,
            unknown_count=unknown_count,
            alerts=alerts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting expiration summary: {str(e)}")

@router.get("/alerts")
async def get_expiration_alerts():
    """Get alerts for expiring ingredients with recipe recommendations"""
    try:
        # Get current date for comparison
        current_date = datetime.now()
        expiration_threshold = current_date + timedelta(days=7)
        
        # Get all ingredients
        ingredients_data = await firebase_service.get_collection("ingredients")
        
        # Get all recipes for matching
        recipes_data = await firebase_service.get_collection("recipes")
        
        expiring_ingredients = []
        
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get("id")
            ingredient_name = ingredient_data.get("name", "")
            expiration_date_raw = ingredient_data.get("expiration_date")
            
            # Skip ingredients without expiration dates
            if not expiration_date_raw:
                continue
            
            # Parse expiration date
            try:
                if isinstance(expiration_date_raw, str):
                    # Try parsing ISO format first
                    if 'T' in expiration_date_raw:
                        expiration_date = datetime.fromisoformat(expiration_date_raw.replace('Z', '+00:00'))
                    else:
                        # Try parsing date only
                        from datetime import datetime as dt
                        expiration_date = dt.strptime(expiration_date_raw, '%Y-%m-%d')
                elif isinstance(expiration_date_raw, datetime):
                    expiration_date = expiration_date_raw
                else:
                    continue
            except (ValueError, TypeError):
                continue
            
            # Check if ingredient is expiring within 7 days
            if expiration_date <= expiration_threshold:
                # Calculate days until expiration
                days_until_expiration = (expiration_date.date() - current_date.date()).days
                
                # Find recipes that use this ingredient
                recommended_recipes = []
                ingredient_name_lower = ingredient_name.lower()
                
                for recipe_data in recipes_data:
                    recipe_id = recipe_data.get("id")
                    recipe_ingredients = recipe_data.get("ingredients", [])
                    
                    # Check if this ingredient is used in the recipe
                    ingredient_found = False
                    for recipe_ingredient in recipe_ingredients:
                        if isinstance(recipe_ingredient, dict):
                            recipe_ingredient_name = recipe_ingredient.get("name", "").lower()
                        else:
                            recipe_ingredient_name = str(recipe_ingredient).lower()
                        
                        # Check for ingredient match (partial matching)
                        if (ingredient_name_lower in recipe_ingredient_name or
                            recipe_ingredient_name in ingredient_name_lower or
                            any(word in recipe_ingredient_name for word in ingredient_name_lower.split() if len(word) > 2)):
                            ingredient_found = True
                            break
                    
                    if ingredient_found:
                        recommended_recipes.append(recipe_id)
                
                # Create expiring ingredient alert
                expiring_ingredient = {
                    "id": ingredient_id,
                    "name": ingredient_name,
                    "expirationDate": expiration_date.isoformat() + ('Z' if expiration_date.tzinfo is None else ''),
                    "daysUntilExpiration": days_until_expiration,
                    "recommendedRecipes": recommended_recipes[:5]  # Limit to 5 recommendations
                }
                
                expiring_ingredients.append(expiring_ingredient)
        
        # Sort by days until expiration (most urgent first)
        expiring_ingredients.sort(key=lambda x: x['daysUntilExpiration'])
        
        return {"expiringIngredients": expiring_ingredients}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching expiration alerts: {str(e)}")

@router.get("/alerts/legacy", response_model=List[ExpirationAlert])
async def get_expiration_alerts_legacy(status: Optional[ExpirationStatus] = None):
    """Get expiration alerts in legacy format, optionally filtered by status"""
    try:
        summary = await get_expiration_summary()
        alerts = summary.alerts
        
        if status:
            alerts = [alert for alert in alerts if alert.status == status]
        
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting expiration alerts: {str(e)}")

@router.get("/settings", response_model=ExpirationSettings)
async def get_expiration_settings():
    """Get expiration management settings"""
    try:
        settings_data = await firebase_service.get_document("expiration_settings", "default")
        
        if not settings_data:
            # Create default settings
            default_settings = ExpirationSettings()
            await firebase_service.create_document("expiration_settings", "default", default_settings.dict())
            return default_settings
        
        return ExpirationSettings(**settings_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting expiration settings: {str(e)}")

@router.put("/settings", response_model=ExpirationSettings)
async def update_expiration_settings(settings: ExpirationSettings):
    """Update expiration management settings"""
    try:
        success = await firebase_service.update_document("expiration_settings", "default", settings.dict())
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update expiration settings")
        
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating expiration settings: {str(e)}")

@router.post("/waste-log", response_model=WasteLog)
async def log_wasted_ingredient(
    ingredient_name: str,
    quantity: float,
    unit: str,
    expiration_date: date,
    reason: Optional[str] = None,
    estimated_cost: Optional[float] = None
):
    """Log a wasted ingredient"""
    try:
        waste_log_id = str(uuid.uuid4())
        waste_log = WasteLog(
            id=waste_log_id,
            ingredient_name=ingredient_name,
            quantity=quantity,
            unit=unit,
            expiration_date=expiration_date,
            reason=reason,
            estimated_cost=estimated_cost
        )
        
        success = await firebase_service.create_document("waste_logs", waste_log_id, waste_log.dict())
        if not success:
            raise HTTPException(status_code=500, detail="Failed to log wasted ingredient")
        
        return waste_log
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging wasted ingredient: {str(e)}")

@router.get("/waste-stats", response_model=WasteStats)
async def get_waste_statistics():
    """Get waste statistics"""
    try:
        waste_logs = await firebase_service.get_collection("waste_logs")
        
        if not waste_logs:
            return WasteStats()
        
        total_items_wasted = len(waste_logs)
        total_estimated_cost = sum(log.get("estimated_cost", 0) for log in waste_logs if log.get("estimated_cost"))
        
        # Find most wasted ingredient
        ingredient_counts = {}
        for log in waste_logs:
            ingredient_name = log.get("ingredient_name", "")
            ingredient_counts[ingredient_name] = ingredient_counts.get(ingredient_name, 0) + 1
        
        most_wasted_ingredient = max(ingredient_counts, key=ingredient_counts.get) if ingredient_counts else None
        
        # Calculate waste by category (simplified - would need ingredient category mapping)
        waste_by_category = {}
        
        # Calculate monthly waste trend (simplified)
        monthly_waste_trend = []
        current_date = datetime.now()
        for i in range(6):  # Last 6 months
            month_start = current_date.replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_waste = [
                log for log in waste_logs 
                if month_start <= datetime.fromisoformat(str(log.get("waste_date", ""))) < month_end
            ]
            
            monthly_waste_trend.append({
                "month": month_start.strftime("%Y-%m"),
                "items_wasted": len(month_waste),
                "estimated_cost": sum(log.get("estimated_cost", 0) for log in month_waste if log.get("estimated_cost"))
            })
        
        return WasteStats(
            total_items_wasted=total_items_wasted,
            total_estimated_cost=total_estimated_cost,
            most_wasted_ingredient=most_wasted_ingredient,
            waste_by_category=waste_by_category,
            monthly_waste_trend=monthly_waste_trend
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting waste statistics: {str(e)}")

@router.get("/recipe-recommendations", response_model=List[RecipeRecommendation])
async def get_recipe_recommendations_for_expiring():
    """Get recipe recommendations based on expiring ingredients"""
    try:
        # Get expiring ingredients
        summary = await get_expiration_summary()
        expiring_ingredients = [
            alert.ingredient_name.lower() 
            for alert in summary.alerts 
            if alert.status == ExpirationStatus.EXPIRING_SOON
        ]
        
        if not expiring_ingredients:
            return []
        
        # Get all recipes
        all_recipes = await firebase_service.get_collection("recipes")
        
        recommendations = []
        for recipe_data in all_recipes:
            recipe_ingredients = [ing["name"].lower() for ing in recipe_data.get("ingredients", [])]
            
            # Find which expiring ingredients are used in this recipe
            used_expiring = [
                ing for ing in expiring_ingredients 
                if any(ing in recipe_ing for recipe_ing in recipe_ingredients)
            ]
            
            if used_expiring:
                # Calculate urgency score based on number of expiring ingredients used
                urgency_score = len(used_expiring) / len(expiring_ingredients)
                
                recommendation = RecipeRecommendation(
                    recipe_id=recipe_data["id"],
                    recipe_title=recipe_data.get("title", "Unknown Recipe"),
                    expiring_ingredients_used=used_expiring,
                    urgency_score=urgency_score,
                    prep_time_minutes=recipe_data.get("prep_time_minutes")
                )
                recommendations.append(recommendation)
        
        # Sort by urgency score (highest first)
        recommendations.sort(key=lambda x: x.urgency_score, reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recipe recommendations: {str(e)}")

@router.delete("/waste-log/{waste_log_id}")
async def delete_waste_log(waste_log_id: str):
    """Delete a waste log entry"""
    try:
        # Check if waste log exists
        existing_log = await firebase_service.get_document("waste_logs", waste_log_id)
        if not existing_log:
            raise HTTPException(status_code=404, detail="Waste log not found")
        
        success = await firebase_service.delete_document("waste_logs", waste_log_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete waste log")
        
        return {"message": "Waste log deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting waste log: {str(e)}")

@router.get("/waste-logs", response_model=List[WasteLog])
async def get_waste_logs(limit: Optional[int] = 50):
    """Get all waste logs"""
    try:
        waste_logs_data = await firebase_service.get_collection("waste_logs", limit)
        
        # Sort by waste_date (most recent first)
        waste_logs_data.sort(key=lambda x: x.get("waste_date", ""), reverse=True)
        
        return [WasteLog(**log) for log in waste_logs_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting waste logs: {str(e)}")