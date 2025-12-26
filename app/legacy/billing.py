"""Legacy billing module - DO NOT MODIFY without extensive testing."""

import os
from typing import Dict, List, Any


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
    Refactored implementation (V2).
    This will be replaced by Gemini's refactored code.
    For now, it calls the legacy implementation to ensure tests pass.
    """
    # TODO: This will be replaced by Gemini's refactored code
    # For now, delegate to legacy to ensure identical behavior
    return _compute_invoice_total_legacy(order)


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
