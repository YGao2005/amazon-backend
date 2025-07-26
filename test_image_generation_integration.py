#!/usr/bin/env python3
"""
Test script for the complete image generation integration in the smart recipe app.

This script tests:
1. GeminiService image generation functionality
2. Recipe generation with automatic image creation
3. Image generator service integration
4. Error handling and fallback mechanisms
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai.gemini_service import gemini_service
from app.services.ai.image_generator import image_generator_service
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageGenerationTester:
    """Test class for image generation integration"""
    
    def __init__(self):
        self.test_results = []
        self.images_generated = []
    
    async def test_gemini_service_availability(self) -> bool:
        """Test if Gemini service is properly configured"""
        logger.info("Testing Gemini service availability...")
        
        try:
            # Check if API key is configured
            if not settings.GEMINI_API_KEY:
                logger.error("GEMINI_API_KEY not found in environment")
                return False
            
            # Check if client is initialized
            if not gemini_service.genai_client:
                logger.warning("Gemini client not initialized - will use mock generation")
                return False
            
            logger.info("Gemini service is properly configured")
            return True
            
        except Exception as e:
            logger.error(f"Error checking Gemini service: {e}")
            return False
    
    async def test_basic_image_generation(self) -> bool:
        """Test basic image generation functionality"""
        logger.info("Testing basic image generation...")
        
        try:
            test_recipe_name = "Spaghetti Carbonara"
            test_description = "Classic Italian pasta dish with eggs, cheese, and pancetta"
            
            image_url = await gemini_service.generate_recipe_image(
                recipe_name=test_recipe_name,
                recipe_description=test_description
            )
            
            if image_url:
                logger.info(f"Successfully generated image: {image_url}")
                self.images_generated.append(image_url)
                
                # Check if it's a local file path
                if image_url.startswith('/'):
                    local_path = image_url[1:]  # Remove leading slash
                    if os.path.exists(local_path):
                        file_size = os.path.getsize(local_path)
                        logger.info(f"Generated image file exists: {local_path} (size: {file_size} bytes)")
                        return True
                    else:
                        logger.warning(f"Generated image file not found: {local_path}")
                        return False
                else:
                    # It's a URL (likely mock)
                    logger.info(f"Generated image URL: {image_url}")
                    return True
            else:
                logger.error("Image generation returned None")
                return False
                
        except Exception as e:
            logger.error(f"Error in basic image generation test: {e}")
            return False
    
    async def test_image_generator_service(self) -> bool:
        """Test the image generator service wrapper"""
        logger.info("Testing image generator service...")
        
        try:
            # Test recipe image generation
            recipe_image = await image_generator_service.generate_recipe_image(
                recipe_title="Chicken Tikka Masala",
                recipe_description="Creamy Indian curry with tender chicken pieces",
                ingredients=["chicken", "tomatoes", "cream", "spices"]
            )
            
            if recipe_image:
                logger.info(f"Image generator service successfully generated recipe image: {recipe_image}")
                self.images_generated.append(recipe_image)
            else:
                logger.warning("Image generator service returned None for recipe image")
                return False
            
            # Test ingredient image generation
            ingredient_image = await image_generator_service.generate_ingredient_image(
                ingredient_name="fresh basil",
                style="clean_background"
            )
            
            if ingredient_image:
                logger.info(f"Image generator service successfully generated ingredient image: {ingredient_image}")
                self.images_generated.append(ingredient_image)
            else:
                logger.warning("Image generator service returned None for ingredient image")
            
            # Test service availability check
            is_available = image_generator_service.is_available()
            logger.info(f"Image generator service availability: {is_available}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in image generator service test: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling with invalid inputs"""
        logger.info("Testing error handling...")
        
        try:
            # Test with empty recipe name
            result1 = await gemini_service.generate_recipe_image("", "Some description")
            logger.info(f"Empty recipe name test result: {result1}")
            
            # Test with None values
            result2 = await gemini_service.generate_recipe_image(None, None)
            logger.info(f"None values test result: {result2}")
            
            # Test with very long inputs
            long_name = "A" * 1000
            long_description = "B" * 2000
            result3 = await gemini_service.generate_recipe_image(long_name, long_description)
            logger.info(f"Long inputs test result: {result3}")
            
            # All should return mock URLs or None, not crash
            logger.info("Error handling tests completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in error handling test: {e}")
            return False
    
    async def test_recipe_generation_integration(self) -> bool:
        """Test the complete recipe generation with image integration"""
        logger.info("Testing recipe generation with image integration...")
        
        try:
            # Test recipe generation (this would normally be called via API)
            test_ingredients = ["chicken breast", "tomatoes", "onions", "garlic", "olive oil"]
            
            # Generate a recipe
            recipe_dict = await gemini_service.generate_recipe(
                ingredients=test_ingredients,
                cuisine_preference="Italian",
                difficulty="medium"
            )
            
            if not recipe_dict:
                logger.error("Recipe generation failed")
                return False
            
            logger.info(f"Generated recipe: {recipe_dict.get('name', 'Unknown')}")
            
            # Test image generation for the recipe
            recipe_name = recipe_dict.get("name", "Test Recipe")
            recipe_description = recipe_dict.get("description", "A delicious test recipe")
            
            image_url = await gemini_service.generate_recipe_image(
                recipe_name=recipe_name,
                recipe_description=recipe_description
            )
            
            if image_url:
                logger.info(f"Successfully generated image for recipe: {image_url}")
                self.images_generated.append(image_url)
                return True
            else:
                logger.warning("Image generation failed for recipe")
                return False
                
        except Exception as e:
            logger.error(f"Error in recipe generation integration test: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        logger.info("Starting comprehensive image generation integration tests...")
        
        tests = [
            ("Gemini Service Availability", self.test_gemini_service_availability),
            ("Basic Image Generation", self.test_basic_image_generation),
            ("Image Generator Service", self.test_image_generator_service),
            ("Error Handling", self.test_error_handling),
            ("Recipe Generation Integration", self.test_recipe_generation_integration),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running test: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                result = await test_func()
                results[test_name] = result
                status = "PASSED" if result else "FAILED"
                logger.info(f"Test '{test_name}': {status}")
            except Exception as e:
                logger.error(f"Test '{test_name}' crashed: {e}")
                results[test_name] = False
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if self.images_generated:
            logger.info(f"\nGenerated {len(self.images_generated)} images:")
            for img_url in self.images_generated:
                logger.info(f"  - {img_url}")
        
        # Check if generated_images directory exists
        if os.path.exists("generated_images"):
            files = os.listdir("generated_images")
            logger.info(f"\nFiles in generated_images directory: {len(files)}")
            for file in files[:5]:  # Show first 5 files
                logger.info(f"  - {file}")
            if len(files) > 5:
                logger.info(f"  ... and {len(files) - 5} more files")

async def main():
    """Main test function"""
    tester = ImageGenerationTester()
    
    try:
        results = await tester.run_all_tests()
        tester.print_summary(results)
        
        # Return appropriate exit code
        all_passed = all(results.values())
        return 0 if all_passed else 1
        
    except Exception as e:
        logger.error(f"Test suite crashed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)