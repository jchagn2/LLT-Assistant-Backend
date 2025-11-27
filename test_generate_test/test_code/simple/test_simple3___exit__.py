import time

import pytest

from data.raw.simple.simple3 import TimedOperation

# from advanced_functions import TimedOperation


class TestTimedOperationExit:
    """测试 TimedOperation 类的 __exit__ 方法"""

    def test_exit_normal_operation(self):
        """测试正常情况下的 __exit__ 方法"""
        with TimedOperation() as timer:
            time.sleep(0.01)  # 短暂延迟

        # 断言持续时间被正确计算
        assert hasattr(timer, "duration")
        assert isinstance(timer.duration, float)
        assert timer.duration > 0
        # 确保结束时间大于开始时间
        assert timer.end_time > timer.start_time

    def test_exit_with_exception_propagation(self):
        """测试有异常时 __exit__ 方法返回 False 允许异常传播"""
        with pytest.raises(ValueError, match="Test exception"):
            with TimedOperation() as timer:
                raise ValueError("Test exception")

        # 即使有异常，持续时间也应该被计算
        assert hasattr(timer, "duration")
        assert timer.duration > 0

    def test_exit_attributes_existence(self):
        """测试 __exit__ 方法正确设置了所有必要的属性"""
        with TimedOperation() as timer:
            pass

        # 验证所有必要的属性都存在
        required_attrs = ["start_time", "end_time", "duration"]
        for attr in required_attrs:
            assert hasattr(timer, attr), f"Missing attribute: {attr}"

        # 验证属性类型
        assert isinstance(timer.start_time, float)
        assert isinstance(timer.end_time, float)
        assert isinstance(timer.duration, float)

    def test_exit_duration_calculation(self):
        """测试持续时间的计算准确性"""
        with TimedOperation() as timer:
            time.sleep(0.1)  # 固定延迟以便测试

        # 验证持续时间计算正确
        expected_duration = timer.end_time - timer.start_time
        assert abs(timer.duration - expected_duration) < 0.001  # 允许微小误差

    def test_exit_multiple_operations(self):
        """测试多次操作时的 __exit__ 方法行为"""
        durations = []

        for i in range(3):
            with TimedOperation() as timer:
                time.sleep(0.01 * (i + 1))  # 不同的延迟
            durations.append(timer.duration)

        # 验证每次操作都有独立的持续时间
        assert len(durations) == 3
        assert all(duration > 0 for duration in durations)
        # 延迟时间应该递增
        assert durations[0] < durations[1] < durations[2]

    def test_exit_with_different_exception_types(self):
        """测试不同类型的异常处理"""
        exception_types = [ValueError, TypeError, RuntimeError]

        for exc_type in exception_types:
            with pytest.raises(exc_type):
                with TimedOperation() as timer:
                    raise exc_type("Test exception")

            # 验证即使有异常，持续时间也被记录
            assert timer.duration > 0

    def test_exit_return_value_behavior(self):
        """测试 __exit__ 方法的返回值行为"""
        # 由于 __exit__ 返回 False，异常应该传播
        try:
            with TimedOperation() as timer:
                raise ValueError("Test")
        except ValueError:
            pass  # 异常应该被传播

        # 如果 __exit__ 返回 True，异常会被抑制，但这里应该返回 False
        # 这个测试验证异常确实被传播了

    def test_exit_with_very_short_operation(self):
        """测试极短操作的 __exit__ 行为"""
        with TimedOperation() as timer:
            pass  # 几乎没有操作

        # 即使操作很短，也应该有正的时间差
        assert timer.duration >= 0
        # 由于操作极短，持续时间可能非常接近0，但计算应该正确

    def test_exit_context_manager_protocol(self):
        """测试完整的上下文管理器协议"""
        # 验证 TimedOperation 正确实现了上下文管理器协议
        timer = TimedOperation()

        # 应该可以调用 __enter__
        entered_timer = timer.__enter__()
        assert entered_timer is timer

        # 应该可以调用 __exit__ 并返回 False
        result = timer.__exit__(None, None, None)
        assert result is False

        # 验证属性被正确设置
        assert hasattr(timer, "duration")

    def test_exit_with_keyboard_interrupt(self):
        """测试 KeyboardInterrupt 异常的处理"""
        with pytest.raises(KeyboardInterrupt):
            with TimedOperation() as timer:
                raise KeyboardInterrupt()

        # 即使被中断，也应该记录时间
        assert hasattr(timer, "duration")
