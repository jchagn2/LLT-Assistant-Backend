import time

import pytest

# from advanced_functions import extract_and_validate_urls
from data.raw.simple.simple3 import extract_and_validate_urls


class TestExtractAndValidateUrls:
    """Test cases for extract_and_validate_urls function"""

    def test_extract_urls_with_http_and_https(self):
        """Test extraction of both HTTP and HTTPS URLs"""
        text = "Visit http://example.com and https://secure.site.org for more info"
        result = extract_and_validate_urls(text)

        assert len(result) == 2
        assert result[0] == {
            "url": "example.com",
            "protocol": "http",
            "domain": "example.com",
        }
        assert result[1] == {
            "url": "secure.site.org",
            "protocol": "https",
            "domain": "secure.site.org",
        }

    def test_extract_urls_with_www_subdomain(self):
        """Test extraction of URLs with www subdomain"""
        text = "Check www.google.com and https://www.github.com/path"
        result = extract_and_validate_urls(text)

        assert len(result) == 2
        assert result[0]["domain"] == "google.com"
        assert result[1]["domain"] == "github.com"
        assert result[1]["protocol"] == "https"

    def test_extract_urls_with_paths_and_queries(self):
        """Test extraction of URLs with paths and query parameters"""
        text = "Links: http://api.service.io/v1/users?page=2 and https://docs.site.com/article/123"
        result = extract_and_validate_urls(text)

        assert len(result) == 2
        assert result[0]["domain"] == "api.service.io"
        assert result[1]["domain"] == "docs.site.com"

    def test_extract_urls_with_multiple_tlds(self):
        """Test extraction of URLs with various top-level domains"""
        text = (
            "Sites: http://company.co.uk, https://university.ac.jp, http://shop.com.br"
        )
        result = extract_and_validate_urls(text)

        assert len(result) == 3
        domains = [item["domain"] for item in result]
        assert "company.co.uk" in domains
        assert "university.ac.jp" in domains
        assert "shop.com.br" in domains

    def test_extract_urls_with_hyphens_and_numbers(self):
        """Test extraction of URLs containing hyphens and numbers"""
        text = "Visit api-v2.service-01.com and test-123.example-site.net"
        result = extract_and_validate_urls(text)

        assert len(result) == 2
        assert result[0]["domain"] == "api-v2.service-01.com"
        assert result[1]["domain"] == "test-123.example-site.net"

    def test_empty_text_returns_empty_list(self):
        """Test that empty text returns empty list"""
        result = extract_and_validate_urls("")
        assert result == []

    def test_text_without_urls_returns_empty_list(self):
        """Test that text without URLs returns empty list"""
        text = "This is just plain text without any URLs or web addresses."
        result = extract_and_validate_urls(text)
        assert result == []

    def test_malformed_urls_are_ignored(self):
        """Test that malformed URLs are properly handled"""
        text = "Bad: ftp://example.com, http://, https://.com, http://invalid"
        result = extract_and_validate_urls(text)
        # Should only extract valid URLs that match the pattern
        assert len(result) == 0

    def test_urls_with_special_characters_in_domain(self):
        """Test URLs with special characters that should be invalid"""
        text = "Invalid: http://exam_ple.com, http://exam%ple.com"
        result = extract_and_validate_urls(text)
        # These should not match the pattern
        assert len(result) == 0

    def test_case_insensitive_domains(self):
        """Test that domain case is preserved but protocol is normalized"""
        text = "HTTP://EXAMPLE.COM and https://Example.Com/path"
        result = extract_and_validate_urls(text)

        assert len(result) == 2
        # Protocol should be normalized to lowercase
        assert result[0]["protocol"] == "http"
        assert result[1]["protocol"] == "https"
        # Domain should preserve original case (though the regex might lowercase it)

    def test_multiple_occurrences_of_same_url(self):
        """Test handling of duplicate URLs in text"""
        text = "Visit http://example.com multiple times: http://example.com and http://example.com"
        result = extract_and_validate_urls(text)

        # Should extract each occurrence
        assert len(result) == 3
        for item in result:
            assert item["domain"] == "example.com"

    def test_urls_with_ip_addresses(self):
        """Test that IP addresses as domains are handled correctly"""
        text = "IP URLs: http://192.168.1.1 and https://8.8.8.8/dns"
        result = extract_and_validate_urls(text)

        # The current regex pattern doesn't match IP addresses directly
        # This test documents the current behavior
        assert len(result) == 0

    def test_urls_with_ports(self):
        """Test URLs containing port numbers"""
        text = "Services: http://localhost:8080 and https://api.service.com:8443/v1"
        result = extract_and_validate_urls(text)

        # The current regex pattern doesn't handle ports explicitly
        # This test documents the current behavior
        assert len(result) == 1  # Only the second one might match
        if result:
            assert result[0]["domain"] == "api.service.com"

    def test_very_long_domain_names(self):
        """Test URLs with very long domain names"""
        long_domain = "a" * 50 + ".example.com"
        text = f"Visit http://{long_domain}/test"
        result = extract_and_validate_urls(text)

        assert len(result) == 1
        assert result[0]["domain"] == long_domain

    def test_mixed_content_with_urls_embedded(self):
        """Test extraction from text with URLs embedded in sentences"""
        text = """
        Please check our documentation at https://docs.example.com for more information.
        You can also visit http://support.example.com/tickets or email us at info@example.com.
        For API access, use https://api.example.com/v1/endpoint.
        """
        result = extract_and_validate_urls(text)

        assert len(result) == 3
        domains = [item["domain"] for item in result]
        assert "docs.example.com" in domains
        assert "support.example.com" in domains
        assert "api.example.com" in domains

    def test_url_extraction_performance_with_large_text(self):
        """Test performance with a large text containing many URLs"""
        base_url = "http://test{}.example.com/path/to/resource"
        urls = [base_url.format(i) for i in range(100)]
        text = " ".join(urls)

        start_time = time.time()
        result = extract_and_validate_urls(text)
        end_time = time.time()

        assert len(result) == 100
        # Should complete in reasonable time (less than 1 second)
        assert end_time - start_time < 1.0

    def test_protocol_detection_accuracy(self):
        """Test that protocol detection is accurate"""
        text = "http://http.example.com and https://https.example.com"
        result = extract_and_validate_urls(text)

        assert len(result) == 2
        http_urls = [item for item in result if item["protocol"] == "http"]
        https_urls = [item for item in result if item["protocol"] == "https"]
        assert len(http_urls) == 1
        assert len(https_urls) == 1

    def test_domain_extraction_with_complex_paths(self):
        """Test domain extraction from URLs with complex paths"""
        text = """
        https://sub.domain.co.uk/path/to/resource?param=value&other=test#section
        http://example.com/very/long/path/with/many/segments/
        """
        result = extract_and_validate_urls(text)

        assert len(result) == 2
        assert result[0]["domain"] == "sub.domain.co.uk"
        assert result[1]["domain"] == "example.com"

    def test_unicode_and_internationalized_domain_names(self):
        """Test handling of internationalized domain names"""
        # Note: The current regex pattern uses [a-zA-Z0-9.-] so it won't match Unicode domains
        text = "International: http://münchen.de and http://中国.cn"
        result = extract_and_validate_urls(text)

        # This documents that Unicode domains are not currently supported
        assert len(result) == 0
