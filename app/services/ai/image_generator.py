# Legacy compatibility wrapper for the new GeminiService
from typing import Optional
from .gemini_service import gemini_service

class ImageGeneratorService:
    """Legacy wrapper for backward compatibility"""
    
    def __init__(self):
        self.gemini_service = gemini_service
    
    async def generate_recipe_image(
        self,
        recipe_title: str,
        recipe_description: str,
        ingredients: list = None,
        style: str = "food_photography"
    ) -> Optional[str]:
        """
        Generate an image for a recipe using Gemini 2.0
        
        Args:
            recipe_title: Title of the recipe
            recipe_description: Description of the recipe
            ingredients: List of main ingredients (optional)
            style: Image style (food_photography, illustration, etc.)
            
        Returns:
            URL of generated image or None if generation fails
        """
        return await self.gemini_service.generate_recipe_image(recipe_title, recipe_description)
    
    async def generate_ingredient_image(
        self,
        ingredient_name: str,
        style: str = "clean_background"
    ) -> Optional[str]:
        """
        Generate an image for an ingredient
        
        Args:
            ingredient_name: Name of the ingredient
            style: Image style
            
        Returns:
            URL of generated image or None if generation fails
        """
        return await self.gemini_service.generate_recipe_image(ingredient_name, f"High-quality image of {ingredient_name}")
    
    async def enhance_food_image(self, image_data: str, enhancement_type: str = "color_enhance") -> Optional[str]:
        """
        Enhance an existing food image
        
        Args:
            image_data: Base64 encoded image data
            enhancement_type: Type of enhancement (color_enhance, lighting, etc.)
            
        Returns:
            Enhanced image as base64 string
        """
        # For now, return the original image as enhancement is not implemented
        return image_data

# Create singleton instance for backward compatibility
image_generator_service = ImageGeneratorService()