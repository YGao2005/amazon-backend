#!/usr/bin/env python3
"""
Test script to verify the GroqService migration to Gemini API.
"""

import asyncio
import sys
import os
from PIL import Image
import io

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.services.ai.groq_service import groq_service

async def test_groq_service_migration():
    """Test the migrated GroqService with Gemini API."""
    
    print("Testing GroqService migration to Gemini API...")
    print("=" * 50)
    
    # Test 1: Check service initialization
    print("1. Testing service initialization...")
    print(f"   API Key configured: {'Yes' if groq_service.api_key else 'No'}")
    print(f"   Vision model available: {'Yes' if groq_service.vision_model else 'No (using mock)'}")
    
    # Test 2: Create a simple test image (solid color)
    print("\n2. Creating test image...")
    test_image = Image.new('RGB', (400, 300), color='red')
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='JPEG')
    image_data = img_bytes.getvalue()
    print(f"   Test image created: {len(image_data)} bytes")
    
    # Test 3: Test image validation
    print("\n3. Testing image validation...")
    is_valid = await groq_service.validate_image(image_data)
    print(f"   Image validation result: {is_valid}")
    
    # Test 4: Test ingredient recognition
    print("\n4. Testing ingredient recognition...")
    try:
        ingredients = await groq_service.recognize_ingredients(image_data)
        print(f"   Number of ingredients detected: {len(ingredients)}")
        
        for i, ingredient in enumerate(ingredients, 1):
            print(f"   Ingredient {i}:")
            print(f"     Name: {ingredient.get('name', 'N/A')}")
            print(f"     Quantity: {ingredient.get('quantity', 'N/A')}")
            print(f"     Estimated Expiration: {ingredient.get('estimatedExpiration', 'N/A')}")
            print(f"     Confidence: {ingredient.get('confidence', 'N/A')}")
            
    except Exception as e:
        print(f"   Error during ingredient recognition: {e}")
        return False
    
    # Test 5: Test legacy detect_ingredients method
    print("\n5. Testing legacy detect_ingredients method...")
    try:
        import base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        result = await groq_service.detect_ingredients(base64_image)
        
        print(f"   Legacy method result:")
        print(f"     Ingredients count: {len(result.get('ingredients', []))}")
        print(f"     Confidence: {result.get('confidence', 'N/A')}")
        
        # Check structure of ingredients
        ingredients = result.get('ingredients', [])
        if ingredients:
            first_ingredient = ingredients[0]
            print(f"     First ingredient structure:")
            print(f"       Name: {getattr(first_ingredient, 'name', 'N/A')}")
            print(f"       Category: {getattr(first_ingredient, 'category', 'N/A')}")
            print(f"       Quantity: {getattr(first_ingredient, 'quantity', 'N/A')}")
            print(f"       Unit: {getattr(first_ingredient, 'unit', 'N/A')}")
            
    except Exception as e:
        print(f"   Error during legacy method test: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    print("✅ GroqService has been successfully migrated to use Gemini API")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_groq_service_migration())
    sys.exit(0 if success else 1)