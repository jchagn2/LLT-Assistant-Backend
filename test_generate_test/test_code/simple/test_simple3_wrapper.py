import threading
import time

import pytest

from data.raw.simple.simple3 import fibonacci_memoized, memoize

# from advanced_functions import fibonacci_memoized, memoize


def test_wrapper_basic_functionality():
    """测试wrapper函数的基本功能 - 缓存机制"""

    @memoize
    def simple_func(x):
        return x * 2

    # 第一次调用应该计算并缓存结果
    result1 = simple_func(5)
    assert result1 == 10

    # 第二次调用相同参数应该返回缓存结果
    result2 = simple_func(5)
    assert result2 == 10
    assert result1 is result2  # 应该是同一个对象（缓存返回）


def test_wrapper_different_arguments():
    """测试wrapper对不同参数的处理"""

    @memoize
    def multi_arg_func(a, b, c=0):
        return a + b + c

    # 测试不同参数组合
    result1 = multi_arg_func(1, 2)
    result2 = multi_arg_func(1, 2, 3)
    result3 = multi_arg_func(1, 2)  # 与result1相同参数

    assert result1 == 3
    assert result2 == 6
    assert result3 == 3
    assert result1 is result3  # 相同参数应该返回缓存


def test_wrapper_with_fibonacci_example():
    """测试wrapper在斐波那契数列中的实际应用"""

    # 测试斐波那契数列的缓存效果
    result1 = fibonacci_memoized(10)
    result2 = fibonacci_memoized(10)

    assert result1 == 55
    assert result2 == 55
    assert result1 is result2  # 验证缓存机制


def test_wrapper_cache_isolation():
    """测试不同函数的缓存是隔离的"""

    @memoize
    def func_a(x):
        return x + 1

    @memoize
    def func_b(x):
        return x * 2

    # 相同参数在不同函数中应该有不同结果
    result_a = func_a(5)
    result_b = func_b(5)

    assert result_a == 6
    assert result_b == 10
    # 缓存应该是隔离的，不会互相影响


def test_wrapper_with_complex_objects():
    """测试wrapper处理复杂对象参数"""

    @memoize
    def process_dict(d):
        return {k: v * 2 for k, v in d.items()}

    test_dict = {"a": 1, "b": 2}
    result1 = process_dict(test_dict)
    result2 = process_dict(test_dict)

    assert result1 == {"a": 2, "b": 4}
    assert result2 == {"a": 2, "b": 4}
    assert result1 is result2  # 验证复杂对象也能正确缓存


def test_wrapper_memory_efficiency():
    """测试wrapper的内存效率（通过执行时间判断）"""

    @memoize
    def expensive_operation(n):
        # 模拟耗时操作
        result = 0
        for i in range(n * 1000):
            result += i
        return result

    # 第一次执行应该较慢
    start_time = time.time()
    result1 = expensive_operation(10)
    first_duration = time.time() - start_time

    # 第二次执行相同参数应该很快（使用缓存）
    start_time = time.time()
    result2 = expensive_operation(10)
    second_duration = time.time() - start_time

    assert result1 == result2
    # 第二次执行应该明显快于第一次（缓存生效）
    assert second_duration < first_duration * 0.5  # 至少快一半


def test_wrapper_with_none_and_false_values():
    """测试wrapper处理None和False等特殊值"""

    @memoize
    def return_special_values(x):
        if x == 1:
            return None
        elif x == 2:
            return False
        elif x == 3:
            return 0
        return x

    # 测试各种特殊值的缓存
    assert return_special_values(1) is None
    assert return_special_values(1) is None  # 应该缓存None

    assert return_special_values(2) is False
    assert return_special_values(2) is False  # 应该缓存False

    assert return_special_values(3) == 0
    assert return_special_values(3) == 0  # 应该缓存0


def test_wrapper_thread_safety():
    """测试wrapper在多线程环境下的线程安全性"""

    @memoize
    def thread_safe_func(x):
        time.sleep(0.01)  # 小延迟增加竞争条件可能性
        return x * x

    results = []
    errors = []

    def worker_thread(x):
        try:
            result = thread_safe_func(x)
            results.append((x, result))
        except Exception as e:
            errors.append(e)

    # 创建多个线程同时访问相同函数
    threads = []
    for i in range(10):
        t = threading.Thread(target=worker_thread, args=(5,))  # 所有线程使用相同参数
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # 验证所有线程得到相同结果且无错误
    assert len(errors) == 0
    assert all(result == 25 for _, result in results)
    # 所有结果应该相同（缓存一致性）
    assert len(set(results)) == 1  # 所有结果应该完全相同


def test_wrapper_cache_persistence():
    """测试wrapper缓存的持久性"""

    call_count = 0

    @memoize
    def counting_func(x):
        nonlocal call_count
        call_count += 1
        return x * 3

    # 多次调用相同参数，实际计算应该只发生一次
    results = [counting_func(7) for _ in range(5)]

    assert all(r == 21 for r in results)
    assert call_count == 1  # 只应该被实际计算一次


def test_wrapper_with_exception_caching():
    """测试wrapper是否缓存异常（不应该缓存异常）"""

    exception_count = 0

    @memoize
    def sometimes_failing_func(x):
        nonlocal exception_count
        if x < 0:
            exception_count += 1
            raise ValueError("Negative input")
        return x * 2

    # 第一次调用应该抛出异常
    with pytest.raises(ValueError, match="Negative input"):
        sometimes_failing_func(-1)

    # 第二次调用相同参数应该再次抛出异常（不缓存异常）
    with pytest.raises(ValueError, match="Negative input"):
        sometimes_failing_func(-1)

    # 验证异常被正确抛出两次（不缓存）
    assert exception_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
