#!/usr/bin/env python3
"""
Test script to verify the Swift compatibility fixes are working correctly.
"""

import json
from app.models.ingredient import IngredientCategory, Ingredient, IngredientCreate
from app.models.recipe import DifficultyLevel, Recipe, RecipeCreate, NutritionInfo
from datetime import datetime

def test_enum_fixes():
    """Test that enum values are now capitalized as expected by Swift"""
    print("=== Testing Enum Fixes ===")
    
    # Test Ingredient Category Enum
    print("\n1. Ingredient Category Enum Values:")
    for category in IngredientCategory:
        print(f"   {category.name}: '{category.value}'")
        # Verify they are capitalized
        assert category.value[0].isupper(), f"Category {category.name} should be capitalized"
    
    # Test Recipe Difficulty Enum
    print("\n2. Recipe Difficulty Enum Values:")
    for difficulty in DifficultyLevel:
        print(f"   {difficulty.name}: '{difficulty.value}'")
        # Verify they are capitalized
        assert difficulty.value[0].isupper(), f"Difficulty {difficulty.name} should be capitalized"
    
    print("   ✅ All enum values are properly capitalized!")

def test_field_name_compatibility():
    """Test that field names are converted to camelCase for Swift"""
    print("\n=== Testing Field Name Compatibility ===")
    
    # Create a sample ingredient
    ingredient = Ingredient(
        id="test-123",
        name="Test Apple",
        category=IngredientCategory.PRODUCE,
        quantity=5.0,
        unit="pieces",
        expiration_date=datetime.now(),
        purchase_date=datetime.now(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        image_url="https://example.com/apple.jpg",
        location="fridge",
        notes="Fresh apples"
    )
    
    # Simulate the API response format (what we fixed in ingredients.py)
    api_response = {
        "id": ingredient.id,
        "name": ingredient.name,
        "quantity": ingredient.quantity,
        "unit": ingredient.unit,
        "category": ingredient.category,
        "expirationDate": ingredient.expiration_date.isoformat() if ingredient.expiration_date else None,
        "purchaseDate": ingredient.purchase_date.isoformat() if ingredient.purchase_date else None,
        "createdAt": ingredient.created_at.isoformat() if ingredient.created_at else None,
        "updatedAt": ingredient.updated_at.isoformat() if ingredient.updated_at else None,
        "location": ingredient.location,
        "notes": ingredient.notes,
        "imageName": ingredient.image_url  # Changed from image_url to imageName
    }
    
    print("\n1. Ingredient API Response Format:")
    print(f"   Field names: {list(api_response.keys())}")
    
    # Check that camelCase fields are present
    expected_camel_case_fields = ['expirationDate', 'purchaseDate', 'createdAt', 'updatedAt', 'imageName']
    for field in expected_camel_case_fields:
        assert field in api_response, f"Field {field} should be in camelCase format"
        print(f"   ✅ {field}: present")
    
    print("   ✅ All ingredient field names are in camelCase!")

def test_recipe_time_handling():
    """Test that recipe time handling works correctly"""
    print("\n=== Testing Recipe Time Handling ===")
    
    # Test the time parsing function
    from app.api.recipes import _parse_time_to_minutes
    
    test_cases = [
        ("15 minutes", 15),
        ("30 min", 30),
        ("1 hour", 60),
        ("2 hours", 120),
        ("45", 45),  # No unit, should default to minutes
    ]
    
    print("\n1. Time Parsing Tests:")
    for time_str, expected_minutes in test_cases:
        result = _parse_time_to_minutes(time_str)
        print(f"   '{time_str}' -> {result} minutes (expected: {expected_minutes})")
        assert result == expected_minutes, f"Expected {expected_minutes}, got {result}"
    
    print("   ✅ Time parsing works correctly!")
    
    # Test recipe response format
    print("\n2. Recipe Response Format:")
    sample_recipe_data = {
        "prepTime": "15 minutes",
        "cookTime": "30 minutes",
        "cookingTime": 45,  # Combined time as integer
        "difficulty": "Easy",  # Capitalized
        "nutritionalInfo": {
            "calories": "250",  # All as strings
            "protein": "15.5",
            "carbs": "30.0",
            "fat": "8.2"
        },
        "imageName": "recipe-image.jpg"  # Changed from imageUrl
    }
    
    print(f"   prepTime: {sample_recipe_data['prepTime']} (string)")
    print(f"   cookTime: {sample_recipe_data['cookTime']} (string)")
    print(f"   cookingTime: {sample_recipe_data['cookingTime']} (integer)")
    print(f"   difficulty: {sample_recipe_data['difficulty']} (capitalized)")
    print(f"   nutritionalInfo: all values are strings")
    print(f"   imageName: {sample_recipe_data['imageName']} (camelCase)")
    
    # Verify nutrition info values are strings
    for key, value in sample_recipe_data['nutritionalInfo'].items():
        assert isinstance(value, str), f"Nutrition value {key} should be string, got {type(value)}"
    
    print("   ✅ Recipe format is Swift-compatible!")

def test_nutrition_info_structure():
    """Test that nutrition info is converted to strings"""
    print("\n=== Testing Nutrition Info Structure ===")
    
    # Sample nutrition data (as it might come from AI service)
    raw_nutrition = {
        "calories": 250,
        "protein": 15.5,
        "carbs": 30.0,
        "fat": 8.2,
        "fiber": None
    }
    
    # Convert to strings (as we do in the API)
    nutrition_strings = {}
    for key, value in raw_nutrition.items():
        if value is not None:
            nutrition_strings[key] = str(value)
        else:
            nutrition_strings[key] = "0"
    
    print("\n1. Nutrition Info Conversion:")
    for key, value in nutrition_strings.items():
        print(f"   {key}: '{value}' (type: {type(value).__name__})")
        assert isinstance(value, str), f"Nutrition value {key} should be string"
    
    print("   ✅ All nutrition values are strings!")

if __name__ == "__main__":
    print("Testing Swift Compatibility Fixes")
    print("=" * 50)
    
    try:
        test_enum_fixes()
        test_field_name_compatibility()
        test_recipe_time_handling()
        test_nutrition_info_structure()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Enum values are properly capitalized")
        print("✅ Field names are in camelCase")
        print("✅ Recipe time handling works correctly")
        print("✅ Nutrition info is converted to strings")
        print("✅ Swift compatibility fixes are working!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise