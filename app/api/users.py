from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List

try:
    from app.services.firebase.firestore import firebase_service
except ImportError:
    # Fallback to mock service for testing
    from app.services.firebase.firestore_mock import firebase_service

router = APIRouter()

# Fixed user ID for single user system
DEMO_USER_ID = "demo_user"

# Default preferences as specified in the requirements
DEFAULT_PREFERENCES = {
    "dietaryRestrictions": [],
    "allergens": [],
    "cuisinePreferences": ["italian", "american", "mexican"],
    "cookingTime": "any",
    "skillLevel": "beginner"
}

@router.get("/preferences")
async def get_preferences():
    """Get user preferences
    
    Returns:
        dict: User preferences with the following structure:
        {
            "dietaryRestrictions": ["vegetarian"],
            "allergens": ["peanuts", "shellfish"],
            "cuisinePreferences": ["italian", "mexican", "thai"],
            "cookingTime": "any",
            "skillLevel": "beginner"
        }
    """
    try:
        # Try to get existing preferences from Firebase
        user_doc = await firebase_service.get_document("users", DEMO_USER_ID)
        
        if user_doc and "preferences" in user_doc:
            # Return existing preferences, filling in any missing fields with defaults
            preferences = user_doc["preferences"]
            result = DEFAULT_PREFERENCES.copy()
            result.update(preferences)
            return result
        else:
            # Return default preferences if no user document exists
            return DEFAULT_PREFERENCES
            
    except Exception as e:
        # If there's any error, return default preferences
        print(f"Error getting preferences: {e}")
        return DEFAULT_PREFERENCES

@router.post("/preferences")
async def update_preferences(preferences: Dict[str, Any]):
    """Update user preferences
    
    Args:
        preferences (dict): Partial or complete preferences to update
        Example:
        {
            "dietaryRestrictions": ["vegan", "gluten-free"],
            "cuisinePreferences": ["indian", "mediterranean"]
        }
    
    Returns:
        dict: Response with success status and complete updated preferences
        {
            "success": true,
            "preferences": {
                "dietaryRestrictions": ["vegan", "gluten-free"],
                "allergens": ["peanuts", "shellfish"],
                "cuisinePreferences": ["indian", "mediterranean"],
                "cookingTime": "any",
                "skillLevel": "beginner"
            }
        }
    """
    try:
        # Get current preferences first
        current_preferences = DEFAULT_PREFERENCES.copy()
        
        try:
            user_doc = await firebase_service.get_document("users", DEMO_USER_ID)
            if user_doc and "preferences" in user_doc:
                current_preferences.update(user_doc["preferences"])
        except Exception:
            # If we can't get current preferences, start with defaults
            pass
        
        # Update only the provided fields (partial update)
        updated_preferences = current_preferences.copy()
        
        # Validate and update each field if provided
        valid_fields = {
            "dietaryRestrictions", "allergens", "cuisinePreferences", 
            "cookingTime", "skillLevel"
        }
        
        for field, value in preferences.items():
            if field in valid_fields:
                updated_preferences[field] = value
        
        # Save updated preferences to Firebase
        user_data = {
            "preferences": updated_preferences,
            "userId": DEMO_USER_ID
        }
        
        # Try to update existing document, create if it doesn't exist
        existing_doc = await firebase_service.get_document("users", DEMO_USER_ID)
        if existing_doc:
            success = await firebase_service.update_document("users", DEMO_USER_ID, user_data)
        else:
            success = await firebase_service.create_document("users", DEMO_USER_ID, user_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save preferences to database")
        
        return {
            "success": True,
            "preferences": updated_preferences
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")