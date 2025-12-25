"""Smoke tests for legacy billing module - verify basic functionality."""

import pytest
from app.legacy.billing import compute_invoice_total
from app.services.billing_service import BillingService
from app.api import handle_checkout_request, get_price_preview, validate_coupon


class TestComputeInvoiceTotal:
    """Basic tests for compute_invoice_total function."""
    
    def test_simple_order(self):
        """Test a simple order with one item."""
        order = {
            "items": [{"name": "Widget", "qty": 1, "price": 10.00, "type": "physical"}],
            "state": "TX"  # No tax
        }
        result = compute_invoice_total(order)
        
        assert result["currency"] == "USD"
        assert result["subtotal"] == 10.00
        assert result["discount"] == 0.0
        assert result["shipping"] == 5.99  # Under $50, so shipping applies
        assert result["tax"] == 0.0  # TX has no tax
        assert result["total"] == 15.99
    
    def test_multiple_items(self):
        """Test order with multiple items."""
        order = {
            "items": [
                {"name": "Widget", "qty": 2, "price": 15.00, "type": "physical"},
                {"name": "Gadget", "qty": 1, "price": 25.00, "type": "physical"}
            ],
            "state": "TX"
        }
        result = compute_invoice_total(order)
        
        assert result["subtotal"] == 55.00  # (2*15) + 25
        assert result["shipping"] == 0.0  # Free shipping over $50
    
    def test_save10_coupon(self):
        """Test SAVE10 coupon applies 10% discount."""
        order = {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "coupon": "SAVE10",
            "state": "TX"
        }
        result = compute_invoice_total(order)
        
        assert result["discount"] == 10.00  # 10% of 100
    
    def test_welcome5_coupon_over_20(self):
        """Test WELCOME5 coupon gives $5 off when subtotal > $20."""
        order = {
            "items": [{"name": "Widget", "qty": 1, "price": 30.00, "type": "physical"}],
            "coupon": "WELCOME5",
            "state": "TX"
        }
        result = compute_invoice_total(order)
        
        assert result["discount"] == 5.00
    
    def test_welcome5_coupon_under_20(self):
        """Test WELCOME5 coupon gives $0 off when subtotal <= $20."""
        order = {
            "items": [{"name": "Widget", "qty": 1, "price": 15.00, "type": "physical"}],
            "coupon": "WELCOME5",
            "state": "TX"
        }
        result = compute_invoice_total(order)
        
        assert result["discount"] == 0.0
    
    def test_half_coupon_with_cap(self):
        """Test HALF coupon is capped at $50."""
        order = {
            "items": [{"name": "Widget", "qty": 1, "price": 200.00, "type": "physical"}],
            "coupon": "HALF",
            "state": "TX"
        }
        result = compute_invoice_total(order)
        
        assert result["discount"] == 50.00  # Capped at $50, not $100
    
    def test_gold_member_discount(self):
        """Test gold member gets 2% additional discount."""
        order = {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "member": "gold",
            "state": "TX"
        }
        result = compute_invoice_total(order)
        
        assert result["discount"] == 2.00  # 2% of 100
    
    def test_platinum_member_discount(self):
        """Test platinum member gets 5% additional discount."""
        order = {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "member": "platinum",
            "state": "TX"
        }
        result = compute_invoice_total(order)
        
        assert result["discount"] == 5.00  # 5% of 100
    
    def test_california_tax(self):
        """Test CA tax rate of 8.25%."""
        order = {
            "items": [{"name": "Widget", "qty": 1, "price": 100.00, "type": "physical"}],
            "state": "CA"
        }
        result = compute_invoice_total(order)
        
        assert result["tax"] == 8.25  # 8.25% of 100
    
    def test_digital_only_no_shipping(self):
        """Test digital-only orders have no shipping."""
        order = {
            "items": [{"name": "eBook", "qty": 1, "price": 20.00, "type": "digital"}],
            "state": "TX"
        }
        result = compute_invoice_total(order)
        
        assert result["shipping"] == 0.0


class TestBillingService:
    """Tests for BillingService class."""
    
    def test_calculate_order_total(self):
        """Test service wrapper works correctly."""
        service = BillingService(default_state="TX")
        items = [{"name": "Widget", "qty": 1, "price": 10.00, "type": "physical"}]
        
        result = service.calculate_order_total(items)
        
        assert result["total"] == 15.99
    
    def test_get_shipping_estimate(self):
        """Test shipping estimate method."""
        service = BillingService()
        items = [{"name": "Widget", "qty": 1, "price": 10.00, "type": "physical"}]
        
        shipping = service.get_shipping_estimate(items)
        
        assert shipping == 5.99


class TestAPI:
    """Tests for API endpoint functions."""
    
    def test_handle_checkout_success(self):
        """Test successful checkout request."""
        request = {
            "items": [{"name": "Widget", "qty": 1, "price": 10.00, "type": "physical"}],
            "state": "TX"
        }
        
        response = handle_checkout_request(request)
        
        assert response["status"] == "success"
        assert "invoice" in response
    
    def test_get_price_preview(self):
        """Test price preview endpoint."""
        items = [{"name": "Widget", "qty": 1, "price": 10.00, "type": "physical"}]
        
        preview = get_price_preview(items, state="TX")
        
        assert "estimated_total" in preview
        assert "breakdown" in preview
