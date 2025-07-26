import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import google.genai as genai_client
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import asyncio
import os
import uuid

from app.core.config import settings
from app.models.recipe import (
    RecipeCreate, RecipeGenerationRequest, RecipeIngredient,
    RecipeStep, DifficultyLevel, MealType, NutritionInfo
)
from app.services.firebase.storage import firebase_storage_service

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.flash_model = genai.GenerativeModel('gemini-1.5-flash')
            self.vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            # Initialize Gemini 2.0 client for image generation
            self.genai_client = genai_client.Client(api_key=self.api_key)
        else:
            logger.warning("GEMINI_API_KEY not found. Using mock implementation.")
            self.flash_model = None
            self.vision_model = None
            self.genai_client = None

    def _create_recipe_prompt(self, ingredients: List[str], dietary_restrictions: List[str] = None, 
                            cuisine_preference: str = None, difficulty: str = "medium") -> str:
        """Create the prompt for recipe generation."""
        restrictions_text = ""
        if dietary_restrictions:
            restrictions_text = f"\nDietary restrictions: {', '.join(dietary_restrictions)}"
        
        cuisine_text = ""
        if cuisine_preference:
            cuisine_text = f"\nCuisine preference: {cuisine_preference}"
            
        return f"""
        Create a detailed recipe using the following available ingredients: {', '.join(ingredients)}
        
        Requirements:
        - Use as many of the provided ingredients as possible
        - Difficulty level: {difficulty}
        {restrictions_text}
        {cuisine_text}
        
        Return the recipe as a JSON object with this exact structure:
        {{
            "name": "Recipe Name",
            "description": "Brief description of the dish",
            "prepTime": "15 minutes",
            "cookTime": "30 minutes",
            "totalTime": "45 minutes",
            "servings": 4,
            "difficulty": "medium",
            "cuisine": "cuisine_type",
            "ingredients": [
                {{
                    "name": "ingredient_name",
                    "amount": "quantity",
                    "unit": "unit_of_measurement"
                }}
            ],
            "instructions": [
                "Step 1: Detailed instruction",
                "Step 2: Detailed instruction"
            ],
            "nutritionalInfo": {{
                "calories": 350,
                "protein": "25g",
                "carbs": "30g",
                "fat": "15g",
                "fiber": "5g"
            }},
            "tags": ["tag1", "tag2", "tag3"],
            "tips": [
                "Helpful tip 1",
                "Helpful tip 2"
            ]
        }}
        
        Make sure the recipe is practical, delicious, and uses the ingredients efficiently.
        """

    async def generate_recipe(self, ingredients: List[str], dietary_restrictions: List[str] = None,
                            cuisine_preference: str = None, difficulty: str = "medium") -> Dict[str, Any]:
        """
        Generate a recipe based on available ingredients and preferences.
        
        Args:
            ingredients: List of available ingredient names
            dietary_restrictions: Optional list of dietary restrictions
            cuisine_preference: Optional cuisine preference
            difficulty: Recipe difficulty level (easy, medium, hard)
            
        Returns:
            Dictionary containing complete recipe information
        """
        if not self.flash_model:
            return self._mock_recipe_generation(ingredients, dietary_restrictions, cuisine_preference)

        try:
            prompt = self._create_recipe_prompt(ingredients, dietary_restrictions, cuisine_preference, difficulty)
            
            # Configure safety settings to be less restrictive for food content
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            response = self.flash_model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2000,
                )
            )
            
            # Parse the JSON response
            content = response.text
            
            try:
                # Find JSON object in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    recipe = json.loads(json_str)
                    
                    # Validate and clean the recipe structure
                    return self._validate_recipe_structure(recipe)
                else:
                    logger.error("No valid JSON object found in Gemini response")
                    return self._mock_recipe_generation(ingredients, dietary_restrictions, cuisine_preference)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Gemini response: {e}")
                return self._mock_recipe_generation(ingredients, dietary_restrictions, cuisine_preference)

        except Exception as e:
            logger.error(f"Error calling Gemini API for recipe generation: {e}")
            return self._mock_recipe_generation(ingredients, dietary_restrictions, cuisine_preference)

    async def generate_recipe_image(self, recipe_name: str, recipe_description: str) -> Optional[str]:
        """
        Generate an appealing food image for a recipe using Gemini 2.0.
        
        Args:
            recipe_name: Name of the recipe
            recipe_description: Description of the dish
            
        Returns:
            URL of the generated image (saved locally) or None if failed
        """
        logger.info(f"GEMINI IMAGE DEBUG: Starting image generation for recipe: {recipe_name}")
        
        # Validate inputs first
        if not self._validate_image_generation_inputs(recipe_name, recipe_description):
            logger.error(f"GEMINI IMAGE DEBUG: Invalid inputs for image generation: recipe_name='{recipe_name}', description='{recipe_description}'")
            return self._mock_image_generation()
        
        if not self.genai_client:
            logger.warning("GEMINI IMAGE DEBUG: Gemini client not available, using mock image generation")
            return self._mock_image_generation()

        try:
            # Create a safe, well-structured prompt
            prompt = self._create_safe_image_prompt(recipe_name, recipe_description)
            
            logger.info(f"GEMINI IMAGE DEBUG: About to call Gemini API for recipe: {recipe_name}")
            logger.debug(f"Using prompt: {prompt[:100]}...")
            
            # Use Gemini 2.0 image generation API with error handling
            try:
                response = self.genai_client.models.generate_content(
                    model="gemini-2.0-flash-preview-image-generation",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=['TEXT', 'IMAGE']
                    )
                )
            except Exception as api_error:
                logger.error(f"Gemini API call failed: {api_error}")
                return self._mock_image_generation()
            
            # Validate response structure
            if not response or not response.candidates:
                logger.error("Invalid response structure from Gemini API")
                return self._mock_image_generation()
            
            # Process the response to extract and save the image
            image_saved = False
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    try:
                        # Convert image data to PIL Image
                        image = Image.open(BytesIO(part.inline_data.data))
                        
                        # Validate image
                        if image.size[0] < 100 or image.size[1] < 100:
                            logger.warning(f"Generated image too small: {image.size}")
                            continue
                        
                        # Create images directory if it doesn't exist
                        images_dir = "generated_images"
                        os.makedirs(images_dir, exist_ok=True)
                        
                        # Generate safe filename
                        safe_name = "".join(c for c in recipe_name if c.isalnum() or c in (' ', '-', '_')).strip()
                        safe_name = safe_name.replace(' ', '_').lower()[:50]  # Limit length
                        image_filename = f"recipe_{uuid.uuid4().hex[:8]}_{safe_name}.png"
                        image_path = os.path.join(images_dir, image_filename)
                        
                        # Save the image with error handling
                        image.save(image_path, "PNG", optimize=True)
                        
                        # Verify file was saved successfully
                        if os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                            logger.info(f"Successfully generated and saved image: {image_path} (size: {image.size})")
                            
                            # Upload to Firebase Storage
                            try:
                                logger.info(f"FIREBASE UPLOAD DEBUG: Starting Firebase upload for image: {image_path}")
                                
                                # Read the image file as bytes
                                with open(image_path, 'rb') as img_file:
                                    image_bytes = img_file.read()
                                
                                # Generate a unique recipe ID for the upload
                                recipe_id = uuid.uuid4().hex[:12]
                                logger.info(f"FIREBASE UPLOAD DEBUG: Generated recipe_id for upload: {recipe_id}")
                                
                                # Upload to Firebase Storage
                                firebase_url = await firebase_storage_service.upload_recipe_image(
                                    image_data=image_bytes,
                                    recipe_id=recipe_id
                                )
                                
                                if firebase_url:
                                    logger.info(f"FIREBASE UPLOAD DEBUG: Successfully uploaded image to Firebase Storage: {firebase_url}")
                                    
                                    # Clean up local file after successful upload
                                    try:
                                        os.remove(image_path)
                                        logger.info(f"FIREBASE UPLOAD DEBUG: Cleaned up local image file: {image_path}")
                                    except Exception as cleanup_error:
                                        logger.warning(f"FIREBASE UPLOAD DEBUG: Failed to clean up local file {image_path}: {cleanup_error}")
                                    
                                    image_saved = True
                                    logger.info(f"GEMINI IMAGE DEBUG: Returning Firebase URL for recipe: {recipe_name}")
                                    return firebase_url
                                else:
                                    logger.error("Firebase Storage upload returned None - falling back to local path")
                                    # Fall back to local path if Firebase upload fails
                                    image_saved = True
                                    return f"/{image_path}"
                                    
                            except Exception as upload_error:
                                logger.error(f"Failed to upload image to Firebase Storage: {upload_error}")
                                # Fall back to local path if Firebase upload fails
                                logger.info(f"Falling back to local path: /{image_path}")
                                image_saved = True
                                return f"/{image_path}"
                        else:
                            logger.error(f"Failed to save image file: {image_path}")
                            
                    except Exception as img_error:
                        logger.error(f"Error processing image data: {img_error}")
                        continue
                        
                elif part.text is not None:
                    logger.info(f"Generated image description: {part.text[:100]}...")
            
            if not image_saved:
                logger.warning("No valid image data found in Gemini response")
                return self._mock_image_generation()
            
        except Exception as e:
            logger.error(f"Unexpected error in generate_recipe_image: {e}", exc_info=True)
            # Fall back to mock generation on error
            return self._mock_image_generation()
        
        # Should not reach here, but just in case
        logger.error("Reached end of generate_recipe_image without returning")
        return self._mock_image_generation()

    # Legacy method for compatibility with existing recipe_generator.py interface
    async def generate_recipe_legacy(self, request: RecipeGenerationRequest) -> Dict[str, Any]:
        """
        Legacy method for compatibility with existing interface.
        Generate a recipe based on RecipeGenerationRequest.
        """
        try:
            # Convert to new format
            recipe_dict = await self.generate_recipe(
                ingredients=request.available_ingredients,
                dietary_restrictions=request.dietary_restrictions,
                cuisine_preference=request.cuisine,
                difficulty=request.max_prep_time and "easy" if request.max_prep_time < 30 else "medium"
            )
            
            # Convert back to RecipeCreate format
            recipe = self._dict_to_recipe_create(recipe_dict, request)
            
            # Determine missing ingredients
            missing_ingredients = self._find_missing_ingredients(
                request.available_ingredients, 
                recipe_dict.get("ingredients", [])
            )
            
            return {
                "recipe": recipe,
                "missing_ingredients": missing_ingredients,
                "confidence": 0.8
            }
            
        except Exception as e:
            logger.error(f"Error in legacy recipe generation: {e}")
            return await self._mock_recipe_generation_legacy(request)

    def _dict_to_recipe_create(self, recipe_dict: Dict[str, Any], request: RecipeGenerationRequest) -> RecipeCreate:
        """Convert recipe dictionary to RecipeCreate object."""
        
        # Parse ingredients
        ingredients = []
        for ing_data in recipe_dict.get("ingredients", []):
            ingredient = RecipeIngredient(
                name=ing_data["name"],
                quantity=self._parse_quantity(ing_data["amount"]),
                unit=ing_data["unit"],
                optional=False
            )
            ingredients.append(ingredient)
        
        # Parse steps
        steps = []
        for i, instruction in enumerate(recipe_dict.get("instructions", [])):
            step = RecipeStep(
                step_number=i + 1,
                instruction=instruction,
                duration_minutes=None
            )
            steps.append(step)
        
        # Parse nutrition info
        nutrition = None
        if recipe_dict.get("nutritionalInfo"):
            nutrition_data = recipe_dict["nutritionalInfo"]
            nutrition = NutritionInfo(
                calories=self._parse_int(nutrition_data.get("calories")),
                protein_g=self._parse_float(nutrition_data.get("protein", "0g")),
                carbs_g=self._parse_float(nutrition_data.get("carbs", "0g")),
                fat_g=self._parse_float(nutrition_data.get("fat", "0g")),
                fiber_g=self._parse_float(nutrition_data.get("fiber", "0g"))
            )
        
        # Map difficulty
        difficulty_map = {
            "easy": DifficultyLevel.EASY,
            "medium": DifficultyLevel.MEDIUM,
            "hard": DifficultyLevel.HARD
        }
        difficulty = difficulty_map.get(
            recipe_dict.get("difficulty", "medium").lower(), 
            DifficultyLevel.MEDIUM
        )
        
        # Determine meal types
        meal_types = []
        if request.meal_type:
            meal_types = [request.meal_type]
        
        recipe = RecipeCreate(
            title=recipe_dict.get("name", "Generated Recipe"),
            description=recipe_dict.get("description", ""),
            ingredients=ingredients,
            steps=steps,
            prep_time_minutes=self._parse_time(recipe_dict.get("prepTime")),
            cook_time_minutes=self._parse_time(recipe_dict.get("cookTime")),
            servings=recipe_dict.get("servings", request.servings),
            difficulty=difficulty,
            meal_type=meal_types,
            cuisine=recipe_dict.get("cuisine", request.cuisine),
            tags=recipe_dict.get("tags", []),
            nutrition=nutrition
        )
        
        return recipe

    def _parse_quantity(self, amount_str: str) -> float:
        """Parse quantity from string."""
        try:
            import re
            numbers = re.findall(r'\d+\.?\d*', str(amount_str))
            if numbers:
                return float(numbers[0])
            return 1.0
        except:
            return 1.0

    def _parse_int(self, value) -> Optional[int]:
        """Parse integer from various formats."""
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                import re
                numbers = re.findall(r'\d+', value)
                if numbers:
                    return int(numbers[0])
            return None
        except:
            return None

    def _parse_float(self, value) -> Optional[float]:
        """Parse float from various formats."""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                import re
                numbers = re.findall(r'\d+\.?\d*', value)
                if numbers:
                    return float(numbers[0])
            return None
        except:
            return None

    def _parse_time(self, time_str) -> Optional[int]:
        """Parse time in minutes from string."""
        try:
            if isinstance(time_str, int):
                return time_str
            if isinstance(time_str, str):
                import re
                numbers = re.findall(r'\d+', time_str)
                if numbers:
                    return int(numbers[0])
            return None
        except:
            return None

    def _validate_recipe_structure(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and ensure recipe has all required fields."""
        required_fields = {
            'name': 'Untitled Recipe',
            'description': 'A delicious recipe',
            'prepTime': '15 minutes',
            'cookTime': '30 minutes',
            'totalTime': '45 minutes',
            'servings': 4,
            'difficulty': 'medium',
            'cuisine': 'International',
            'ingredients': [],
            'instructions': [],
            'nutritionalInfo': {
                'calories': 0,
                'protein': '0g',
                'carbs': '0g',
                'fat': '0g',
                'fiber': '0g'
            },
            'tags': [],
            'tips': []
        }
        
        # Ensure all required fields exist
        for field, default_value in required_fields.items():
            if field not in recipe:
                recipe[field] = default_value
        
        # Validate ingredients structure
        if recipe['ingredients']:
            validated_ingredients = []
            for ingredient in recipe['ingredients']:
                if isinstance(ingredient, dict):
                    validated_ingredients.append({
                        'name': ingredient.get('name', 'Unknown'),
                        'amount': ingredient.get('amount', '1'),
                        'unit': ingredient.get('unit', 'piece')
                    })
            recipe['ingredients'] = validated_ingredients
        
        # Ensure instructions is a list
        if not isinstance(recipe['instructions'], list):
            recipe['instructions'] = [str(recipe['instructions'])]
        
        # Ensure tags is a list
        if not isinstance(recipe['tags'], list):
            recipe['tags'] = []
            
        # Ensure tips is a list
        if not isinstance(recipe['tips'], list):
            recipe['tips'] = []
        
        return recipe

    def _find_missing_ingredients(self, available: List[str], required: List[Dict[str, Any]]) -> List[str]:
        """Find ingredients that are required but not available"""
        available_lower = [ing.lower() for ing in available]
        missing = []
        
        for req_ing in required:
            ing_name = req_ing["name"].lower()
            # Check if any available ingredient contains the required ingredient name
            if not any(ing_name in avail or avail in ing_name for avail in available_lower):
                missing.append(req_ing["name"])
        
        return missing

    def _mock_recipe_generation(self, ingredients: List[str], dietary_restrictions: List[str] = None,
                              cuisine_preference: str = None) -> Dict[str, Any]:
        """Mock recipe generation for development/testing."""
        primary_ingredient = ingredients[0] if ingredients else "mixed ingredients"
        
        return {
            "name": f"Delicious {primary_ingredient.title()} Recipe",
            "description": f"A wonderful dish featuring {primary_ingredient} and other fresh ingredients",
            "prepTime": "15 minutes",
            "cookTime": "25 minutes",
            "totalTime": "40 minutes",
            "servings": 4,
            "difficulty": "medium",
            "cuisine": cuisine_preference or "International",
            "ingredients": [
                {
                    "name": ingredient,
                    "amount": "1",
                    "unit": "piece"
                } for ingredient in ingredients[:5]  # Use first 5 ingredients
            ],
            "instructions": [
                "Prepare all ingredients by washing and chopping as needed.",
                f"Heat a large pan over medium heat and add the {primary_ingredient}.",
                "Cook for 5-7 minutes until tender.",
                "Add remaining ingredients and seasonings.",
                "Cook for an additional 15-20 minutes until everything is well combined.",
                "Taste and adjust seasoning as needed.",
                "Serve hot and enjoy!"
            ],
            "nutritionalInfo": {
                "calories": 320,
                "protein": "18g",
                "carbs": "35g",
                "fat": "12g",
                "fiber": "6g"
            },
            "tags": ["healthy", "easy", "quick", cuisine_preference or "international"],
            "tips": [
                "Make sure to taste and adjust seasoning throughout cooking.",
                "This recipe can be easily doubled for larger servings.",
                "Store leftovers in the refrigerator for up to 3 days."
            ]
        }

    async def _mock_recipe_generation_legacy(self, request: RecipeGenerationRequest) -> Dict[str, Any]:
        """Mock recipe generation for legacy compatibility."""
        
        # Create a simple recipe based on available ingredients
        available_ingredients = request.available_ingredients[:3]  # Use first 3 ingredients
        
        ingredients = []
        for i, ing_name in enumerate(available_ingredients):
            ingredient = RecipeIngredient(
                name=ing_name,
                quantity=1.0 + i * 0.5,
                unit="cup" if i == 0 else "pieces",
                optional=False
            )
            ingredients.append(ingredient)
        
        # Add a common ingredient that might be missing
        ingredients.append(RecipeIngredient(
            name="Salt",
            quantity=1.0,
            unit="tsp",
            optional=False
        ))
        
        steps = [
            RecipeStep(
                step_number=1,
                instruction=f"Prepare all ingredients: {', '.join(available_ingredients)}",
                duration_minutes=5
            ),
            RecipeStep(
                step_number=2,
                instruction="Heat a pan over medium heat and add the main ingredients",
                duration_minutes=10
            ),
            RecipeStep(
                step_number=3,
                instruction="Cook until tender and season with salt to taste",
                duration_minutes=15
            ),
            RecipeStep(
                step_number=4,
                instruction="Serve hot and enjoy!",
                duration_minutes=2
            )
        ]
        
        nutrition = NutritionInfo(
            calories=320,
            protein_g=18.0,
            carbs_g=35.0,
            fat_g=12.0,
            fiber_g=6.0
        )
        
        recipe = RecipeCreate(
            title=f"Simple {available_ingredients[0]} Dish",
            description=f"A quick and easy recipe using {', '.join(available_ingredients)}",
            ingredients=ingredients,
            steps=steps,
            prep_time_minutes=10,
            cook_time_minutes=25,
            servings=request.servings,
            difficulty=DifficultyLevel.EASY,
            meal_type=[request.meal_type] if request.meal_type else [MealType.DINNER],
            cuisine=request.cuisine or "Home Cooking",
            tags=["quick", "easy", "homemade"],
            nutrition=nutrition
        )
        
        missing_ingredients = ["Salt"] if "salt" not in [ing.lower() for ing in request.available_ingredients] else []
        
        return {
            "recipe": recipe,
            "missing_ingredients": missing_ingredients,
            "confidence": 0.75
        }

    def _mock_image_generation(self) -> str:
        """Mock image generation - returns a placeholder image URL."""
        logger.info("Using mock image generation - returning placeholder URL")
        # In a real implementation, this would upload to Firebase Storage
        return "https://via.placeholder.com/400x300/FF6B6B/FFFFFF?text=Delicious+Recipe"
    
    def _validate_image_generation_inputs(self, recipe_name: str, recipe_description: str) -> bool:
        """
        Validate inputs for image generation
        
        Args:
            recipe_name: Name of the recipe
            recipe_description: Description of the dish
            
        Returns:
            True if inputs are valid, False otherwise
        """
        if not recipe_name or not recipe_name.strip():
            logger.error("Recipe name is empty or None")
            return False
            
        if not recipe_description or not recipe_description.strip():
            logger.warning("Recipe description is empty - using recipe name only")
            
        # Check for potentially problematic content
        problematic_terms = ['nsfw', 'explicit', 'inappropriate']
        combined_text = f"{recipe_name} {recipe_description}".lower()
        
        for term in problematic_terms:
            if term in combined_text:
                logger.warning(f"Potentially problematic content detected: {term}")
                return False
                
        return True
    
    def _create_safe_image_prompt(self, recipe_name: str, recipe_description: str) -> str:
        """
        Create a safe, well-structured prompt for image generation
        
        Args:
            recipe_name: Name of the recipe
            recipe_description: Description of the dish
            
        Returns:
            Safe prompt string for image generation
        """
        # Sanitize inputs
        safe_name = recipe_name.strip()[:100]  # Limit length
        safe_description = recipe_description.strip()[:500] if recipe_description else ""
        
        prompt = f"""Create a high-quality, professional food photography image of {safe_name}.

Description: {safe_description}

Style requirements:
- Professional food photography with excellent lighting
- Appetizing presentation on elegant dishware
- Clean, modern plating with artistic arrangement
- Warm, inviting colors that enhance appetite appeal
- Sharp focus on the food with shallow depth of field
- Minimal, clean background (white or neutral tones)
- Restaurant-quality presentation
- High resolution and crisp details
- Family-friendly and appropriate content only

The image should make the dish look absolutely delicious and appealing, perfect for a modern recipe application. Focus on the food presentation and avoid any inappropriate or non-food related content."""

        return prompt

    async def get_recipe_suggestions(self, ingredients: List[str], count: int = 3) -> List[Dict[str, Any]]:
        """
        Get multiple recipe suggestions based on available ingredients.
        
        Args:
            ingredients: List of available ingredient names
            count: Number of recipe suggestions to generate
            
        Returns:
            List of recipe dictionaries
        """
        recipes = []
        
        # Generate different types of recipes
        recipe_types = [
            {"difficulty": "easy", "cuisine": "American"},
            {"difficulty": "medium", "cuisine": "Italian"},
            {"difficulty": "medium", "cuisine": "Asian"}
        ]
        
        for i in range(min(count, len(recipe_types))):
            recipe_type = recipe_types[i]
            recipe = await self.generate_recipe(
                ingredients=ingredients,
                difficulty=recipe_type["difficulty"],
                cuisine_preference=recipe_type["cuisine"]
            )
            recipes.append(recipe)
            
            # Add a small delay to avoid rate limiting
            if self.flash_model:
                await asyncio.sleep(1)
        
        return recipes

# Create singleton instance
gemini_service = GeminiService()