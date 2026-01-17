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
TAX_RATES = {
    "CA": 0.0825,
    "NY": 0.07,
    "TX": 0.0
}
TAX_RATE_DEFAULT = 0.05
PRECISION_DECIMALS = 2
CURRENCY_USD = "USD"

# Helper functions
def _calculate_items_subtotal(items: List[Dict[str, Any]]) -> Tuple[float, bool]:
    """
    Calculates the raw subtotal and checks for the presence of physical items.
    
    Args:
        items: List of item dictionaries containing qty and price.
        
    Returns:
        A tuple containing the float subtotal and a boolean indicating if physical items exist.
    """
    subtotal = 0.0
    has_physical = False
    for item in items:
        subtotal += item["qty"] * item["price"]
        if item.get("type") == "physical":
            has_physical = True
    return subtotal, has_physical

def _calculate_total_discount(subtotal: float, coupon: Optional[str], member: Optional[str]) -> float:
    """
    Aggregates coupon-based and membership-based discounts.
    
    Args:
        subtotal: The base subtotal amount.
        coupon: The coupon code string.
        member: The membership tier string.
        
    Returns:
        The total discount amount as a float.
    """
    discount = 0.0
    
    # Coupon Logic
    if coupon == "SAVE10":
        discount = subtotal * DISCOUNT_SAVE10_RATE
    elif coupon == "WELCOME5":
        if subtotal > DISCOUNT_WELCOME5_THRESHOLD:
            discount = DISCOUNT_WELCOME5_VALUE
    elif coupon == "HALF":
        discount = subtotal * DISCOUNT_HALF_RATE
        if discount > DISCOUNT_HALF_LIMIT:
            discount = DISCOUNT_HALF_LIMIT
            
    # Member Logic (Additive to coupon)
    if member == "gold":
        discount += subtotal * MEMBER_GOLD_RATE
    elif member == "platinum":
        discount += subtotal * MEMBER_PLATINUM_RATE
        
    return discount

def _calculate_shipping_fee(subtotal: float, has_physical: bool) -> float:
    """
    Determines shipping costs based on subtotal and item types.
    
    Args:
        subtotal: The base subtotal amount.
        has_physical: Boolean indicating if the order contains physical items.
        
    Returns:
        The shipping fee as a float.
    """
    if has_physical:
        return 0.0 if subtotal > SHIPPING_FREE_THRESHOLD else SHIPPING_STANDARD_FEE
    return 0.0

def _calculate_tax_amount(subtotal_after_discount: float, state: str) -> float:
    """
    Computes tax based on the state and the post-discount subtotal.
    
    Args:
        subtotal_after_discount: Subtotal after all discounts are applied.
        state: The state code string.
        
    Returns:
        The calculated tax amount as a float.
    """
    rate = TAX_RATES.get(state, TAX_RATE_DEFAULT)
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
    # 1. Calculate base subtotal and physical status
    items = order.get("items", [])
    subtotal, has_physical = _calculate_items_subtotal(items)

    # 2. Calculate total discounts (Coupon + Member)
    discount_amount = _calculate_total_discount(
        subtotal, 
        order.get("coupon"), 
        order.get("member")
    )

    # 3. Calculate shipping fee
    shipping_fee = _calculate_shipping_fee(subtotal, has_physical)

    # 4. Calculate tax based on subtotal after all discounts
    subtotal_after_discount = subtotal - discount_amount
    tax_amount = _calculate_tax_amount(subtotal_after_discount, order.get("state", ""))

    # 5. Calculate final total
    final_total = subtotal - discount_amount + shipping_fee + tax_amount

    return {
        "currency": CURRENCY_USD,
        "subtotal": round(subtotal, PRECISION_DECIMALS),
        "discount": round(discount_amount, PRECISION_DECIMALS),
        "shipping": round(shipping_fee, PRECISION_DECIMALS),
        "tax": round(tax_amount, PRECISION_DECIMALS),
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