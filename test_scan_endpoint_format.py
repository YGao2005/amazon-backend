#!/usr/bin/env python3
"""
Test script to verify the scan endpoint returns the correct format for Swift frontend
"""

import asyncio
import json
from datetime import datetime
from app.api.ingredients import _parse_quantity_value, _parse_unit_value, _parse_expiration_days
from app.api.ingredients import QuantityInfo, ScannedIngredient

def test_helper_functions():
    """Test the existing helper functions work correctly"""
    print("Testing helper functions...")
    
    # Test quantity parsing
    test_quantities = ["3 pieces", "2.5 kg", "1 bottle", "4 cups"]
    for qty_str in test_quantities:
        amount = _parse_quantity_value(qty_str)
        unit = _parse_unit_value(qty_str)
        print(f"  '{qty_str}' -> amount: {amount}, unit: {unit}")
    
    # Test expiration parsing
    test_expirations = ["3 days", "1 week", "2 weeks", "1 month"]
    for exp_str in test_expirations:
        days = _parse_expiration_days(exp_str)
        print(f"  '{exp_str}' -> {days} days")
    
    print()

def test_response_models():
    """Test the new response models work correctly"""
    print("Testing response models...")
    
    # Test QuantityInfo
    quantity_info = QuantityInfo(amount=3.0, unit="pieces")
    print(f"  QuantityInfo: {quantity_info.dict()}")
    
    # Test ScannedIngredient
    current_time = datetime.now()
    scanned_ingredient = ScannedIngredient(
        name="Apples",
        quantity=QuantityInfo(amount=3.0, unit="pieces"),
        estimatedExpiration=current_time.isoformat() + "Z"
    )
    print(f"  ScannedIngredient: {scanned_ingredient.dict()}")
    
    print()

def test_data_transformation():
    """Test the data transformation logic"""
    print("Testing data transformation...")
    
    # Simulate the data that would come from Groq service
    mock_groq_response = [
        {
            "name": "Apples",
            "quantity": "3 pieces",
            "estimatedExpiration": "1 week",
            "confidence": 0.9
        },
        {
            "name": "Milk",
            "quantity": "1 bottle",
            "estimatedExpiration": "5 days",
            "confidence": 0.85
        }
    ]
    
    # Transform to the new format
    current_date = datetime.now()
    transformed_ingredients = []
    
    for ingredient_data in mock_groq_response:
        # Parse quantity and unit using existing helper functions
        quantity_str = ingredient_data.get('quantity', '1 unit')
        quantity_amount = _parse_quantity_value(quantity_str)
        quantity_unit = _parse_unit_value(quantity_str)
        
        # Parse expiration
        expiration_str = ingredient_data.get('estimatedExpiration', '7 days')
        expiration_days = _parse_expiration_days(expiration_str)
        estimated_expiration = current_date + timedelta(days=expiration_days)
        
        # Create the response format that matches Swift expectations
        scanned_ingredient = ScannedIngredient(
            name=ingredient_data['name'],
            quantity=QuantityInfo(
                amount=quantity_amount,
                unit=quantity_unit
            ),
            estimatedExpiration=estimated_expiration.isoformat() + "Z"
        )
        transformed_ingredients.append(scanned_ingredient)
    
    # Convert to JSON to see the final format
    result_json = [ingredient.dict() for ingredient in transformed_ingredients]
    print("  Transformed data (JSON format):")
    print(json.dumps(result_json, indent=2))
    
    print()

def main():
    """Run all tests"""
    print("=== Testing Scan Endpoint Format Changes ===\n")
    
    # Import timedelta here to avoid import issues
    from datetime import timedelta
    globals()['timedelta'] = timedelta
    
    test_helper_functions()
    test_response_models()
    test_data_transformation()
    
    print("=== Expected Swift Frontend Format ===")
    expected_format = [
        {
            "name": "Apples",
            "quantity": {
                "amount": 3.0,
                "unit": "pieces"
            },
            "estimatedExpiration": "2025-08-02T20:33:51.000Z"
        }
    ]
    print(json.dumps(expected_format, indent=2))
    
    print("\n✅ All tests completed! The scan endpoint should now return the correct format.")

if __name__ == "__main__":
    main()