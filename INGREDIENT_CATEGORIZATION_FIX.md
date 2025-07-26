# Ingredient Categorization Fix

## Problem
The AI scanning service was trying to classify ingredients as "FRUIT" and "VEGETABLE" but the backend `IngredientCategory` enum only had "Produce". This caused AttributeError exceptions:

```
ERROR:app.api.ingredients:Error processing ingredient Limes: type object 'IngredientCategory' has no attribute 'FRUIT'
ERROR:app.api.ingredients:Error processing ingredient Green Bell Peppers: type object 'IngredientCategory' has no attribute 'VEGETABLE'
```

## Root Cause
The `_guess_ingredient_category()` function in `app/api/ingredients.py` was trying to return `IngredientCategory.FRUIT` and `IngredientCategory.VEGETABLE`, which don't exist in the enum.

## Available Categories
The backend supports exactly these categories:
- **Produce** - For fruits and vegetables
- **Dairy** - For milk, cheese, yogurt, etc.
- **Protein** - For meat, fish, eggs, beans, nuts, etc.
- **Grains** - For rice, bread, pasta, flour, etc.
- **Spices** - For salt, pepper, herbs, seasonings, etc.
- **Other** - For everything else

## Solution Implemented

### 1. Fixed the categorization function
Updated `_guess_ingredient_category()` in `app/api/ingredients.py` to:
- Map both fruits and vegetables to `IngredientCategory.PRODUCE`
- Use comprehensive ingredient lists for better detection
- Handle specific problematic ingredients like "Green Bell Peppers" and "Limes"

### 2. Enhanced ingredient detection
- Added extensive lists of fruits and vegetables
- Improved detection for various forms (singular/plural, variations)
- Maintained proper categorization for all other food types

### 3. Fixed test files
Updated test files to use correct categories:
- `test_ingredients_api.py` - Changed VEGETABLE/FRUIT to PRODUCE
- `simple_test.py` - Changed VEGETABLE to PRODUCE

## Key Changes

### Before (Broken):
```python
if any(word in name_lower for word in ['apple', 'banana', 'orange']):
    return IngredientCategory.FRUIT  # ❌ Doesn't exist
elif any(word in name_lower for word in ['tomato', 'onion', 'carrot']):
    return IngredientCategory.VEGETABLE  # ❌ Doesn't exist
```

### After (Fixed):
```python
produce_items = [
    # Fruits
    'apple', 'apples', 'banana', 'bananas', 'orange', 'oranges', 'lime', 'limes',
    # Vegetables  
    'tomato', 'tomatoes', 'green bell pepper', 'green bell peppers', 'onion', 'onions',
    # ... comprehensive list
]

if any(item in name_lower for item in produce_items):
    return IngredientCategory.PRODUCE  # ✅ Correct mapping
```

## Testing
Created comprehensive tests in `test_ingredient_categorization_fix.py` that verify:
- ✅ Fruits are categorized as PRODUCE
- ✅ Vegetables are categorized as PRODUCE  
- ✅ Other categories (Dairy, Protein, Grains, Spices) work correctly
- ✅ Specific problematic ingredients (Limes, Green Bell Peppers) are fixed
- ✅ All existing functionality is preserved

## Result
- ✅ No more AttributeError exceptions
- ✅ All fruits and vegetables properly categorized as "Produce"
- ✅ Scanning service works correctly with backend enum
- ✅ All existing categories continue to work
- ✅ Enhanced ingredient detection with comprehensive lists

The fix ensures that the AI scanning service output aligns perfectly with the backend's available categories: "Produce", "Dairy", "Protein", "Grains", "Spices", "Other".