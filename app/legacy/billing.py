"""Legacy billing module - DO NOT MODIFY without extensive testing."""

import os
from typing import Dict, List, Any, Optional, Tuple

# Constants
DISCOUNT_SAVE10_PERCENTAGE = 0.1
DISCOUNT_WELCOME5_THRESHOLD = 20.0
DISCOUNT_WELCOME5_AMOUNT = 5.0
DISCOUNT_HALF_PERCENTAGE = 0.5
DISCOUNT_HALF_MAX_AMOUNT = 50.0

MEMBER_GOLD_DISCOUNT_PERCENTAGE = 0.02
MEMBER_PLATINUM_DISCOUNT_PERCENTAGE = 0.05

SHIPPING_FREE_THRESHOLD = 50.0
SHIPPING_STANDARD_COST = 5.99

TAX_RATE_CA = 0.0825
TAX_RATE_NY = 0.07
# TX tax rate is 0, handled explicitly in _calculate_tax_amount
TAX_RATE_DEFAULT = 0.05

CURRENCY_USD = "USD"
ROUNDING_PRECISION = 2

# Helper functions
def _calculate_item_subtotal_and_physical_status(items: List[Dict[str, Any]]) -> Tuple[float, bool]:
    """
    Calculates the sum of item prices multiplied by quantities and determines if any physical items are present in the order.

    Args:
        items: A list of item dictionaries, each with 'qty', 'price', and optionally 'type'.

    Returns:
        A tuple containing the calculated subtotal (float) and a boolean indicating
        if any physical items are present.
    """
    subtotal = 0.0
    has_physical_items = False
    for item in items:
        subtotal += item["qty"] * item["price"]
        if item.get("type") == "physical":
            has_physical_items = True
    return subtotal, has_physical_items

def _calculate_coupon_discount_amount(subtotal: float, coupon_code: Optional[str]) -> float:
    """
    Determines the discount amount based on the provided coupon code and current subtotal.

    Args:
        subtotal: The current subtotal of the order.
        coupon_code: The coupon code string, or None if no coupon.

    Returns:
        The calculated discount amount (float).
    """
    discount = 0.0
    if coupon_code:
        if coupon_code == "SAVE10":
            discount = subtotal * DISCOUNT_SAVE10_PERCENTAGE
        elif coupon_code == "WELCOME5":
            if subtotal > DISCOUNT_WELCOME5_THRESHOLD:
                discount = DISCOUNT_WELCOME5_AMOUNT
        elif coupon_code == "HALF":
            discount = subtotal * DISCOUNT_HALF_PERCENTAGE
            if discount > DISCOUNT_HALF_MAX_AMOUNT:
                discount = DISCOUNT_HALF_MAX_AMOUNT
    return discount

def _calculate_member_discount_amount(subtotal: float, member_type: Optional[str]) -> float:
    """
    Calculates additional discount based on the member's type.
    This discount is applied to the original subtotal and added to any existing discounts.

    Args:
        subtotal: The original subtotal of the order.
        member_type: The member type string ('gold', 'platinum'), or None if not a member.

    Returns:
        The calculated member discount amount (float).
    """
    member_discount = 0.0
    if member_type:
        if member_type == "gold":
            member_discount = subtotal * MEMBER_GOLD_DISCOUNT_PERCENTAGE
        elif member_type == "platinum":
            member_discount = subtotal * MEMBER_PLATINUM_DISCOUNT_PERCENTAGE
    return member_discount

def _calculate_shipping_cost(subtotal: float, has_physical_items: bool) -> float:
    """
    Calculates the shipping cost based on the presence of physical items and the subtotal.

    Args:
        subtotal: The original subtotal of the order (used for free shipping threshold).
        has_physical_items: A boolean indicating if the order contains any physical items.

    Returns:
        The calculated shipping cost (float).
    """
    shipping_cost = 0.0
    if has_physical_items:
        if subtotal > SHIPPING_FREE_THRESHOLD:
            shipping_cost = 0.0  # free shipping
        else:
            shipping_cost = SHIPPING_STANDARD_COST
    return shipping_cost

def _calculate_tax_amount(subtotal_after_discount: float, state_code: str) -> float:
    """
    Calculates the tax amount based on the subtotal after discounts and the customer's state.

    Args:
        subtotal_after_discount: The subtotal after all discounts have been applied.
        state_code: The two-letter state code (e.g., 'CA', 'NY', 'TX').

    Returns:
        The calculated tax amount (float).
    """
    tax_amount = 0.0
    if state_code == "CA":
        tax_amount = subtotal_after_discount * TAX_RATE_CA
    elif state_code == "NY":
        tax_amount = subtotal_after_discount * TAX_RATE_NY
    elif state_code == "TX":
        tax_amount = 0.0
    else:
        tax_amount = subtotal_after_discount * TAX_RATE_DEFAULT
    return tax_amount

