#!/usr/bin/env python3
"""
Test script for user preferences API endpoints
This script tests the exact API requirements specified in the task
"""
import requests
import json
import time
import subprocess
import sys
import os

def test_api_endpoints():
    """Test the preferences API endpoints"""
    base_url = "http://localhost:8000/api"
    
    print("🧪 Testing User Preferences API Endpoints")
    print("=" * 60)
    
    # Test 1: Get default preferences
    print("\n1️⃣ GET /api/preferences (default preferences)")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/preferences", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Response:")
            print(json.dumps(data, indent=2))
            
            # Verify expected structure
            expected_keys = {"dietaryRestrictions", "allergens", "cuisinePreferences", "cookingTime", "skillLevel"}
            if set(data.keys()) == expected_keys:
                print("✅ Response structure is correct")
            else:
                print(f"❌ Response structure mismatch")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Update preferences (partial)
    print("\n2️⃣ POST /api/preferences (partial update)")
    print("-" * 40)
    update_data = {
        "dietaryRestrictions": ["vegan", "gluten-free"],
        "cuisinePreferences": ["indian", "mediterranean"]
    }
    try:
        response = requests.post(
            f"{base_url}/preferences",
            json=update_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📤 Request:")
            print(json.dumps(update_data, indent=2))
            print(f"📄 Response:")
            print(json.dumps(data, indent=2))
            
            # Verify response structure
            if "success" in data and "preferences" in data:
                print("✅ Response structure is correct")
                if data["success"] is True:
                    print("✅ Update was successful")
                else:
                    print("❌ Update failed")
            else:
                print("❌ Response structure is incorrect")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get updated preferences
    print("\n3️⃣ GET /api/preferences (after update)")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/preferences", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Response:")
            print(json.dumps(data, indent=2))
            
            # Verify the updates were applied
            if (data.get("dietaryRestrictions") == ["vegan", "gluten-free"] and
                data.get("cuisinePreferences") == ["indian", "mediterranean"]):
                print("✅ Updates were correctly applied")
            else:
                print("❌ Updates were not applied correctly")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Update different fields
    print("\n4️⃣ POST /api/preferences (update different fields)")
    print("-" * 40)
    update_data2 = {
        "allergens": ["peanuts", "shellfish"],
        "skillLevel": "intermediate",
        "cookingTime": "30min"
    }
    try:
        response = requests.post(
            f"{base_url}/preferences",
            json=update_data2,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📤 Request:")
            print(json.dumps(update_data2, indent=2))
            print(f"📄 Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Final verification
    print("\n5️⃣ GET /api/preferences (final verification)")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/preferences", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Final preferences:")
            print(json.dumps(data, indent=2))
            
            # Verify all updates
            expected_final = {
                "dietaryRestrictions": ["vegan", "gluten-free"],
                "cuisinePreferences": ["indian", "mediterranean"],
                "allergens": ["peanuts", "shellfish"],
                "skillLevel": "intermediate",
                "cookingTime": "30min"
            }
            
            print("\n🔍 Verification:")
            all_correct = True
            for key, expected in expected_final.items():
                actual = data.get(key)
                if actual == expected:
                    print(f"✅ {key}: {actual}")
                else:
                    print(f"❌ {key}: expected {expected}, got {actual}")
                    all_correct = False
            
            if all_correct:
                print("\n🎉 ALL TESTS PASSED! The preferences API is working correctly.")
            else:
                print("\n❌ Some tests failed. Please check the implementation.")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main test function"""
    print("🚀 Starting User Preferences API Test")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("You can start it with: uvicorn main:app --reload")
    
    # Wait a moment for user to start server if needed
    input("\nPress Enter when the server is ready...")
    
    test_api_endpoints()
    
    print("\n" + "="*60)
    print("🏁 Test completed!")

if __name__ == "__main__":
    main()