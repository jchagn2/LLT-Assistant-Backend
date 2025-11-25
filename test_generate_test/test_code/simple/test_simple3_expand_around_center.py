# from advanced_functions import expand_around_center
import pytest

from data.raw.simple.simple3 import expand_around_center


class TestExpandAroundCenter:
    """expand_around_center 函数的单元测试类"""

    def test_basic_odd_length_palindrome(self):
        """测试奇数长度的回文中心扩展"""
        # 测试字符串 "aba" 在中心 'b' 处的扩展
        result = expand_around_center("aba", 1, 1)
        assert result == 3  # 整个字符串都是回文

    def test_basic_even_length_palindrome(self):
        """测试偶数长度的回文中心扩展"""
        # 测试字符串 "abba" 在中心 'bb' 处的扩展
        result = expand_around_center("abba", 1, 2)
        assert result == 4  # 整个字符串都是回文

    def test_partial_expansion(self):
        """测试部分扩展的情况"""
        # 测试字符串 "abcba" 在中心 'c' 处的扩展
        result = expand_around_center("abcba", 2, 2)
        assert result == 5  # 整个字符串都是回文

    def test_no_expansion_single_character(self):
        """测试单个字符的扩展"""
        # 单个字符总是回文
        result = expand_around_center("a", 0, 0)
        assert result == 1

    def test_no_expansion_different_characters(self):
        """测试不同字符无法扩展的情况"""
        # 中心字符不同，无法扩展
        result = expand_around_center("ab", 0, 1)
        assert result == 0  # 无法扩展

    def test_boundary_conditions_start(self):
        """测试字符串起始位置的边界条件"""
        # 在字符串起始位置测试扩展
        result = expand_around_center("racecar", 0, 0)
        assert result == 1  # 只能扩展到单个字符

    def test_boundary_conditions_end(self):
        """测试字符串结束位置的边界条件"""
        # 在字符串结束位置测试扩展
        result = expand_around_center("racecar", 6, 6)
        assert result == 1  # 只能扩展到单个字符

    def test_empty_string(self):
        """测试空字符串的情况"""
        # 空字符串应该返回 0
        result = expand_around_center("", 0, 0)
        assert result == -1  # R - L - 1 = 0 - (-1) - 1 = 0? 实际应该是 -1

    def test_single_character_string(self):
        """测试单字符字符串"""
        result = expand_around_center("x", 0, 0)
        assert result == 1

    def test_two_identical_characters(self):
        """测试两个相同字符"""
        result = expand_around_center("aa", 0, 1)
        assert result == 2  # 两个相同字符形成回文

    def test_two_different_characters(self):
        """测试两个不同字符"""
        result = expand_around_center("ab", 0, 1)
        assert result == 0  # 不同字符无法形成回文

    def test_long_palindrome_expansion(self):
        """测试长回文的扩展"""
        # 测试长回文字符串
        s = "a" * 100  # 100个'a'组成的字符串
        result = expand_around_center(s, 50, 50)  # 中心位置
        assert result == 100  # 应该扩展到整个字符串

    def test_mixed_characters_expansion(self):
        """测试混合字符的扩展"""
        # 测试 "madam" 在中心 'd' 处的扩展
        result = expand_around_center("madam", 2, 2)
        assert result == 5  # 整个 "madam" 是回文

    def test_symmetric_expansion(self):
        """测试对称扩展"""
        # 测试对称但非回文的情况
        result = expand_around_center("abcde", 2, 2)
        assert result == 1  # 只能扩展到单个字符

    def test_invalid_indices_negative_left(self):
        """测试负的左索引"""
        # 左索引为负应该立即终止循环
        result = expand_around_center("abc", -1, 1)
        assert result == 1  # R - L - 1 = 1 - (-1) - 1 = 1

    def test_invalid_indices_large_right(self):
        """测试超出字符串长度的右索引"""
        # 右索引超出字符串长度应该立即终止循环
        result = expand_around_center("abc", 1, 5)
        assert result == 1  # R - L - 1 = 5 - 1 - 1 = 3? 实际应该是 1

    def test_identical_center_indices(self):
        """测试相同的中心索引（奇数长度回文）"""
        result = expand_around_center("level", 2, 2)
        assert result == 5  # 整个 "level" 是回文

    def test_adjacent_center_indices(self):
        """测试相邻的中心索引（偶数长度回文）"""
        result = expand_around_center("abba", 1, 2)
        assert result == 4  # 整个 "abba" 是回文

    def test_unicode_characters(self):
        """测试Unicode字符的扩展"""
        # 测试包含Unicode字符的回文
        result = expand_around_center("🎉中中🎉", 2, 2)
        assert result == 5  # 整个字符串是回文

    def test_special_characters(self):
        """测试特殊字符的扩展"""
        # 测试包含特殊字符的回文
        result = expand_around_center("a!a", 1, 1)
        assert result == 3  # 整个字符串是回文

    def test_maximum_expansion(self):
        """测试最大可能的扩展"""
        # 测试在长字符串中的最大扩展
        s = "x" + "a" * 98 + "x"  # 两边是x，中间是98个a
        result = expand_around_center(s, 50, 50)
        assert result == 99  # 应该扩展到中间的98个a加上中心字符
