from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid
import logging
from datetime import datetime

from app.models.recipe import Recipe, RecipeCreate, RecipeIngredient, RecipeStep, NutritionInfo, DifficultyLevel, MealType
from app.models.ingredient import Ingredient
from app.services.firebase.firestore import firebase_service
from app.services.firebase.storage import firebase_storage_service
from app.services.ai.gemini_service import gemini_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["recipes"])

# Request/Response models for the specific API endpoints
class GenerateRecipeRequest(BaseModel):
    mustUseIngredients: Optional[List[str]] = None
    preferenceOverrides: Optional[Dict[str, Any]] = None

class GenerateImageRequest(BaseModel):
    recipeId: str
    recipeName: str
    description: str

class CookRecipeRequest(BaseModel):
    recipeId: str
    rating: int
    notes: Optional[str] = None

class RecipeResponse(BaseModel):
    id: str
    name: str
    description: str
    ingredients: List[Dict[str, Any]]
    instructions: List[str]
    prepTime: str
    cookTime: str
    cookingTime: int  # Combined time in minutes for Swift
    servings: int
    difficulty: str
    cuisine: str
    nutritionalInfo: Dict[str, str]  # All values as strings for Swift
    tags: List[str]
    tips: List[str]
    imageName: Optional[str] = None  # Changed from imageUrl to imageName
    matchScore: Optional[float] = None
    createdAt: str
    updatedAt: str
    cookedCount: int = 0
    lastCooked: Optional[str] = None
    rating: Optional[float] = None

