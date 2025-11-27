# from advanced_functions import create_resource, User
import pytest

from data.raw.simple.simple3 import create_resource


class TestCreateResource:
    """Test cases for the create_resource factory function."""

    def test_create_user_with_required_fields(self):
        """Test creating a user with only required fields."""
        # Arrange
        resource_type = "user"
        user_data = {"id": 1, "name": "John Doe", "email": "john@example.com"}

        # Act
        result = create_resource(resource_type, **user_data)

        # Assert
        assert isinstance(result, dict)
        assert result["id"] == 1
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["balance"] == 0.0  # Default value
        assert result["is_active"] is True  # Default value

    def test_create_user_with_all_fields(self):
        """Test creating a user with all fields provided."""
        # Arrange
        resource_type = "user"
        user_data = {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "balance": 100.50,
            "is_active": False,
        }

        # Act
        result = create_resource(resource_type, **user_data)

        # Assert
        assert result["id"] == 2
        assert result["name"] == "Jane Smith"
        assert result["email"] == "jane@example.com"
        assert result["balance"] == 100.50
        assert result["is_active"] is False

    def test_create_user_missing_required_field(self):
        """Test creating a user with missing required fields."""
        # Arrange
        resource_type = "user"
        user_data = {
            "id": 1,
            "name": "John Doe",
            # Missing email field
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            create_resource(resource_type, **user_data)

        assert "Missing required fields for 'user'" in str(exc_info.value)
        assert "email" in str(exc_info.value)

    def test_create_user_with_extra_fields(self):
        """Test creating a user with extra fields that should be ignored."""
        # Arrange
        resource_type = "user"
        user_data = {
            "id": 3,
            "name": "Bob Wilson",
            "email": "bob@example.com",
            "extra_field": "should_be_ignored",
            "another_extra": 123,
        }

        # Act
        result = create_resource(resource_type, **user_data)

        # Assert
        assert result["id"] == 3
        assert result["name"] == "Bob Wilson"
        assert result["email"] == "bob@example.com"
        assert "extra_field" not in result
        assert "another_extra" not in result

    def test_create_product_with_minimal_fields(self):
        """Test creating a product with minimal fields."""
        # Arrange
        resource_type = "product"
        product_data = {"id": 1, "name": "Laptop"}

        # Act
        result = create_resource(resource_type, **product_data)

        # Assert
        assert isinstance(result, dict)
        assert result["id"] == 1
        assert result["name"] == "Laptop"
        assert result["price"] == 0.0  # Default value
        assert result["category"] == "uncategorized"  # Default value

    def test_create_product_with_all_fields(self):
        """Test creating a product with all fields provided."""
        # Arrange
        resource_type = "product"
        product_data = {
            "id": 2,
            "name": "Smartphone",
            "price": 999.99,
            "category": "Electronics",
        }

        # Act
        result = create_resource(resource_type, **product_data)

        # Assert
        assert result["id"] == 2
        assert result["name"] == "Smartphone"
        assert result["price"] == 999.99
        assert result["category"] == "Electronics"

    def test_create_product_with_extra_fields(self):
        """Test creating a product with extra fields that should be ignored."""
        # Arrange
        resource_type = "product"
        product_data = {
            "id": 3,
            "name": "Tablet",
            "price": 499.99,
            "category": "Electronics",
            "description": "A great tablet",  # Extra field
            "weight": 0.5,  # Extra field
        }

        # Act
        result = create_resource(resource_type, **product_data)

        # Assert
        assert result["id"] == 3
        assert result["name"] == "Tablet"
        assert result["price"] == 499.99
        assert result["category"] == "Electronics"
        assert "description" not in result
        assert "weight" not in result

    def test_unknown_resource_type(self):
        """Test creating an unknown resource type."""
        # Arrange
        resource_type = "unknown_type"
        data = {"id": 1, "name": "Test"}

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            create_resource(resource_type, **data)

        assert "Unknown resource type: unknown_type" in str(exc_info.value)

    def test_empty_resource_type(self):
        """Test creating a resource with empty type."""
        # Arrange
        resource_type = ""
        data = {"id": 1, "name": "Test"}

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            create_resource(resource_type, **data)

        assert "Unknown resource type:" in str(exc_info.value)

    def test_none_resource_type(self):
        """Test creating a resource with None type."""
        # Arrange
        resource_type = None
        data = {"id": 1, "name": "Test"}

        # Act & Assert
        with pytest.raises(TypeError):
            create_resource(resource_type, **data)

    def test_user_with_none_values(self):
        """Test creating a user with None values for required fields."""
        # Arrange
        resource_type = "user"
        user_data = {"id": None, "name": None, "email": None}

        # Act
        result = create_resource(resource_type, **user_data)

        # Assert
        assert result["id"] is None
        assert result["name"] is None
        assert result["email"] is None

    def test_user_with_empty_strings(self):
        """Test creating a user with empty string values."""
        # Arrange
        resource_type = "user"
        user_data = {"id": 1, "name": "", "email": ""}

        # Act
        result = create_resource(resource_type, **user_data)

        # Assert
        assert result["id"] == 1
        assert result["name"] == ""
        assert result["email"] == ""

    def test_user_balance_edge_cases(self):
        """Test creating users with edge case balance values."""
        test_cases = [
            (0.0, 0.0),  # Zero balance
            (-100.0, -100.0),  # Negative balance
            (999999.99, 999999.99),  # Large positive balance
            (0.001, 0.001),  # Very small balance
        ]

        for balance_input, expected_balance in test_cases:
            with self.subTest(balance=balance_input):
                # Arrange
                resource_type = "user"
                user_data = {
                    "id": 1,
                    "name": "Test User",
                    "email": "test@example.com",
                    "balance": balance_input,
                }

                # Act
                result = create_resource(resource_type, **user_data)

                # Assert
                assert result["balance"] == expected_balance

    def test_product_price_edge_cases(self):
        """Test creating products with edge case price values."""
        test_cases = [
            (0.0, 0.0),  # Zero price
            (-50.0, -50.0),  # Negative price
            (1000000.0, 1000000.0),  # Large price
            (0.01, 0.01),  # Small price
        ]

        for price_input, expected_price in test_cases:
            with self.subTest(price=price_input):
                # Arrange
                resource_type = "product"
                product_data = {"id": 1, "name": "Test Product", "price": price_input}

                # Act
                result = create_resource(resource_type, **product_data)

                # Assert
                assert result["price"] == expected_price
