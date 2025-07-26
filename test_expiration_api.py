No#!/usr/bin/env python3
"""
Test script for the expiration management API endpoint
"""
import asyncio
import json
from datetime import datetime, timedelta
from app.api.expiration import get_expiration_alerts

async def test_expiration_alerts():
    """Test the expiration alerts endpoint"""
    try:
        print("Testing expiration alerts endpoint...")
        
        # Call the endpoint function directly
        result = await get_expiration_alerts()
        
        print("✅ Expiration alerts endpoint executed successfully!")
        print(f"Response structure: {type(result)}")
        
        if isinstance(result, dict) and "expiringIngredients" in result:
            expiring_count = len(result["expiringIngredients"])
            print(f"📊 Found {expiring_count} expiring ingredients")
            
            if expiring_count > 0:
                print("\n🔍 Sample expiring ingredient:")
                sample = result["expiringIngredients"][0]
                print(f"  - ID: {sample.get('id', 'N/A')}")
                print(f"  - Name: {sample.get('name', 'N/A')}")
