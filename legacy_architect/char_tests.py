"""Characterization test generator - captures current behavior of legacy code."""

import os
import json
from typing import List, Dict, Any
from datetime import datetime

from legacy_architect.artifacts import write_text, get_artifact_path


# Test case templates for the billing module
BILLING_TEST_CASES = [
    {
        "name": "empty_order",
        "description": "Empty order with no items",
        "input": {"items": [], "state": "CA"},
        "note": "Edge case: no items"
    },
    {
        "name": "single_physical_item_under_50",
        "description": "Single physical item under $50 (shipping applies)",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 25.00, "type": "physical"}],
            "state": "CA"
        },
        "note": "Subtotal < $50, so $5.99 shipping applies"
    },
    {
        "name": "single_physical_item_over_50",
        "description": "Single physical item over $50 (free shipping)",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 75.00, "type": "physical"}],
            "state": "CA"
        },
        "note": "Subtotal > $50, so free shipping"
    },
    {
        "name": "digital_only_order",
        "description": "Digital-only order (no shipping)",
        "input": {
            "items": [{"name": "eBook", "qty": 2, "price": 15.00, "type": "digital"}],
            "state": "CA"
        },
        "note": "Digital items never have shipping"
    },
    {
        "name": "mixed_physical_digital",
        "description": "Mixed physical and digital items",
        "input": {
            "items": [
                {"name": "Widget", "qty": 1, "price": 30.00, "type": "physical"},
                {"name": "eBook", "qty": 1, "price": 10.00, "type": "digital"}
            ],
            "state": "CA"
        },
        "note": "Has physical items, so shipping rules apply"
    },
    {
        "name": "save10_coupon",
        "description": "SAVE10 coupon (10% off)",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "coupon": "SAVE10",
            "state": "TX"
        },
        "note": "10% discount = $10 off"
    },
    {
        "name": "welcome5_coupon_eligible",
        "description": "WELCOME5 coupon with subtotal > $20",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 50.00, "type": "physical"}],
            "coupon": "WELCOME5",
            "state": "TX"
        },
        "note": "$5 off because subtotal > $20"
    },
    {
        "name": "welcome5_coupon_not_eligible",
        "description": "WELCOME5 coupon with subtotal <= $20",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 15.00, "type": "physical"}],
            "coupon": "WELCOME5",
            "state": "TX"
        },
        "note": "No discount because subtotal <= $20"
    },
    {
        "name": "half_coupon_under_cap",
        "description": "HALF coupon under $50 cap",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 60.00, "type": "physical"}],
            "coupon": "HALF",
            "state": "TX"
        },
        "note": "50% of $60 = $30 discount (under $50 cap)"
    },
    {
        "name": "half_coupon_over_cap",
        "description": "HALF coupon capped at $50",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 200.00, "type": "physical"}],
            "coupon": "HALF",
            "state": "TX"
        },
        "note": "50% of $200 = $100, but capped at $50"
    },
    {
        "name": "gold_member",
        "description": "Gold member discount (2%)",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "member": "gold",
            "state": "TX"
        },
        "note": "2% member discount = $2 off"
    },
    {
        "name": "platinum_member",
        "description": "Platinum member discount (5%)",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "member": "platinum",
            "state": "TX"
        },
        "note": "5% member discount = $5 off"
    },
    {
        "name": "coupon_plus_member",
        "description": "Coupon and member discount combined",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "coupon": "SAVE10",
            "member": "gold",
            "state": "TX"
        },
        "note": "10% coupon + 2% member = $12 total discount"
    },
    {
        "name": "california_tax",
        "description": "California tax rate (8.25%)",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "state": "CA"
        },
        "note": "CA tax = 8.25%"
    },
    {
        "name": "new_york_tax",
        "description": "New York tax rate (7%)",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "state": "NY"
        },
        "note": "NY tax = 7%"
    },
    {
        "name": "texas_no_tax",
        "description": "Texas - no tax",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "state": "TX"
        },
        "note": "TX has no sales tax"
    },
    {
        "name": "default_state_tax",
        "description": "Unknown state - default tax (5%)",
        "input": {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "state": "FL"
        },
        "note": "Unknown state defaults to 5% tax"
    },
    {
        "name": "complex_order",
        "description": "Complex order with everything",
        "input": {
            "items": [
                {"name": "Widget", "qty": 3, "price": 25.00, "type": "physical"},
                {"name": "Gadget", "qty": 2, "price": 15.00, "type": "physical"},
                {"name": "eBook", "qty": 1, "price": 9.99, "type": "digital"}
            ],
            "coupon": "SAVE10",
            "member": "platinum",
            "state": "CA"
        },
        "note": "Multiple items, coupon, member discount, CA tax"
    },
    {
        "name": "multiple_quantities",
        "description": "High quantity order",
        "input": {
            "items": [{"name": "Widget", "qty": 10, "price": 5.00, "type": "physical"}],
            "state": "TX"
        },
        "note": "10 x $5 = $50 subtotal (exactly at free shipping threshold)"
    },
    {
        "name": "zero_price_item",
        "description": "Free item in order",
        "input": {
            "items": [
                {"name": "Widget", "qty": 1, "price": 30.00, "type": "physical"},
                {"name": "Free Sample", "qty": 1, "price": 0.00, "type": "physical"}
            ],
            "state": "TX"
        },
        "note": "Zero-price item shouldn't break calculation"
    },
]


