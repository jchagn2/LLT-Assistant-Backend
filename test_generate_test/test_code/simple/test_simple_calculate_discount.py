# from math_functions import calculate_discount
import pytest

from data.raw.simple.simple import calculate_discount


class TestCalculateDiscount:
    """Test cases for calculate_discount function"""

    def test_normal_discount(self):
        """Test typical discount scenarios"""
        # 10% discount
        assert calculate_discount(100.0, 10.0) == 90.0
        # 25% discount
        assert calculate_discount(200.0, 25.0) == 150.0
        # 50% discount
        assert calculate_discount(1000.0, 50.0) == 500.0

    def test_edge_case_discounts(self):
        """Test edge case discount percentages"""
        # 0% discount (no discount)
        assert calculate_discount(100.0, 0.0) == 100.0
        # 100% discount (free)
        assert calculate_discount(100.0, 100.0) == 0.0
        # Default parameter (0% discount)
        assert calculate_discount(100.0) == 100.0

    def test_boundary_discount_values(self):
        """Test discount values at and beyond boundaries"""
        # Negative discount (should be clamped to 0%)
        assert calculate_discount(100.0, -10.0) == 100.0
        assert calculate_discount(100.0, -1.0) == 100.0
        assert calculate_discount(100.0, -100.0) == 100.0

        # Discount above 100% (should be clamped to 100%)
        assert calculate_discount(100.0, 110.0) == 0.0
        assert calculate_discount(100.0, 150.0) == 0.0
        assert calculate_discount(100.0, 1000.0) == 0.0

    def test_decimal_prices_and_discounts(self):
        """Test with decimal prices and discount percentages"""
        # Decimal prices
        assert calculate_discount(99.99, 10.0) == pytest.approx(89.991)
        assert calculate_discount(49.95, 20.0) == pytest.approx(39.96)

        # Decimal discount percentages
        assert calculate_discount(100.0, 12.5) == 87.5
        assert calculate_discount(200.0, 33.33) == pytest.approx(133.34)

    def test_zero_and_negative_prices(self):
        """Test with zero and negative prices"""
        # Zero price
        assert calculate_discount(0.0, 50.0) == 0.0
        assert calculate_discount(0.0, 100.0) == 0.0
        assert calculate_discount(0.0, 0.0) == 0.0

        # Negative price (unusual but should work mathematically)
        assert calculate_discount(-100.0, 10.0) == -90.0
        assert calculate_discount(-50.0, 50.0) == -25.0
        assert calculate_discount(-100.0, 100.0) == 0.0

    def test_large_values(self):
        """Test with large price values"""
        # Large prices
        assert calculate_discount(1000000.0, 10.0) == 900000.0
        assert calculate_discount(999999.99, 1.0) == pytest.approx(989999.9901)

    def test_precision_calculation(self):
        """Test calculation precision"""
        # Ensure floating point precision is handled correctly
        result = calculate_discount(100.0, 33.333)
        expected = 100.0 * (1 - 33.333 / 100)
        assert result == pytest.approx(expected)

        # Test with exact fractions
        assert calculate_discount(300.0, 33.333) == pytest.approx(200.001)

    def test_discount_clamping_behavior(self):
        """Specifically test the clamping behavior for invalid discounts"""
        # Test that negative discounts are clamped to 0%
        assert calculate_discount(100.0, -0.1) == 100.0
        assert calculate_discount(100.0, -50.0) == 100.0

        # Test that discounts >100% are clamped to 100%
        assert calculate_discount(100.0, 100.1) == 0.0
        assert calculate_discount(100.0, 200.0) == 0.0

        # Test boundary values exactly at 0% and 100%
        assert calculate_discount(100.0, 0.0) == 100.0
        assert calculate_discount(100.0, 100.0) == 0.0
