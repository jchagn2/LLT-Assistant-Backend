# from complex_functions import solve_quadratic_equation
import math

import pytest

from data.raw.simple.simple2 import solve_quadratic_equation


class TestSolveQuadraticEquation:
    """测试一元二次方程求解函数 solve_quadratic_equation"""

    def test_two_real_roots(self):
        """测试有两个实数根的情况"""
        # 方程: x^2 - 5x + 6 = 0, 根为 2 和 3
        result = solve_quadratic_equation(1, -5, 6)
        expected = [3.0, 2.0]  # 注意：较大的根在前
        assert len(result) == 2
        assert math.isclose(result[0], expected[0], rel_tol=1e-9)
        assert math.isclose(result[1], expected[1], rel_tol=1e-9)

    def test_one_real_root(self):
        """测试有一个实数根的情况（判别式为0）"""
        # 方程: x^2 - 4x + 4 = 0, 根为 2（重根）
        result = solve_quadratic_equation(1, -4, 4)
        expected = [2.0]
        assert len(result) == 1
        assert math.isclose(result[0], expected[0], rel_tol=1e-9)

    def test_complex_roots(self):
        """测试有两个复数根的情况"""
        # 方程: x^2 + 2x + 5 = 0, 根为 -1 ± 2i
        result = solve_quadratic_equation(1, 2, 5)
        expected = [complex(-1, 2), complex(-1, -2)]
        assert len(result) == 2
        assert result[0] == expected[0]
        assert result[1] == expected[1]

    def test_negative_discriminant(self):
        """测试负判别式产生复数根"""
        # 方程: x^2 + 1 = 0, 根为 i 和 -i
        result = solve_quadratic_equation(1, 0, 1)
        expected = [complex(0, 1), complex(0, -1)]
        assert len(result) == 2
        assert result[0] == expected[0]
        assert result[1] == expected[1]

    def test_float_coefficients(self):
        """测试浮点数系数"""
        # 方程: 0.5x^2 - 1.5x + 1 = 0, 根为 1 和 2
        result = solve_quadratic_equation(0.5, -1.5, 1)
        expected = [2.0, 1.0]
        assert len(result) == 2
        assert math.isclose(result[0], expected[0], rel_tol=1e-9)
        assert math.isclose(result[1], expected[1], rel_tol=1e-9)

    def test_negative_a_coefficient(self):
        """测试负的二次项系数"""
        # 方程: -x^2 + 3x - 2 = 0, 根为 1 和 2
        result = solve_quadratic_equation(-1, 3, -2)
        expected = [1.0, 2.0]
        assert len(result) == 2
        assert math.isclose(result[0], expected[0], rel_tol=1e-9)
        assert math.isclose(result[1], expected[1], rel_tol=1e-9)

    def test_zero_a_coefficient_raises_error(self):
        """测试a=0时抛出ValueError"""
        with pytest.raises(ValueError, match="Coefficient 'a' cannot be zero"):
            solve_quadratic_equation(0, 2, 3)

    def test_large_coefficients(self):
        """测试大系数的情况"""
        # 方程: 1e6x^2 - 2e6x + 1e6 = 0, 根为 1（重根）
        result = solve_quadratic_equation(1e6, -2e6, 1e6)
        expected = [1.0]
        assert len(result) == 1
        assert math.isclose(result[0], expected[0], rel_tol=1e-9)

    def test_small_coefficients(self):
        """测试小系数的情况"""
        # 方程: 1e-6x^2 - 2e-6x + 1e-6 = 0, 根为 1（重根）
        result = solve_quadratic_equation(1e-6, -2e-6, 1e-6)
        expected = [1.0]
        assert len(result) == 1
        assert math.isclose(result[0], expected[0], rel_tol=1e-9)

    def test_edge_case_zero_b(self):
        """测试b=0的情况"""
        # 方程: x^2 - 4 = 0, 根为 2 和 -2
        result = solve_quadratic_equation(1, 0, -4)
        expected = [2.0, -2.0]
        assert len(result) == 2
        assert math.isclose(result[0], expected[0], rel_tol=1e-9)
        assert math.isclose(result[1], expected[1], rel_tol=1e-9)

    def test_edge_case_zero_c(self):
        """测试c=0的情况"""
        # 方程: x^2 - 3x = 0, 根为 3 和 0
        result = solve_quadratic_equation(1, -3, 0)
        expected = [3.0, 0.0]
        assert len(result) == 2
        assert math.isclose(result[0], expected[0], rel_tol=1e-9)
        assert math.isclose(result[1], expected[1], rel_tol=1e-9)

    def test_near_zero_discriminant(self):
        """测试判别式接近0的情况"""
        # 方程: x^2 - 2x + 1.0000000001 = 0 (判别式接近0)
        result = solve_quadratic_equation(1, -2, 1.0000000001)
        assert len(result) == 2
        # 应该是两个非常接近的实数根
        assert all(isinstance(root, float) for root in result)

    def test_return_type_consistency(self):
        """测试返回类型的正确性"""
        # 实数根情况
        real_roots = solve_quadratic_equation(1, -3, 2)
        assert all(isinstance(root, float) for root in real_roots)

        # 复数根情况
        complex_roots = solve_quadratic_equation(1, 0, 1)
        assert all(isinstance(root, complex) for root in complex_roots)
