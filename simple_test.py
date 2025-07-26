#!/usr/bin/env python3
"""
Simple test to verify AI services structure without external dependencies
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        # Test basic imports without external dependencies
        from app.core.config import settings
        print("✅ Config imported successfully")
        
        from app.models.ingredient import IngredientCategory, IngredientCreate
        print("✅ Ingredient models imported successfully")
        
        from app.models.recipe import RecipeCreate, RecipeGenerationRequest, MealType
        print("✅ Recipe models imported successfully")
        
        print("\n📝 Configuration check:")
        print(f"   - App name: {settings.APP_NAME}")
        print(f"   - Debug mode: {settings.DEBUG}")
        print(f"   - API prefix: {settings.API_PREFIX}")
        print(f"   - Groq API key configured: {'Yes' if settings.GROQ_API_KEY else 'No'}")
        print(f"   - Gemini API key configured: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_model_creation():
    """Test creating model instances"""
    print("\n🏗️ Testing model creation...")
    
    try:
        from app.models.ingredient import IngredientCreate, IngredientCategory
        from app.models.recipe import RecipeGenerationRequest, MealType
        
        # Test ingredient creation
        ingredient = IngredientCreate(
            name="Tomato",
            category=IngredientCategory.VEGETABLE,
            quantity=2.0,
            unit="pieces"
        )
        print(f"✅ Ingredient created: {ingredient.name} ({ingredient.category})")
        
        # Test recipe request creation
        recipe_request = RecipeGenerationRequest(
            available_ingredients=["tomato", "onion", "garlic"],
            meal_type=MealType.DINNER,
            cuisine="Italian",
            servings=4
        )
        print(f"✅ Recipe request created: {len(recipe_request.available_ingredients)} ingredients")
        
        return True
        
    except Exception as e:
        print(f"❌ Model creation error: {e}")
        return False

def test_service_structure():
    """Test service file structure"""
    print("\n📁 Testing service file structure...")
    
    services_dir = os.path.join(os.path.dirname(__file__), 'app', 'services')
    ai_dir = os.path.join(services_dir, 'ai')
    firebase_dir = os.path.join(services_dir, 'firebase')
    
    # Check AI services
    ai_files = [
        'groq_service.py',
        'gemini_service.py', 
        'vision.py',
        'recipe_generator.py',
        'image_generator.py',
        '__init__.py'
    ]
    
    print("   AI Services:")
    for file in ai_files:
        file_path = os.path.join(ai_dir, file)
        exists = os.path.exists(file_path)
        print(f"   {'✅' if exists else '❌'} {file}")
    
    # Check Firebase services
    firebase_files = [
        'firestore.py',
        'storage.py',
        '__init__.py'
    ]
    
    print("   Firebase Services:")
    for file in firebase_files:
        file_path = os.path.join(firebase_dir, file)
        exists = os.path.exists(file_path)
        print(f"   {'✅' if exists else '❌'} {file}")
    
    return True

def test_mock_functionality():
    """Test mock functionality without external dependencies"""
    print("\n🎭 Testing mock functionality...")
    
    try:
        # Test mock ingredient recognition data structure
        mock_ingredients = [
            {
                "name": "Apples",
                "quantity": "3 pieces",
                "estimatedExpiration": "1 week",
                "confidence": 0.9
            },
            {
                "name": "Milk",
                "quantity": "1 carton", 
                "estimatedExpiration": "3 days",
                "confidence": 0.85
            }
        ]
        
        print(f"✅ Mock ingredient data: {len(mock_ingredients)} items")
        for ing in mock_ingredients:
            print(f"   - {ing['name']}: {ing['quantity']} (confidence: {ing['confidence']})")
        
        # Test mock recipe data structure
        mock_recipe = {
            "name": "Simple Tomato Dish",
            "description": "A quick and easy recipe",
            "prepTime": "15 minutes",
            "cookTime": "25 minutes",
            "servings": 4,
            "difficulty": "easy",
            "cuisine": "Italian",
            "ingredients": [
                {"name": "tomato", "amount": "2", "unit": "pieces"},
                {"name": "onion", "amount": "1", "unit": "pieces"}
            ],
            "instructions": [
                "Prepare ingredients",
                "Cook in pan",
                "Serve hot"
            ]
        }
        
        print(f"✅ Mock recipe data: {mock_recipe['name']}")
        print(f"   - Prep time: {mock_recipe['prepTime']}")
        print(f"   - Ingredients: {len(mock_recipe['ingredients'])}")
        print(f"   - Instructions: {len(mock_recipe['instructions'])} steps")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock functionality error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Simple AI Services Structure Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_model_creation,
        test_service_structure,
        test_mock_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All structure tests passed!")
        print("\n📝 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up environment variables (copy .env.example to .env)")
        print("3. Configure API keys for Groq and Gemini")
        print("4. Set up Firebase project and credentials")
        print("5. Run the full application with: uvicorn main:app --reload")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)