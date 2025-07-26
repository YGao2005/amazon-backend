from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Any, Optional
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

# Response models for scan endpoint
class QuantityInfo(BaseModel):
    amount: float
    unit: str

class ScannedIngredient(BaseModel):
    name: str
    quantity: QuantityInfo
    estimatedExpiration: Optional[str] = None
    category: str

# Legacy response models (keeping for backward compatibility if needed)
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
                    "expirationDate": ingredient.expiration_date.isoformat() if ingredient.expiration_date else None,
                    "purchaseDate": ingredient.purchase_date.isoformat() if ingredient.purchase_date else None,
                    "createdAt": ingredient.created_at.isoformat() if ingredient.created_at else None,
                    "updatedAt": ingredient.updated_at.isoformat() if ingredient.updated_at else None,
                    "location": ingredient.location,
                    "notes": ingredient.notes,
                    "imageName": ingredient.image_url
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

@router.post("/scan", response_model=List[ScannedIngredient])
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
            return []
        
        # Process and store recognized ingredients in Firebase
        scanned_ingredients = []
        current_date = datetime.now()
        
        for ingredient_data in recognized_ingredients:
            try:
                # Parse expiration date from relative time (e.g., "3 days", "1 week")
                expiration_str = ingredient_data.get('estimatedExpiration', '7 days')
                expiration_days = _parse_expiration_days(expiration_str)
                estimated_expiration = current_date + timedelta(days=expiration_days)
                
                # Parse quantity and unit using existing helper functions
                quantity_str = ingredient_data.get('quantity', '1 unit')
                quantity_amount = _parse_quantity_value(quantity_str)
                quantity_unit = _parse_unit_value(quantity_str)
                
                # Guess category
                category = _guess_ingredient_category(ingredient_data['name'])
                
                # Check if ingredient already exists (case-insensitive)
                existing_ingredient = await _find_existing_ingredient_by_name(ingredient_data['name'])
                
                if existing_ingredient:
                    # Update existing ingredient by merging quantities
                    ingredient_id = existing_ingredient["id"]
                    existing_quantity = existing_ingredient.get("quantity", 0)
                    existing_unit = existing_ingredient.get("unit", quantity_unit)
                    existing_expiration = existing_ingredient.get("expiration_date")
                    
                    # Merge quantities (only if units match, otherwise keep separate)
                    if existing_unit.lower() == quantity_unit.lower():
                        new_quantity = existing_quantity + quantity_amount
                    else:
                        # If units don't match, keep the new quantity and unit
                        new_quantity = quantity_amount
                        quantity_unit = quantity_unit
                    
                    # Use the earlier expiration date (more conservative approach)
                    if existing_expiration:
                        existing_exp_date = datetime.fromisoformat(existing_expiration.replace('Z', '+00:00')) if isinstance(existing_expiration, str) else existing_expiration
                        final_expiration = min(estimated_expiration, existing_exp_date)
                    else:
                        final_expiration = estimated_expiration
                    
                    # Prepare update data
                    update_data = {
                        "quantity": new_quantity,
                        "unit": quantity_unit,
                        "expiration_date": final_expiration,
                        "updated_at": current_date,
                        "notes": f"Updated from scan, confidence: {ingredient_data.get('confidence', 0.8):.2f}. Previous quantity: {existing_quantity} {existing_unit}"
                    }
                    
                    success = await firebase_service.update_document("ingredients", ingredient_id, update_data)
                    if success:
                        # Create the response format that matches Swift expectations
                        scanned_ingredient = ScannedIngredient(
                            name=ingredient_data['name'],
                            quantity=QuantityInfo(
                                amount=new_quantity,
                                unit=quantity_unit
                            ),
                            estimatedExpiration=final_expiration.isoformat() + "Z",  # ISO8601 format with Z suffix
                            category=category.value  # Include the category in the response
                        )
                        scanned_ingredients.append(scanned_ingredient)
                        logger.info(f"Successfully updated existing ingredient: {ingredient_data['name']} (quantity: {existing_quantity} -> {new_quantity})")
                    else:
                        logger.error(f"Failed to update existing ingredient: {ingredient_data['name']}")
                else:
                    # Create new ingredient
                    ingredient_create = IngredientCreate(
                        name=ingredient_data['name'],
                        category=category,
                        quantity=quantity_amount,
                        unit=quantity_unit,
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
                        # Create the response format that matches Swift expectations
                        scanned_ingredient = ScannedIngredient(
                            name=ingredient_data['name'],
                            quantity=QuantityInfo(
                                amount=quantity_amount,
                                unit=quantity_unit
                            ),
                            estimatedExpiration=estimated_expiration.isoformat() + "Z",  # ISO8601 format with Z suffix
                            category=category.value  # Include the category in the response
                        )
                        scanned_ingredients.append(scanned_ingredient)
                        logger.info(f"Successfully created new ingredient: {ingredient_data['name']}")
                    else:
                        logger.error(f"Failed to create new ingredient: {ingredient_data['name']}")
                    
            except Exception as e:
                logger.error(f"Error processing ingredient {ingredient_data.get('name', 'unknown')}: {e}")
                continue
        
        return scanned_ingredients
        
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
async def _find_existing_ingredient_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find existing ingredient by name (case-insensitive)"""
    try:
        # Query for ingredients with matching name (case-insensitive)
        existing_ingredients = await firebase_service.query_collection(
            "ingredients", "name", "==", name
        )
        
        if existing_ingredients:
            return existing_ingredients[0]  # Return the first match
        
        # If no exact match, try case-insensitive search
        all_ingredients = await firebase_service.get_collection("ingredients")
        for ingredient in all_ingredients:
            if ingredient.get("name", "").lower() == name.lower():
                return ingredient
        
        return None
    except Exception as e:
        logger.error(f"Error finding existing ingredient by name '{name}': {e}")
        return None

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
    
    # Produce (fruits and vegetables) - map both FRUIT and VEGETABLE to PRODUCE
    produce_items = [
        # Fruits
        'apple', 'apples', 'banana', 'bananas', 'orange', 'oranges', 'berry', 'berries',
        'strawberry', 'strawberries', 'blueberry', 'blueberries', 'raspberry', 'raspberries',
        'grape', 'grapes', 'lemon', 'lemons', 'lime', 'limes', 'pear', 'pears', 'peach', 'peaches',
        'plum', 'plums', 'cherry', 'cherries', 'mango', 'mangoes', 'pineapple', 'avocado', 'avocados',
        'kiwi', 'melon', 'watermelon', 'cantaloupe', 'grapefruit', 'coconut', 'papaya', 'fig', 'figs',
        # Vegetables
        'tomato', 'tomatoes', 'onion', 'onions', 'carrot', 'carrots', 'lettuce', 'spinach',
        'potato', 'potatoes', 'bell pepper', 'bell peppers', 'green bell pepper', 'green bell peppers',
        'red bell pepper', 'red bell peppers', 'yellow bell pepper', 'yellow bell peppers',
        'cucumber', 'cucumbers', 'broccoli', 'cauliflower', 'cabbage', 'celery', 'radish', 'radishes',
        'beet', 'beets', 'corn', 'peas', 'green beans', 'asparagus', 'zucchini', 'squash', 'eggplant',
        'mushroom', 'mushrooms', 'kale', 'arugula', 'chard', 'leek', 'leeks', 'scallion', 'scallions',
        'green onion', 'shallot', 'shallots', 'pepper', 'peppers'
    ]
    
    # Protein sources
    protein_items = [
        'chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb', 'salmon', 'tuna', 'cod', 'shrimp',
        'crab', 'lobster', 'eggs', 'egg', 'tofu', 'tempeh', 'seitan', 'beans', 'lentils', 'chickpeas',
        'black beans', 'kidney beans', 'pinto beans', 'navy beans', 'lima beans', 'edamame',
        'nuts', 'almonds', 'walnuts', 'pecans', 'cashews', 'peanuts', 'pistachios', 'hazelnuts',
        'bacon', 'ham', 'sausage', 'ground beef', 'ground turkey', 'ground chicken', 'steak',
        'pork chops', 'chicken breast', 'chicken thighs', 'duck', 'venison', 'bison'
    ]
    
    # Dairy products
    dairy_items = [
        'milk', 'cheese', 'yogurt', 'butter', 'cream', 'sour cream', 'cottage cheese', 'ricotta',
        'mozzarella', 'cheddar', 'swiss', 'parmesan', 'feta', 'goat cheese', 'cream cheese',
        'half and half', 'heavy cream', 'whipped cream', 'ice cream', 'frozen yogurt', 'kefir',
        'buttermilk', 'condensed milk', 'evaporated milk', 'powdered milk'
    ]
    
    # Grains and starches
    grain_items = [
        'rice', 'bread', 'pasta', 'flour', 'oats', 'quinoa', 'barley', 'wheat', 'rye', 'millet',
        'buckwheat', 'amaranth', 'bulgur', 'couscous', 'farro', 'spelt', 'teff', 'cornmeal',
        'polenta', 'grits', 'cereal', 'crackers', 'bagel', 'bagels', 'muffin', 'muffins',
        'tortilla', 'tortillas', 'pita', 'naan', 'rolls', 'buns', 'croissant', 'croissants',
        'pancake mix', 'baking mix', 'breadcrumbs', 'oatmeal', 'granola', 'muesli'
    ]
    
    # Spices and seasonings
    spice_items = [
        'salt', 'black pepper', 'white pepper', 'garlic', 'ginger', 'basil', 'oregano', 'thyme', 'rosemary', 'sage',
        'parsley', 'cilantro', 'dill', 'mint', 'chives', 'tarragon', 'bay leaves', 'cumin',
        'coriander', 'paprika', 'chili powder', 'cayenne', 'turmeric', 'curry powder', 'garam masala',
        'cinnamon', 'nutmeg', 'cloves', 'allspice', 'cardamom', 'vanilla', 'extract', 'garlic powder',
        'onion powder', 'dried herbs', 'italian seasoning', 'herbs de provence', 'everything bagel seasoning',
        'red pepper flakes', 'black peppercorns', 'mustard seed', 'fennel seeds', 'caraway seeds',
        'anise', 'star anise', 'saffron'
    ]
    
    # Check each category - check spices first since some items like "pepper" could be ambiguous
    if any(item in name_lower for item in spice_items):
        return IngredientCategory.SPICES
    elif any(item in name_lower for item in produce_items):
        return IngredientCategory.PRODUCE
    elif any(item in name_lower for item in protein_items):
        return IngredientCategory.PROTEIN
    elif any(item in name_lower for item in dairy_items):
        return IngredientCategory.DAIRY
    elif any(item in name_lower for item in grain_items):
        return IngredientCategory.GRAINS
    else:
        return IngredientCategory.OTHER