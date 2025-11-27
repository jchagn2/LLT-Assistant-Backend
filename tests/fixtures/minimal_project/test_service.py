"""Test suite for the service module.

This module provides test functions that call service functions.
Used as part of the minimal test project for Neo4j graph validation.
"""

from tests.fixtures.minimal_project.service import display_price, get_total_price


def test_get_total_price():
    """Test that get_total_price correctly calculates total with tax.

    Calls:
        - get_total_price (from service)
    """
    result = get_total_price(100.0)
    assert result == 110.0, "Expected 100 + 10% tax = 110"


def test_display_price():
    """Test that display_price formats the total correctly.

    Calls:
        - display_price (from service)
    """
    result = display_price(100.0)
    assert result == "$110.00", "Expected formatted price string"
