import math

import pytest

# from advanced_functions import calculate_complex_expression, DataProcessingError
from data.raw.simple.simple3 import DataProcessingError, calculate_complex_expression


class TestCalculateComplexExpression:
    """测试复杂数学表达式计算函数"""

    def test_basic_arithmetic_operations(self):
        """测试基本算术运算"""
        # 加法
        assert calculate_complex_expression("a + b", {"a": 5, "b": 3}) == 8.0

        # 减法
        assert calculate_complex_expression("x - y", {"x": 10, "y": 4}) == 6.0

        # 乘法
        assert calculate_complex_expression("m * n", {"m": 7, "n": 6}) == 42.0

        # 除法
        assert calculate_complex_expression("p / q", {"p": 15, "q": 3}) == 5.0

        # 混合运算
        assert (
            calculate_complex_expression("a + b * c", {"a": 2, "b": 3, "c": 4}) == 14.0
        )

    def test_complex_expressions_with_parentheses(self):
        """测试带括号的复杂表达式"""
        # 基本括号
        assert (
            calculate_complex_expression("(a + b) * c", {"a": 2, "b": 3, "c": 4})
            == 20.0
        )

        # 嵌套括号
        assert (
            calculate_complex_expression(
                "(a * (b + c)) / d", {"a": 2, "b": 3, "c": 4, "d": 2}
            )
            == 7.0
        )

        # 多层嵌套
        assert (
            calculate_complex_expression(
                "((a + b) * c) - (d / e)", {"a": 1, "b": 2, "c": 3, "d": 9, "e": 3}
            )
            == 6.0
        )

    def test_floating_point_operations(self):
        """测试浮点数运算"""
        # 浮点数计算
        assert calculate_complex_expression("a + b", {"a": 2.5, "b": 3.7}) == 6.2

        # 浮点数除法
        assert calculate_complex_expression("x / y", {"x": 5.0, "y": 2.0}) == 2.5

        # 混合整数和浮点数
        assert (
            calculate_complex_expression("a * b + c", {"a": 2, "b": 1.5, "c": 0.5})
            == 3.5
        )

    def test_whitespace_handling(self):
        """测试空格处理"""
        # 带空格的表达式
        assert calculate_complex_expression("  a  +  b  ", {"a": 3, "b": 4}) == 7.0

        # 制表符和换行符
        assert calculate_complex_expression("a\t+\nb", {"a": 5, "b": 2}) == 7.0

    def test_edge_cases(self):
        """测试边界情况"""
        # 零值运算
        assert calculate_complex_expression("a * b", {"a": 0, "b": 5}) == 0.0
        assert calculate_complex_expression("a + 0", {"a": 10}) == 10.0

        # 负值运算
        assert calculate_complex_expression("a + b", {"a": -5, "b": 3}) == -2.0
        assert calculate_complex_expression("a * b", {"a": -2, "b": -3}) == 6.0

        # 大数值运算
        assert (
            calculate_complex_expression("a * b", {"a": 1000000, "b": 1000000})
            == 1000000000000.0
        )

    def test_error_cases_invalid_input_types(self):
        """测试无效输入类型"""
        # 表达式不是字符串
        with pytest.raises(ValueError, match="Invalid input types"):
            calculate_complex_expression(123, {"a": 1})

        # 变量不是字典
        with pytest.raises(ValueError, match="Invalid input types"):
            calculate_complex_expression("a + b", "not_a_dict")

    def test_error_cases_invalid_characters(self):
        """测试表达式中的无效字符"""
        # 包含不允许的字符
        with pytest.raises(ValueError, match="Expression contains invalid characters"):
            calculate_complex_expression("a + b;", {"a": 1, "b": 2})

        # 包含特殊符号
        with pytest.raises(ValueError, match="Expression contains invalid characters"):
            calculate_complex_expression("a @ b", {"a": 1, "b": 2})

        # 包含方括号
        with pytest.raises(ValueError, match="Expression contains invalid characters"):
            calculate_complex_expression("a[b]", {"a": 1, "b": 2})

    def test_error_cases_undefined_variables(self):
        """测试未定义变量"""
        # 变量未在字典中定义
        with pytest.raises(ValueError, match="Undefined variable in expression"):
            calculate_complex_expression("x + y", {"x": 1})  # y未定义

        # 多个未定义变量
        with pytest.raises(ValueError, match="Undefined variable in expression"):
            calculate_complex_expression("a + b + c", {"a": 1})  # b, c未定义

    def test_error_cases_syntax_errors(self):
        """测试语法错误"""
        # 不完整的表达式
        with pytest.raises(ValueError, match="Invalid expression syntax"):
            calculate_complex_expression("a + ", {"a": 1})

        # 括号不匹配
        with pytest.raises(ValueError, match="Invalid expression syntax"):
            calculate_complex_expression("(a + b", {"a": 1, "b": 2})

        # 无效的操作符组合
        with pytest.raises(ValueError, match="Invalid expression syntax"):
            calculate_complex_expression("a + * b", {"a": 1, "b": 2})

    def test_error_cases_non_numeric_results(self):
        """测试非数值结果"""
        # 表达式结果为字符串（理论上不可能，但测试边界）
        # 这里我们测试表达式本身有效但可能产生非数值的情况
        with pytest.raises(ValueError, match="Expression did not evaluate to a number"):
            # 使用eval的安全限制应该防止这种情况，但测试异常处理
            # 实际上由于安全限制，这个测试可能不会触发，但保留作为文档
            pass

    def test_division_by_zero_handling(self):
        """测试除零处理"""
        # 除零应该产生浮点数无穷大或引发异常
        # 由于使用eval，Python会处理除零异常
        with pytest.raises(ZeroDivisionError):
            calculate_complex_expression("a / 0", {"a": 5})

    def test_complex_real_world_scenarios(self):
        """测试真实世界复杂场景"""
        # 物理公式：速度 = 距离 / 时间
        assert calculate_complex_expression("d / t", {"d": 100, "t": 5}) == 20.0

        # 财务计算：复利
        assert (
            calculate_complex_expression(
                "p * (1 + r) ** n", {"p": 1000, "r": 0.05, "n": 2}
            )
            == 1102.5
        )

        # 几何计算：圆面积
        assert calculate_complex_expression(
            "pi * r ** 2", {"pi": math.pi, "r": 5}
        ) == pytest.approx(78.5398, 0.001)

    def test_variable_names_edge_cases(self):
        """测试变量名边界情况"""
        # 单字母变量
        assert (
            calculate_complex_expression(
                "a + b + c + d + e", {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
            )
            == 15.0
        )

        # 多字母变量名
        assert (
            calculate_complex_expression(
                "price * quantity + tax", {"price": 10, "quantity": 5, "tax": 2.5}
            )
            == 52.5
        )

    def test_expression_with_constants(self):
        """测试包含常量的表达式"""
        # 混合变量和数字常量
        assert calculate_complex_expression("a * 2 + 3.14", {"a": 5}) == 13.14

        # 只有常量（无变量）
        assert calculate_complex_expression("2 + 3 * 4", {}) == 14.0

    # def test_performance_with_large_expressions