@router.post("/generate")
async def generate_recipes(request: GenerateRecipeRequest):
    """Generate recipe recommendations using Gemini Flash"""
    try:
        logger.info("Starting recipe generation")
        
        # Get available ingredients from Firebase
        ingredients_data = await firebase_service.get_collection("ingredients")
        available_ingredients = [ing["name"] for ing in ingredients_data if ing.get("quantity", 0) > 0]
        
        logger.info(f"Found {len(available_ingredients)} available ingredients")
        
        # If mustUseIngredients specified, filter available ingredients
        if request.mustUseIngredients:
            # Ensure must-use ingredients are included
            for must_use in request.mustUseIngredients:
                if must_use not in available_ingredients:
                    available_ingredients.append(must_use)
        
        # Extract preferences
        preferences = request.preferenceOverrides or {}
        cuisine_preferences = preferences.get("cuisinePreferences", [])
        cooking_time = preferences.get("cookingTime", "medium")
        
        # Map cooking time to difficulty
        difficulty_map = {
            "under30": "easy",
            "30to60": "medium", 
            "over60": "hard"
        }
        difficulty = difficulty_map.get(cooking_time, "medium")
        
        # Generate multiple recipe suggestions
        recipes = []
        cuisines_to_try = cuisine_preferences if cuisine_preferences else ["International", "Italian", "American"]
        
        for i, cuisine in enumerate(cuisines_to_try[:3]):  # Generate up to 3 recipes
            try:
                # Generate recipe using Gemini service
                recipe_dict = await gemini_service.generate_recipe(
                    ingredients=available_ingredients,
                    cuisine_preference=cuisine,
                    difficulty=difficulty
                )
                
                # Calculate match score based on available ingredients
                match_score = calculate_match_score(recipe_dict.get("ingredients", []), available_ingredients)
                
                # Create recipe ID
                recipe_id = str(uuid.uuid4())
                recipe_name = recipe_dict.get("name", "Generated Recipe")
                recipe_description = recipe_dict.get("description", "")
                
                # Generate image for the recipe with comprehensive error handling
                logger.info(f"Generating image for recipe: {recipe_name}")
                image_url = None
                image_generation_attempted = False
                
                try:
                    # Only attempt image generation if we have valid inputs
                    if recipe_name and recipe_name.strip():
                        image_generation_attempted = True
                        logger.debug(f"Attempting image generation for: {recipe_name}")
                        
                        image_url = await gemini_service.generate_recipe_image(
                            recipe_name=recipe_name,
                            recipe_description=recipe_description or "A delicious recipe"
                        )
                        
                        if image_url:
                            logger.info(f"Successfully generated image for recipe: {recipe_name}")
                            logger.info(f"IMAGE FIX: Received image URL from Gemini service: {image_url}")
                            if image_url.startswith('http'):
                                logger.info(f"IMAGE FIX: URL appears to be Firebase Storage URL - SUCCESS!")
                            else:
                                logger.warning(f"IMAGE FIX: URL appears to be local path - Firebase upload may have failed")
                        else:
                            logger.warning(f"Image generation returned None for recipe: {recipe_name}")
                    else:
                        logger.warning(f"Skipping image generation due to invalid recipe name: '{recipe_name}'")
                        
                except Exception as img_error:
                    logger.error(f"Error generating image for recipe '{recipe_name}': {img_error}", exc_info=True)
                    # Continue with recipe creation even if image generation fails
                    image_url = None
                
                # Log final image generation status
                if image_generation_attempted:
                    if image_url:
                        logger.info(f"Image generation completed successfully for recipe: {recipe_name}")
                    else:
                        logger.warning(f"Image generation failed for recipe: {recipe_name}, proceeding without image")
                else:
                    logger.info(f"Image generation skipped for recipe: {recipe_name}")
                
                # Parse time values for Swift compatibility
                prep_time_str = recipe_dict.get("prepTime", "15 minutes")
                cook_time_str = recipe_dict.get("cookTime", "30 minutes")
                prep_minutes = _parse_time_to_minutes(prep_time_str)
                cook_minutes = _parse_time_to_minutes(cook_time_str)
                total_minutes = prep_minutes + cook_minutes
                
                # Convert nutrition info to strings
                nutrition_info = recipe_dict.get("nutritionalInfo", {})
                nutrition_strings = {}
                for key, value in nutrition_info.items():
                    if value is not None:
                        nutrition_strings[key] = str(value)
                    else:
                        nutrition_strings[key] = "0"
                
                recipe_data = {
                    "id": recipe_id,
                    "name": recipe_name,
                    "description": recipe_description,
                    "ingredients": recipe_dict.get("ingredients", []),
                    "instructions": recipe_dict.get("instructions", []),
                    "prepTime": prep_time_str,
                    "cookTime": cook_time_str,
                    "cookingTime": total_minutes,  # Combined time as integer
                    "servings": recipe_dict.get("servings", 4),
                    "difficulty": recipe_dict.get("difficulty", "Medium"),  # Ensure capitalized
                    "cuisine": recipe_dict.get("cuisine", cuisine),
                    "nutritionalInfo": nutrition_strings,  # All values as strings
                    "tags": recipe_dict.get("tags", []),
                    "tips": recipe_dict.get("tips", []),
                    "imageName": image_url,  # Changed from imageUrl to imageName - Should now be Firebase Storage URL
                    "matchScore": match_score,
                    "createdAt": datetime.utcnow().isoformat(),
                    "updatedAt": datetime.utcnow().isoformat(),
                    "cookedCount": 0,
                    "lastCooked": None,
                    "rating": None,
                    "status": "generated"
                }
                
                # Store in Firebase
                success = await firebase_service.create_document("recipes", recipe_id, recipe_data)
                if success:
                    recipes.append(RecipeResponse(**recipe_data))
                    logger.info(f"Generated and stored recipe with image: {recipe_data['name']}")
                    logger.info(f"IMAGE FIX: Recipe stored with imageName: {image_url}")
                    if image_url and image_url.startswith('http'):
                        logger.info(f"IMAGE FIX: Successfully stored Firebase Storage URL in database")
                    else:
                        logger.warning(f"IMAGE FIX: Stored what appears to be local path - check Firebase upload")
                else:
                    logger.error(f"Failed to store recipe: {recipe_data['name']}")
                    
            except Exception as e:
                logger.error(f"Error generating recipe for cuisine {cuisine}: {e}")
                continue
        
        return {"recipes": recipes}
        
    except Exception as e:
        logger.error(f"Error in recipe generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recipes: {str(e)}")

