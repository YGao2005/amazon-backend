from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Any
from pydantic import BaseModel
import uuid
import base64
import logging
from datetime import datetime, timedelta

from app.models.ingredient import (
    Ingredient, IngredientCreate, IngredientUpdate
)
from app.services.firebase.firestore import firebase_service
from app.services.ai.groq_service import groq_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["ingredients"])

# Request models for the specific API endpoints
class ScanRequest(BaseModel):
    image: str  # base64 encoded image string

class UpdateRequest(BaseModel):
    ingredients: List[IngredientCreate]

# Response models
class ScanResponseIngredient(BaseModel):
    name: str
    quantity: str
    estimatedExpiration: str
    confidence: float

class ScanResponse(BaseModel):
    ingredients: List[ScanResponseIngredient]

@router.get("/")
async def get_ingredients():
    """Get all ingredients from inventory"""
    try:
        logger.info("Fetching all ingredients from inventory")
        ingredients_data = await firebase_service.get_collection("ingredients")
        
        # Convert to Ingredient objects and return with proper structure
        ingredients = []
        for ingredient_data in ingredients_data:
            try:
                ingredient = Ingredient(**ingredient_data)
                ingredients.append({
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "quantity": ingredient.quantity,
                    "unit": ingredient.unit,
                    "category": ingredient.category,
                    "expiration_date": ingredient.expiration_date.isoformat() if ingredient.expiration_date else None,
                    "purchase_date": ingredient.purchase_date.isoformat() if ingredient.purchase_date else None,
                    "created_at": ingredient.created_at.isoformat() if ingredient.created_at else None,
                    "updated_at": ingredient.updated_at.isoformat() if ingredient.updated_at else None,
                    "location": ingredient.location,
                    "notes": ingredient.notes,
                    "image_url": ingredient.image_url
                })
            except Exception as e:
                logger.warning(f"Error processing ingredient {ingredient_data.get('id', 'unknown')}: {e}")
                continue
        
        return {"ingredients": ingredients}
    except Exception as e:
        logger.error(f"Error fetching ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch ingredients: {str(e)}")

