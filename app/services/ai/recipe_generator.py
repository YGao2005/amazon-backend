# Legacy compatibility wrapper for the new GeminiService
from .gemini_service import gemini_service

class RecipeGeneratorService:
    """Legacy wrapper for backward compatibility"""
    
    def __init__(self):
        self.gemini_service = gemini_service
    
    async def generate_recipe(self, request):
        """
        Generate a recipe based on available ingredients using Gemini Flash
        
        Args:
            request: Recipe generation request with available ingredients and preferences
            
        Returns:
            Dictionary containing generated recipe, missing ingredients, and confidence
        """
        return await self.gemini_service.generate_recipe_legacy(request)

# Create singleton instance for backward compatibility
recipe_generator_service = RecipeGeneratorService()