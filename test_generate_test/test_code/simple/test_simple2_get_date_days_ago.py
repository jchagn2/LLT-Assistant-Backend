# from complex_functions import get_date_days_ago
from datetime import datetime, timedelta

import pytest

from data.raw.simple.simple2 import get_date_days_ago


class TestGetDateDaysAgo:
    """Test cases for get_date_days_ago function"""

    def test_with_custom_date_valid_format(self):
        """Test with custom date string and valid format"""
        result = get_date_days_ago(5, "2023-10-27", "%Y-%m-%d")
        expected = "2023-10-22"
        assert result == expected

    def test_with_custom_date_different_format(self):
        """Test with custom date string using different format"""
        result = get_date_days_ago(10, "27/10/2023", "%d/%m/%Y")
        expected = "17/10/2023"
        assert result == expected

    def test_without_custom_date(self):
        """Test without custom date (should use current date)"""
        # Since we can't predict the exact current date, we'll test the logic
        # by verifying the difference is correct
        result = get_date_days_ago(7)
        result_date = datetime.strptime(result, "%Y-%m-%d")
        expected_date = datetime.now() - timedelta(days=7)

        # The dates should be the same day (ignore time component)
        assert result_date.date() == expected_date.date()

    def test_zero_days(self):
        """Test with zero days difference"""
        result = get_date_days_ago(0, "2023-10-27")
        assert result == "2023-10-27"

    def test_negative_days(self):
        """Test with negative days (future date)"""
        result = get_date_days_ago(-5, "2023-10-27")
        expected = "2023-11-01"  # 5 days after Oct 27
        assert result == expected

    def test_large_number_of_days(self):
        """Test with large number of days"""
        result = get_date_days_ago(365, "2023-10-27")
        expected = "2022-10-27"  # Exactly one year before
        assert result == expected

    def test_cross_month_boundary(self):
        """Test when calculation crosses month boundary"""
        result = get_date_days_ago(15, "2023-10-15")
        expected = "2023-09-30"  # Cross from October to September
        assert result == expected

    def test_cross_year_boundary(self):
        """Test when calculation crosses year boundary"""
        result = get_date_days_ago(10, "2023-01-05")
        expected = "2022-12-26"  # Cross from 2023 to 2022
        assert result == expected

    def test_leap_year_february(self):
        """Test with leap year February dates"""
        result = get_date_days_ago(1, "2020-03-01")  # Leap year
        expected = "2020-02-29"  # Should land on Feb 29th
        assert result == expected

    def test_invalid_date_string_format(self):
        """Test with invalid date string that doesn't match format"""
        with pytest.raises(
            ValueError, match="Invalid date string 'invalid-date' for format '%Y-%m-%d'"
        ):
            get_date_days_ago(5, "invalid-date", "%Y-%m-%d")

    def test_invalid_date_format_mismatch(self):
        """Test when date string doesn't match the specified format"""
        with pytest.raises(ValueError):
            get_date_days_ago(5, "2023/10/27", "%Y-%m-%d")  # Wrong separator

    def test_empty_date_string(self):
        """Test with empty date string"""
        with pytest.raises(ValueError):
            get_date_days_ago(5, "", "%Y-%m-%d")

    def test_none_date_string(self):
        """Test with None as date string (should use current date)"""
        result = get_date_days_ago(3, None)
        result_date = datetime.strptime(result, "%Y-%m-%d")
        expected_date = datetime.now() - timedelta(days=3)
        assert result_date.date() == expected_date.date()

    def test_custom_date_format_with_time(self):
        """Test with custom date format that includes time"""
        result = get_date_days_ago(2, "2023-10-27 14:30:00", "%Y-%m-%d %H:%M:%S")
        expected = "2023-10-25 14:30:00"  # Time should be preserved
        assert result == expected

    def test_edge_case_last_day_of_year(self):
        """Test edge case: last day of the year"""
        result = get_date_days_ago(1, "2023-12-31")
        expected = "2023-12-30"
        assert result == expected

    def test_edge_case_first_day_of_year(self):
        """Test edge case: first day of the year"""
        result = get_date_days_ago(1, "2023-01-01")
        expected = "2022-12-31"  # Cross year boundary
        assert result == expected

    def test_very_large_days_value(self):
        """Test with very large number of days"""
        result = get_date_days_ago(10000, "2023-10-27")
        # Just verify it returns a valid date string without error
        datetime.strptime(result, "%Y-%m-%d")  # Should not raise ValueError

    def test_different_locale_formats(self):
        """Test with various international date formats"""
        # US format
        result1 = get_date_days_ago(5, "10/27/2023", "%m/%d/%Y")
        assert result1 == "10/22/2023"

        # European format
        result2 = get_date_days_ago(5, "27.10.2023", "%d.%m.%Y")
        assert result2 == "22.10.2023"

        # ISO format
        result3 = get_date_days_ago(5, "20231027", "%Y%m%d")
        assert result3 == "20231022"
