"""Utility functions for price calculations.

This module provides basic utility functions that are called by the service layer.
Used as part of the minimal test project for Neo4j graph validation.
"""


def calculate_tax(price: float, rate: float = 0.1) -> float:
    """Calculate tax amount for a given price.

    Args:
        price: The base price
        rate: Tax rate (default 10%)

    Returns:
        The calculated tax amount
    """
    return price * rate


def format_price(price: float, currency: str = "$") -> str:
    """Format a price value as a currency string.

    Args:
        price: The price value
        currency: Currency symbol (default $)

    Returns:
        Formatted price string
    """
    return f"{currency}{price:.2f}"
