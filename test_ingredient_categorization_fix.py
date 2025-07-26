#!/usr/bin/env python3
"""
Test script to verify the ingredient categorization fix.
This tests that FRUIT and VEGETABLE categories are properly mapped to PRODUCE.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.ingredients import _guess_ingredient_category
from app.models.ingredient import IngredientCategory

def test_fruit_categorization():
    """Test that fruits are categorized as PRODUCE"""
    fruits = [
        "Apples", "Bananas", "Oranges", "Limes", "Lemons", "Grapes", 
        "Strawberries", "Blueberries", "Mangoes", "Pineapple", "Avocado"
    ]
    
    print("Testing fruit categorization:")
    for fruit in fruits:
        category = _guess_ingredient_category(fruit)
        print(f"  {fruit}: {category}")
        assert category == IngredientCategory.PRODUCE, f"{fruit} should be categorized as PRODUCE, got {category}"
    
    print("✅ All fruits correctly categorized as PRODUCE")

def test_vegetable_categorization():
    """Test that vegetables are categorized as PRODUCE"""
    vegetables = [
        "Tomatoes", "Onions", "Carrots", "Lettuce", "Spinach", "Potatoes", 
        "Green Bell Peppers", "Red Bell Peppers", "Cucumbers", "Broccoli",
        "Bell Pepper", "Bell Peppers", "Pepper", "Peppers"
    ]
    
    print("\nTesting vegetable categorization:")
    for vegetable in vegetables:
        category = _guess_ingredient_category(vegetable)
        print(f"  {vegetable}: {category}")
        assert category == IngredientCategory.PRODUCE, f"{vegetable} should be categorized as PRODUCE, got {category}"
    
    print("✅ All vegetables correctly categorized as PRODUCE")

def test_other_categories():
    """Test that other categories still work correctly"""
    test_cases = [
        ("Chicken", IngredientCategory.PROTEIN),
        ("Beef", IngredientCategory.PROTEIN),
        ("Milk", IngredientCategory.DAIRY),
        ("Cheese", IngredientCategory.DAIRY),
        ("Rice", IngredientCategory.GRAINS),
        ("Bread", IngredientCategory.GRAINS),
        ("Salt", IngredientCategory.SPICES),
        ("Garlic", IngredientCategory.SPICES),
        ("Unknown Item", IngredientCategory.OTHER)
    ]
    
    print("\nTesting other categories:")
    for item, expected_category in test_cases:
        category = _guess_ingredient_category(item)
        print(f"  {item}: {category}")
        assert category == expected_category, f"{item} should be categorized as {expected_category}, got {category}"
    
    print("✅ All other categories working correctly")

def test_problematic_ingredients():
    """Test the specific ingredients mentioned in the error logs"""
    problematic_ingredients = [
        "Limes",
        "Green Bell Peppers"
    ]
    
    print("\nTesting problematic ingredients from error logs:")
    for ingredient in problematic_ingredients:
        try:
            category = _guess_ingredient_category(ingredient)
            print(f"  {ingredient}: {category}")
            assert category == IngredientCategory.PRODUCE, f"{ingredient} should be categorized as PRODUCE, got {category}"
        except AttributeError as e:
            print(f"  ❌ {ingredient}: AttributeError - {e}")
            raise
    
    print("✅ Problematic ingredients now working correctly")

def main():
    """Run all categorization tests"""
    print("🧪 Testing ingredient categorization fix...")
    print("=" * 50)
    
    try:
        test_fruit_categorization()
        test_vegetable_categorization()
        test_other_categories()
        test_problematic_ingredients()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! The categorization fix is working correctly.")
        print("\nKey fixes implemented:")
        print("- FRUIT and VEGETABLE categories now map to PRODUCE")
        print("- Enhanced produce detection with more comprehensive lists")
        print("- Specific handling for 'Green Bell Peppers' and 'Limes'")
        print("- All existing categories still work correctly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()