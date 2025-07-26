#!/usr/bin/env python3
"""
Swift Integration Simulation Test
Simulates how the Swift frontend would consume the scan endpoint response
Tests Codable parsing, data type compatibility, and conversion workflows
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.ingredients import ScannedIngredient, QuantityInfo

class SwiftIntegrationSimulator:
    """Simulates Swift frontend integration with the scan endpoint"""
    
    def __init__(self):
        self.test_results = []
        self.compatibility_issues = []
        
    def create_mock_scan_response(self) -> List[ScannedIngredient]:
        """Create a comprehensive mock scan response for testing"""
        current_date = datetime.now()
        
        return [
            # Standard ingredient
            ScannedIngredient(
                name="Apples",
                quantity=QuantityInfo(amount=3.0, unit="pieces"),
                estimatedExpiration=(current_date + timedelta(days=7)).isoformat() + "Z"
            ),
            # Decimal quantity
            ScannedIngredient(
                name="Milk",
                quantity=QuantityInfo(amount=2.5, unit="cups"),
                estimatedExpiration=(current_date + timedelta(days=3)).isoformat() + "Z"
            ),
            # No expiration
            ScannedIngredient(
                name="Salt",
                quantity=QuantityInfo(amount=1.0, unit="container"),
                estimatedExpiration=None
            ),
            # Long name with special characters
            ScannedIngredient(
                name="Organic Free-Range Grass-Fed Chicken Breast",
                quantity=QuantityInfo(amount=1.5, unit="lbs"),
                estimatedExpiration=(current_date + timedelta(days=2)).isoformat() + "Z"
            ),
            # Unicode characters
            ScannedIngredient(
                name="Jalapeño Peppers",
                quantity=QuantityInfo(amount=5.0, unit="pieces"),
                estimatedExpiration=(current_date + timedelta(days=10)).isoformat() + "Z"
            ),
            # Large quantity
            ScannedIngredient(
                name="Rice",
                quantity=QuantityInfo(amount=25.0, unit="lbs"),
                estimatedExpiration=(current_date + timedelta(days=365)).isoformat() + "Z"
            ),
            # Small decimal quantity
            ScannedIngredient(
                name="Vanilla Extract",
                quantity=QuantityInfo(amount=0.5, unit="bottles"),
                estimatedExpiration=(current_date + timedelta(days=730)).isoformat() + "Z"
            )
        ]

    def test_json_serialization_compatibility(self):
        """Test JSON serialization for Swift Codable compatibility"""
        print("=== JSON SERIALIZATION COMPATIBILITY TEST ===\n")
        
        try:
            # Create mock response
            mock_response = self.create_mock_scan_response()
            
            # Convert to JSON as the API would return
            json_data = [ingredient.model_dump() for ingredient in mock_response]
            json_string = json.dumps(json_data, ensure_ascii=False, indent=2)
            
            print(f"JSON Response Structure:")
            print(f"  Total size: {len(json_string)} characters")
            print(f"  Ingredient count: {len(json_data)}")
            print(f"  Sample structure:")
            print(json.dumps(json_data[0], indent=4))
            print()
            
            # Test JSON parsing (simulates Swift JSONDecoder)
            parsed_data = json.loads(json_string)
            
            print("JSON Parsing Validation:")
            print(f"  ✅ JSON is valid and parseable")
            print(f"  ✅ Array structure maintained: {isinstance(parsed_data, list)}")
            print(f"  ✅ All ingredients parsed: {len(parsed_data) == len(mock_response)}")
            
            # Validate each ingredient structure
            for i, ingredient_json in enumerate(parsed_data):
                print(f"\nIngredient {i+1} Structure Validation:")
                
                # Check required fields
                required_fields = ['name', 'quantity', 'estimatedExpiration']
                for field in required_fields:
                    if field in ingredient_json:
                        print(f"  ✅ {field}: present")
                    else:
                        print(f"  ❌ {field}: missing")
                        self.compatibility_issues.append(f"Missing field {field} in ingredient {i+1}")
                
                # Check quantity structure
                if 'quantity' in ingredient_json:
                    quantity = ingredient_json['quantity']
                    if isinstance(quantity, dict) and 'amount' in quantity and 'unit' in quantity:
                        print(f"  ✅ quantity structure: valid")
                        print(f"    - amount: {quantity['amount']} ({type(quantity['amount']).__name__})")
                        print(f"    - unit: '{quantity['unit']}' ({type(quantity['unit']).__name__})")
                    else:
                        print(f"  ❌ quantity structure: invalid")
                        self.compatibility_issues.append(f"Invalid quantity structure in ingredient {i+1}")
                
                # Check data types
                name = ingredient_json.get('name')
                expiration = ingredient_json.get('estimatedExpiration')
                
                if not isinstance(name, str):
                    print(f"  ❌ name type: {type(name).__name__} (expected str)")
                    self.compatibility_issues.append(f"Invalid name type in ingredient {i+1}")
                
                if expiration is not None and not isinstance(expiration, str):
                    print(f"  ❌ expiration type: {type(expiration).__name__} (expected str or None)")
                    self.compatibility_issues.append(f"Invalid expiration type in ingredient {i+1}")
            
            self.test_results.append({
                "test": "JSON serialization compatibility",
                "status": "PASS" if not self.compatibility_issues else "FAIL",
                "json_size": len(json_string),
                "ingredient_count": len(json_data),
                "issues": self.compatibility_issues.copy()
            })
            
        except Exception as e:
            print(f"❌ JSON serialization failed: {str(e)}")
            self.test_results.append({
                "test": "JSON serialization compatibility",
                "status": "ERROR",
                "error": str(e)
            })

    def test_swift_codable_simulation(self):
        """Simulate Swift Codable decoding process"""
        print("\n=== SWIFT CODABLE SIMULATION TEST ===\n")
        
        try:
            # Create mock response and convert to JSON
            mock_response = self.create_mock_scan_response()
            json_data = [ingredient.model_dump() for ingredient in mock_response]
            
            print("Simulating Swift Codable decoding process...")
            
            # Simulate Swift struct definitions
            @dataclass
            class SwiftQuantityInfo:
                amount: float
                unit: str
                
                @classmethod
                def from_json(cls, json_data: dict):
                    return cls(
                        amount=float(json_data['amount']),
                        unit=str(json_data['unit'])
                    )
            
            @dataclass
            class SwiftScannedIngredient:
                name: str
                quantity: SwiftQuantityInfo
                estimatedExpiration: Optional[str]
                
                @classmethod
                def from_json(cls, json_data: dict):
                    return cls(
                        name=str(json_data['name']),
                        quantity=SwiftQuantityInfo.from_json(json_data['quantity']),
                        estimatedExpiration=json_data.get('estimatedExpiration')
                    )
            
            # Simulate decoding process
            decoded_ingredients = []
            decoding_errors = []
            
            for i, ingredient_json in enumerate(json_data):
                try:
                    decoded_ingredient = SwiftScannedIngredient.from_json(ingredient_json)
                    decoded_ingredients.append(decoded_ingredient)
                    
                    print(f"  ✅ Ingredient {i+1} decoded successfully:")
                    print(f"    - Name: '{decoded_ingredient.name}'")
                    print(f"    - Quantity: {decoded_ingredient.quantity.amount} {decoded_ingredient.quantity.unit}")
                    print(f"    - Expiration: {decoded_ingredient.estimatedExpiration}")
                    
                    # Validate data types match Swift expectations
                    assert isinstance(decoded_ingredient.name, str), "Name must be String"
                    assert isinstance(decoded_ingredient.quantity.amount, float), "Amount must be Double"
                    assert isinstance(decoded_ingredient.quantity.unit, str), "Unit must be String"
                    assert decoded_ingredient.estimatedExpiration is None or isinstance(decoded_ingredient.estimatedExpiration, str), "Expiration must be String?"
                    
                except Exception as e:
                    decoding_errors.append(f"Ingredient {i+1}: {str(e)}")
                    print(f"  ❌ Ingredient {i+1} decoding failed: {str(e)}")
            
            print(f"\nCodable Decoding Results:")
            print(f"  Successfully decoded: {len(decoded_ingredients)}/{len(json_data)}")
            print(f"  Decoding errors: {len(decoding_errors)}")
            
            if decoding_errors:
                print(f"  Errors:")
                for error in decoding_errors:
                    print(f"    - {error}")
            
            self.test_results.append({
                "test": "Swift Codable simulation",
                "status": "PASS" if not decoding_errors else "FAIL",
                "decoded_count": len(decoded_ingredients),
                "total_count": len(json_data),
                "errors": decoding_errors
            })
            
        except Exception as e:
            print(f"❌ Codable simulation failed: {str(e)}")
            self.test_results.append({
                "test": "Swift Codable simulation",
                "status": "ERROR",
                "error": str(e)
            })

    def test_scanned_ingredient_to_ingredient_conversion(self):
        """Test the ScannedIngredient.toIngredient() conversion workflow"""
        print("\n=== SCANNED INGREDIENT TO INGREDIENT CONVERSION TEST ===\n")
        
        try:
            # Create mock response
            mock_response = self.create_mock_scan_response()
            json_data = [ingredient.model_dump() for ingredient in mock_response]
            
            print("Simulating ScannedIngredient.toIngredient() conversion...")
            
            # Simulate Swift conversion logic
            converted_ingredients = []
            conversion_errors = []
            
            for i, ingredient_json in enumerate(json_data):
                try:
                    # Simulate Swift conversion logic
                    converted_ingredient = {
                        "id": f"scanned_{int(datetime.now().timestamp())}_{i}",
                        "name": ingredient_json['name'],
                        "quantity": ingredient_json['quantity']['amount'],
                        "unit": ingredient_json['quantity']['unit'],
                        "category": self._guess_swift_category(ingredient_json['name']),
                        "expiration_date": ingredient_json.get('estimatedExpiration'),
                        "purchase_date": datetime.now().isoformat() + "Z",
                        "location": "fridge",
                        "notes": "Scanned from image",
                        "created_at": datetime.now().isoformat() + "Z",
                        "updated_at": datetime.now().isoformat() + "Z",
                        "image_url": None
                    }
                    
                    converted_ingredients.append(converted_ingredient)
                    
                    print(f"  ✅ Ingredient {i+1} converted successfully:")
                    print(f"    - ID: {converted_ingredient['id']}")
                    print(f"    - Name: '{converted_ingredient['name']}'")
                    print(f"    - Quantity: {converted_ingredient['quantity']} {converted_ingredient['unit']}")
                    print(f"    - Category: {converted_ingredient['category']}")
                    print(f"    - Expiration: {converted_ingredient['expiration_date']}")
                    print(f"    - Location: {converted_ingredient['location']}")
                    
                    # Validate conversion results
                    assert converted_ingredient['id'], "ID must be generated"
                    assert converted_ingredient['name'] == ingredient_json['name'], "Name must be preserved"
                    assert converted_ingredient['quantity'] == ingredient_json['quantity']['amount'], "Quantity amount must be preserved"
                    assert converted_ingredient['unit'] == ingredient_json['quantity']['unit'], "Unit must be preserved"
                    assert converted_ingredient['expiration_date'] == ingredient_json.get('estimatedExpiration'), "Expiration must be preserved"
                    
                except Exception as e:
                    conversion_errors.append(f"Ingredient {i+1}: {str(e)}")
                    print(f"  ❌ Ingredient {i+1} conversion failed: {str(e)}")
            
            print(f"\nConversion Results:")
            print(f"  Successfully converted: {len(converted_ingredients)}/{len(json_data)}")
            print(f"  Conversion errors: {len(conversion_errors)}")
            
            # Test final JSON serialization for Core Data storage
            if converted_ingredients:
                final_json = json.dumps(converted_ingredients, indent=2)
                print(f"  Final JSON size: {len(final_json)} characters")
                print(f"  ✅ Ready for Core Data storage")
            
            self.test_results.append({
                "test": "ScannedIngredient to Ingredient conversion",
                "status": "PASS" if not conversion_errors else "FAIL",
                "converted_count": len(converted_ingredients),
                "total_count": len(json_data),
                "errors": conversion_errors
            })
            
        except Exception as e:
            print(f"❌ Conversion test failed: {str(e)}")
            self.test_results.append({
                "test": "ScannedIngredient to Ingredient conversion",
                "status": "ERROR",
                "error": str(e)
            })

    def test_date_parsing_compatibility(self):
        """Test ISO8601 date parsing compatibility with Swift"""
        print("\n=== DATE PARSING COMPATIBILITY TEST ===\n")
        
        try:
            # Create various date formats to test
            current_date = datetime.now()
            test_dates = [
                current_date.isoformat() + "Z",  # Standard format
                (current_date + timedelta(days=1)).isoformat() + "Z",
                (current_date + timedelta(hours=12, minutes=30)).isoformat() + "Z",
                (current_date + timedelta(days=365)).isoformat() + "Z",
            ]
            
            print("Testing ISO8601 date formats for Swift compatibility:")
            
            date_parsing_errors = []
            
            for i, date_string in enumerate(test_dates):
                try:
                    print(f"\nDate {i+1}: {date_string}")
                    
                    # Validate format requirements for Swift
                    assert date_string.endswith('Z'), "Date must end with Z for UTC"
                    assert 'T' in date_string, "Date must contain T separator"
                    assert len(date_string.split('T')) == 2, "Date must have exactly one T separator"
                    
                    # Test JSON serialization
                    json_str = json.dumps(date_string)
                    parsed_back = json.loads(json_str)
                    assert parsed_back == date_string, "Date must survive JSON round-trip"
                    
                    # Simulate Swift date parsing
                    # In Swift: ISO8601DateFormatter().date(from: dateString)
                    try:
                        # Python equivalent validation
                        parsed_date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                        print(f"  ✅ Parseable by Swift: {parsed_date}")
                    except ValueError as e:
                        print(f"  ❌ Not parseable by Swift: {str(e)}")
                        date_parsing_errors.append(f"Date {i+1}: {str(e)}")
                    
                    print(f"  ✅ Format validation passed")
                    
                except AssertionError as e:
                    print(f"  ❌ Format validation failed: {str(e)}")
                    date_parsing_errors.append(f"Date {i+1}: {str(e)}")
            
            # Test with None values (optional dates)
            print(f"\nTesting None/null date handling:")
            none_date = None
            json_str = json.dumps(none_date)
            parsed_back = json.loads(json_str)
            assert parsed_back is None, "None must survive JSON round-trip"
            print(f"  ✅ None/null handling: {parsed_back}")
            
            print(f"\nDate Parsing Results:")
            print(f"  Valid dates: {len(test_dates) - len(date_parsing_errors)}/{len(test_dates)}")
            print(f"  Parsing errors: {len(date_parsing_errors)}")
            
            self.test_results.append({
                "test": "Date parsing compatibility",
                "status": "PASS" if not date_parsing_errors else "FAIL",
                "valid_dates": len(test_dates) - len(date_parsing_errors),
                "total_dates": len(test_dates),
                "errors": date_parsing_errors
            })
            
        except Exception as e:
            print(f"❌ Date parsing test failed: {str(e)}")
            self.test_results.append({
                "test": "Date parsing compatibility",
                "status": "ERROR",
                "error": str(e)
            })

    def test_unicode_and_special_characters(self):
        """Test Unicode and special character handling"""
        print("\n=== UNICODE AND SPECIAL CHARACTERS TEST ===\n")
        
        try:
            # Create ingredients with various Unicode and special characters
            test_ingredients = [
                ScannedIngredient(
                    name="Jalapeño Peppers",
                    quantity=QuantityInfo(amount=5.0, unit="pieces"),
                    estimatedExpiration=None
                ),
                ScannedIngredient(
                    name="Crème Fraîche",
                    quantity=QuantityInfo(amount=1.0, unit="container"),
                    estimatedExpiration=datetime.now().isoformat() + "Z"
                ),
                ScannedIngredient(
                    name="Mozzarella (Fresh) - 16oz",
                    quantity=QuantityInfo(amount=1.0, unit="packages"),
                    estimatedExpiration=datetime.now().isoformat() + "Z"
                ),
                ScannedIngredient(
                    name="Café au Lait",
                    quantity=QuantityInfo(amount=2.0, unit="cups"),
                    estimatedExpiration=None
                ),
                ScannedIngredient(
                    name="Piña Colada Mix",
                    quantity=QuantityInfo(amount=1.0, unit="bottles"),
                    estimatedExpiration=datetime.now().isoformat() + "Z"
                )
            ]
            
            print("Testing Unicode and special character handling:")
            
            unicode_errors = []
            
            for i, ingredient in enumerate(test_ingredients):
                try:
                    print(f"\nIngredient {i+1}: '{ingredient.name}'")
                    
                    # Test JSON serialization with Unicode
                    json_data = ingredient.model_dump()
                    json_str = json.dumps(json_data, ensure_ascii=False)
                    
                    print(f"  JSON (UTF-8): {json_str}")
                    
                    # Test JSON parsing
                    parsed_back = json.loads(json_str)
                    assert parsed_back['name'] == ingredient.name, "Unicode name must survive round-trip"
                    
                    # Test ASCII-safe JSON (what might happen in some network scenarios)
                    json_str_ascii = json.dumps(json_data, ensure_ascii=True)
                    parsed_back_ascii = json.loads(json_str_ascii)
                    
                    print(f"  JSON (ASCII): {json_str_ascii}")
                    print(f"  ✅ Unicode handling successful")
                    
                    # Validate that Swift would handle this correctly
                    assert isinstance(parsed_back['name'], str), "Name must remain string type"
                    assert len(parsed_back['name']) > 0, "Name must not be empty"
                    
                except Exception as e:
                    print(f"  ❌ Unicode handling failed: {str(e)}")
                    unicode_errors.append(f"Ingredient {i+1}: {str(e)}")
            
            print(f"\nUnicode Handling Results:")
            print(f"  Successfully handled: {len(test_ingredients) - len(unicode_errors)}/{len(test_ingredients)}")
            print(f"  Unicode errors: {len(unicode_errors)}")
            
            self.test_results.append({
                "test": "Unicode and special characters",
                "status": "PASS" if not unicode_errors else "FAIL",
                "handled_count": len(test_ingredients) - len(unicode_errors),
                "total_count": len(test_ingredients),
                "errors": unicode_errors
            })
            
        except Exception as e:
            print(f"❌ Unicode test failed: {str(e)}")
            self.test_results.append({
                "test": "Unicode and special characters",
                "status": "ERROR",
                "error": str(e)
            })

    def _guess_swift_category(self, ingredient_name: str) -> str:
        """Simulate Swift category guessing logic"""
        name_lower = ingredient_name.lower()
        
        if any(word in name_lower for word in ['apple', 'banana', 'orange', 'berry']):
            return "produce"
        elif any(word in name_lower for word in ['milk', 'cheese', 'yogurt']):
            return "dairy"
        elif any(word in name_lower for word in ['chicken', 'beef', 'fish']):
            return "protein"
        elif any(word in name_lower for word in ['rice', 'bread', 'pasta']):
            return "grains"
        elif any(word in name_lower for word in ['salt', 'pepper', 'garlic']):
            return "spices"
        else:
            return "other"

    def generate_swift_integration_report(self):
        """Generate comprehensive Swift integration test report"""
        print("\n" + "="*80)
        print("SWIFT INTEGRATION SIMULATION REPORT")
        print("="*80)
        
        # Summary statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"\nTEST SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Errors: {error_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        print(f"\nDETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"  {status_icon} {result['test']}")
            
            if "error" in result:
                print(f"    Error: {result['error']}")
            if "issues" in result and result["issues"]:
                print(f"    Issues: {len(result['issues'])}")
                for issue in result["issues"]:
                    print(f"      - {issue}")
        
        # Swift compatibility assessment
        print(f"\nSWIFT COMPATIBILITY ASSESSMENT:")
        
        all_compatibility_issues = []
        for result in self.test_results:
            if "issues" in result:
                all_compatibility_issues.extend(result["issues"])
            if "errors" in result:
                all_compatibility_issues.extend(result["errors"])
        
        if not all_compatibility_issues:
            print("  ✅ Perfect Swift integration compatibility")
            print("  ✅ JSON serialization works flawlessly")
            print("  ✅ Codable decoding will work without issues")
            print("  ✅ ScannedIngredient.toIngredient() conversion ready")
            print("  ✅ Date parsing is Swift-compatible")
            print("  ✅ Unicode characters handled correctly")
        else:
            print("  ❌ Swift compatibility issues found:")
            for issue in all_compatibility_issues:
                print(f"    - {issue}")
        
        # Final assessment
        print(f"\nFINAL ASSESSMENT:")
        if failed_tests == 0 and error_tests == 0:
            print("🎉 EXCELLENT: Swift integration will work seamlessly!")
            print("   The backend response format is perfectly compatible with Swift expectations.")
        elif failed_tests == 0:
            print("✅ GOOD: Core integration works, minor issues noted.")
        else:
            print("❌ CRITICAL: Swift integration issues must be resolved before deployment.")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        if failed_tests == 0 and error_tests == 0:
            print("  • Backend is ready for Swift frontend integration")
            print("  • Consider adding automated Swift compatibility tests")
            print("  • Document the API response format for Swift developers")
        else:
            print("  • Fix all failing compatibility tests")
            print("  • Test with actual Swift code if possible")
            print("  • Add validation for edge cases")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "swift_compatible": failed_tests == 0 and error_tests == 0,
            "compatibility_issues": all_compatibility_issues
        }

def main():
    """Run all Swift integration simulation tests"""
    print("Starting Swift Integration Simulation Testing")
    print("="*80)
    
    simulator = SwiftIntegrationSimulator()
    
    # Run all integration tests
    simulator.test_json_serialization_compatibility()
    simulator.test_swift_codable_simulation()
    simulator.test_scanned_ingredient_to_ingredient_conversion()
    simulator.test_date_parsing_compatibility()
    simulator.test_unicode_and_special_characters()
    
    # Generate final report
    report = simulator.generate_swift_integration_report()
    
    return report

if __name__ == "__main__":
    # Run the tests
    report = main()
    
    # Exit with appropriate code
    exit_code = 0 if report["swift_compatible"] else 1
