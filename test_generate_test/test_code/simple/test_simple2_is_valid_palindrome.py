# from complex_functions import is_valid_palindrome
import pytest

from data.raw.simple.simple2 import is_valid_palindrome


class TestIsValidPalindrome:
    """测试 is_valid_palindrome 函数"""

    def test_typical_palindromes(self):
        """测试典型的回文字符串"""
        # 标准回文
        assert is_valid_palindrome("A man, a plan, a canal: Panama") == True
        assert is_valid_palindrome("race a car") == False

        # 数字回文
        assert is_valid_palindrome("12321") == True
        assert is_valid_palindrome("12345") == False

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        assert is_valid_palindrome("Aba") == True
        assert is_valid_palindrome("AbBa") == True
        assert is_valid_palindrome("AbcBa") == True
        assert is_valid_palindrome("AbcDa") == False

    def test_with_special_characters(self):
        """测试包含特殊字符的情况"""
        # 包含标点符号和空格
        assert is_valid_palindrome("A man, a plan, a canal: Panama") == True
        assert is_valid_palindrome("Was it a car or a cat I saw?") == True
        assert is_valid_palindrome("No 'x' in Nixon") == True

        # 包含各种特殊字符
        assert is_valid_palindrome("a!#$%b@&*()b a") == True  # 清理后为 "abba"
        assert is_valid_palindrome("a!b@c#d$e") == False  # 清理后为 "abcde"

    def test_alphanumeric_mixed(self):
        """测试字母数字混合"""
        assert is_valid_palindrome("a1b2b1a") == True
        assert is_valid_palindrome("1a2b3c3b2a1") == True
        assert is_valid_palindrome("1a2b3c4d5e") == False

    def test_edge_cases(self):
        """测试边界情况"""
        # 空字符串
        assert is_valid_palindrome("") == True  # 空字符串是回文

        # 单个字符
        assert is_valid_palindrome("a") == True
        assert is_valid_palindrome("1") == True
        assert is_valid_palindrome("!") == True  # 清理后为空字符串

        # 只有特殊字符
        assert is_valid_palindrome("!@#$%") == True  # 清理后为空字符串
        assert is_valid_palindrome("  ") == True  # 只有空格

    def test_unicode_and_international(self):
        """测试Unicode和国际字符"""
        # 注意：函数只处理ASCII字母数字，非ASCII字符会被过滤掉
        assert (
            is_valid_palindrome("café é fac") == True
        )  # 重音字符被过滤，清理后为 "caffac"
        assert (
            is_valid_palindrome("中文文中文") == True
        )  # 中文字符被过滤，清理后为空字符串

    def test_long_strings(self):
        """测试长字符串"""
        # 长回文
        long_palindrome = "a" * 1000 + "b" + "a" * 1000
        assert is_valid_palindrome(long_palindrome) == True

        # 长非回文（中间不同）
        long_non_palindrome = "a" * 1000 + "b" + "c" + "a" * 1000
        assert is_valid_palindrome(long_non_palindrome) == False

    def test_numbers_only(self):
        """测试纯数字字符串"""
        assert is_valid_palindrome("12321") == True
        assert is_valid_palindrome("12345") == False
        assert is_valid_palindrome("1") == True
        assert is_valid_palindrome("11") == True
        assert is_valid_palindrome("12") == False

    def test_whitespace_handling(self):
        """测试空格处理"""
        assert is_valid_palindrome("  a  b  a  ") == True  # 清理后为 "aba"
        assert is_valid_palindrome("a b c b a") == True  # 清理后为 "abcba"
        assert is_valid_palindrome("a b c d e") == False  # 清理后为 "abcde"

    def test_mixed_case_alphanumeric(self):
        """测试混合大小写字母数字"""
        assert is_valid_palindrome("A1b2B1a") == True  # 清理后为 "a1b2b1a"
        assert is_valid_palindrome("M4d4m") == True  # 清理后为 "m4d4m"
        assert is_valid_palindrome("H3ll0 W0rld") == False  # 清理后为 "h3ll0w0rld"

    def test_palindrome_with_only_special_chars(self):
        """测试只有特殊字符的情况"""
        # 这些在清理后都变成空字符串，空字符串是回文
        assert is_valid_palindrome("!@#$%") == True
        assert is_valid_palindrome("   ") == True
        assert is_valid_palindrome("\n\t\r") == True

    def test_known_palindromes(self):
        """测试一些著名的回文"""
        assert is_valid_palindrome("Able was I ere I saw Elba") == True
        assert is_valid_palindrome("Madam, I'm Adam") == True
        assert is_valid_palindrome("Never odd or even") == True
        assert is_valid_palindrome("This is not a palindrome") == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
