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

async def test_default_recipe_generation():
    """Test default recipe generation behavior (likely causing duplication)"""
    print("=" * 80)
    print("TESTING DEFAULT RECIPE GENERATION (LIKELY DUPLICATION SOURCE)")
    print("=" * 80)
    
    # Create a request with NO cuisine preferences (uses default behavior)
    request = GenerateRecipeRequest(
        mustUseIngredients=["chicken", "rice"],
        preferenceOverrides={
            "cookingTime": "under30"
            # NO cuisinePreferences - this should trigger default behavior
        }
    )
    
    print(f"Request: mustUseIngredients={request.mustUseIngredients}")
    print(f"Request: preferenceOverrides={request.preferenceOverrides}")
    print("\nDefault behavior: Should use ['International', 'Italian', 'American'] cuisines")
    print("Expected: Will likely generate 3 recipes with 3 images (DUPLICATION!)")
    print("Actual behavior will be shown in logs below:")
    print("-" * 80)
    
    try:
        # Call the recipe generation endpoint
        result = await generate_recipes(request)
        
        print("-" * 80)
        print("RESULTS ANALYSIS:")
        print(f"Number of recipes returned: {len(result['recipes'])}")
        
        for i, recipe in enumerate(result['recipes']):
            print(f"Recipe {i+1}:")
            print(f"  - Name: {recipe.name}")
            print(f"  - ID: {recipe.id}")
            print(f"  - Cuisine: {recipe.cuisine}")
            print(f"  - Image: {recipe.imageName}")
            print()
        
        # Check for duplication issues
        if len(result['recipes']) > 1:
            print("🚨 DUPLICATION CONFIRMED!")
            print(f"Generated {len(result['recipes'])} recipes when user likely expected only 1")
            print("This is the source of the duplication problem!")
            
            # Check for duplicate names
            names = [r.name for r in result['recipes']]
            if len(names) != len(set(names)):
                print("🚨 DUPLICATE RECIPE NAMES FOUND!")
            
            # Check for duplicate images
            images = [r.imageName for r in result['recipes'] if r.imageName]
            print(f"Generated {len(images)} images")
            if len(images) != len(set(images)):
                print("🚨 DUPLICATE IMAGES FOUND!")
                
        else:
            print("✅ No duplication detected - only 1 recipe generated")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_default_recipe_generation())