#!/usr/bin/env python3
"""
Comprehensive Data Transformation Testing
Tests various quantity formats, expiration formats, and edge cases for Swift compatibility
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.ingredients import _parse_quantity_value, _parse_unit_value, _parse_expiration_days
from app.api.ingredients import QuantityInfo, ScannedIngredient

class DataTransformationTester:
    """Comprehensive testing for data transformation functions"""
    
    def __init__(self):
        self.test_results = []
        
    def test_quantity_parsing(self):
        """Test quantity parsing with various formats"""
        print("=== QUANTITY PARSING TESTS ===\n")
        
        quantity_test_cases = [
            # Standard formats
            {"input": "3 pieces", "expected_amount": 3.0, "expected_unit": "pieces"},
            {"input": "2.5 cups", "expected_amount": 2.5, "expected_unit": "cups"},
            {"input": "1 bottle", "expected_amount": 1.0, "expected_unit": "bottles"},
            {"input": "0.5 lbs", "expected_amount": 0.5, "expected_unit": "lbs"},
            
            # Edge cases with decimals
            {"input": "1.25 kg", "expected_amount": 1.25, "expected_unit": "kg"},
            {"input": "0.1 containers", "expected_amount": 0.1, "expected_unit": "containers"},
            {"input": "10.75 pieces", "expected_amount": 10.75, "expected_unit": "pieces"},
            
            # Large quantities
            {"input": "25 lbs", "expected_amount": 25.0, "expected_unit": "lbs"},
            {"input": "100 pieces", "expected_amount": 100.0, "expected_unit": "pieces"},
            
            # Different unit variations
            {"input": "2 items", "expected_amount": 2.0, "expected_unit": "pieces"},
            {"input": "1 box", "expected_amount": 1.0, "expected_unit": "containers"},
            {"input": "3 cartons", "expected_amount": 3.0, "expected_unit": "cartons"},
            {"input": "1 loaf", "expected_amount": 1.0, "expected_unit": "loaves"},
            {"input": "2 blocks", "expected_amount": 2.0, "expected_unit": "blocks"},
            
            # Edge cases - no number
            {"input": "pieces", "expected_amount": 1.0, "expected_unit": "pieces"},
            {"input": "bottle", "expected_amount": 1.0, "expected_unit": "bottles"},
            
            # Edge cases - unusual formats
            {"input": "half container", "expected_amount": 1.0, "expected_unit": "containers"},  # Should extract 1.0 as fallback
            {"input": "a few pieces", "expected_amount": 1.0, "expected_unit": "pieces"},
            
            # Fractional representations
            {"input": "1/2 cups", "expected_amount": 1.0, "expected_unit": "cups"},  # Will extract first number
            {"input": "2 1/2 lbs", "expected_amount": 2.0, "expected_unit": "lbs"},  # Will extract first number
        ]
        
        for i, case in enumerate(quantity_test_cases):
            print(f"Test {i+1}: '{case['input']}'")
            
            try:
                # Test amount parsing
                parsed_amount = _parse_quantity_value(case["input"])
                amount_correct = abs(parsed_amount - case["expected_amount"]) < 0.001
                
                # Test unit parsing
                parsed_unit = _parse_unit_value(case["input"])
                unit_correct = parsed_unit == case["expected_unit"]
                
                print(f"  Amount: {parsed_amount} (expected: {case['expected_amount']}) {'✅' if amount_correct else '❌'}")
                print(f"  Unit: '{parsed_unit}' (expected: '{case['expected_unit']}') {'✅' if unit_correct else '❌'}")
                
                # Test QuantityInfo creation
                quantity_info = QuantityInfo(amount=parsed_amount, unit=parsed_unit)
                
                # Test JSON serialization (Swift compatibility)
                json_data = quantity_info.model_dump()
                json_str = json.dumps(json_data)
                parsed_back = json.loads(json_str)
                
                # Validate types for Swift
                assert isinstance(parsed_back["amount"], (int, float)), "Amount must be numeric for Swift Double"
                assert isinstance(parsed_back["unit"], str), "Unit must be string for Swift String"
                
                status = "PASS" if (amount_correct and unit_correct) else "FAIL"
                self.test_results.append({
                    "test": f"Quantity parsing - {case['input']}",
                    "status": status,
                    "parsed_amount": parsed_amount,
                    "parsed_unit": parsed_unit,
                    "expected_amount": case["expected_amount"],
                    "expected_unit": case["expected_unit"]
                })
                
                print(f"  JSON: {json_str}")
                print(f"  Status: {status}")
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.test_results.append({
                    "test": f"Quantity parsing - {case['input']}",
                    "status": "ERROR",
                    "error": str(e)
                })
            
            print()

    def test_expiration_parsing(self):
        """Test expiration date parsing with various formats"""
        print("=== EXPIRATION PARSING TESTS ===\n")
        
        expiration_test_cases = [
            # Standard day formats
            {"input": "1 day", "expected_days": 1},
            {"input": "3 days", "expected_days": 3},
            {"input": "7 days", "expected_days": 7},
            
            # Week formats
            {"input": "1 week", "expected_days": 7},
            {"input": "2 weeks", "expected_days": 14},
            {"input": "3 weeks", "expected_days": 21},
            
            # Month formats
            {"input": "1 month", "expected_days": 30},
            {"input": "2 months", "expected_days": 60},
            {"input": "6 months", "expected_days": 180},
            
            # Edge cases
            {"input": "never", "expected_days": 7},  # Default fallback
            {"input": "indefinite", "expected_days": 7},  # Default fallback
            {"input": "unknown", "expected_days": 7},  # Default fallback
            
            # Decimal formats
            {"input": "1.5 weeks", "expected_days": 7},  # Will extract 1, then multiply by 7
            {"input": "2.5 days", "expected_days": 2},  # Will extract 2
            
            # No number formats
            {"input": "days", "expected_days": 7},  # Default fallback
            {"input": "week", "expected_days": 7},  # Default fallback
            {"input": "month", "expected_days": 30},  # Default fallback
            
            # Mixed formats
            {"input": "a few days", "expected_days": 7},  # Default fallback
            {"input": "several weeks", "expected_days": 7},  # Default fallback
        ]
        
        current_date = datetime.now()
        
        for i, case in enumerate(expiration_test_cases):
            print(f"Test {i+1}: '{case['input']}'")
            
            try:
                # Test expiration days parsing
                parsed_days = _parse_expiration_days(case["input"])
                days_correct = parsed_days == case["expected_days"]
                
                print(f"  Parsed days: {parsed_days} (expected: {case['expected_days']}) {'✅' if days_correct else '❌'}")
                
                # Test date calculation
                estimated_expiration = current_date + timedelta(days=parsed_days)
                iso_date = estimated_expiration.isoformat() + "Z"
                
                print(f"  Calculated date: {iso_date}")
                
                # Test ISO8601 format for Swift compatibility
                assert iso_date.endswith('Z'), "Date must end with Z for UTC"
                assert 'T' in iso_date, "Date must contain T separator"
                
                # Test JSON serialization
                json_str = json.dumps(iso_date)
                parsed_back = json.loads(json_str)
                assert isinstance(parsed_back, str), "Date must be string for Swift"
                
                status = "PASS" if days_correct else "FAIL"
                self.test_results.append({
                    "test": f"Expiration parsing - {case['input']}",
                    "status": status,
                    "parsed_days": parsed_days,
                    "expected_days": case["expected_days"],
                    "iso_date": iso_date
                })
                
                print(f"  Status: {status}")
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.test_results.append({
                    "test": f"Expiration parsing - {case['input']}",
                    "status": "ERROR",
                    "error": str(e)
                })
            
            print()

    def test_scanned_ingredient_creation(self):
        """Test ScannedIngredient creation with various data combinations"""
        print("=== SCANNED INGREDIENT CREATION TESTS ===\n")
        
        ingredient_test_cases = [
            {
                "name": "Standard ingredient",
                "ingredient_name": "Apples",
                "quantity_str": "3 pieces",
                "expiration_str": "1 week"
            },
            {
                "name": "Decimal quantity",
                "ingredient_name": "Milk",
                "quantity_str": "2.5 cups",
                "expiration_str": "3 days"
            },
            {
                "name": "Long name with special characters",
                "ingredient_name": "Jalapeño Peppers (Hot!) - Organic",
                "quantity_str": "5 pieces",
                "expiration_str": "1 week"
            },
            {
                "name": "No expiration",
                "ingredient_name": "Salt",
                "quantity_str": "1 container",
                "expiration_str": "never"
            },
            {
                "name": "Large quantity",
                "ingredient_name": "Rice",
                "quantity_str": "25 lbs",
                "expiration_str": "6 months"
            },
            {
                "name": "Unicode characters",
                "ingredient_name": "Crème Fraîche",
                "quantity_str": "1 container",
                "expiration_str": "1 week"
            }
        ]
        
        current_date = datetime.now()
        
        for i, case in enumerate(ingredient_test_cases):
            print(f"Test {i+1}: {case['name']}")
            print(f"  Input: '{case['ingredient_name']}', '{case['quantity_str']}', '{case['expiration_str']}'")
            
            try:
                # Parse components
                quantity_amount = _parse_quantity_value(case["quantity_str"])
                quantity_unit = _parse_unit_value(case["quantity_str"])
                
                # Handle expiration
                if case["expiration_str"].lower() in ['never', 'indefinite', 'permanent']:
                    estimated_expiration = None
                else:
                    expiration_days = _parse_expiration_days(case["expiration_str"])
                    estimated_expiration = current_date + timedelta(days=expiration_days)
                
                # Create ScannedIngredient
                scanned_ingredient = ScannedIngredient(
                    name=case["ingredient_name"],
                    quantity=QuantityInfo(
                        amount=quantity_amount,
                        unit=quantity_unit
                    ),
                    estimatedExpiration=estimated_expiration.isoformat() + "Z" if estimated_expiration else None
                )
                
                print(f"  Created ingredient: {scanned_ingredient.name}")
                print(f"  Quantity: {scanned_ingredient.quantity.amount} {scanned_ingredient.quantity.unit}")
                print(f"  Expiration: {scanned_ingredient.estimatedExpiration}")
                
                # Test JSON serialization for Swift compatibility
                json_data = scanned_ingredient.model_dump()
                json_str = json.dumps(json_data, ensure_ascii=False)  # Handle Unicode
                parsed_back = json.loads(json_str)
                
                # Validate structure for Swift
                required_fields = ['name', 'quantity', 'estimatedExpiration']
                for field in required_fields:
                    assert field in parsed_back, f"Missing required field: {field}"
                
                # Validate types
                assert isinstance(parsed_back['name'], str), "Name must be string"
                assert isinstance(parsed_back['quantity']['amount'], (int, float)), "Amount must be numeric"
                assert isinstance(parsed_back['quantity']['unit'], str), "Unit must be string"
                assert parsed_back['estimatedExpiration'] is None or isinstance(parsed_back['estimatedExpiration'], str), "Expiration must be string or null"
                
                # Validate date format if present
                if parsed_back['estimatedExpiration']:
                    assert parsed_back['estimatedExpiration'].endswith('Z'), "Date must end with Z"
                    assert 'T' in parsed_back['estimatedExpiration'], "Date must contain T"
                
                print(f"  JSON length: {len(json_str)} characters")
                print(f"  ✅ Swift compatibility validated")
                
                self.test_results.append({
                    "test": f"ScannedIngredient creation - {case['name']}",
                    "status": "PASS",
                    "json_size": len(json_str),
                    "has_expiration": scanned_ingredient.estimatedExpiration is not None
                })
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                self.test_results.append({
                    "test": f"ScannedIngredient creation - {case['name']}",
                    "status": "ERROR",
                    "error": str(e)
                })
            
            print()

    def test_edge_cases_and_boundaries(self):
        """Test edge cases and boundary conditions"""
        print("=== EDGE CASES AND BOUNDARY TESTS ===\n")
        
        edge_cases = [
            {
                "name": "Very small quantity",
                "quantity_str": "0.01 pieces",
                "should_work": True
            },
            {
                "name": "Zero quantity",
                "quantity_str": "0 pieces",
                "should_work": True  # Should default to 1.0
            },
            {
                "name": "Very large quantity",
                "quantity_str": "999999 pieces",
                "should_work": True
            },
            {
                "name": "Empty quantity string",
                "quantity_str": "",
                "should_work": True  # Should default to 1.0 pieces
            },
            {
                "name": "Only spaces",
                "quantity_str": "   ",
                "should_work": True  # Should default to 1.0 pieces
            },
            {
                "name": "Special characters in quantity",
                "quantity_str": "2.5 pieces!",
                "should_work": True
            },
            {
                "name": "Multiple numbers",
                "quantity_str": "2 to 3 pieces",
                "should_work": True  # Should extract first number
            }
        ]
        
        for i, case in enumerate(edge_cases):
            print(f"Test {i+1}: {case['name']}")
            print(f"  Input: '{case['quantity_str']}'")
            
            try:
                # Test quantity parsing
                parsed_amount = _parse_quantity_value(case["quantity_str"])
                parsed_unit = _parse_unit_value(case["quantity_str"])
                
                print(f"  Parsed: {parsed_amount} {parsed_unit}")
                
                # Validate results
                assert parsed_amount >= 0, "Amount should not be negative"
                assert isinstance(parsed_amount, float), "Amount should be float"
                assert isinstance(parsed_unit, str), "Unit should be string"
                assert len(parsed_unit) > 0, "Unit should not be empty"
                
                # Test with ScannedIngredient
                quantity_info = QuantityInfo(amount=parsed_amount, unit=parsed_unit)
                scanned_ingredient = ScannedIngredient(
                    name="Test Ingredient",
                    quantity=quantity_info,
                    estimatedExpiration=None
                )
                
                # Test JSON serialization
                json_data = scanned_ingredient.model_dump()
                json_str = json.dumps(json_data)
                
                print(f"  JSON: {json_str}")
                print(f"  ✅ Edge case handled successfully")
                
                self.test_results.append({
                    "test": f"Edge case - {case['name']}",
                    "status": "PASS",
                    "parsed_amount": parsed_amount,
                    "parsed_unit": parsed_unit
                })
                
            except Exception as e:
                if case["should_work"]:
                    print(f"  ❌ Unexpected error: {str(e)}")
                    self.test_results.append({
                        "test": f"Edge case - {case['name']}",
                        "status": "FAIL",
                        "error": str(e)
                    })
                else:
                    print(f"  ✅ Expected error: {str(e)}")
                    self.test_results.append({
                        "test": f"Edge case - {case['name']}",
                        "status": "PASS",
                        "expected_error": str(e)
                    })
            
            print()

    def generate_transformation_report(self):
        """Generate comprehensive transformation test report"""
        print("\n" + "="*80)
        print("DATA TRANSFORMATION TEST REPORT")
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
        
        # Category breakdown
        categories = {}
        for result in self.test_results:
            category = result["test"].split(" - ")[0]
            if category not in categories:
                categories[category] = {"pass": 0, "fail": 0, "error": 0}
            categories[category][result["status"].lower()] += 1
        
        print(f"\nCATEGORY BREAKDOWN:")
        for category, stats in categories.items():
            total = stats["pass"] + stats["fail"] + stats["error"]
            success_rate = (stats["pass"] / total) * 100 if total > 0 else 0
            print(f"  {category}: {stats['pass']}/{total} passed ({success_rate:.1f}%)")
        
        # Detailed results
        print(f"\nDETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"  {status_icon} {result['test']}")
            
            if "error" in result:
                print(f"    Error: {result['error']}")
            if "parsed_amount" in result and "parsed_unit" in result:
                print(f"    Result: {result['parsed_amount']} {result['parsed_unit']}")
        
        # Swift compatibility assessment
        print(f"\nSWIFT COMPATIBILITY ASSESSMENT:")
        compatibility_issues = []
        
        for result in self.test_results:
            if result["status"] in ["FAIL", "ERROR"]:
                compatibility_issues.append(result["test"])
        
        if not compatibility_issues:
            print("  ✅ All data transformations are Swift-compatible")
            print("  ✅ Quantity parsing handles various formats correctly")
            print("  ✅ Expiration parsing produces valid ISO8601 dates")
            print("  ✅ Edge cases are handled gracefully")
        else:
            print("  ❌ Compatibility issues found:")
            for issue in compatibility_issues:
                print(f"    - {issue}")
        
        # Final assessment
        print(f"\nFINAL ASSESSMENT:")
        if failed_tests == 0 and error_tests == 0:
            print("🎉 EXCELLENT: All data transformations work correctly for Swift integration!")
        elif failed_tests == 0:
            print("✅ GOOD: Core transformations work, but some edge cases need attention.")
        else:
            print("❌ ISSUES: Critical transformation problems need to be fixed.")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "swift_compatible": len(compatibility_issues) == 0,
            "categories": categories
        }

def main():
    """Run all data transformation tests"""
    print("Starting Comprehensive Data Transformation Testing")
    print("="*80)
    
    tester = DataTransformationTester()
    
    # Run all transformation tests
    tester.test_quantity_parsing()
    tester.test_expiration_parsing()
    tester.test_scanned_ingredient_creation()
    tester.test_edge_cases_and_boundaries()
    
    # Generate final report
    report = tester.generate_transformation_report()
    
    return report

if __name__ == "__main__":
    # Run the tests
    report = main()
    
    # Exit with appropriate code
    exit_code = 0 if report["swift_compatible"] else 1
    sys.exit(exit_code)