@router.get("/{ingredient_id}", response_model=Ingredient)
async def get_ingredient(ingredient_id: str):
    """Get a specific ingredient by ID"""
    try:
        ingredient_data = await firebase_service.get_document("ingredients", ingredient_id)
        if not ingredient_data:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        return Ingredient(id=ingredient_id, **ingredient_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ingredient: {str(e)}")

@router.post("/", response_model=Ingredient)
async def create_ingredient(ingredient: IngredientCreate):
    """Create a new ingredient"""
    try:
        ingredient_id = str(uuid.uuid4())
        ingredient_data = ingredient.dict()
        ingredient_data.update({
            "id": ingredient_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        success = await firebase_service.create_document("ingredients", ingredient_id, ingredient_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create ingredient")
        
        return Ingredient(**ingredient_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ingredient: {str(e)}")

@router.put("/{ingredient_id}", response_model=Ingredient)
async def update_ingredient(ingredient_id: str, ingredient_update: IngredientUpdate):
    """Update an existing ingredient"""
    try:
        # Check if ingredient exists
        existing_ingredient = await firebase_service.get_document("ingredients", ingredient_id)
        if not existing_ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        # Prepare update data
        update_data = ingredient_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        success = await firebase_service.update_document("ingredients", ingredient_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update ingredient")
        
        # Get updated ingredient
        updated_ingredient = await firebase_service.get_document("ingredients", ingredient_id)
        return Ingredient(id=ingredient_id, **updated_ingredient)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating ingredient: {str(e)}")

@router.delete("/{ingredient_id}")
async def delete_ingredient(ingredient_id: str):
    """Delete an ingredient"""
    try:
        # Check if ingredient exists
        existing_ingredient = await firebase_service.get_document("ingredients", ingredient_id)
        if not existing_ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        success = await firebase_service.delete_document("ingredients", ingredient_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete ingredient")
        
        return {"message": "Ingredient deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting ingredient: {str(e)}")

@router.post("/scan")
async def scan_ingredients(request: ScanRequest):
    """Scan fridge contents from photo using Groq Llama Vision"""
    try:
        logger.info("Starting ingredient scanning from image")
        
        # Validate base64 image
        if not request.image:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Remove data URL prefix if present
        image_data = request.image
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64 image to bytes for Groq service
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid base64 image data")
        
        # Validate image
        if not await groq_service.validate_image(image_bytes):
            raise HTTPException(status_code=400, detail="Invalid or unsuitable image for ingredient recognition")
        
        # Use Groq service to analyze the image
        logger.info("Analyzing image with Groq Vision API")
        recognized_ingredients = await groq_service.recognize_ingredients(image_bytes)
        
        if not recognized_ingredients:
            logger.warning("No ingredients recognized in image")
            return {"ingredients": []}
        
        # Process and store recognized ingredients in Firebase
        stored_ingredients = []
        current_date = datetime.now()
        
        for ingredient_data in recognized_ingredients:
            try:
                # Parse expiration date from relative time (e.g., "3 days", "1 week")
                expiration_str = ingredient_data.get('estimatedExpiration', '7 days')
                expiration_days = _parse_expiration_days(expiration_str)
                estimated_expiration = current_date + timedelta(days=expiration_days)
                
                # Parse quantity and unit
                quantity_str = ingredient_data.get('quantity', '1 unit')
                quantity = _parse_quantity_value(quantity_str)
                unit = _parse_unit_value(quantity_str)
                
                # Guess category
                category = _guess_ingredient_category(ingredient_data['name'])
                
                # Create ingredient object
                ingredient_create = IngredientCreate(
                    name=ingredient_data['name'],
                    category=category,
                    quantity=quantity,
                    unit=unit,
                    expiration_date=estimated_expiration,
                    purchase_date=current_date,
                    location="fridge",  # Default location for scanned items
                    notes=f"Scanned from image, confidence: {ingredient_data.get('confidence', 0.8):.2f}"
                )
                
                # Store in Firebase
                ingredient_id = str(uuid.uuid4())
                ingredient_data_dict = ingredient_create.dict()
                ingredient_data_dict.update({
                    "id": ingredient_id,
                    "created_at": current_date,
                    "updated_at": current_date
                })
                
                success = await firebase_service.create_document("ingredients", ingredient_id, ingredient_data_dict)
                if success:
                    stored_ingredient = {
                        "name": ingredient_data['name'],
                        "quantity": quantity_str,
                        "estimatedExpiration": expiration_str,
                        "confidence": ingredient_data.get('confidence', 0.8)
                    }
                    stored_ingredients.append(stored_ingredient)
                    logger.info(f"Successfully stored ingredient: {ingredient_data['name']}")
                else:
                    logger.error(f"Failed to store ingredient: {ingredient_data['name']}")
                    
            except Exception as e:
                logger.error(f"Error processing ingredient {ingredient_data.get('name', 'unknown')}: {e}")
                continue
        
        return {"ingredients": stored_ingredients}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to scan ingredients: {str(e)}")

@router.post("/update")
async def update_ingredients(request: UpdateRequest):
    """Add or update ingredients manually"""
    try:
        logger.info(f"Updating {len(request.ingredients)} ingredients")
        
        updated_ingredient_ids = []
        current_time = datetime.now()
        
        for ingredient_create in request.ingredients:
            try:
                # Check if ingredient with same name already exists
                existing_ingredients = await firebase_service.query_collection(
                    "ingredients", "name", "==", ingredient_create.name
                )
                
                if existing_ingredients:
                    # Update existing ingredient
                    existing_ingredient = existing_ingredients[0]
                    ingredient_id = existing_ingredient["id"]
                    
                    # Prepare update data
                    update_data = ingredient_create.dict()
                    update_data["updated_at"] = current_time
                    
                    # If quantity is being updated, add to existing quantity
                    if ingredient_create.quantity:
                        existing_quantity = existing_ingredient.get("quantity", 0)
                        update_data["quantity"] = existing_quantity + ingredient_create.quantity
                    
                    success = await firebase_service.update_document("ingredients", ingredient_id, update_data)
                    if success:
                        updated_ingredient_ids.append(ingredient_id)
                        logger.info(f"Updated existing ingredient: {ingredient_create.name}")
                    else:
                        logger.error(f"Failed to update ingredient: {ingredient_create.name}")
                else:
                    # Create new ingredient
                    ingredient_id = str(uuid.uuid4())
                    ingredient_data = ingredient_create.dict()
                    ingredient_data.update({
                        "id": ingredient_id,
                        "created_at": current_time,
                        "updated_at": current_time
                    })
                    
                    success = await firebase_service.create_document("ingredients", ingredient_id, ingredient_data)
                    if success:
                        updated_ingredient_ids.append(ingredient_id)
                        logger.info(f"Created new ingredient: {ingredient_create.name}")
                    else:
                        logger.error(f"Failed to create ingredient: {ingredient_create.name}")
                        
            except Exception as e:
                logger.error(f"Error processing ingredient {ingredient_create.name}: {e}")
                continue
        
        return {
            "success": True,
            "updated_ingredient_ids": updated_ingredient_ids,
            "message": f"Successfully processed {len(updated_ingredient_ids)} ingredients"
        }
        
    except Exception as e:
        logger.error(f"Error updating ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update ingredients: {str(e)}")

@router.post("/upload-image/{ingredient_id}")
async def upload_ingredient_image(ingredient_id: str, file: UploadFile = File(...)):
    """Upload an image for an ingredient"""
    try:
        # Check if ingredient exists
        existing_ingredient = await firebase_service.get_document("ingredients", ingredient_id)
        if not existing_ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Upload to Firebase Storage
            blob_name = f"ingredients/{ingredient_id}/{file.filename}"
            image_url = await firebase_service.upload_image(tmp_file_path, blob_name)
            
            if not image_url:
                raise HTTPException(status_code=500, detail="Failed to upload image")
            
            # Update ingredient with image URL
            update_data = {
                "image_url": image_url,
                "updated_at": datetime.utcnow()
            }
            
            success = await firebase_service.update_document("ingredients", ingredient_id, update_data)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update ingredient with image URL")
            
            return {"message": "Image uploaded successfully", "image_url": image_url}
        
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@router.get("/expiring/soon", response_model=List[Ingredient])
async def get_expiring_ingredients(days: int = 3):
    """Get ingredients that are expiring within specified days"""
    try:
        from datetime import date, timedelta
        
        cutoff_date = date.today() + timedelta(days=days)
        
        # This is a simplified version - in a real implementation, 
        # you'd want to use Firestore's query capabilities more effectively
        all_ingredients = await firebase_service.get_collection("ingredients")
        
        expiring_ingredients = []
        for ingredient_data in all_ingredients:
            if ingredient_data.get("expiration_date"):
                exp_date = datetime.fromisoformat(ingredient_data["expiration_date"]).date()
                if exp_date <= cutoff_date:
                    expiring_ingredients.append(Ingredient(**ingredient_data))
        
        return expiring_ingredients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching expiring ingredients: {str(e)}")

# Helper functions
def _parse_expiration_days(expiration_str: str) -> int:
    """Parse expiration string to number of days"""
    expiration_lower = expiration_str.lower()
    
    if 'day' in expiration_lower:
        # Extract number of days
        import re
        numbers = re.findall(r'\d+', expiration_str)
        if numbers:
            return int(numbers[0])
        return 7  # Default to 7 days
    elif 'week' in expiration_lower:
        # Extract number of weeks and convert to days
        import re
        numbers = re.findall(r'\d+', expiration_str)
        if numbers:
            return int(numbers[0]) * 7
        return 7  # Default to 1 week
    elif 'month' in expiration_lower:
        # Extract number of months and convert to days
        import re
        numbers = re.findall(r'\d+', expiration_str)
        if numbers:
            return int(numbers[0]) * 30
        return 30  # Default to 1 month
    else:
        return 7  # Default to 7 days

def _parse_quantity_value(quantity_str: str) -> float:
    """Parse quantity from string"""
    try:
        import re
        numbers = re.findall(r'\d+\.?\d*', quantity_str)
        if numbers:
            return float(numbers[0])
        return 1.0
    except:
        return 1.0

def _parse_unit_value(quantity_str: str) -> str:
    """Parse unit from quantity string"""
    quantity_lower = quantity_str.lower()
    
    if 'piece' in quantity_lower or 'item' in quantity_lower:
        return 'pieces'
    elif 'bottle' in quantity_lower:
        return 'bottles'
    elif 'container' in quantity_lower or 'box' in quantity_lower:
        return 'containers'
    elif 'cup' in quantity_lower:
        return 'cups'
    elif 'lb' in quantity_lower or 'pound' in quantity_lower:
        return 'lbs'
    elif 'kg' in quantity_lower:
        return 'kg'
    elif 'carton' in quantity_lower:
        return 'cartons'
    elif 'loaf' in quantity_lower or 'loaves' in quantity_lower:
        return 'loaves'
    elif 'block' in quantity_lower:
        return 'blocks'
    else:
        return 'pieces'

def _guess_ingredient_category(ingredient_name: str):
    """Guess ingredient category based on name"""
    from app.models.ingredient import IngredientCategory
    
    name_lower = ingredient_name.lower()
    
    # Simple category mapping
    if any(word in name_lower for word in ['apple', 'banana', 'orange', 'berry', 'grape', 'lemon', 'lime']):
        return IngredientCategory.FRUIT
    elif any(word in name_lower for word in ['tomato', 'onion', 'carrot', 'lettuce', 'spinach', 'potato', 'pepper']):
        return IngredientCategory.VEGETABLE
    elif any(word in name_lower for word in ['chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb']):
        return IngredientCategory.MEAT
    elif any(word in name_lower for word in ['milk', 'cheese', 'yogurt', 'butter', 'cream']):
        return IngredientCategory.DAIRY
    elif any(word in name_lower for word in ['rice', 'bread', 'pasta', 'flour', 'oats', 'quinoa']):
        return IngredientCategory.GRAIN
    elif any(word in name_lower for word in ['salt', 'pepper', 'garlic', 'ginger', 'basil', 'oregano']):
        return IngredientCategory.SPICE
    elif any(word in name_lower for word in ['sauce', 'oil', 'vinegar', 'ketchup', 'mustard']):
        return IngredientCategory.CONDIMENT
    elif any(word in name_lower for word in ['juice', 'water', 'soda', 'coffee', 'tea']):
        return IngredientCategory.BEVERAGE
    else:
        return IngredientCategory.OTHER