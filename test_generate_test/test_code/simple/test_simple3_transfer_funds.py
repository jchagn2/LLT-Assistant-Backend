# from advanced_functions import transfer_funds, InsufficientFundsError, DataProcessingError, User
from datetime import datetime

import pytest

from data.raw.simple.simple3 import (
    DataProcessingError,
    InsufficientFundsError,
    User,
    transfer_funds,
)


class TestTransferFunds:
    """Test cases for the transfer_funds function"""

    def test_successful_transfer(self):
        """Test successful fund transfer between active users with sufficient balance"""
        # Setup
        from_user: User = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "balance": 1000.0,
            "is_active": True,
        }
        to_user: User = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "balance": 500.0,
            "is_active": True,
        }
        amount = 200.0

        # Execute
        result = transfer_funds(from_user, to_user, amount)

        # Assert
        assert result["success"] is True
        assert result["from_user_id"] == 1
        assert result["to_user_id"] == 2
        assert result["amount"] == 200.0
        assert "timestamp" in result
        assert isinstance(datetime.fromisoformat(result["timestamp"]), datetime)

        # Verify balances were updated correctly
        assert from_user["balance"] == 800.0
        assert to_user["balance"] == 700.0

    def test_transfer_exact_balance(self):
        """Test transfer when amount equals sender's exact balance"""
        from_user: User = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "balance": 500.0,
            "is_active": True,
        }
        to_user: User = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "balance": 100.0,
            "is_active": True,
        }
        amount = 500.0

        result = transfer_funds(from_user, to_user, amount)

        assert result["success"] is True
        assert from_user["balance"] == 0.0
        assert to_user["balance"] == 600.0

    def test_insufficient_funds(self):
        """Test transfer when sender has insufficient funds"""
        from_user: User = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "balance": 100.0,
            "is_active": True,
        }
        to_user: User = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "balance": 500.0,
            "is_active": True,
        }
        amount = 200.0

        with pytest.raises(InsufficientFundsError) as exc_info:
            transfer_funds(from_user, to_user, amount)

        assert "insufficient funds" in str(exc_info.value).lower()
        assert from_user["balance"] == 100.0  # Balance should remain unchanged
        assert to_user["balance"] == 500.0

    def test_zero_amount(self):
        """Test transfer with zero amount (invalid)"""
        from_user: User = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "balance": 1000.0,
            "is_active": True,
        }
        to_user: User = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "balance": 500.0,
            "is_active": True,
        }
        amount = 0.0

        with pytest.raises(ValueError) as exc_info:
            transfer_funds(from_user, to_user, amount)

        assert "positive" in str(exc_info.value).lower()

    def test_negative_amount(self):
        """Test transfer with negative amount (invalid)"""
        from_user: User = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "balance": 1000.0,
            "is_active": True,
        }
        to_user: User = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "balance": 500.0,
            "is_active": True,
        }
        amount = -100.0

        with pytest.raises(ValueError) as exc_info:
            transfer_funds(from_user, to_user, amount)

        assert "positive" in str(exc_info.value).lower()

    def test_sender_inactive(self):
        """Test transfer when sender is inactive"""
        from_user: User = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "balance": 1000.0,
            "is_active": False,
        }
        to_user: User = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "balance": 500.0,
            "is_active": True,
        }
        amount = 200.0

        with pytest.raises(ValueError) as exc_info:
            transfer_funds(from_user, to_user, amount)

        assert "active" in str(exc_info.value).lower()

    def test_receiver_inactive(self):
        """Test transfer when receiver is inactive"""
        from_user: User = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "balance": 1000.0,
            "is_active": True,
        }
        to_user: User = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "balance": 500.0,
            "is_active": False,
        }
        amount = 200.0

        with pytest.raises(ValueError) as exc_info:
            transfer_funds(from_user, to_user, amount)

        assert "active" in str(exc_info.value).lower()

    def test_both_users_inactive(self):
        """Test transfer when both users are inactive"""
        from_user: User = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "balance": 1000.0,
            "is_active": False,
        }
        to_user: User = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "balance": 500.0,
            "is_active": False,
        }
        amount = 200.0

        with pytest.raises(ValueError) as exc_info:
            transfer_funds(from_user, to_user, amount)

        assert "active" in str(exc_info.value).lower()

    def test_small_amount_transfer(self):
        """Test transfer with very small amount (edge case)"""
        from_user: User = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "balance": 1000.0,
            "is_active": True,
        }
        to_user: User = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "balance": 500.0,
            "is_active": True,
        }
        amount = 0.01

        result = transfer_funds(from_user, to_user, amount)

        assert result["success"] is True
        assert (
            abs(from_user["balance"] - 999.99) < 0.001
        )  # Handle floating point precision
        assert abs(to_user["balance"] - 500.01) < 0.001

    def test_large_amount_transfer(self):
        """Test transfer with large amount"""
        from_user: User = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "balance": 1000000.0,
            "is_active": True,
        }
        to_user: User = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "balance": 500.0,
            "is_active": True,
        }
        amount = 999999.99

        result = transfer_funds(from_user, to_user, amount)

        assert result["success"] is True
        assert abs(from_user["balance"] - 0.01) < 0.001
        assert abs(to_user["balance"] - 1000499.99) < 0.001

    # def test_user_missing_is_active_field(self):
    #     """Test transfer when user dict is missing is_active field"""
    #     from_user: User = {
    #         "id": 1,
    #         "name": "Alice",
    #         "email": "alice@example.com