@router.post("/image")
async def generate_recipe_image(request: GenerateImageRequest):
    """Generate image for a recipe using Gemini 2.0"""
    try:
        logger.info(f"Generating image for recipe: {request.recipeName}")
        
        # Check if recipe exists
        recipe_data = await firebase_service.get_document("recipes", request.recipeId)
        if not recipe_data:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Generate image using Gemini 2.0 (currently returns mock URL)
        image_url = await gemini_service.generate_recipe_image(
            recipe_name=request.recipeName,
            recipe_description=request.description
        )
        
        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to generate recipe image")
        
        # Update recipe with image URL
        update_data = {
            "imageName": image_url,  # Changed from imageUrl to imageName
            "updatedAt": datetime.utcnow().isoformat()
        }
        
        success = await firebase_service.update_document("recipes", request.recipeId, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update recipe with image URL")
        
        return {
            "success": True,
            "imageName": image_url,  # Changed from imageUrl to imageName
            "message": "Recipe image generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recipe image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recipe image: {str(e)}")

@router.get("/")
async def get_recipes(
    status: str = "all",  # "all", "cooked", "saved"
    sort: str = "recent"  # "recent", "rating", "expiring"
):
    """Fetch all saved recipes with filtering and sorting"""
    try:
        logger.info(f"Fetching recipes with status={status}, sort={sort}")
        
        # Get all recipes from Firebase
        recipes_data = await firebase_service.get_collection("recipes")
        
        # Apply status filtering
        filtered_recipes = []
        for recipe_data in recipes_data:
            if status == "all":
                filtered_recipes.append(recipe_data)
            elif status == "cooked" and recipe_data.get("cookedCount", 0) > 0:
                filtered_recipes.append(recipe_data)
            elif status == "saved" and recipe_data.get("cookedCount", 0) == 0:
                filtered_recipes.append(recipe_data)
        
        # Apply sorting
        if sort == "recent":
            filtered_recipes.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        elif sort == "rating":
            filtered_recipes.sort(key=lambda x: x.get("rating", 0), reverse=True)
        elif sort == "expiring":
            # For expiring sort, we'd need to check ingredient expiration dates
            # This is a simplified version
            filtered_recipes.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        
        # Convert to response format
        recipes = []
        for recipe_data in filtered_recipes:
            try:
                # Parse time values for Swift compatibility
                prep_time_str = recipe_data.get("prepTime", "15 minutes")
                cook_time_str = recipe_data.get("cookTime", "30 minutes")
                cooking_time = recipe_data.get("cookingTime")
                
                # If cookingTime not stored, calculate it
                if cooking_time is None:
                    prep_minutes = _parse_time_to_minutes(prep_time_str)
                    cook_minutes = _parse_time_to_minutes(cook_time_str)
                    cooking_time = prep_minutes + cook_minutes
                
                # Convert nutrition info to strings
                nutrition_info = recipe_data.get("nutritionalInfo", {})
                nutrition_strings = {}
                for key, value in nutrition_info.items():
                    if value is not None:
                        nutrition_strings[key] = str(value)
                    else:
                        nutrition_strings[key] = "0"
                
                recipe_response = RecipeResponse(
                    id=recipe_data.get("id", ""),
                    name=recipe_data.get("name", ""),
                    description=recipe_data.get("description", ""),
                    ingredients=recipe_data.get("ingredients", []),
                    instructions=recipe_data.get("instructions", []),
                    prepTime=prep_time_str,
                    cookTime=cook_time_str,
                    cookingTime=cooking_time,
                    servings=recipe_data.get("servings", 1),
                    difficulty=recipe_data.get("difficulty", "Medium"),  # Ensure capitalized
                    cuisine=recipe_data.get("cuisine", ""),
                    nutritionalInfo=nutrition_strings,  # All values as strings
                    tags=recipe_data.get("tags", []),
                    tips=recipe_data.get("tips", []),
                    imageName=recipe_data.get("imageName") or recipe_data.get("imageUrl"),  # Support both field names
                    matchScore=recipe_data.get("matchScore"),
                    createdAt=recipe_data.get("createdAt", ""),
                    updatedAt=recipe_data.get("updatedAt", ""),
                    cookedCount=recipe_data.get("cookedCount", 0),
                    lastCooked=recipe_data.get("lastCooked"),
                    rating=recipe_data.get("rating")
                )
                recipes.append(recipe_response)
            except Exception as e:
                logger.warning(f"Error processing recipe {recipe_data.get('id', 'unknown')}: {e}")
                continue
        
        return {"recipes": recipes}
        
    except Exception as e:
        logger.error(f"Error fetching recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recipes: {str(e)}")

@router.post("/cooked")
async def mark_recipe_cooked(request: CookRecipeRequest):
    """Mark recipe as cooked and update inventory"""
    try:
        logger.info(f"Marking recipe {request.recipeId} as cooked")
        
        # Check if recipe exists
        recipe_data = await firebase_service.get_document("recipes", request.recipeId)
        if not recipe_data:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Update recipe statistics
        cooked_count = recipe_data.get("cookedCount", 0) + 1
        update_data = {
            "cookedCount": cooked_count,
            "lastCooked": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat()
        }
        
        if request.rating:
            update_data["rating"] = request.rating
        
        # Update recipe in Firebase
        success = await firebase_service.update_document("recipes", request.recipeId, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update recipe")
        
        # Update ingredient inventory by removing used ingredients
        recipe_ingredients = recipe_data.get("ingredients", [])
        updated_ingredients = []
        
        for recipe_ingredient in recipe_ingredients:
            ingredient_name = recipe_ingredient.get("name", "").lower()
            required_amount = parse_quantity(recipe_ingredient.get("amount", "1"))
            
            # Find matching ingredient in inventory
            inventory_ingredients = await firebase_service.query_collection(
                "ingredients", "name", "==", ingredient_name
            )
            
            # Try case-insensitive search if exact match not found
            if not inventory_ingredients:
                all_ingredients = await firebase_service.get_collection("ingredients")
                inventory_ingredients = [
                    ing for ing in all_ingredients 
                    if ing.get("name", "").lower() == ingredient_name
                ]
            
            if inventory_ingredients:
                inventory_ingredient = inventory_ingredients[0]
                current_quantity = inventory_ingredient.get("quantity", 0)
                
                # Calculate new quantity (don't go below 0)
                new_quantity = max(0, current_quantity - required_amount)
                
                # Update ingredient quantity
                ingredient_update = {
                    "quantity": new_quantity,
                    "updated_at": datetime.utcnow()
                }
                
                ingredient_success = await firebase_service.update_document(
                    "ingredients", inventory_ingredient["id"], ingredient_update
                )
                
                if ingredient_success:
                    updated_ingredients.append({
                        "name": inventory_ingredient["name"],
                        "previousQuantity": current_quantity,
                        "newQuantity": new_quantity,
                        "used": required_amount
                    })
                    logger.info(f"Updated ingredient {inventory_ingredient['name']}: {current_quantity} -> {new_quantity}")
        
        # Log cooking activity
        cooking_log = {
            "recipeId": request.recipeId,
            "recipeName": recipe_data.get("name", ""),
            "cookedAt": datetime.utcnow().isoformat(),
            "rating": request.rating,
            "notes": request.notes,
            "ingredientsUsed": updated_ingredients
        }
        
        log_id = str(uuid.uuid4())
        await firebase_service.create_document("cooking_logs", log_id, cooking_log)
        
        return {
            "success": True,
            "message": "Recipe marked as cooked successfully",
            "updatedIngredients": updated_ingredients,
            "cookedCount": cooked_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking recipe as cooked: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark recipe as cooked: {str(e)}")

# Helper functions
def calculate_match_score(recipe_ingredients: List[Dict[str, Any]], available_ingredients: List[str]) -> float:
    """Calculate how well available ingredients match recipe requirements"""
    if not recipe_ingredients:
        return 0.0
    
    available_lower = [ing.lower() for ing in available_ingredients]
    matches = 0
    
    for recipe_ing in recipe_ingredients:
        ing_name = recipe_ing.get("name", "").lower()
        # Check if any available ingredient contains the recipe ingredient name
        if any(ing_name in avail or avail in ing_name for avail in available_lower):
            matches += 1
    
    return matches / len(recipe_ingredients)

def parse_quantity(amount_str: str) -> float:
    """Parse quantity from string format"""
    try:
        import re
        numbers = re.findall(r'\d+\.?\d*', str(amount_str))
        if numbers:
            return float(numbers[0])
        return 1.0
    except:
        return 1.0

def convert_units(from_unit: str, to_unit: str, quantity: float) -> float:
    """Simple unit conversion for common cooking measurements"""
    # This is a simplified conversion - in a real app you'd want a more comprehensive system
    conversions = {
        ("cups", "ml"): 236.588,
        ("tbsp", "ml"): 14.787,
        ("tsp", "ml"): 4.929,
        ("oz", "g"): 28.35,
        ("lb", "g"): 453.592,
        ("kg", "g"): 1000,
    }
    
    conversion_factor = conversions.get((from_unit.lower(), to_unit.lower()), 1.0)
    return quantity * conversion_factor

def _parse_time_to_minutes(time_str: str) -> int:
    """Parse time string like '15 minutes' or '1 hour' to minutes"""
    try:
        import re
        time_lower = time_str.lower()
        
        # Extract numbers from the string
        numbers = re.findall(r'\d+', time_str)
        if not numbers:
            return 30  # Default to 30 minutes
        
        value = int(numbers[0])
        
        # Check for time units
        if 'hour' in time_lower:
            return value * 60
        elif 'minute' in time_lower or 'min' in time_lower:
            return value
        else:
            # If no unit specified, assume minutes
            return value
    except:
        return 30  # Default to 30 minutes