"""Billing service - wraps legacy billing module for business logic."""

from app.legacy.billing import compute_invoice_total


class BillingService:
    """Service layer for billing operations."""
    
    def __init__(self, default_state: str = "CA"):
        self.default_state = default_state
    
    def calculate_order_total(self, items: list, coupon: str = None, 
                              member: str = None, state: str = None) -> dict:
        """
        Calculate total for an order.
        
        Args:
            items: List of items with qty, price, and optional type
            coupon: Optional coupon code (SAVE10, WELCOME5, HALF)
            member: Optional member level (gold, platinum)
            state: State for tax calculation (defaults to instance default)
        
        Returns:
            Invoice dict with subtotal, discount, shipping, tax, total
        """
        order = {
            "items": items,
            "state": state or self.default_state
        }
        
        if coupon:
            order["coupon"] = coupon
        if member:
            order["member"] = member
        
        return compute_invoice_total(order)
    
    def get_shipping_estimate(self, items: list) -> float:
        """Get shipping estimate for items."""
        result = self.calculate_order_total(items)
        return result["shipping"]
    
    def apply_member_discount(self, items: list, member: str) -> float:
        """Calculate how much a member saves."""
        without_member = self.calculate_order_total(items)
        with_member = self.calculate_order_total(items, member=member)
        return without_member["total"] - with_member["total"]
