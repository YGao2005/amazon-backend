# Legacy compatibility wrapper for the new GroqService
from .groq_service import groq_service

class VisionService:
    """Legacy wrapper for backward compatibility"""
    
    def __init__(self):
        self.groq_service = groq_service
    
    async def detect_ingredients(self, image_data: str):
        """
        Detect ingredients from image using Groq's Llama Vision model
        
        Args:
            image_data: Base64 encoded image data
            
        Returns:
            Dictionary containing detected ingredients and confidence score
        """
        return await self.groq_service.detect_ingredients(image_data)

# Create singleton instance for backward compatibility
vision_service = VisionService()