import asyncio
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.api.recipes import generate_recipes, GenerateRecipeRequest

# Configure logging to see our debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def test_comprehensive_recipe_generation():
    """Comprehensive test to ensure fix works in all scenarios"""
    print("=" * 80)
    print("COMPREHENSIVE TEST: RECIPE DUPLICATION FIX VALIDATION")
    print("=" * 80)
    
    test_cases = [
        {
            "name": "No cuisine preferences (default behavior)",
            "request": GenerateRecipeRequest(
                mustUseIngredients=["chicken", "rice"],
                preferenceOverrides={"cookingTime": "under30"}
            ),
            "expected_recipes": 1,
            "description": "Should default to 'International' and generate 1 recipe"
        },
        {
            "name": "Single cuisine preference",
            "request": GenerateRecipeRequest(
                mustUseIngredients=["beef", "potatoes"],
                preferenceOverrides={
                    "cuisinePreferences": ["Italian"],
                    "cookingTime": "30to60"
                }
            ),
            "expected_recipes": 1,
            "description": "Should generate 1 Italian recipe"
        },
        {
            "name": "Multiple cuisine preferences",
            "request": GenerateRecipeRequest(
                mustUseIngredients=["fish", "vegetables"],
                preferenceOverrides={
                    "cuisinePreferences": ["Asian", "Mediterranean", "Mexican"],
                    "cookingTime": "over60"
                }
            ),
            "expected_recipes": 1,
            "description": "Should take first cuisine (Asian) and generate 1 recipe"
        }
    ]
    
    all_tests_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {test_case['name']}")
        print(f"{'='*60}")
        print(f"Description: {test_case['description']}")
        print(f"Expected recipes: {test_case['expected_recipes']}")
        print(f"Request: {test_case['request']}")
        print("-" * 60)
        
        try:
            # Call the recipe generation endpoint
            result = await generate_recipes(test_case['request'])
            
            actual_recipes = len(result['recipes'])
            expected_recipes = test_case['expected_recipes']
            
            print(f"\nRESULTS:")
            print(f"Expected: {expected_recipes} recipe(s)")
            print(f"Actual: {actual_recipes} recipe(s)")
            
            if actual_recipes == expected_recipes:
                print("✅ TEST PASSED")
                
                # Show recipe details
                for j, recipe in enumerate(result['recipes'], 1):
                    print(f"  Recipe {j}:")
                    print(f"    - Name: {recipe.name}")
                    print(f"    - Cuisine: {recipe.cuisine}")
                    print(f"    - Has Image: {'Yes' if recipe.imageName else 'No'}")
                    if recipe.imageName:
                        print(f"    - Image URL: {recipe.imageName[:50]}...")
            else:
                print("❌ TEST FAILED")
                print(f"   Expected {expected_recipes} recipe(s), got {actual_recipes}")
                all_tests_passed = False
                
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            all_tests_passed = False
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("FINAL RESULTS")
    print(f"{'='*80}")
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Recipe duplication fix is working correctly")
        print("✅ Only 1 recipe with 1 image is generated in all scenarios")
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️ Recipe duplication fix needs additional work")
    
    return all_tests_passed

if __name__ == "__main__":
    success = asyncio.run(test_comprehensive_recipe_generation())
    sys.exit(0 if success else 1)