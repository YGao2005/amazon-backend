import asyncio
import json
import base64
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

# Test the duplicate ingredient removal functionality
async def test_duplicate_ingredient_removal():
    """Test that scanning the same ingredient multiple times merges quantities instead of creating duplicates"""
    
    # Mock the firebase service
    mock_firebase = AsyncMock()
    
    # Mock existing ingredient in database
    existing_avocado = {
        "id": "existing-avocado-id",
        "name": "Avocado",
        "quantity": 2.0,
        "unit": "pieces",
        "category": "Produce",
        "expiration_date": (datetime.now() + timedelta(days=5)).isoformat(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "location": "fridge",
        "notes": "Previously scanned"
    }
    
    # Mock groq service response for scanning avocados
    mock_groq_response = [
        {
            "name": "Avocado",
            "quantity": "3 pieces",
            "estimatedExpiration": "4 days",
            "confidence": 0.9
        }
    ]
    
    # Mock the services
    with patch('app.api.ingredients.firebase_service', mock_firebase), \
         patch('app.api.ingredients.groq_service') as mock_groq:
        
        # Setup mocks
        mock_groq.validate_image = AsyncMock(return_value=True)
        mock_groq.recognize_ingredients = AsyncMock(return_value=mock_groq_response)
        
        # First call: return existing ingredient (simulating duplicate found)
        mock_firebase.query_collection = AsyncMock(return_value=[existing_avocado])
        mock_firebase.get_collection = AsyncMock(return_value=[existing_avocado])
        mock_firebase.update_document = AsyncMock(return_value=True)
        
        # Import the endpoint function
        from app.api.ingredients import scan_ingredients, ScanRequest
        
        # Create test request
        test_image = base64.b64encode(b"fake_image_data").decode()
        request = ScanRequest(image=test_image)
        
        # Call the scan endpoint
        result = await scan_ingredients(request)
        
        # Verify the result
        assert len(result) == 1
        scanned_ingredient = result[0]
        
        # Check that the ingredient name matches
        assert scanned_ingredient.name == "Avocado"
        
        # Check that quantities were merged (2 existing + 3 new = 5)
        assert scanned_ingredient.quantity.amount == 5.0
        assert scanned_ingredient.quantity.unit == "pieces"
        
        # Verify that update_document was called (not create_document)
        mock_firebase.update_document.assert_called_once()
        update_call = mock_firebase.update_document.call_args
        
        # Check the update data
        args = update_call[0]
        ingredient_id = args[1]  # collection name is args[0], document id is args[1], data is args[2]
        update_data = args[2]
        assert ingredient_id == "existing-avocado-id"
        assert update_data["quantity"] == 5.0
        assert update_data["unit"] == "pieces"
        assert "Updated from scan" in update_data["notes"]
        
        print("✅ Test passed: Duplicate ingredient quantities were merged correctly")

async def test_new_ingredient_creation():
    """Test that scanning a new ingredient creates it normally"""
    
    # Mock the firebase service
    mock_firebase = AsyncMock()
    
    # Mock groq service response for scanning tomatoes
    mock_groq_response = [
        {
            "name": "Tomato",
            "quantity": "4 pieces",
            "estimatedExpiration": "6 days",
            "confidence": 0.85
        }
    ]
    
    # Mock the services
    with patch('app.api.ingredients.firebase_service', mock_firebase), \
         patch('app.api.ingredients.groq_service') as mock_groq:
        
        # Setup mocks
        mock_groq.validate_image = AsyncMock(return_value=True)
        mock_groq.recognize_ingredients = AsyncMock(return_value=mock_groq_response)
        
        # No existing ingredient found
        mock_firebase.query_collection = AsyncMock(return_value=[])
        mock_firebase.get_collection = AsyncMock(return_value=[])
        mock_firebase.create_document = AsyncMock(return_value=True)
        
        # Import the endpoint function
        from app.api.ingredients import scan_ingredients, ScanRequest
        
        # Create test request
        test_image = base64.b64encode(b"fake_image_data").decode()
        request = ScanRequest(image=test_image)
        
        # Call the scan endpoint
        result = await scan_ingredients(request)
        
        # Verify the result
        assert len(result) == 1
        scanned_ingredient = result[0]
        
        # Check that the ingredient was created correctly
        assert scanned_ingredient.name == "Tomato"
        assert scanned_ingredient.quantity.amount == 4.0
        assert scanned_ingredient.quantity.unit == "pieces"
        
        # Verify that create_document was called (not update_document)
        mock_firebase.create_document.assert_called_once()
        
        print("✅ Test passed: New ingredient was created correctly")

async def test_case_insensitive_duplicate_detection():
    """Test that duplicate detection works with different cases (Avocado vs avocado)"""
    
    # Mock the firebase service
    mock_firebase = AsyncMock()
    
    # Mock existing ingredient with different case
    existing_avocado = {
        "id": "existing-avocado-id",
        "name": "avocado",  # lowercase
        "quantity": 1.0,
        "unit": "pieces",
        "category": "Produce",
        "expiration_date": (datetime.now() + timedelta(days=5)).isoformat(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "location": "fridge",
        "notes": "Previously scanned"
    }
    
    # Mock groq service response with different case
    mock_groq_response = [
        {
            "name": "Avocado",  # capitalized
            "quantity": "2 pieces",
            "estimatedExpiration": "4 days",
            "confidence": 0.9
        }
    ]
    
    # Mock the services
    with patch('app.api.ingredients.firebase_service', mock_firebase), \
         patch('app.api.ingredients.groq_service') as mock_groq:
        
        # Setup mocks
        mock_groq.validate_image = AsyncMock(return_value=True)
        mock_groq.recognize_ingredients = AsyncMock(return_value=mock_groq_response)
        
        # Query collection returns empty (exact match fails)
        mock_firebase.query_collection = AsyncMock(return_value=[])
        # But get_collection returns the existing ingredient (case-insensitive fallback)
        mock_firebase.get_collection = AsyncMock(return_value=[existing_avocado])
        mock_firebase.update_document = AsyncMock(return_value=True)
        
        # Import the endpoint function
        from app.api.ingredients import scan_ingredients, ScanRequest
        
        # Create test request
        test_image = base64.b64encode(b"fake_image_data").decode()
        request = ScanRequest(image=test_image)
        
        # Call the scan endpoint
        result = await scan_ingredients(request)
        
        # Verify the result
        assert len(result) == 1
        scanned_ingredient = result[0]
        
        # Check that quantities were merged despite case difference
        assert scanned_ingredient.quantity.amount == 3.0  # 1 + 2
        
        # Verify that update_document was called
        mock_firebase.update_document.assert_called_once()
        
        print("✅ Test passed: Case-insensitive duplicate detection works correctly")

async def main():
    """Run all tests"""
    print("Testing duplicate ingredient removal functionality...\n")
    
    try:
        await test_duplicate_ingredient_removal()
        await test_new_ingredient_creation()
        await test_case_insensitive_duplicate_detection()
        
        print("\n🎉 All tests passed! Duplicate ingredient removal is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())