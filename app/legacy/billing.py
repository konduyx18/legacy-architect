"""Legacy billing module - DO NOT MODIFY without extensive testing"""

import os

def compute_invoice_total(order: dict) -> dict:
    """Calculate invoice total with discounts, tax, and shipping."""
    
    # Check for new version
    if os.environ.get("BILLING_V2"):
        # TODO: implement refactored version
        pass
    
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
            # else:
            #     d = 0  # old logic
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
        # elif m == "silver":  # deprecated
        #     d = d + (s * 0.01)
    
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


# Legacy helper functions (unused)
# def apply_discount(amount, percent):
#     return amount * (1 - percent)
# 
# def calculate_tax_old(amount, state):
#     # Old tax calculation - replaced by inline logic
#     rates = {"CA": 0.0825, "NY": 0.07, "TX": 0}
#     return amount * rates.get(state, 0.05)
