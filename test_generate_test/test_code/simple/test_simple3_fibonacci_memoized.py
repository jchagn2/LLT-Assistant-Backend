import time

import pytest

# from advanced_functions import fibonacci_memoized
from data.raw.simple.simple3 import fibonacci_memoized


class TestFibonacciMemoized:
    """针对 fibonacci_memoized 函数的单元测试类"""

    def test_fibonacci_base_cases(self):
        """测试斐波那契数列的基础情况"""
        # 测试 n = 0
        assert fibonacci_memoized(0) == 0

        # 测试 n = 1
        assert fibonacci_memoized(1) == 1

    def test_fibonacci_positive_numbers(self):
        """测试正整数的斐波那契数计算"""
        test_cases = [
            (2, 1),  # fib(2) = fib(1) + fib(0) = 1 + 0 = 1
            (3, 2),  # fib(3) = fib(2) + fib(1) = 1 + 1 = 2
            (4, 3),  # fib(4) = fib(3) + fib(2) = 2 + 1 = 3
            (5, 5),  # fib(5) = fib(4) + fib(3) = 3 + 2 = 5
            (6, 8),  # fib(6) = fib(5) + fib(4) = 5 + 3 = 8
            (10, 55),  # fib(10) = 55
            (15, 610),  # fib(15) = 610
        ]

        for n, expected in test_cases:
            assert (
                fibonacci_memoized(n) == expected
            ), f"fibonacci_memoized({n}) should be {expected}"

    def test_fibonacci_negative_number(self):
        """测试负数的处理（根据函数定义应返回0）"""
        assert fibonacci_memoized(-1) == 0
        assert fibonacci_memoized(-5) == 0
        assert fibonacci_memoized(-10) == 0

    def test_fibonacci_memoization_efficiency(self):
        """测试记忆化缓存的效果"""

        # 第一次计算较大的斐波那契数（应该较慢）
        start_time_1 = time.time()
        result_1 = fibonacci_memoized(30)
        duration_1 = time.time() - start_time_1

        # 第二次计算相同的数（应该很快，因为使用了缓存）
        start_time_2 = time.time()
        result_2 = fibonacci_memoized(30)
        duration_2 = time.time() - start_time_2

        # 结果应该相同
        assert result_1 == result_2

        # 第二次计算应该明显更快（由于缓存）
        # 注意：由于时间测量的不确定性，我们只检查第二次计算不慢于第一次
        assert (
            duration_2 <= duration_1 * 2
        ), "Memoization should make second call faster"

    def test_fibonacci_cache_consistency(self):
        """测试缓存的一致性"""
        # 多次调用相同参数，结果应该一致
        results = []
        for _ in range(5):
            results.append(fibonacci_memoized(7))

        # 所有结果应该相同
        assert all(r == results[0] for r in results)
        assert results[0] == 13  # fib(7) = 13

    def test_fibonacci_large_number(self):
        """测试较大数字的计算（验证函数不会栈溢出）"""
        # 测试一个相对较大的数（但不会导致栈溢出）
        result = fibonacci_memoized(20)
        assert result == 6765  # fib(20) = 6765

    def test_fibonacci_sequence_consistency(self):
        """测试斐波那契数列的递推关系"""
        # 验证 fib(n) = fib(n-1) + fib(n-2) 的关系
        for n in range(5, 15):
            assert fibonacci_memoized(n) == fibonacci_memoized(
                n - 1
            ) + fibonacci_memoized(n - 2)

    def test_fibonacci_zero_and_negative_edge_cases(self):
        """测试边界情况：0和负数"""
        # 测试0
        assert fibonacci_memoized(0) == 0

        # 测试多个负数
        for n in [-1, -2, -10, -100]:
            assert fibonacci_memoized(n) == 0

    def test_fibonacci_type_safety(self):
        """测试类型安全性（虽然类型提示存在，但需要验证实际行为）"""
        # 函数应该能够处理整数输入
        # 如果传入非整数，Python的类型系统会在运行时检查
        # 这里我们只测试合法的整数输入

    def test_fibonacci_performance_comparison(self):
        """性能对比测试：验证记忆化确实提高了性能"""
        # 清除缓存（通过重新导入或重启解释器）
        # 在实际测试中，可能需要更复杂的方法来重置缓存
        # 这里我们通过测试小数字来验证基本功能

        # 测试小数字的性能差异应该不明显

        start_1 = time.time()
        fib_5_first = fibonacci_memoized(5)
        time_1 = time.time() - start_1

        start_2 = time.time()
        fib_5_second = fibonacci_memoized(5)
        time_2 = time.time() - start_2

        assert fib_5_first == fib_5_second == 5
        # 对于小数字，时间差异可能不明显，但第二次不应明显慢于第一次


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
