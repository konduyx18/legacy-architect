"""API endpoints for billing - simulates REST API layer."""

from app.legacy.billing import compute_invoice_total


def handle_checkout_request(request_data: dict) -> dict:
    """
    Handle checkout API request.
    
    Args:
        request_data: Dict with items, coupon, member, state
    
    Returns:
        API response with invoice and status
    """
    try:
        invoice = compute_invoice_total(request_data)
        return {
            "status": "success",
            "invoice": invoice
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def get_price_preview(items: list, state: str = "CA") -> dict:
    """
    Get price preview without committing to purchase.
    
    Args:
        items: List of items
        state: State for tax calculation
    
    Returns:
        Preview dict with estimated total
    """
    order = {"items": items, "state": state}
    result = compute_invoice_total(order)
    return {
        "estimated_total": result["total"],
        "breakdown": result
    }


def validate_coupon(coupon: str, items: list) -> dict:
    """
    Validate a coupon code and show potential savings.
    
    Args:
        coupon: Coupon code to validate
        items: Items to calculate savings for
    
    Returns:
        Validation result with savings amount
    """
    valid_coupons = ["SAVE10", "WELCOME5", "HALF"]
    
    if coupon not in valid_coupons:
        return {"valid": False, "message": "Invalid coupon code"}
    
    without_coupon = compute_invoice_total({"items": items, "state": "CA"})
    with_coupon = compute_invoice_total({"items": items, "state": "CA", "coupon": coupon})
    
    savings = without_coupon["total"] - with_coupon["total"]
    
    return {
        "valid": True,
        "coupon": coupon,
        "savings": round(savings, 2)
    }
