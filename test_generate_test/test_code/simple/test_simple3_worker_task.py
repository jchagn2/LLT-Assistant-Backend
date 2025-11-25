import queue
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

# from advanced_functions import worker_task
from data.raw.simple.simple3 import worker_task


class TestWorkerTask:
    """Test cases for worker_task function"""

    def test_worker_task_successful_completion(self):
        """Test worker task completes successfully with normal delay"""
        # Arrange
        task_id = 1
        result_dict = {}
        delay = 0.1

        # Act
        worker_task(task_id, result_dict, delay)

        # Assert
        assert task_id in result_dict
        assert result_dict[task_id] == f"Task {task_id} completed successfully."

    def test_worker_task_zero_delay(self):
        """Test worker task with zero delay (edge case)"""
        # Arrange
        task_id = 2
        result_dict = {}
        delay = 0.0

        # Act
        worker_task(task_id, result_dict, delay)

        # Assert
        assert task_id in result_dict
        assert result_dict[task_id] == f"Task {task_id} completed successfully."

    def test_worker_task_multiple_tasks(self):
        """Test multiple worker tasks running concurrently"""
        # Arrange
        num_tasks = 3
        result_dict = {}
        threads = []

        # Act
        for i in range(num_tasks):
            thread = threading.Thread(target=worker_task, args=(i, result_dict, 0.05))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Assert
        assert len(result_dict) == num_tasks
        for i in range(num_tasks):
            assert i in result_dict
            assert result_dict[i] == f"Task {i} completed successfully."

    def test_worker_task_negative_delay(self):
        """Test worker task with negative delay (should handle gracefully)"""
        # Arrange
        task_id = 3
        result_dict = {}
        delay = -0.1

        # Act
        worker_task(task_id, result_dict, delay)

        # Assert
        assert task_id in result_dict
        assert result_dict[task_id] == f"Task {task_id} completed successfully."

    def test_worker_task_large_delay(self):
        """Test worker task with large delay"""
        # Arrange
        task_id = 4
        result_dict = {}
        delay = 0.5  # Larger delay to test timing

        # Act & Assert - verify the function doesn't hang

        def run_worker():
            worker_task(task_id, result_dict, delay)

        # Start thread with timeout
        thread = threading.Thread(target=run_worker)
        thread.start()
        thread.join(timeout=delay + 1.0)  # Add buffer time

        # Verify thread completed
        assert not thread.is_alive()
        assert task_id in result_dict

    def test_worker_task_thread_safety(self):
        """Test that worker_task is thread-safe when accessing shared dictionary"""
        # Arrange
        result_dict = {}
        num_threads = 5
        threads = []

        # Act
        for i in range(num_threads):
            thread = threading.Thread(target=worker_task, args=(i, result_dict, 0.01))
            threads.append(thread)

        # Start all threads nearly simultaneously
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Assert
        assert len(result_dict) == num_threads
        # Verify all tasks completed successfully
        for i in range(num_threads):
            assert result_dict[i] == f"Task {i} completed successfully."

    @patch("advanced_functions.time.sleep")
    @patch("advanced_functions.print")
    def test_worker_task_mocked_sleep(self, mock_print, mock_sleep):
        """Test worker_task with mocked sleep to verify timing behavior"""
        # Arrange
        task_id = 5
        result_dict = {}
        delay = 0.2

        # Act
        worker_task(task_id, result_dict, delay)

        # Assert
        mock_sleep.assert_called_once_with(delay)
        mock_print.assert_any_call(f"Task {task_id} starting with delay {delay}s...")
        mock_print.assert_any_call(f"Task {task_id} finished.")
        assert task_id in result_dict
        assert result_dict[task_id] == f"Task {task_id} completed successfully."

    def test_worker_task_result_dict_mutation(self):
        """Test that worker_task properly mutates the shared result dictionary"""
        # Arrange
        task_id = 6
        result_dict = {"existing_key": "existing_value"}
        delay = 0.1

        # Act
        worker_task(task_id, result_dict, delay)

        # Assert
        assert len(result_dict) == 2
        assert "existing_key" in result_dict
        assert result_dict["existing_key"] == "existing_value"
        assert task_id in result_dict
        assert result_dict[task_id] == f"Task {task_id} completed successfully."

    def test_worker_task_very_short_delay(self):
        """Test worker task with very short delay (edge case)"""
        # Arrange
        task_id = 7
        result_dict = {}
        delay = 0.001  # Very short delay

        # Act
        worker_task(task_id, result_dict, delay)

        # Assert
        assert task_id in result_dict
        assert result_dict[task_id] == f"Task {task_id} completed successfully."

    def test_worker_task_sequential_execution(self):
        """Test multiple worker tasks executed sequentially"""
        # Arrange
        result_dict = {}
        tasks = [(1, 0.1), (2, 0.05), (3, 0.01)]

        # Act - execute sequentially (not concurrently)
        for task_id, delay in tasks:
            worker_task(task_id, result_dict, delay)

        # Assert
        assert len(result_dict) == len(tasks)
        for task_id, _ in tasks:
            assert task_id in result_dict
            assert result_dict[task_id] == f"Task {task_id} completed successfully."

    @patch("advanced_functions.time.sleep")
    def test_worker_task_exception_handling(self, mock_sleep):
        """Test that worker_task handles exceptions gracefully"""
        # Arrange
        task_id = 8
        result_dict = {}
        delay = 0.1

        # Make sleep raise an exception
        mock_sleep.side_effect = Exception("Sleep interrupted")

        # Act & Assert
        with pytest.raises(Exception, match="Sleep interrupted"):
            worker_task(task_id, result_dict, delay)

        # Verify result_dict was not modified due to exception
        assert task_id not in result_dict

    def test_worker_task_different_task_ids(self):
        """Test worker task with various task ID types"""
        # Arrange
        test_cases = [
            (0, "minimum task ID"),
            (100, "large task ID"),
            (-1, "negative task ID"),
        ]

        for task_id, description in test_cases:
            with self.subTest(description=description):
                result_dict = {}
                delay = 0.01

                # Act
                worker_task(task_id, result_dict, delay)

                # Assert
                assert task_id in result_dict
                assert result_dict[task_id] == f"Task {task_id} completed successfully."

    def test_worker_task_performance(self):
        """Test that worker_task completes within reasonable time"""
        # Arrange
        task_id = 9
        result_dict = {}
        delay = 0.1

        # Act & measure time
        start_time = time.time()
        worker_task(task_id, result_dict, delay)
        end_time = time.time()

        execution_time = end_time - start_time

        # Assert - should take at least the delay time but not excessively more
        assert execution_time >= delay
        assert execution_time < delay + 0.5  # Allow some overhead
        assert task_id in result_dict

    def test_worker_task_with_none_result_dict(self):
        """Test worker task behavior when result_dict is None"""
        # Arrange
        task_id = 10
        result_dict = None
        delay = 0.1

        # Act & Assert
        with pytest.raises(TypeError):
            worker_task(task_id, result_dict, delay)

    def test_worker_task_with_invalid_delay_type(self):
        """Test worker task with invalid delay type"""
        # Arrange
        task_id = 11
        result_dict = {}
        delay = "invalid"  # Wrong type

        # Act & Assert
        with pytest.raises(TypeError):
            worker_task(task_id, result_dict, delay)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
