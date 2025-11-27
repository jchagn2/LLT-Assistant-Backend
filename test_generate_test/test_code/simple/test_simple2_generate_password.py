# from complex_functions import generate_password
import random
import string
from unittest.mock import patch

import pytest

from data.raw.simple.simple2 import generate_password


class TestGeneratePassword:
    """Test cases for the generate_password function"""

    def test_generate_password_default_length(self):
        """Test generating password with default length"""
        password = generate_password()

        # Should generate 12 character password by default
        assert len(password) == 12
        # Should contain at least one of each required character type
        assert any(c in string.ascii_uppercase for c in password)
        assert any(c in string.ascii_lowercase for c in password)
        assert any(c in string.digits for c in password)
        assert any(c in string.punctuation for c in password)

    def test_generate_password_custom_length(self):
        """Test generating password with custom valid length"""
        for length in [8, 10, 15, 20]:
            password = generate_password(length)
            assert len(password) == length
            # Verify all required character types are present
            assert any(c in string.ascii_uppercase for c in password)
            assert any(c in string.ascii_lowercase for c in password)
            assert any(c in string.digits for c in password)
            assert any(c in string.punctuation for c in password)

    def test_generate_password_minimum_length(self):
        """Test generating password with minimum allowed length"""
        password = generate_password(8)
        assert len(password) == 8
        # Even at minimum length, should contain all character types
        assert any(c in string.ascii_uppercase for c in password)
        assert any(c in string.ascii_lowercase for c in password)
        assert any(c in string.digits for c in password)
        assert any(c in string.punctuation for c in password)

    def test_generate_password_length_too_short(self):
        """Test that length less than 8 raises ValueError"""
        with pytest.raises(
            ValueError, match="Password length must be at least 8 characters"
        ):
            generate_password(7)

        with pytest.raises(
            ValueError, match="Password length must be at least 8 characters"
        ):
            generate_password(0)

        with pytest.raises(
            ValueError, match="Password length must be at least 8 characters"
        ):
            generate_password(-5)

    def test_generate_password_character_distribution(self):
        """Test that password contains characters from all required sets"""
        # Test multiple generations to ensure robustness
        for _ in range(10):
            password = generate_password(12)

            # Check for presence of each character type
            has_upper = any(c in string.ascii_uppercase for c in password)
            has_lower = any(c in string.ascii_lowercase for c in password)
            has_digit = any(c in string.digits for c in password)
            has_punct = any(c in string.punctuation for c in password)

            assert has_upper, f"Missing uppercase in: {password}"
            assert has_lower, f"Missing lowercase in: {password}"
            assert has_digit, f"Missing digit in: {password}"
            assert has_punct, f"Missing punctuation in: {password}"

    def test_generate_password_randomness(self):
        """Test that generated passwords are different (random)"""
        passwords = [generate_password(12) for _ in range(5)]

        # All passwords should be different (very low probability of collision)
        assert len(set(passwords)) == len(
            passwords
        ), "Generated passwords should be random"

        # Each password should be unique
        for i, pass1 in enumerate(passwords):
            for j, pass2 in enumerate(passwords):
                if i != j:
                    assert pass1 != pass2, f"Passwords {i} and {j} should be different"

    def test_generate_password_valid_characters(self):
        """Test that password only contains allowed characters"""
        password = generate_password(15)
        allowed_chars = string.ascii_letters + string.digits + string.punctuation

        for char in password:
            assert char in allowed_chars, f"Invalid character '{char}' in password"

    @patch("complex_functions.random.shuffle")
    @patch("complex_functions.random.choice")
    def test_generate_password_internal_logic(self, mock_choice, mock_shuffle):
        """Test the internal logic of password generation"""
        # Mock random.choice to return predictable values
        mock_choice.side_effect = ["A", "a", "1", "!"] + ["x"] * 8  # 4 fixed + 8 filler

        password = generate_password(12)

        # Verify shuffle was called (password should be shuffled)
        mock_shuffle.assert_called_once()

        # Verify random.choice was called the correct number of times
        assert mock_choice.call_count == 12

    def test_generate_password_edge_case_lengths(self):
        """Test edge case lengths"""
        # Test exactly 8 characters
        password_8 = generate_password(8)
        assert len(password_8) == 8

        # Test a longer password
        password_20 = generate_password(20)
        assert len(password_20) == 20

        # Verify all character types are present even in longer passwords
        assert any(c in string.ascii_uppercase for c in password_20)
        assert any(c in string.ascii_lowercase for c in password_20)
        assert any(c in string.digits for c in password_20)
        assert any(c in string.punctuation for c in password_20)

    def test_generate_password_stress_test(self):
        """Test generating multiple passwords to ensure consistency"""
        for length in [8, 12, 16, 24]:
            for _ in range(3):  # Generate multiple passwords for each length
                password = generate_password(length)
                assert len(password) == length

                # Basic character type validation
                assert any(c.isupper() for c in password)
                assert any(c.islower() for c in password)
                assert any(c.isdigit() for c in password)
                assert any(c in string.punctuation for c in password)
