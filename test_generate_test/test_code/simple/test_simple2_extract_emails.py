# from complex_functions import extract_emails
import pytest

from data.raw.simple.simple2 import extract_emails


class TestExtractEmails:
    """Test cases for extract_emails function"""

    def test_extract_multiple_valid_emails(self):
        """Test extracting multiple valid emails from text"""
        text = "Contact us at john.doe@example.com or jane_smith123@test.co.uk for more info."
        expected = ["john.doe@example.com", "jane_smith123@test.co.uk"]
        result = extract_emails(text)
        assert result == expected

    def test_extract_emails_with_mixed_case(self):
        """Test extracting emails with mixed case characters"""
        text = "Emails: Test.User@Example.COM, mixed_CASE@domain.org"
        expected = ["Test.User@Example.COM", "mixed_CASE@domain.org"]
        result = extract_emails(text)
        assert result == expected

    def test_extract_emails_with_special_chars(self):
        """Test extracting emails with special characters in local part"""
        text = "Contact support at user+tag@domain.com or user.name%test@example.org"
        expected = ["user+tag@domain.com", "user.name%test@example.org"]
        result = extract_emails(text)
        assert result == expected

    def test_extract_emails_with_numbers(self):
        """Test extracting emails containing numbers"""
        text = "Email addresses: user123@test.com, test456@example789.org"
        expected = ["user123@test.com", "test456@example789.org"]
        result = extract_emails(text)
        assert result == expected

    def test_no_emails_found(self):
        """Test when no emails are present in the text"""
        text = "This is just regular text without any email addresses."
        result = extract_emails(text)
        assert result == []

    def test_empty_string(self):
        """Test with empty string input"""
        text = ""
        result = extract_emails(text)
        assert result == []

    def test_emails_at_text_boundaries(self):
        """Test emails appearing at the beginning and end of text"""
        text = "first@example.com some text in between last@test.org"
        expected = ["first@example.com", "last@test.org"]
        result = extract_emails(text)
        assert result == expected

    def test_emails_with_multiple_dots_in_domain(self):
        """Test emails with multiple dots in domain part"""
        text = "Email: user@sub.domain.co.uk should be valid"
        expected = ["user@sub.domain.co.uk"]
        result = extract_emails(text)
        assert result == expected

    def test_emails_separated_by_punctuation(self):
        """Test emails separated by various punctuation marks"""
        text = "Emails: one@test.com, two@example.org; three@domain.net!"
        expected = ["one@test.com", "two@example.org", "three@domain.net"]
        result = extract_emails(text)
        assert result == expected

    def test_invalid_email_patterns_ignored(self):
        """Test that invalid email patterns are correctly ignored"""
        text = """
        Valid: valid@email.com
        Invalid: @missinglocal.com
        Invalid: missingdomain@
        Invalid: no@tld
        Invalid: spaces in@email.com
        Valid: another.valid@test.org
        """
        expected = ["valid@email.com", "another.valid@test.org"]
        result = extract_emails(text)
        assert result == expected

    def test_emails_in_parentheses(self):
        """Test emails enclosed in parentheses"""
        text = "Contact (support@company.com) or (sales@example.org)"
        expected = ["support@company.com", "sales@example.org"]
        result = extract_emails(text)
        assert result == expected

    def test_emails_with_quotes(self):
        """Test emails surrounded by quotes"""
        text = "Email: \"user@test.com\" or 'another@example.org'"
        expected = ["user@test.com", "another@example.org"]
        result = extract_emails(text)
        assert result == expected

    def test_emails_in_html_like_text(self):
        """Test emails in HTML-like text content"""
        text = '<a href="mailto:contact@website.com">Email us</a> or info@site.org'
        expected = ["contact@website.com", "info@site.org"]
        result = extract_emails(text)
        assert result == expected

    def test_emails_with_underscores(self):
        """Test emails with underscores in local part"""
        text = "Addresses: first_last@domain.com and user_name@test.org"
        expected = ["first_last@domain.com", "user_name@test.org"]
        result = extract_emails(text)
        assert result == expected

    def test_emails_with_hyphens(self):
        """Test emails with hyphens in domain part"""
        text = "Email: user@sub-domain.com and test@my-domain.org"
        expected = ["user@sub-domain.com", "test@my-domain.org"]
        result = extract_emails(text)
        assert result == expected

    def test_duplicate_emails(self):
        """Test that duplicate emails are returned as duplicates"""
        text = "Email: test@example.com appears twice: test@example.com"
        expected = ["test@example.com", "test@example.com"]
        result = extract_emails(text)
        assert result == expected

    def test_emails_with_numeric_domains(self):
        """Test emails with numeric domains (valid per RFC)"""
        text = "Email: user@123.com should be valid"
        expected = ["user@123.com"]
        result = extract_emails(text)
        assert result == expected

    def test_very_long_email(self):
        """Test extraction of very long but valid email addresses"""
        text = (
            "Long email: very.long.email.address.with.many.parts@sub.domain.example.com"
        )
        expected = ["very.long.email.address.with.many.parts@sub.domain.example.com"]
        result = extract_emails(text)
        assert result == expected

    def test_emails_with_unicode_chars_ignored(self):
        """Test that emails with non-ASCII characters are ignored (pattern is ASCII-only)"""
        text = "English: test@example.com, Unicode: 用户@例子.中国 (should be ignored)"
        expected = ["test@example.com"]
        result = extract_emails(text)
        assert result == expected

    def test_whitespace_around_emails(self):
        """Test emails surrounded by various whitespace characters"""
        text = (
            "Email:\ttab@test.com\nNewline: user@example.org\rReturn: test@domain.net"
        )
        expected = ["tab@test.com", "user@example.org", "test@domain.net"]
        result = extract_emails(text)
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
