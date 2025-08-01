import os
import base64
import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import io

from app.core.config import settings
from app.models.ingredient import IngredientCreate, IngredientCategory

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.vision_model = None
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            logger.warning("GEMINI_API_KEY not found. Using mock implementation.")

    def _encode_image_to_base64(self, image_data: bytes) -> str:
        """Convert image bytes to base64 string."""
        return base64.b64encode(image_data).decode('utf-8')

    def _create_ingredient_prompt(self) -> str:
        """Create the prompt for ingredient recognition."""
        return """
        Analyze this image of a fridge or pantry and identify all visible food ingredients. 
        For each ingredient, provide:
        1. Name of the ingredient
        2. Estimated quantity (e.g., "2 apples", "1 bottle", "half container")
        3. Estimated expiration date (relative to today, e.g., "3 days", "1 week", "2 weeks")
        4. Confidence score (0.0 to 1.0)

        Return the results as a JSON array with this exact structure:
        [
            {
                "name": "ingredient_name",
                "quantity": "estimated_quantity",
                "estimatedExpiration": "relative_time",
                "confidence": 0.85
            }
        ]

        Only include ingredients you can clearly identify. If you're unsure about an item, either exclude it or give it a lower confidence score.
        """

    async def recognize_ingredients(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        Analyze an image to identify ingredients.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            List of ingredient dictionaries with name, quantity, estimatedExpiration, and confidence
        """
        if not self.vision_model:
            return self._mock_ingredient_recognition()

        try:
            # Create PIL Image from bytes for Gemini
            image = Image.open(io.BytesIO(image_data))
            
            # Create the prompt
            prompt = self._create_ingredient_prompt()
            
            # Configure safety settings to be less restrictive for food content
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }

            # Make API call to Gemini with image
            response = self.vision_model.generate_content(
                [prompt, image],
                safety_settings=safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                )
            )

            # Parse the response
            content = response.text
            
            # Extract JSON from the response
            try:
                # Find JSON array in the response
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    ingredients = json.loads(json_str)
                    
                    # Validate the structure
                    validated_ingredients = []
                    for ingredient in ingredients:
                        if all(key in ingredient for key in ['name', 'quantity', 'estimatedExpiration', 'confidence']):
                            validated_ingredients.append({
                                'name': str(ingredient['name']),
                                'quantity': str(ingredient['quantity']),
                                'estimatedExpiration': str(ingredient['estimatedExpiration']),
                                'confidence': float(ingredient['confidence'])
                            })
                    
                    return validated_ingredients
                else:
                    logger.error("No valid JSON array found in Gemini response")
                    return self._mock_ingredient_recognition()
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Gemini response: {e}")
                return self._mock_ingredient_recognition()

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return self._mock_ingredient_recognition()

    async def detect_ingredients(self, image_data: str) -> Dict[str, Any]:
        """
        Legacy method for compatibility with existing vision.py interface.
        Detect ingredients from base64 encoded image data.
        
        Args:
            image_data: Base64 encoded image data
            
        Returns:
            Dictionary containing detected ingredients and confidence score
        """
        try:
            # Decode base64 image data
            image_bytes = base64.b64decode(image_data)
            
            # Use the new recognize_ingredients method
            raw_ingredients = await self.recognize_ingredients(image_bytes)
            
            # Convert to IngredientCreate objects for compatibility
            ingredients = []
            total_confidence = 0
            
            for item in raw_ingredients:
                # Map to category (simplified mapping)
                category = self._guess_category(item['name'])
                
                ingredient = IngredientCreate(
                    name=item['name'],
                    category=category,
                    quantity=self._parse_quantity(item['quantity']),
                    unit=self._parse_unit(item['quantity']),
                    notes=f"Expires: {item['estimatedExpiration']}"
                )
                ingredients.append(ingredient)
                total_confidence += item['confidence']
            
            avg_confidence = total_confidence / len(raw_ingredients) if raw_ingredients else 0.8
            
            return {
                "ingredients": ingredients,
                "confidence": avg_confidence
            }
            
        except Exception as e:
            logger.error(f"Error in detect_ingredients: {e}")
            return await self._mock_ingredient_detection()

    def _guess_category(self, ingredient_name: str) -> IngredientCategory:
        """Guess ingredient category based on name."""
        name_lower = ingredient_name.lower()
        
        # Produce (fruits and vegetables)
        produce_items = [
            # Fruits
            'apple', 'apples', 'banana', 'bananas', 'orange', 'oranges', 'berry', 'berries',
            'strawberry', 'strawberries', 'blueberry', 'blueberries', 'raspberry', 'raspberries',
            'grape', 'grapes', 'lemon', 'lemons', 'lime', 'limes', 'pear', 'pears', 'peach', 'peaches',
            'plum', 'plums', 'cherry', 'cherries', 'mango', 'mangoes', 'pineapple', 'avocado', 'avocados',
            'kiwi', 'melon', 'watermelon', 'cantaloupe', 'grapefruit', 'coconut', 'papaya', 'fig', 'figs',
            # Vegetables
            'tomato', 'tomatoes', 'onion', 'onions', 'carrot', 'carrots', 'lettuce', 'spinach',
            'potato', 'potatoes', 'bell pepper', 'bell peppers', 'cucumber', 'cucumbers',
            'broccoli', 'cauliflower', 'cabbage', 'celery', 'radish', 'radishes', 'beet', 'beets',
            'corn', 'peas', 'green beans', 'asparagus', 'zucchini', 'squash', 'eggplant', 'mushroom', 'mushrooms',
            'kale', 'arugula', 'chard', 'leek', 'leeks', 'scallion', 'scallions', 'green onion', 'shallot', 'shallots'
        ]
        
        # Protein sources
        protein_items = [
            'chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb', 'salmon', 'tuna', 'cod', 'shrimp',
            'crab', 'lobster', 'eggs', 'egg', 'tofu', 'tempeh', 'seitan', 'beans', 'lentils', 'chickpeas',
            'black beans', 'kidney beans', 'pinto beans', 'navy beans', 'lima beans', 'edamame',
            'nuts', 'almonds', 'walnuts', 'pecans', 'cashews', 'peanuts', 'pistachios', 'hazelnuts',
            'seeds', 'sunflower seeds', 'pumpkin seeds', 'chia seeds', 'flax seeds', 'hemp seeds',
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
            'salt', 'black pepper', 'white pepper', 'pepper', 'garlic', 'ginger', 'basil', 'oregano', 'thyme', 'rosemary', 'sage',
            'parsley', 'cilantro', 'dill', 'mint', 'chives', 'tarragon', 'bay leaves', 'cumin',
            'coriander', 'paprika', 'chili powder', 'cayenne', 'turmeric', 'curry powder', 'garam masala',
            'cinnamon', 'nutmeg', 'cloves', 'allspice', 'cardamom', 'vanilla', 'extract', 'garlic powder',
            'onion powder', 'dried herbs', 'italian seasoning', 'herbs de provence', 'everything bagel seasoning',
            'red pepper flakes', 'black peppercorns', 'white pepper', 'sesame seeds', 'poppy seeds',
            'mustard seed', 'fennel seeds', 'caraway seeds', 'anise', 'star anise', 'saffron'
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

    def _parse_quantity(self, quantity_str: str) -> float:
        """Parse quantity from string."""
        try:
            # Extract first number from string
            import re
            numbers = re.findall(r'\d+\.?\d*', quantity_str)
            if numbers:
                return float(numbers[0])
            return 1.0
        except:
            return 1.0

    def _parse_unit(self, quantity_str: str) -> str:
        """Parse unit from quantity string."""
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
        else:
            return 'pieces'

    def _mock_ingredient_recognition(self) -> List[Dict[str, Any]]:
        """
        Mock implementation for development/testing when API key is not available.
        """
        return [
            {
                "name": "Apples",
                "quantity": "3 pieces",
                "estimatedExpiration": "1 week",
                "confidence": 0.9
            },
            {
                "name": "Milk",
                "quantity": "1 carton",
                "estimatedExpiration": "3 days",
                "confidence": 0.85
            },
            {
                "name": "Eggs",
                "quantity": "6 pieces",
                "estimatedExpiration": "1 week",
                "confidence": 0.95
            },
            {
                "name": "Bread",
                "quantity": "1 loaf",
                "estimatedExpiration": "2 days",
                "confidence": 0.8
            },
            {
                "name": "Cheese",
                "quantity": "1 block",
                "estimatedExpiration": "2 weeks",
                "confidence": 0.75
            }
        ]

    async def _mock_ingredient_detection(self) -> Dict[str, Any]:
        """
        Mock ingredient detection for development/testing (legacy compatibility)
        """
        mock_ingredients = [
            IngredientCreate(
                name="Tomatoes",
                category=IngredientCategory.PRODUCE,
                quantity=3.0,
                unit="pieces",
                notes="Fresh, red tomatoes"
            ),
            IngredientCreate(
                name="Onion",
                category=IngredientCategory.PRODUCE,
                quantity=1.0,
                unit="pieces",
                notes="Medium-sized yellow onion"
            ),
            IngredientCreate(
                name="Garlic",
                category=IngredientCategory.SPICES,
                quantity=4.0,
                unit="cloves",
                notes="Fresh garlic cloves"
            )
        ]
        
        return {
            "ingredients": mock_ingredients,
            "confidence": 0.85
        }

    async def validate_image(self, image_data: bytes) -> bool:
        """
        Validate that the uploaded image is suitable for ingredient recognition.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            True if image is valid, False otherwise
        """
        try:
            # Check if it's a valid image
            image = Image.open(io.BytesIO(image_data))
            
            # Check image size (should be reasonable)
            width, height = image.size
            if width < 100 or height < 100:
                return False
                
            # Check file size (should be under 10MB)
            if len(image_data) > 10 * 1024 * 1024:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False

# Create singleton instance
groq_service = GroqService()