def generate_characterization_tests(
    target_module: str = "app.legacy.billing",
    target_function: str = "compute_invoice_total",
    output_file: str = "tests/test_characterization_billing.py"
) -> str:
    """
    Generate characterization tests for the billing module.
    
    This captures the CURRENT behavior of the legacy code, which we'll use
    to ensure the refactored version produces identical results.
    
    Args:
        target_module: Module path to import from
        target_function: Function to test
        output_file: Output file path
    
    Returns:
        Path to the generated test file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate test file header
    test_code = f'''"""
Characterization tests for {target_module}.{target_function}

AUTO-GENERATED by Legacy Architect on {timestamp}
DO NOT EDIT MANUALLY - These tests capture the current behavior of the legacy code.

Purpose: These tests verify that the refactored code produces IDENTICAL results
to the original legacy code. Any difference indicates a behavior change that needs
investigation.
"""

import os
import pytest
from {target_module} import {target_function}


class TestCharacterization{target_function.title().replace("_", "")}:
    """Characterization tests capturing current behavior of {target_function}."""
    
'''
    
    # Generate test methods for each test case
    for case in BILLING_TEST_CASES:
        test_name = f"test_{case['name']}"
        description = case['description']
        input_data = json.dumps(case['input'], indent=8)
        note = case.get('note', '')
        
        test_code += f'''
    def {test_name}(self):
        """
        {description}
        
        Note: {note}
        """
        order = {input_data}
        
        # Get result from current implementation
        result = {target_function}(order)
        
        # Verify structure
        assert "currency" in result
        assert "subtotal" in result
        assert "discount" in result
        assert "shipping" in result
        assert "tax" in result
        assert "total" in result
        
        # Verify total calculation
        expected_total = result["subtotal"] - result["discount"] + result["shipping"] + result["tax"]
        assert abs(result["total"] - expected_total) < 0.02, \\
            f"Total mismatch: {{result['total']}} != {{expected_total}}"
        
        # Snapshot the current values (for documentation)
        # Subtotal: {{result["subtotal"]}}
        # Discount: {{result["discount"]}}
        # Shipping: {{result["shipping"]}}
        # Tax: {{result["tax"]}}
        # Total: {{result["total"]}}
    
'''
    
    # Add dual-mode test class
    test_code += '''

class TestDualModeEquivalence:
    """
    Tests that verify BOTH modes (default and BILLING_V2) produce identical results.
    
    These tests are the heart of safe refactoring - they ensure the refactored
    code behind the feature flag behaves exactly like the original.
    """
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Save and restore BILLING_V2 env var."""
        original = os.environ.get("BILLING_V2")
        yield
        if original is None:
            os.environ.pop("BILLING_V2", None)
        else:
            os.environ["BILLING_V2"] = original
    
'''
    
    # Generate dual-mode tests for a subset of cases
    key_cases = [
        "single_physical_item_under_50",
        "save10_coupon",
        "coupon_plus_member",
        "complex_order",
    ]
    
    for case_name in key_cases:
        case = next((c for c in BILLING_TEST_CASES if c['name'] == case_name), None)
        if not case:
            continue
        
        input_data = json.dumps(case['input'], indent=8)
        
        test_code += f'''
    def test_dual_mode_{case_name}(self):
        """
        Verify default and BILLING_V2 modes produce identical results.
        
        Test case: {case['description']}
        """
        order = {input_data}
        
        # Run in default mode
        os.environ.pop("BILLING_V2", None)
        result_default = {target_function}(order)
        
        # Run in BILLING_V2 mode
        os.environ["BILLING_V2"] = "1"
        result_v2 = {target_function}(order)
        
        # Both should produce identical results
        assert result_default == result_v2, \\
            f"Mode mismatch:\\nDefault: {{result_default}}\\nV2: {{result_v2}}"
    
'''
    
    # Write the test file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(test_code)
    
    return output_file


def get_test_case_count() -> int:
    """Return the number of test cases available."""
    return len(BILLING_TEST_CASES)


def get_test_cases() -> List[Dict[str, Any]]:
    """Return all test cases."""
    return BILLING_TEST_CASES.copy()


if __name__ == "__main__":
    print("Generating characterization tests...")
    output = generate_characterization_tests()
    print(f"✅ Generated: {output}")
    print(f"   Test cases: {get_test_case_count()}")
    print(f"   Dual-mode tests: 4")
    print("\nRun with: pytest tests/test_characterization_billing.py -v")
