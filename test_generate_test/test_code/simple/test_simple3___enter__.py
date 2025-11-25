import threading
import time

import pytest

# from advanced_functions import TimedOperation
from data.raw.simple.simple3 import TimedOperation


class TestTimedOperationEnter:
    """Test suite for TimedOperation.__enter__ method"""

    def test_enter_returns_self(self):
        """Test that __enter__ returns the TimedOperation instance itself"""
        # Arrange
        timer = TimedOperation()

        # Act
        with timer as context_obj:
            # Assert
            assert context_obj is timer
            assert isinstance(context_obj, TimedOperation)

    def test_enter_sets_start_time(self):
        """Test that __enter__ correctly sets the start_time attribute"""
        # Arrange
        timer = TimedOperation()

        # Act
        with timer as context_obj:
            # Assert
            assert hasattr(context_obj, "start_time")
            assert isinstance(context_obj.start_time, float)
            assert context_obj.start_time > 0
            # Should be recent (within last second)
            assert time.time() - context_obj.start_time < 1

    def test_enter_multiple_contexts_independent(self):
        """Test that multiple context managers have independent start times"""
        # Arrange
        timer1 = TimedOperation()
        timer2 = TimedOperation()

        # Act & Assert
        with timer1 as ctx1:
            time.sleep(0.01)  # Small delay to ensure different start times
            with timer2 as ctx2:
                assert ctx1.start_time < ctx2.start_time
                assert ctx2.start_time - ctx1.start_time >= 0.01

    def test_enter_nested_context_managers(self):
        """Test that nested context managers work correctly"""
        # Arrange
        outer_timer = TimedOperation()
        inner_timer = TimedOperation()

        # Act & Assert
        with outer_timer as outer:
            outer_start = outer.start_time

            with inner_timer as inner:
                inner_start = inner.start_time

                # Both should have start times set
                assert hasattr(outer, "start_time")
                assert hasattr(inner, "start_time")
                assert inner_start > outer_start

    def test_enter_reused_context_manager(self):
        """Test that a context manager can be reused"""
        # Arrange
        timer = TimedOperation()

        # Act & Assert - First use
        with timer as ctx1:
            first_start = ctx1.start_time

        # Small delay between uses
        time.sleep(0.01)

        # Second use - should work fine
        with timer as ctx2:
            second_start = ctx2.start_time
            assert second_start > first_start

    def test_enter_with_exception_in_context(self):
        """Test that __enter__ works even when context block raises exception"""
        # Arrange
        timer = TimedOperation()

        # Act & Assert
        try:
            with timer as ctx:
                assert hasattr(ctx, "start_time")
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception

        # Start time should still have been set
        assert hasattr(timer, "start_time")

    def test_enter_attribute_accessibility(self):
        """Test that start_time is accessible within and outside context"""
        # Arrange
        timer = TimedOperation()

        # Act & Assert - Within context
        with timer as ctx:
            assert ctx.start_time is not None

        # Outside context - start_time should still be accessible
        assert hasattr(timer, "start_time")
        assert timer.start_time is not None

    def test_enter_timing_accuracy(self):
        """Test that start_time accurately reflects entry time"""
        # Arrange
        timer = TimedOperation()
        before_enter = time.time()

        # Act
        with timer as ctx:
            after_enter = time.time()

            # Assert - start_time should be between before and after
            assert before_enter <= ctx.start_time <= after_enter

    def test_enter_concurrent_access(self):
        """Test that __enter__ handles concurrent access correctly"""
        # Arrange

        results = []
        timer = TimedOperation()

        def worker(worker_id):
            with timer as ctx:
                results.append((worker_id, ctx.start_time))

        # Act
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Assert - Each worker should get its own context with proper start time
        assert len(results) == 3
        worker_ids, start_times = zip(*results)
        assert set(worker_ids) == {0, 1, 2}
        # All start times should be valid
        assert all(isinstance(st, float) for st in start_times)
        assert all(st > 0 for st in start_times)

    def test_enter_method_signature(self):
        """Test that __enter__ has correct method signature and behavior"""
        # Arrange
        timer = TimedOperation()

        # Act - Test that __enter__ can be called directly (though not typical)
        context_obj = timer.__enter__()

        # Assert
        assert context_obj is timer
        assert hasattr(context_obj, "start_time")

        # Cleanup - must call __exit__ since we called __enter__ directly
        timer.__exit__(None, None, None)
