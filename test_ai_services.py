#!/usr/bin/env python3
"""
Test script for AI services integration
This script tests the AI services with mock data to ensure they work correctly.
"""

import asyncio
import base64
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai.groq_service import groq_service
from app.services.ai.gemini_service import gemini_service
from app.models.recipe import RecipeGenerationRequest, MealType

async def test_groq_ingredient_recognition():
    """Test Groq service for ingredient recognition"""
    print("🔍 Testing Groq Ingredient Recognition...")
    
    # Create a simple test image (1x1 pixel PNG in base64)
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    test_image_bytes = base64.b64decode(test_image_b64)
    
    try:
        # Test new method
        ingredients = await groq_service.recognize_ingredients(test_image_bytes)
        print(f"✅ Groq recognize_ingredients: Found {len(ingredients)} ingredients")
        for ing in ingredients[:3]:  # Show first 3
            print(f"   - {ing['name']}: {ing['quantity']} (confidence: {ing['confidence']})")
        
        # Test legacy method
        legacy_result = await groq_service.detect_ingredients(test_image_b64)
        print(f"✅ Groq detect_ingredients (legacy): Found {len(legacy_result['ingredients'])} ingredients")
        print(f"   - Confidence: {legacy_result['confidence']}")
        
    except Exception as e:
        print(f"❌ Groq service error: {e}")

async def test_gemini_recipe_generation():
    """Test Gemini service for recipe generation"""
    print("\n🍳 Testing Gemini Recipe Generation...")
    
    try:
        # Test new method
        ingredients = ["tomatoes", "onions", "garlic", "olive oil"]
        recipe_dict = await gemini_service.generate_recipe(
            ingredients=ingredients,
            dietary_restrictions=["vegetarian"],
            cuisine_preference="Italian"
        )
        
        print(f"✅ Gemini generate_recipe: {recipe_dict['name']}")
        print(f"   - Cuisine: {recipe_dict['cuisine']}")
        print(f"   - Prep time: {recipe_dict['prepTime']}")
        print(f"   - Ingredients: {len(recipe_dict['ingredients'])}")
        
        # Test legacy method
        request = RecipeGenerationRequest(
            available_ingredients=ingredients,
            meal_type=MealType.DINNER,
            cuisine="Italian",
            dietary_restrictions=["vegetarian"],
            servings=4
        )
        
        legacy_result = await gemini_service.generate_recipe_legacy(request)
        print(f"✅ Gemini generate_recipe_legacy: {legacy_result['recipe'].title}")
        print(f"   - Missing ingredients: {len(legacy_result['missing_ingredients'])}")
        print(f"   - Confidence: {legacy_result['confidence']}")
        
    except Exception as e:
        print(f"❌ Gemini recipe generation error: {e}")

async def test_gemini_image_generation():
    """Test Gemini service for image generation"""
    print("\n🖼️ Testing Gemini Image Generation...")
    
    try:
        image_url = await gemini_service.generate_recipe_image(
            recipe_name="Italian Tomato Pasta",
            recipe_description="A delicious pasta dish with fresh tomatoes and herbs"
        )
        
        if image_url:
            print(f"✅ Gemini image generation: {image_url}")
        else:
            print("⚠️ Gemini image generation returned None (expected for mock)")
            
    except Exception as e:
        print(f"❌ Gemini image generation error: {e}")

async def test_recipe_suggestions():
    """Test getting multiple recipe suggestions"""
    print("\n📋 Testing Recipe Suggestions...")
    
    try:
        ingredients = ["chicken", "rice", "vegetables", "soy sauce"]
        suggestions = await gemini_service.get_recipe_suggestions(ingredients, count=2)
        
        print(f"✅ Recipe suggestions: Generated {len(suggestions)} recipes")
        for i, recipe in enumerate(suggestions, 1):
            print(f"   {i}. {recipe['name']} ({recipe['cuisine']})")
            
    except Exception as e:
        print(f"❌ Recipe suggestions error: {e}")

async def test_image_validation():
    """Test image validation"""
    print("\n✅ Testing Image Validation...")
    
    try:
        # Test with valid image data
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        test_image_bytes = base64.b64decode(test_image_b64)
        
        is_valid = await groq_service.validate_image(test_image_bytes)
        print(f"✅ Image validation: {'Valid' if is_valid else 'Invalid'}")
        
        # Test with invalid data
        invalid_data = b"not an image"
        is_invalid = await groq_service.validate_image(invalid_data)
        print(f"✅ Invalid data validation: {'Valid' if is_invalid else 'Invalid (expected)'}")
        
    except Exception as e:
        print(f"❌ Image validation error: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting AI Services Integration Tests")
    print("=" * 50)
    
    await test_groq_ingredient_recognition()
    await test_gemini_recipe_generation()
    await test_gemini_image_generation()
    await test_recipe_suggestions()
    await test_image_validation()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("\n📝 Notes:")
    print("- All services are using mock implementations since API keys are not configured")
    print("- To use real APIs, set GROQ_API_KEY and GEMINI_API_KEY environment variables")
    print("- Firebase Storage requires proper Firebase configuration")

if __name__ == "__main__":
    asyncio.run(main())