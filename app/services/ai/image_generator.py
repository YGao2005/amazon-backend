# Enhanced image generator service with proper Gemini 2.0 integration
import logging
from typing import Optional, List
from .gemini_service import gemini_service

logger = logging.getLogger(__name__)

class ImageGeneratorService:
    """Enhanced image generator service with proper Gemini 2.0 integration"""
    
    def __init__(self):
        self.gemini_service = gemini_service
    
    async def generate_recipe_image(
        self,
        recipe_title: str,
        recipe_description: str,
        ingredients: List[str] = None,
        style: str = "food_photography"
    ) -> Optional[str]:
        """
        Generate an image for a recipe using Gemini 2.0
        
        Args:
            recipe_title: Title of the recipe
            recipe_description: Description of the recipe
            ingredients: List of main ingredients (optional, used to enhance description)
            style: Image style (food_photography, illustration, etc.)
            
        Returns:
            URL/path of generated image or None if generation fails
        """
        try:
            # Enhance description with ingredients if provided
            enhanced_description = recipe_description
            if ingredients:
                main_ingredients = ", ".join(ingredients[:5])  # Use first 5 ingredients
                enhanced_description = f"{recipe_description}. Main ingredients: {main_ingredients}"
            
            logger.info(f"Generating {style} image for recipe: {recipe_title}")
            
            # Use the updated Gemini service for image generation
            image_url = await self.gemini_service.generate_recipe_image(
                recipe_name=recipe_title,
                recipe_description=enhanced_description
            )
            
            if image_url:
                logger.info(f"Successfully generated image for recipe: {recipe_title}")
                return image_url
            else:
                logger.warning(f"Image generation returned None for recipe: {recipe_title}")
                return None
                
        except Exception as e:
            logger.error(f"Error in generate_recipe_image for {recipe_title}: {e}")
            return None
    
    async def generate_ingredient_image(
        self,
        ingredient_name: str,
        style: str = "clean_background"
    ) -> Optional[str]:
        """
        Generate an image for an ingredient
        
        Args:
            ingredient_name: Name of the ingredient
            style: Image style (clean_background, natural, artistic, etc.)
            
        Returns:
            URL/path of generated image or None if generation fails
        """
        try:
            # Create a detailed description for ingredient image
            style_descriptions = {
                "clean_background": "on a clean white background with professional lighting",
                "natural": "in a natural setting with soft lighting",
                "artistic": "with artistic composition and creative lighting"
            }
            
            style_desc = style_descriptions.get(style, "with professional presentation")
            description = f"High-quality, detailed image of fresh {ingredient_name} {style_desc}. The image should be clear, well-lit, and suitable for a cooking application."
            
            logger.info(f"Generating {style} image for ingredient: {ingredient_name}")
            
            image_url = await self.gemini_service.generate_recipe_image(
                recipe_name=f"Fresh {ingredient_name}",
                recipe_description=description
            )
            
            if image_url:
                logger.info(f"Successfully generated image for ingredient: {ingredient_name}")
                return image_url
            else:
                logger.warning(f"Image generation returned None for ingredient: {ingredient_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error in generate_ingredient_image for {ingredient_name}: {e}")
            return None
    
    async def generate_cooking_step_image(
        self,
        step_description: str,
        recipe_context: str = ""
    ) -> Optional[str]:
        """
        Generate an image for a specific cooking step
        
        Args:
            step_description: Description of the cooking step
            recipe_context: Additional context about the recipe
            
        Returns:
            URL/path of generated image or None if generation fails
        """
        try:
            # Create enhanced description for cooking step
            full_description = f"Cooking step illustration: {step_description}"
            if recipe_context:
                full_description += f". Recipe context: {recipe_context}"
            
            full_description += ". Show hands performing the cooking action with ingredients and cooking tools in a clean, well-lit kitchen setting."
            
            logger.info(f"Generating cooking step image: {step_description[:50]}...")
            
            image_url = await self.gemini_service.generate_recipe_image(
                recipe_name="Cooking Step",
                recipe_description=full_description
            )
            
            if image_url:
                logger.info("Successfully generated cooking step image")
                return image_url
            else:
                logger.warning("Cooking step image generation returned None")
                return None
                
        except Exception as e:
            logger.error(f"Error in generate_cooking_step_image: {e}")
            return None
    
    async def enhance_food_image(self, image_data: str, enhancement_type: str = "color_enhance") -> Optional[str]:
        """
        Enhance an existing food image (placeholder for future implementation)
        
        Args:
            image_data: Base64 encoded image data
            enhancement_type: Type of enhancement (color_enhance, lighting, etc.)
            
        Returns:
            Enhanced image as base64 string or None if enhancement fails
        """
        logger.info(f"Image enhancement requested with type: {enhancement_type}")
        logger.warning("Image enhancement is not yet implemented - returning original image")
        # For now, return the original image as enhancement is not implemented
        # In the future, this could use additional AI services for image enhancement
        return image_data
    
    def is_available(self) -> bool:
        """
        Check if image generation service is available
        
        Returns:
            True if service is available, False otherwise
        """
        return self.gemini_service.genai_client is not None

# Create singleton instance for backward compatibility
image_generator_service = ImageGeneratorService()