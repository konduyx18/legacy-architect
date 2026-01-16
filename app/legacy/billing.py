"""Legacy billing module - DO NOT MODIFY without extensive testing."""

import os
from typing import Dict, List, Any, Optional, Tuple

# Constants
DISCOUNT_SAVE10_RATE = 0.1
DISCOUNT_WELCOME5_THRESHOLD = 20.0
DISCOUNT_WELCOME5_VALUE = 5.0
DISCOUNT_HALF_RATE = 0.5
DISCOUNT_HALF_LIMIT = 50.0
MEMBER_GOLD_RATE = 0.02
MEMBER_PLATINUM_RATE = 0.05
SHIPPING_FREE_THRESHOLD = 50.0
SHIPPING_STANDARD_FEE = 5.99
TAX_RATE_CA = 0.0825
TAX_RATE_NY = 0.07
TAX_RATE_TX = 0.0
TAX_RATE_DEFAULT = 0.05
PRECISION_DECIMALS = 2
CURRENCY_USD = "USD"

# Helper functions
def _calculate_base_subtotal(items: List[Dict[str, Any]]) -> Tuple[float, bool]:
    """Calculates the sum of (qty * price) and identifies if any item is 'physical'."""
    subtotal = 0.0
    has_physical = False
    for item in items:
        subtotal += item.get("qty", 0) * item.get("price", 0.0)
        if item.get("type") == "physical":
            has_physical = True
    return subtotal, has_physical

def _get_coupon_discount(subtotal: float, coupon_code: Optional[str]) -> float:
    """Calculates the discount amount based on the coupon code and subtotal."""
    if not coupon_code:
        return 0.0
    
    if coupon_code == "SAVE10":
        return subtotal * DISCOUNT_SAVE10_RATE
    if coupon_code == "WELCOME5":
        return DISCOUNT_WELCOME5_VALUE if subtotal > DISCOUNT_WELCOME5_THRESHOLD else 0.0
    if coupon_code == "HALF":
        discount = subtotal * DISCOUNT_HALF_RATE
        return min(discount, DISCOUNT_HALF_LIMIT)
    return 0.0

def _get_member_discount(subtotal: float, member_type: Optional[str]) -> float:
    """Calculates the additional discount based on membership tier (Gold/Platinum)."""
    if member_type == "gold":
        return subtotal * MEMBER_GOLD_RATE
    if member_type == "platinum":
        return subtotal * MEMBER_PLATINUM_RATE
    return 0.0

def _get_shipping_fee(subtotal: float, has_physical: bool) -> float:
    """Determines shipping cost based on subtotal and physical item presence."""
    if has_physical:
        return 0.0 if subtotal > SHIPPING_FREE_THRESHOLD else SHIPPING_STANDARD_FEE
    return 0.0

def _get_tax_total(subtotal_after_discount: float, state_code: str) -> float:
    """Calculates tax based on the state code and the subtotal after discounts."""
    rates = {
        "CA": TAX_RATE_CA,
        "NY": TAX_RATE_NY,
        "TX": TAX_RATE_TX
    }
    rate = rates.get(state_code, TAX_RATE_DEFAULT)
    return subtotal_after_discount * rate


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
    Uses centralized constants and helper functions to ensure logic parity with legacy.

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

    # 1. Calculate base subtotal and physical status
    subtotal, has_physical = _calculate_base_subtotal(items)

    # 2. Calculate discounts (Coupon + Member)
    coupon_discount = _get_coupon_discount(subtotal, coupon_code)
    member_discount = _get_member_discount(subtotal, member_type)
    total_discount = coupon_discount + member_discount

    # 3. Calculate shipping fee
    shipping_fee = _get_shipping_fee(subtotal, has_physical)

    # 4. Calculate tax based on subtotal after all discounts
    subtotal_after_discount = subtotal - total_discount
    tax_total = _get_tax_total(subtotal_after_discount, state_code)

    # 5. Calculate final total
    final_total = subtotal - total_discount + shipping_fee + tax_total

    return {
        "currency": CURRENCY_USD,
        "subtotal": round(subtotal, PRECISION_DECIMALS),
        "discount": round(total_discount, PRECISION_DECIMALS),
        "shipping": round(shipping_fee, PRECISION_DECIMALS),
        "tax": round(tax_total, PRECISION_DECIMALS),
        "total": round(final_total, PRECISION_DECIMALS)
    }


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