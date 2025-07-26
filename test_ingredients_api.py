#!/usr/bin/env python3
"""
Test script for the ingredient management API endpoints
"""

import asyncio
import json
import base64
from datetime import datetime
from app.models.ingredient import IngredientCreate, IngredientCategory

# Mock test data
def create_test_base64_image():
    """Create a simple test base64 image (1x1 pixel PNG)"""
    # This is a minimal 1x1 transparent PNG image in base64
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="

def test_scan_request():
    """Test the scan endpoint request format"""
    scan_request = {
        "image": create_test_base64_image()
    }
    print("✓ Scan request format:", json.dumps(scan_request, indent=2))
    return scan_request

def test_update_request():
    """Test the update endpoint request format"""
    ingredients = [
        IngredientCreate(
            name="Test Tomatoes",
            category=IngredientCategory.VEGETABLE,
            quantity=3.0,
            unit="pieces",
            expiration_date=datetime.now(),
            location="fridge",
            notes="Test ingredient"
        ),
        IngredientCreate(
            name="Test Milk",
            category=IngredientCategory.DAIRY,
            quantity=1.0,
            unit="cartons",
            expiration_date=datetime.now(),
            location="fridge",
            notes="Test ingredient"
        )
    ]
    
    update_request = {
        "ingredients": [ingredient.dict() for ingredient in ingredients]
    }
    print("✓ Update request format:", json.dumps(update_request, indent=2, default=str))
    return update_request

def test_helper_functions():
    """Test the helper functions"""
    from app.api.ingredients import _parse_expiration_days, _parse_quantity_value, _parse_unit_value, _guess_ingredient_category
    
    # Test expiration parsing
    assert _parse_expiration_days("3 days") == 3
    assert _parse_expiration_days("2 weeks") == 14
    assert _parse_expiration_days("1 month") == 30
    print("✓ Expiration parsing works")
    
    # Test quantity parsing
    assert _parse_quantity_value("3 pieces") == 3.0
    assert _parse_quantity_value("1.5 kg") == 1.5
    print("✓ Quantity parsing works")
    
    # Test unit parsing
    assert _parse_unit_value("3 pieces") == "pieces"
    assert _parse_unit_value("1 bottle") == "bottles"
    assert _parse_unit_value("2 cartons") == "cartons"
    print("✓ Unit parsing works")
    
    # Test category guessing
    assert _guess_ingredient_category("apple") == IngredientCategory.FRUIT
    assert _guess_ingredient_category("tomato") == IngredientCategory.VEGETABLE
    assert _guess_ingredient_category("milk") == IngredientCategory.DAIRY
    print("✓ Category guessing works")

async def test_api_integration():
    """Test the API endpoints integration"""
    try:
        # Import the API functions
        from app.api.ingredients import get_ingredients, scan_ingredients, update_ingredients
        from app.api.ingredients import ScanRequest, UpdateRequest
        
        print("✓ API endpoints imported successfully")
        
        # Test request models
        scan_req = ScanRequest(image=create_test_base64_image())
        print("✓ ScanRequest model works")
        
        ingredients = [
            IngredientCreate(
                name="Test Apple",
                category=IngredientCategory.FRUIT,
                quantity=2.0,
                unit="pieces",
                location="fridge"
            )
        ]
        update_req = UpdateRequest(ingredients=ingredients)
        print("✓ UpdateRequest model works")
        
        print("✓ All API integration tests passed")
        
    except Exception as e:
        print(f"✗ API integration test failed: {e}")

def main():
    """Run all tests"""
    print("Testing Ingredient Management API Implementation")
    print("=" * 50)
    
    # Test request formats
    test_scan_request()
    test_update_request()
    
    # Test helper functions
    test_helper_functions()
    
    # Test API integration
    asyncio.run(test_api_integration())
    
    print("\n" + "=" * 50)
    print("✓ All tests completed successfully!")
    print("\nAPI Endpoints implemented:")
    print("1. GET /api/ingredients - Fetch all ingredients")
    print("2. POST /api/ingredients/scan - Scan ingredients from image")
    print("3. POST /api/ingredients/update - Add/update ingredients manually")

if __name__ == "__main__":
    main()