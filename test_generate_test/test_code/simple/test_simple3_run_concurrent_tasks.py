# from advanced_functions import run_concurrent_tasks, worker_task
import time
from unittest.mock import MagicMock, patch

import pytest

from data.raw.simple.simple3 import run_concurrent_tasks, worker_task


class TestRunConcurrentTasks:
    """Test cases for the run_concurrent_tasks function."""

    def test_run_concurrent_tasks_basic_functionality(self):
        """Test basic functionality with a small number of tasks."""
        # Arrange
        num_tasks = 3

        # Act
        results = run_concurrent_tasks(num_tasks)

        # Assert
        assert isinstance(results, dict)
        assert len(results) == num_tasks
        for i in range(num_tasks):
            assert i in results
            assert f"Task {i} completed successfully." in results[i]

    def test_run_concurrent_tasks_single_task(self):
        """Test with a single task (edge case)."""
        # Arrange
        num_tasks = 1

        # Act
        results = run_concurrent_tasks(num_tasks)

        # Assert
        assert len(results) == 1
        assert 0 in results
        assert "Task 0 completed successfully." == results[0]

    def test_run_concurrent_tasks_zero_tasks(self):
        """Test with zero tasks (edge case)."""
        # Arrange
        num_tasks = 0

        # Act
        results = run_concurrent_tasks(num_tasks)

        # Assert
        assert isinstance(results, dict)
        assert len(results) == 0

    def test_run_concurrent_tasks_large_number(self):
        """Test with a larger number of tasks."""
        # Arrange
        num_tasks = 10

        # Act
        start_time = time.time()
        results = run_concurrent_tasks(num_tasks)
        end_time = time.time()

        # Assert
        assert len(results) == num_tasks
        # Verify all tasks completed
        for i in range(num_tasks):
            assert i in results
            assert f"Task {i} completed successfully." in results[i]

        # Verify concurrent execution (should be faster than sequential)
        # Each task has delay of (i+1)*0.1 seconds
        # Sequential would take sum(0.1, 0.2, ..., 1.0) = 5.5 seconds
        # Concurrent should be much faster (close to the longest task: 1.0 second)
        execution_time = end_time - start_time
        assert execution_time < 2.0  # Allow some overhead for thread management

    def test_run_concurrent_tasks_thread_safety(self):
        """Test that results dictionary is properly populated by multiple threads."""
        # Arrange
        num_tasks = 5

        # Act
        results = run_concurrent_tasks(num_tasks)

        # Assert
        # Verify all expected keys are present
        expected_keys = set(range(num_tasks))
        actual_keys = set(results.keys())
        assert expected_keys == actual_keys

        # Verify all values are properly formatted
        for task_id, result in results.items():
            assert isinstance(task_id, int)
            assert isinstance(result, str)
            assert f"Task {task_id} completed successfully." == result

    @patch("advanced_functions.threading.Thread")
    def test_run_concurrent_tasks_thread_creation(self, mock_thread_class):
        """Test that threads are properly created and started."""
        # Arrange
        num_tasks = 3
        mock_threads = []

        def mock_thread_init(target, args):
            mock_thread = MagicMock()
            mock_thread.start = MagicMock()
            mock_thread.join = MagicMock()
            mock_threads.append(mock_thread)
            return mock_thread

        mock_thread_class.side_effect = mock_thread_init

        # Act
        results = run_concurrent_tasks(num_tasks)

        # Assert
        assert mock_thread_class.call_count == num_tasks
        for i, call in enumerate(mock_thread_class.call_args_list):
            args, kwargs = call
            assert kwargs["target"] == worker_task
            assert kwargs["args"][0] == i  # task_id
            assert isinstance(kwargs["args"][1], dict)  # result_dict
            assert kwargs["args"][2] == (i + 1) * 0.1  # delay

    def test_run_concurrent_tasks_result_isolation(self):
        """Test that multiple calls don't interfere with each other."""
        # Arrange
        num_tasks_1 = 2
        num_tasks_2 = 3

        # Act
        results_1 = run_concurrent_tasks(num_tasks_1)
        results_2 = run_concurrent_tasks(num_tasks_2)

        # Assert
        # Results should be independent
        assert len(results_1) == num_tasks_1
        assert len(results_2) == num_tasks_2
        assert set(results_1.keys()) == {0, 1}
        assert set(results_2.keys()) == {0, 1, 2}

    def test_run_concurrent_tasks_delay_progression(self):
        """Test that delays progress as expected (0.1, 0.2, 0.3, ...)."""
        # Arrange
        num_tasks = 4

        # Act
        start_time = time.time()
        results = run_concurrent_tasks(num_tasks)
        end_time = time.time()

        # Assert
        execution_time = end_time - start_time
        # Should complete in roughly the time of the longest task (0.4s) plus overhead
        assert 0.3 <= execution_time <= 1.0

        # Verify all tasks completed despite different delays
        assert len(results) == num_tasks
        for i in range(num_tasks):
            assert i in results

    @patch("advanced_functions.time.sleep")
    def test_run_concurrent_tasks_with_mocked_sleep(self, mock_sleep):
        """Test with mocked sleep to verify task execution order doesn't matter."""
        # Arrange
        num_tasks = 3
        sleep_calls = []

        def mock_sleep_side_effect(delay):
            sleep_calls.append(delay)

        mock_sleep.side_effect = mock_sleep_side_effect

        # Act
        results = run_concurrent_tasks(num_tasks)

        # Assert
        assert mock_sleep.call_count == num_tasks
        expected_delays = [0.1, 0.2, 0.3]
        # Since threads run concurrently, order might vary, but all delays should be called
        assert set(sleep_calls) == set(expected_delays)
        assert len(results) == num_tasks

    def test_run_concurrent_tasks_very_large_number(self):
        """Test with a very large number of tasks (stress test)."""
        # Arrange
        num_tasks = 50  # Large but reasonable number

        # Act
        start_time = time.time()
        results = run_concurrent_tasks(num_tasks)
        end_time = time.time()

        # Assert
        assert len(results) == num_tasks
        # Should complete in reasonable time (longest task is 5.0 seconds)
        execution_time = end_time - start_time
        assert execution_time < 6.0  # Allow some overhead

        # Verify all tasks completed successfully
        for i in range(num_tasks):
            assert i in results
            assert f"Task {i} completed successfully." in results[i]
