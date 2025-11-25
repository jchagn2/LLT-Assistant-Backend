# from math_functions import get_grade
import pytest

from data.raw.simple.simple import get_grade


class TestGetGrade:
    """Test cases for the get_grade function"""

    def test_grade_a_boundaries(self):
        """Test A grade boundaries (90-100)"""
        assert get_grade(90) == "A"
        assert get_grade(95) == "A"
        assert get_grade(100) == "A"

    def test_grade_b_boundaries(self):
        """Test B grade boundaries (80-89)"""
        assert get_grade(80) == "B"
        assert get_grade(85) == "B"
        assert get_grade(89) == "B"

    def test_grade_c_boundaries(self):
        """Test C grade boundaries (70-79)"""
        assert get_grade(70) == "C"
        assert get_grade(75) == "C"
        assert get_grade(79) == "C"

    def test_grade_d_boundaries(self):
        """Test D grade boundaries (60-69)"""
        assert get_grade(60) == "D"
        assert get_grade(65) == "D"
        assert get_grade(69) == "D"

    def test_grade_f_boundaries(self):
        """Test F grade boundaries (0-59)"""
        assert get_grade(0) == "F"
        assert get_grade(30) == "F"
        assert get_grade(59) == "F"

    def test_grade_transition_points(self):
        """Test exact transition points between grades"""
        assert get_grade(90) == "A"  # A starts at 90
        assert get_grade(89) == "B"  # B ends at 89
        assert get_grade(80) == "B"  # B starts at 80
        assert get_grade(79) == "C"  # C ends at 79
        assert get_grade(70) == "C"  # C starts at 70
        assert get_grade(69) == "D"  # D ends at 69
        assert get_grade(60) == "D"  # D starts at 60
        assert get_grade(59) == "F"  # F ends at 59

    def test_edge_cases_within_range(self):
        """Test edge cases within valid range"""
        assert get_grade(0) == "F"  # Minimum valid score
        assert get_grade(100) == "A"  # Maximum valid score
        assert get_grade(50) == "F"  # Middle of F range
        assert get_grade(95) == "A"  # Middle of A range

    def test_invalid_scores_negative(self):
        """Test that negative scores raise ValueError"""
        with pytest.raises(ValueError, match="Score must be between 0 and 100."):
            get_grade(-1)
        with pytest.raises(ValueError, match="Score must be between 0 and 100."):
            get_grade(-100)

    def test_invalid_scores_above_100(self):
        """Test that scores above 100 raise ValueError"""
        with pytest.raises(ValueError, match="Score must be between 0 and 100."):
            get_grade(101)
        with pytest.raises(ValueError, match="Score must be between 0 and 100."):
            get_grade(150)

    def test_boundary_values(self):
        """Test all boundary values"""
        # Valid boundaries
        assert get_grade(0) == "F"
        assert get_grade(100) == "A"

        # Grade boundaries
        assert get_grade(60) == "D"
        assert get_grade(70) == "C"
        assert get_grade(80) == "B"
        assert get_grade(90) == "A"

    def test_random_scores_in_each_grade_range(self):
        """Test random scores within each grade range"""
        # A grade samples
        assert get_grade(92) == "A"
        assert get_grade(98) == "A"

        # B grade samples
        assert get_grade(83) == "B"
        assert get_grade(87) == "B"

        # C grade samples
        assert get_grade(72) == "C"
        assert get_grade(78) == "C"

        # D grade samples
        assert get_grade(63) == "D"
        assert get_grade(68) == "D"

        # F grade samples
        assert get_grade(45) == "F"
        assert get_grade(20) == "F"
