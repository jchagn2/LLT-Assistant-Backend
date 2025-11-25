# from complex_functions import calculate_user_balance
import pytest

from data.raw.simple.simple2 import calculate_user_balance


class TestCalculateUserBalance:
    """Test cases for calculate_user_balance function"""

    def test_normal_case_with_positive_transactions(self):
        """Test normal case with positive transactions"""
        users = [
            {
                "id": 1,
                "transactions": [
                    {"amount": 100.0},
                    {"amount": 50.5},
                    {"amount": 25.25},
                ],
            },
            {"id": 2, "transactions": [{"amount": 200.0}, {"amount": 75.75}]},
        ]
        result = calculate_user_balance(users, 1)
        assert result == 175.75  # 100 + 50.5 + 25.25 = 175.75

    def test_normal_case_with_mixed_transactions(self):
        """Test normal case with mixed positive and negative transactions"""
        users = [
            {
                "id": 1,
                "transactions": [
                    {"amount": 100.0},
                    {"amount": -50.0},
                    {"amount": 25.5},
                    {"amount": -10.25},
                ],
            }
        ]
        result = calculate_user_balance(users, 1)
        assert result == 65.25  # 100 - 50 + 25.5 - 10.25 = 65.25

    def test_user_not_found(self):
        """Test when user ID doesn't exist"""
        users = [
            {"id": 1, "transactions": [{"amount": 100.0}]},
            {"id": 2, "transactions": [{"amount": 200.0}]},
        ]
        result = calculate_user_balance(users, 999)
        assert result == -1.0

    def test_empty_transactions_list(self):
        """Test user with empty transactions list"""
        users = [{"id": 1, "transactions": []}]
        result = calculate_user_balance(users, 1)
        assert result == 0.0

    def test_missing_transactions_key(self):
        """Test user without transactions key"""
        users = [
            {
                "id": 1
                # Missing 'transactions' key
            }
        ]
        result = calculate_user_balance(users, 1)
        assert result == 0.0

    def test_transactions_with_missing_amount_key(self):
        """Test transactions with missing amount key"""
        users = [
            {
                "id": 1,
                "transactions": [
                    {"amount": 100.0},
                    {"description": "No amount key"},  # Missing amount
                    {"amount": 50.0},
                ],
            }
        ]
        result = calculate_user_balance(users, 1)
        assert result == 150.0  # 100 + 0 + 50 = 150

    def test_negative_balance(self):
        """Test case resulting in negative balance"""
        users = [
            {
                "id": 1,
                "transactions": [
                    {"amount": 50.0},
                    {"amount": -100.0},
                    {"amount": -25.5},
                ],
            }
        ]
        result = calculate_user_balance(users, 1)
        assert result == -75.5  # 50 - 100 - 25.5 = -75.5

    def test_zero_balance(self):
        """Test case resulting in zero balance"""
        users = [
            {
                "id": 1,
                "transactions": [
                    {"amount": 100.0},
                    {"amount": -50.0},
                    {"amount": -50.0},
                ],
            }
        ]
        result = calculate_user_balance(users, 1)
        assert result == 0.0

    def test_large_number_of_transactions(self):
        """Test with large number of transactions"""
        users = [
            {
                "id": 1,
                "transactions": [
                    {"amount": 0.01} for _ in range(1000)
                ],  # 1000 transactions of 0.01
            }
        ]
        result = calculate_user_balance(users, 1)
        assert result == 10.0  # 1000 * 0.01 = 10.0

    def test_rounding_precision(self):
        """Test rounding to 2 decimal places"""
        users = [
            {
                "id": 1,
                "transactions": [
                    {"amount": 0.333},
                    {"amount": 0.333},
                    {"amount": 0.334},
                ],
            }
        ]
        result = calculate_user_balance(users, 1)
        assert result == 1.0  # 0.333 + 0.333 + 0.334 = 1.0 (rounded)

    def test_empty_users_list(self):
        """Test with empty users list"""
        users = []
        result = calculate_user_balance(users, 1)
        assert result == -1.0

    def test_duplicate_user_ids(self):
        """Test when multiple users have same ID (first match should be used)"""
        users = [
            {"id": 1, "transactions": [{"amount": 100.0}]},
            {"id": 1, "transactions": [{"amount": 200.0}]},  # Duplicate ID
        ]
        result = calculate_user_balance(users, 1)
        assert result == 100.0  # Should use first match

    def test_transactions_with_none_values(self):
        """Test transactions with None values"""
        users = [
            {
                "id": 1,
                "transactions": [
                    {"amount": 100.0},
                    {"amount": None},  # None value
                    {"amount": 50.0},
                ],
            }
        ]
        result = calculate_user_balance(users, 1)
        assert result == 150.0  # 100 + 0 + 50 = 150

    def test_user_with_no_id_key(self):
        """Test user missing id key"""
        users = [
            {"name": "John", "transactions": [{"amount": 100.0}]},  # Missing 'id' key
            {"id": 1, "transactions": [{"amount": 200.0}]},
        ]
        result = calculate_user_balance(users, 1)
        assert result == 200.0  # Should find user with id=1

    def test_very_large_amounts(self):
        """Test with very large transaction amounts"""
        users = [
            {
                "id": 1,
                "transactions": [
                    {"amount": 1000000.0},
                    {"amount": -500000.0},
                    {"amount": 250000.0},
                ],
            }
        ]
        result = calculate_user_balance(users, 1)
        assert result == 750000.0  # 1,000,000 - 500,000 + 250,000 = 750,000

    def test_mixed_data_types_in_transactions(self):
        """Test with mixed data types in transactions list"""
        users = [
            {
                "id": 1,
                "transactions": [
                    {"amount": 100},
                    {"amount": 50.5},
                    {"amount": "25"},  # String that can't be converted
                    {"amount": 75.25},
                ],
            }
        ]
        # This will cause TypeError when summing, but function should handle it
        result = calculate_user_balance(users, 1)
        # The exact behavior depends on how Python handles mixed types in sum
        # This test documents the current behavior
        assert isinstance(result, float)
