# from complex_functions import calculate_shipping_cost
import pytest

from data.raw.simple.simple2 import calculate_shipping_cost


class TestCalculateShippingCost:
    """Test cases for calculate_shipping_cost function"""

    def test_normal_shipping_standard_service(self):
        """Test normal shipping with standard service for different destinations"""
        # Test various destinations with normal weights
        assert calculate_shipping_cost(5.0, "US") == 5.0
        assert calculate_shipping_cost(5.0, "UK") == 7.5
        assert calculate_shipping_cost(5.0, "China") == 6.0
        assert calculate_shipping_cost(5.0, "Japan") == 7.0
        assert calculate_shipping_cost(5.0, "Australia") == 8.0

    def test_normal_shipping_express_service(self):
        """Test normal shipping with express service"""
        # Express service should double the base rate
        assert calculate_shipping_cost(5.0, "US", True) == 10.0  # 5.0 * 2
        assert calculate_shipping_cost(5.0, "UK", True) == 15.0  # 7.5 * 2

    def test_heavy_package_surcharge(self):
        """Test packages over 10kg incur weight surcharge"""
        # Packages over 10kg should have additional surcharge of 2.5 per kg over 10
        assert calculate_shipping_cost(11.0, "US") == 7.5  # 5.0 + (11-10)*2.5
        assert calculate_shipping_cost(15.0, "China") == 18.5  # 6.0 + (15-10)*2.5
        assert (
            calculate_shipping_cost(20.0, "UK", True) == 45.0
        )  # (7.5 + (20-10)*2.5) * 2

    def test_edge_case_weight_boundaries(self):
        """Test weight boundaries (exactly 10kg and just above/below)"""
        # Exactly 10kg - no surcharge
        assert calculate_shipping_cost(10.0, "US") == 5.0
        assert calculate_shipping_cost(10.0, "Japan", True) == 14.0  # 7.0 * 2

        # Just above 10kg
        assert calculate_shipping_cost(10.1, "US") == 5.25  # 5.0 + 0.1*2.5
        assert calculate_shipping_cost(10.5, "China") == 7.25  # 6.0 + 0.5*2.5

        # Just below 10kg
        assert calculate_shipping_cost(9.9, "UK") == 7.5
        assert calculate_shipping_cost(9.5, "Australia") == 8.0

    def test_unknown_destination_default_rate(self):
        """Test shipping to unknown destinations uses default rate"""
        # Unknown destinations should use default rate of 10.0
        assert calculate_shipping_cost(5.0, "Canada") == 10.0
        assert calculate_shipping_cost(5.0, "Germany") == 10.0
        assert calculate_shipping_cost(12.0, "France") == 15.0  # 10.0 + (12-10)*2.5
        assert calculate_shipping_cost(8.0, "Brazil", True) == 20.0  # 10.0 * 2

    def test_zero_weight_raises_error(self):
        """Test that zero weight raises ValueError"""
        with pytest.raises(ValueError, match="Weight must be positive."):
            calculate_shipping_cost(0.0, "US")

    def test_negative_weight_raises_error(self):
        """Test that negative weight raises ValueError"""
        with pytest.raises(ValueError, match="Weight must be positive."):
            calculate_shipping_cost(-5.0, "UK")

    def test_very_small_weight(self):
        """Test with very small positive weights"""
        assert calculate_shipping_cost(0.1, "US") == 5.0
        assert calculate_shipping_cost(0.001, "China") == 6.0
        assert calculate_shipping_cost(0.5, "Japan", True) == 14.0

    def test_very_large_weight(self):
        """Test with very large weights"""
        assert calculate_shipping_cost(100.0, "US") == 230.0  # 5.0 + (100-10)*2.5
        assert (
            calculate_shipping_cost(50.0, "UK", True) == 207.5
        )  # (7.5 + (50-10)*2.5) * 2

    def test_rounding_behavior(self):
        """Test that results are properly rounded to 2 decimal places"""
        # Test cases that would require rounding
        assert (
            calculate_shipping_cost(11.333, "US") == 8.33
        )  # 5.0 + 1.333*2.5 = 8.3325 → 8.33
        assert (
            calculate_shipping_cost(12.777, "China", True) == 19.44
        )  # (6.0 + 2.777*2.5)*2 = 19.4425 → 19.44

    def test_case_sensitivity_destination(self):
        """Test destination case sensitivity"""
        # Assuming the function is case-sensitive for destination
        assert (
            calculate_shipping_cost(5.0, "us") == 10.0
        )  # lowercase should use default rate
        assert (
            calculate_shipping_cost(5.0, "Us") == 10.0
        )  # mixed case should use default rate
        assert calculate_shipping_cost(5.0, "US") == 5.0  # uppercase should work

    def test_express_false_explicit(self):
        """Test explicit False for is_express parameter"""
        assert calculate_shipping_cost(5.0, "US", False) == 5.0
        assert calculate_shipping_cost(5.0, "UK", False) == 7.5

    def test_combination_edge_cases(self):
        """Test combination of edge cases"""
        # Unknown destination + heavy weight + express
        assert (
            calculate_shipping_cost(15.0, "UnknownCountry", True) == 35.0
        )  # (10.0 + 5*2.5) * 2

        # Known destination + heavy weight + standard
        assert calculate_shipping_cost(25.0, "Australia") == 45.5  # 8.0 + 15*2.5 = 45.5
