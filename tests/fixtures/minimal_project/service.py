"""Service layer for price operations.

This module provides service functions that call utility functions.
Used as part of the minimal test project for Neo4j graph validation.
"""

from tests.fixtures.minimal_project.utils import calculate_tax, format_price


def get_total_price(base_price: float, tax_rate: float = 0.1) -> float:
    """Calculate the total price including tax.

    Args:
        base_price: The base price before tax
        tax_rate: Tax rate (default 10%)

    Returns:
        Total price including tax

    Calls:
        - calculate_tax (from utils)
    """
    tax = calculate_tax(base_price, tax_rate)
    return base_price + tax


def display_price(base_price: float) -> str:
    """Display the total price in a formatted string.

    Args:
        base_price: The base price before tax

    Returns:
        Formatted string showing total price

    Calls:
        - get_total_price (internal)
        - format_price (from utils)
    """
    total = get_total_price(base_price)
    return format_price(total)
