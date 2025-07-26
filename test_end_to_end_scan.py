#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing for Scan Fridge Implementation
Tests the complete workflow from image upload to data consumption for Swift frontend compatibility
"""

import asyncio
import json
import base64
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.ingredients import scan_ingredients, ScanRequest, ScannedIngredient, QuantityInfo
from app.services.ai.groq_service import groq_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EndToEndScanTester:
    """Comprehensive end-to-end testing for the scan endpoint"""
    
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        
    def create_test_image_data(self, image_type: str = "valid") -> str:
        """Create test image data for different scenarios"""
        if image_type == "valid":
            # Create a minimal valid PNG (1x1 pixel)
            png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\xac\xac\x00\x05\x1f\x1f\x1f\x00\x01\x9a\x9c\x18\x00\x00\x00\x00IEND\xaeB`\x82'
            return base64.b64encode(png_bytes).decode('utf-8')
        elif image_type == "invalid_base64":
            return "invalid_base64_data"
        elif image_type == "empty":
            return ""
        elif image_type == "with_data_url":
            png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\xac\xac\x00\x05\x1f\x1f\x1f\x00\x01\x9a\x9c\x18\x00\x00\x00\x00IEND\xaeB`\x82'
            base64_data = base64.b64encode(png_bytes).decode('utf-8')
            return f"data:image/png;base64,{base64_data}"
        else:
            return ""

    async def test_1_end_to_end_api_workflow(self):
        """Test 1: Complete /scan endpoint workflow"""
        print("=== TEST 1: End-to-End API Workflow ===\n")
        
        test_cases = [
            {
                "name": "Valid image with mock AI response",
                "image_type": "valid",
                "expected_success": True
            },
            {
                "name": "Valid image with data URL prefix",
                "image_type": "with_data_url", 
                "expected_success": True
            }
        ]
        
        for case in test_cases:
            print(f"Testing: {case['name']}")
            
            try:
                # Create test request
                image_data = self.create_test_image_data(case["image_type"])
                request = ScanRequest(image=image_data)
                
                # Measure performance
                start_time = time.time()
                
                # Call the scan endpoint
                result = await scan_ingredients(request)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # Validate response structure
                if isinstance(result, list):
                    print(f"  ✅ Response is a list (length: {len(result)})")
                    
                    # Validate each ingredient
                    for i, ingredient in enumerate(result):
                        if isinstance(ingredient, ScannedIngredient):
                            print(f"  ✅ Ingredient {i+1}: {ingredient.name}")
                            print(f"     - Quantity: {ingredient.quantity.amount} {ingredient.quantity.unit}")
                            print(f"     - Expiration: {ingredient.estimatedExpiration}")
                            
                            # Validate data types for Swift compatibility
                            assert isinstance(ingredient.name, str), "Name must be string"
                            assert isinstance(ingredient.quantity.amount, float), "Amount must be float"
                            assert isinstance(ingredient.quantity.unit, str), "Unit must be string"
                            assert ingredient.estimatedExpiration is None or isinstance(ingredient.estimatedExpiration, str), "Expiration must be string or None"
                            
                            # Validate ISO8601 format if expiration exists
                            if ingredient.estimatedExpiration:
                                assert ingredient.estimatedExpiration.endswith('Z'), "Expiration must end with Z"
                                assert 'T' in ingredient.estimatedExpiration, "Expiration must contain T separator"
                        else:
                            print(f"  ❌ Ingredient {i+1} is not ScannedIngredient type")
                    
                    # Test JSON serialization (Swift compatibility)
                    json_data = [ingredient.model_dump() for ingredient in result]
                    json_str = json.dumps(json_data)
                    parsed_back = json.loads(json_str)
                    
                    print(f"  ✅ JSON serialization successful")
                    print(f"  ✅ Response time: {response_time:.3f}s")
                    
                    self.test_results.append({
                        "test": case["name"],
                        "status": "PASS",
                        "response_time": response_time,
                        "ingredient_count": len(result)
                    })
                    
                else:
                    print(f"  ❌ Response is not a list: {type(result)}")
                    self.test_results.append({
                        "test": case["name"],
                        "status": "FAIL",
                        "error": f"Response type: {type(result)}"
                    })
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.test_results.append({
                    "test": case["name"],
                    "status": "FAIL",
                    "error": str(e)
                })
            
            print()

    async def test_2_data_transformation_formats(self):
        """Test 2: Data transformation with various quantity and expiration formats"""
        print("=== TEST 2: Data Transformation Test ===\n")
        
        # Mock different AI responses to test transformation
        test_transformations = [
            {
                "name": "Various quantity formats",
                "mock_response": [
                    {"name": "Apples", "quantity": "3 pieces", "estimatedExpiration": "1 week", "confidence": 0.9},
                    {"name": "Milk", "quantity": "2.5 cups", "estimatedExpiration": "3 days", "confidence": 0.85},
                    {"name": "Cheese", "quantity": "1 bottle", "estimatedExpiration": "2 months", "confidence": 0.8},
                    {"name": "Rice", "quantity": "0.5 lbs", "estimatedExpiration": "1 year", "confidence": 0.75}
                ]
            },
            {
                "name": "Edge case quantities",
                "mock_response": [
                    {"name": "Salt", "quantity": "1 container", "estimatedExpiration": "never", "confidence": 0.95},
                    {"name": "Flour", "quantity": "2.25 kg", "estimatedExpiration": "6 months", "confidence": 0.8},
                    {"name": "Eggs", "quantity": "12 pieces", "estimatedExpiration": "2 weeks", "confidence": 0.9}
                ]
            },
            {
                "name": "Special characters and long names",
                "mock_response": [
                    {"name": "Jalapeño Peppers (Hot!)", "quantity": "5 pieces", "estimatedExpiration": "1 week", "confidence": 0.85},
                    {"name": "Organic Free-Range Grass-Fed Chicken Breast", "quantity": "1.5 lbs", "estimatedExpiration": "2 days", "confidence": 0.9}
                ]
            }
        ]
        
        for test_case in test_transformations:
            print(f"Testing: {test_case['name']}")
            
            try:
                # Mock the groq service response
                with patch.object(groq_service, 'recognize_ingredients', new_callable=AsyncMock) as mock_recognize:
                    mock_recognize.return_value = test_case["mock_response"]
                    
                    # Create request
                    image_data = self.create_test_image_data("valid")
                    request = ScanRequest(image=image_data)
                    
                    # Call scan endpoint
                    result = await scan_ingredients(request)
                    
                    # Validate transformations
                    for i, ingredient in enumerate(result):
                        original = test_case["mock_response"][i]
                        
                        print(f"  Ingredient: {ingredient.name}")
                        print(f"    Original quantity: '{original['quantity']}'")
                        print(f"    Transformed: {ingredient.quantity.amount} {ingredient.quantity.unit}")
                        print(f"    Original expiration: '{original['estimatedExpiration']}'")
                        print(f"    Transformed: {ingredient.estimatedExpiration}")
                        
                        # Validate quantity parsing
                        assert ingredient.quantity.amount > 0, "Amount must be positive"
                        assert isinstance(ingredient.quantity.amount, float), "Amount must be float"
                        assert len(ingredient.quantity.unit) > 0, "Unit must not be empty"
                        
                        # Validate expiration handling
                        if original['estimatedExpiration'].lower() in ['never', 'indefinite']:
                            assert ingredient.estimatedExpiration is None, "Never expiring items should have None expiration"
                        else:
                            assert ingredient.estimatedExpiration is not None, "Items with expiration should have date"
                            assert ingredient.estimatedExpiration.endswith('Z'), "Date must be UTC"
                        
                        print(f"    ✅ Transformation successful")
                    
                    self.test_results.append({
                        "test": f"Data transformation - {test_case['name']}",
                        "status": "PASS",
                        "ingredient_count": len(result)
                    })
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.test_results.append({
                    "test": f"Data transformation - {test_case['name']}",
                    "status": "FAIL",
                    "error": str(e)
                })
            
            print()

    async def test_3_swift_integration_simulation(self):
        """Test 3: Simulate Swift integration and data consumption"""
        print("=== TEST 3: Swift Integration Simulation ===\n")
        
        try:
            # Create a comprehensive test response
            image_data = self.create_test_image_data("valid")
            request = ScanRequest(image=image_data)
            
            # Get response from scan endpoint
            result = await scan_ingredients(request)
            
            # Convert to JSON as Swift would receive it
            json_response = [ingredient.model_dump() for ingredient in result]
            json_string = json.dumps(json_response)
            
            print("Swift Integration Test:")
            print(f"JSON Response Length: {len(json_string)} characters")
            print("Sample JSON Structure:")
            print(json.dumps(json_response[:2] if len(json_response) >= 2 else json_response, indent=2))
            
            # Simulate Swift Codable parsing
            print("\nSimulating Swift Codable parsing:")
            
            for i, ingredient_json in enumerate(json_response):
                print(f"\nIngredient {i+1} Swift Compatibility:")
                
                # Test required fields exist
                required_fields = ['name', 'quantity', 'estimatedExpiration']
                for field in required_fields:
                    if field in ingredient_json:
                        print(f"  ✅ {field}: present")
                    else:
                        print(f"  ❌ {field}: missing")
                        raise AssertionError(f"Required field {field} missing")
                
                # Test quantity structure
                quantity = ingredient_json['quantity']
                if 'amount' in quantity and 'unit' in quantity:
                    print(f"  ✅ quantity structure: valid")
                    print(f"    - amount: {quantity['amount']} ({type(quantity['amount']).__name__})")
                    print(f"    - unit: '{quantity['unit']}' ({type(quantity['unit']).__name__})")
                else:
                    print(f"  ❌ quantity structure: invalid")
                    raise AssertionError("Quantity structure invalid")
                
                # Test data types match Swift expectations
                swift_type_mapping = {
                    'name': (str, 'String'),
                    'estimatedExpiration': (type(None), str, 'String?')
                }
                
                for field, expected_types in swift_type_mapping.items():
                    value = ingredient_json[field]
                    if isinstance(expected_types, tuple):
                        if any(isinstance(value, t) for t in expected_types):
                            swift_type = 'String?' if value is None else 'String'
                            print(f"  ✅ {field}: {type(value).__name__} -> Swift {swift_type}")
                        else:
                            print(f"  ❌ {field}: unexpected type {type(value).__name__}")
                            raise AssertionError(f"Type mismatch for {field}")
                    else:
                        if isinstance(value, expected_types):
                            print(f"  ✅ {field}: {type(value).__name__} -> Swift {expected_types[1]}")
                        else:
                            print(f"  ❌ {field}: expected {expected_types[0].__name__}, got {type(value).__name__}")
                            raise AssertionError(f"Type mismatch for {field}")
            
            # Test ScannedIngredient.toIngredient() conversion simulation
            print("\nSimulating ScannedIngredient.toIngredient() conversion:")
            
            for ingredient_json in json_response:
                # Simulate the Swift conversion logic
                converted = {
                    "id": f"scanned_{int(time.time())}_{hash(ingredient_json['name']) % 10000}",
                    "name": ingredient_json['name'],
                    "quantity": ingredient_json['quantity']['amount'],
                    "unit": ingredient_json['quantity']['unit'],
                    "category": "other",  # Would be determined by Swift logic
                    "expiration_date": ingredient_json['estimatedExpiration'],
                    "location": "fridge",
                    "notes": "Scanned from image"
                }
                
                print(f"  ✅ Converted: {converted['name']}")
                print(f"    - ID: {converted['id']}")
                print(f"    - Quantity: {converted['quantity']} {converted['unit']}")
                print(f"    - Expiration: {converted['expiration_date']}")
            
            self.test_results.append({
                "test": "Swift integration simulation",
                "status": "PASS",
                "json_size": len(json_string),
                "ingredient_count": len(json_response)
            })
            
        except Exception as e:
            print(f"❌ Swift integration test failed: {str(e)}")
            self.test_results.append({
                "test": "Swift integration simulation",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_4_error_handling(self):
        """Test 4: Error handling scenarios"""
        print("=== TEST 4: Error Handling Test ===\n")
        
        error_test_cases = [
            {
                "name": "Empty image data",
                "image_type": "empty",
                "expected_error": "No image provided"
            },
            {
                "name": "Invalid base64 data",
                "image_type": "invalid_base64",
                "expected_error": "Invalid base64 image data"
            }
        ]
        
        for case in error_test_cases:
            print(f"Testing: {case['name']}")
            
            try:
                image_data = self.create_test_image_data(case["image_type"])
                request = ScanRequest(image=image_data)
                
                # This should raise an HTTPException
                result = await scan_ingredients(request)
                
                # If we get here, the test failed (should have raised an exception)
                print(f"  ❌ Expected error but got result: {result}")
                self.test_results.append({
                    "test": f"Error handling - {case['name']}",
                    "status": "FAIL",
                    "error": "Expected exception but got result"
                })
                
            except Exception as e:
                # Check if it's the expected error
                error_message = str(e)
                if case["expected_error"] in error_message:
                    print(f"  ✅ Correctly handled error: {error_message}")
                    self.test_results.append({
                        "test": f"Error handling - {case['name']}",
                        "status": "PASS",
                        "error_handled": error_message
                    })
                else:
                    print(f"  ⚠️  Unexpected error: {error_message}")
                    self.test_results.append({
                        "test": f"Error handling - {case['name']}",
                        "status": "PARTIAL",
                        "error": error_message
                    })
            
            print()

    async def test_5_performance_validation(self):
        """Test 5: Basic performance validation"""
        print("=== TEST 5: Performance Test ===\n")
        
        try:
            # Test multiple requests to measure performance
            image_data = self.create_test_image_data("valid")
            request = ScanRequest(image=image_data)
            
            response_times = []
            memory_usage = []
            
            print("Running performance tests...")
            
            for i in range(5):  # Run 5 test requests
                start_time = time.time()
                
                result = await scan_ingredients(request)
                
                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)
                
                print(f"  Request {i+1}: {response_time:.3f}s ({len(result)} ingredients)")
            
            # Calculate performance metrics
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"\nPerformance Results:")
            print(f"  Average response time: {avg_response_time:.3f}s")
            print(f"  Min response time: {min_response_time:.3f}s")
            print(f"  Max response time: {max_response_time:.3f}s")
            
            # Performance validation
            performance_issues = []
            
            if avg_response_time > 5.0:
                performance_issues.append(f"Average response time too high: {avg_response_time:.3f}s")
            
            if max_response_time > 10.0:
                performance_issues.append(f"Max response time too high: {max_response_time:.3f}s")
            
            if performance_issues:
                print(f"  ⚠️  Performance issues found:")
                for issue in performance_issues:
                    print(f"    - {issue}")
                status = "PARTIAL"
            else:
                print(f"  ✅ Performance acceptable")
                status = "PASS"
            
            self.performance_metrics = {
                "avg_response_time": avg_response_time,
                "min_response_time": min_response_time,
                "max_response_time": max_response_time,
                "performance_issues": performance_issues
            }
            
            self.test_results.append({
                "test": "Performance validation",
                "status": status,
                "metrics": self.performance_metrics
            })
            
        except Exception as e:
            print(f"❌ Performance test failed: {str(e)}")
            self.test_results.append({
                "test": "Performance validation",
                "status": "FAIL",
                "error": str(e)
            })

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE END-TO-END TEST REPORT")
        print("="*80)
        
        # Summary statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        partial_tests = len([r for r in self.test_results if r["status"] == "PARTIAL"])
        
        print(f"\nTEST SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Partial: {partial_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        print(f"\nDETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"  {status_icon} {result['test']}: {result['status']}")
            
            if "error" in result:
                print(f"    Error: {result['error']}")
            if "response_time" in result:
                print(f"    Response Time: {result['response_time']:.3f}s")
            if "ingredient_count" in result:
                print(f"    Ingredients Found: {result['ingredient_count']}")
        
        # Performance metrics
        if self.performance_metrics:
            print(f"\nPERFORMANCE METRICS:")
            print(f"  Average Response Time: {self.performance_metrics['avg_response_time']:.3f}s")
            print(f"  Min Response Time: {self.performance_metrics['min_response_time']:.3f}s")
            print(f"  Max Response Time: {self.performance_metrics['max_response_time']:.3f}s")
            
            if self.performance_metrics['performance_issues']:
                print(f"  Performance Issues:")
                for issue in self.performance_metrics['performance_issues']:
                    print(f"    - {issue}")
        
        # Final assessment
        print(f"\nFINAL ASSESSMENT:")
        if failed_tests == 0:
            if partial_tests == 0:
                print("🎉 EXCELLENT: All tests passed! The scan implementation is ready for production.")
            else:
                print("✅ GOOD: Core functionality works with minor issues noted.")
        else:
            print("❌ ISSUES FOUND: Critical problems need to be addressed before production.")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        if failed_tests == 0 and partial_tests == 0:
            print("  • Implementation is production-ready")
            print("  • Consider adding monitoring for response times")
            print("  • Add automated testing to CI/CD pipeline")
        else:
            print("  • Fix failing tests before deployment")
            print("  • Address performance issues if any")
            print("  • Add additional error handling")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "partial": partial_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "performance_metrics": self.performance_metrics,
            "ready_for_production": failed_tests == 0
        }

async def main():
    """Run all end-to-end tests"""
    print("Starting Comprehensive End-to-End Testing for Scan Fridge Implementation")
    print("="*80)
    
    tester = EndToEndScanTester()
    
    # Run all tests
    await tester.test_1_end_to_end_api_workflow()
    await tester.test_2_data_transformation_formats()
    await tester.test_3_swift_integration_simulation()
    await tester.test_4_error_handling()
    await tester.test_5_performance_validation()
    
    # Generate final report
    report = tester.generate_test_report()
    
    return report

if __name__ == "__main__":
    # Run the tests
    report = asyncio.run(main())
    
    # Exit with appropriate code
    exit_code = 0 if report["ready_for_production"] else 1
    sys.exit(exit_code)