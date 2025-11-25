import pytest

from data.raw.simple.simple3 import (
    expand_around_center,
    find_longest_palindromic_substring,
)

# from advanced_functions import expand_around_center, find_longest_palindromic_substring


class TestFindLongestPalindromicSubstring:
    """测试查找最长回文子串功能"""

    def test_empty_string(self):
        """测试空字符串输入"""
        result = find_longest_palindromic_substring("")
        assert result == ""

    def test_single_character(self):
        """测试单字符字符串"""
        result = find_longest_palindromic_substring("a")
        assert result == "a"

    def test_all_same_characters(self):
        """测试所有字符相同的情况"""
        result = find_longest_palindromic_substring("aaaa")
        assert result == "aaaa"

    def test_typical_odd_length_palindrome(self):
        """测试典型的奇数长度回文"""
        result = find_longest_palindromic_substring("babad")
        # 可能返回 "bab" 或 "aba"，都是有效的
        assert result in ["bab", "aba"]

    def test_typical_even_length_palindrome(self):
        """测试典型的偶数长度回文"""
        result = find_longest_palindromic_substring("cbbd")
        assert result == "bb"

    def test_multiple_palindromes_same_length(self):
        """测试存在多个相同长度的回文"""
        result = find_longest_palindromic_substring("abcbaabcba")
        # 应该返回第一个最长的回文
        assert result == "abcba"

    def test_no_palindrome(self):
        """测试没有回文的情况"""
        result = find_longest_palindromic_substring("abc")
        # 单个字符也被认为是回文
        assert len(result) == 1
        assert result in ["a", "b", "c"]

    def test_entire_string_is_palindrome(self):
        """测试整个字符串就是回文"""
        result = find_longest_palindromic_substring("racecar")
        assert result == "racecar"

    def test_palindrome_at_beginning(self):
        """测试回文在字符串开头"""
        result = find_longest_palindromic_substring("abacdfg")
        assert result == "aba"

    def test_palindrome_at_end(self):
        """测试回文在字符串末尾"""
        result = find_longest_palindromic_substring("fgdcaba")
        assert result == "aba"

    def test_palindrome_in_middle(self):
        """测试回文在字符串中间"""
        result = find_longest_palindromic_substring("fgabahijk")
        assert result == "aba"

    def test_long_complex_string(self):
        """测试长的复杂字符串"""
        result = find_longest_palindromic_substring("forgeeksskeegfor")
        assert result == "geeksskeeg"

    def test_string_with_numbers(self):
        """测试包含数字的字符串"""
        result = find_longest_palindromic_substring("12321abc")
        assert result == "12321"

    def test_string_with_special_characters(self):
        """测试包含特殊字符的字符串"""
        result = find_longest_palindromic_substring("a!b!a!c")
        assert result == "a!b!a"

    def test_unicode_characters(self):
        """测试Unicode字符"""
        result = find_longest_palindromic_substring("中文文中")
        assert result == "文中文"

    def test_case_sensitivity(self):
        """测试大小写敏感性"""
        result = find_longest_palindromic_substring("Aa")
        # 大小写不同，最长回文是单个字符
        assert len(result) == 1

    def test_whitespace_handling(self):
        """测试空格处理"""
        result = find_longest_palindromic_substring("a b a")
        assert result == "a b a"

    def test_none_input(self):
        """测试None输入"""
        with pytest.raises(TypeError):
            find_longest_palindromic_substring(None)

    def test_non_string_input(self):
        """测试非字符串输入"""
        with pytest.raises(TypeError):
            find_longest_palindromic_substring(123)

    def test_very_long_string(self):
        """测试超长字符串的性能"""
        long_string = "a" * 1000 + "b" + "a" * 1000
        result = find_longest_palindromic_substring(long_string)
        assert result == "a" * 1000 + "b" + "a" * 1000


class TestExpandAroundCenter:
    """测试辅助函数expand_around_center"""

    def test_expand_odd_length(self):
        """测试奇数长度扩展"""
        result = expand_around_center("aba", 1, 1)
        assert result == 3  # 扩展到整个"aba"

    def test_expand_even_length(self):
        """测试偶数长度扩展"""
        result = expand_around_center("abba", 1, 2)
        assert result == 4  # 扩展到整个"abba"

    def test_expand_no_expansion(self):
        """测试无法扩展的情况"""
        result = expand_around_center("abc", 1, 1)
        assert result == 1  # 只能扩展到单个字符

    def test_expand_at_boundaries(self):
        """测试在边界处扩展"""
        result = expand_around_center("a", 0, 0)
        assert result == 1

    def test_expand_partial(self):
        """测试部分扩展"""
        result = expand_around_center("xabay", 2, 2)
        assert result == 3  # 扩展到"aba"


def test_integration_with_complex_scenarios():
    """集成测试：复杂场景"""
    test_cases = [
        ("babad", ["bab", "aba"]),  # 多个有效结果
        ("cbbd", ["bb"]),
        ("a", ["a"]),
        ("ac", ["a", "c"]),
        ("bb", ["bb"]),
        ("abcba", ["abcba"]),
    ]

    for input_str, expected_options in test_cases:
        result = find_longest_palindromic_substring(input_str)
        assert result in expected_options, f"Input: {input_str}, Result: {result}"


def test_algorithm_correctness():
    """测试算法正确性"""
    # 验证一些经典的回文测试用例
    test_strings = [
        ("madam", "madam"),
        ("racecar", "racecar"),
        ("noon", "noon"),
        ("level", "level"),
        ("rotor", "rotor"),
    ]

    for input_str, expected in test_strings:
        result = find_longest_palindromic_substring(input_str)
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