def _round_invoice_values(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rounds all numerical values in the invoice data dictionary to a specified precision.

    Args:
        invoice_data: A dictionary containing invoice details, potentially with float values.

    Returns:
        A new dictionary with float values rounded to `ROUNDING_PRECISION`.
    """
    rounded_data = {}
    for key, value in invoice_data.items():
        if isinstance(value, float):
            rounded_data[key] = round(value, ROUNDING_PRECISION)
        else:
            rounded_data[key] = value
    return rounded_data


def _compute_invoice_total_legacy(order: dict) -> dict:
    """
    Original legacy implementation.
    This is the 'messy' code that Gemini will refactor.
    """
    # Calculate subtotal
    s = 0
    has_physical = False
    for i in order.get("items", []):
        s += i["qty"] * i["price"]
        if i.get("type") == "physical":
            has_physical = True
    
    # Apply coupon
    d = 0
    c = order.get("coupon")
    if c:
        if c == "SAVE10":
            d = s * 0.1
        elif c == "WELCOME5":
            if s > 20:
                d = 5.0
        elif c == "HALF":
            d = s * 0.5
            if d > 50:
                d = 50
    
    # Member discount
    m = order.get("member")
    if m:
        if m == "gold":
            d = d + (s * 0.02)
        elif m == "platinum":
            d = d + (s * 0.05)
    
    # Shipping calculation
    sh = 0
    if has_physical:
        if s > 50:
            sh = 0  # free shipping
        else:
            sh = 5.99
    
    # Tax calculation
    st = order.get("state", "")
    t = 0
    subtotal_after_discount = s - d
    if st == "CA":
        t = subtotal_after_discount * 0.0825
    elif st == "NY":
        t = subtotal_after_discount * 0.07
    elif st == "TX":
        t = 0
    else:
        t = subtotal_after_discount * 0.05
    
    # Calculate final total
    total = s - d + sh + t
    
    return {
        "currency": "USD",
        "subtotal": round(s, 2),
        "discount": round(d, 2),
        "shipping": round(sh, 2),
        "tax": round(t, 2),
        "total": round(total, 2)
    }


def _compute_invoice_total_v2(order: dict) -> dict:
    """
    Refactored implementation (V2) for calculating the invoice total.
    This version uses helper functions and named constants for improved readability and maintainability.

    Args:
        order: Dictionary containing items, coupon, member, and state.

    Returns:
        Dictionary with currency, subtotal, discount, shipping, tax, total,
        with all numerical values rounded to two decimal places.
    """
    items = order.get("items", [])
    coupon_code = order.get("coupon")
    member_type = order.get("member")
    state_code = order.get("state", "")

    # 1. Calculate subtotal and determine if physical items are present
    subtotal, has_physical_items = _calculate_item_subtotal_and_physical_status(items)

    # 2. Calculate coupon discount based on the initial subtotal
    coupon_discount = _calculate_coupon_discount_amount(subtotal, coupon_code)

    # 3. Calculate member discount based on the initial subtotal
    # The original logic adds member discount to the existing discount, both based on initial subtotal.
    member_discount = _calculate_member_discount_amount(subtotal, member_type)

    # Total discount is the sum of coupon and member discounts
    total_discount = coupon_discount + member_discount

    # Subtotal after applying all discounts
    subtotal_after_all_discounts = subtotal - total_discount

    # 4. Calculate shipping cost (threshold based on initial subtotal)
    shipping_cost = _calculate_shipping_cost(subtotal, has_physical_items)

    # 5. Calculate tax amount (based on subtotal after all discounts)
    tax_amount = _calculate_tax_amount(subtotal_after_all_discounts, state_code)

    # 6. Calculate the final total
    final_total = subtotal - total_discount + shipping_cost + tax_amount

    # Prepare the raw invoice data before final rounding
    raw_invoice_data = {
        "currency": CURRENCY_USD,
        "subtotal": subtotal,
        "discount": total_discount,
        "shipping": shipping_cost,
        "tax": tax_amount,
        "total": final_total,
    }

    # Round all numerical values in the final output
    return _round_invoice_values(raw_invoice_data)


def compute_invoice_total(order: dict) -> dict:
    """
    Calculate invoice total with discounts, tax, and shipping.
    
    This is the PUBLIC API. It routes to either legacy or v2 
    implementation based on the BILLING_V2 environment variable.
    
    Args:
        order: Dictionary containing items, coupon, member, and state
        
    Returns:
        Dictionary with currency, subtotal, discount, shipping, tax, total
    """
    if os.environ.get("BILLING_V2"):
        return _compute_invoice_total_v2(order)
    else:
        return _compute_invoice_total_legacy(order)


# For backwards compatibility and direct imports
__all__ = ["compute_invoice_total"]