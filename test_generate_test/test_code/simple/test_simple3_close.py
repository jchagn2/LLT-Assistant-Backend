import threading
from unittest.mock import MagicMock, patch

import pytest

from data.raw.simple.simple3 import SingletonDatabase


class TestCloseFunction:
    """Test cases for the close method in SingletonDatabase class"""

    def test_close_method_exists(self):
        """Test that close method exists and is callable"""
        # Arrange
        db = SingletonDatabase()

        # Act & Assert
        assert hasattr(db, "close")
        assert callable(db.close)

    def test_close_method_prints_correct_message(self):
        """Test that close method prints the correct connection message"""
        # Arrange
        db = SingletonDatabase()
        connection_string = db.get_connection()

        # Act & Assert
        with patch("builtins.print") as mock_print:
            db.close()
            mock_print.assert_called_once_with(
                f"Closing connection: {connection_string}"
            )

    def test_close_method_called_multiple_times(self):
        """Test that close method can be called multiple times without errors"""
        # Arrange
        db = SingletonDatabase()

        # Act & Assert
        with patch("builtins.print") as mock_print:
            # Call close multiple times
            db.close()
            db.close()
            db.close()

            # Should print the same message each time
            assert mock_print.call_count == 3
            # All calls should have the same connection string
            connection_string = db.get_connection()
            expected_call = f"Closing connection: {connection_string}"
            for call in mock_print.call_args_list:
                assert call[0][0] == expected_call

    def test_close_after_get_connection(self):
        """Test close method behavior after get_connection has been called"""
        # Arrange
        db = SingletonDatabase()
        original_connection = db.get_connection()

        # Act
        with patch("builtins.print") as mock_print:
            db.close()

        # Assert
        mock_print.assert_called_once_with(f"Closing connection: {original_connection}")
        # Connection should still be available after close (singleton behavior)
        assert db.get_connection() == original_connection

    def test_close_preserves_singleton_instance(self):
        """Test that close method doesn't affect the singleton instance"""
        # Arrange
        db1 = SingletonDatabase()
        db2 = SingletonDatabase()

        # Act
        with patch("builtins.print"):
            db1.close()

        # Assert - both references should point to same instance
        assert db1 is db2
        assert db1.get_connection() == db2.get_connection()

    def test_close_in_different_threads(self):
        """Test close method behavior when called from different threads"""
        # Arrange
        db = SingletonDatabase()
        connection_string = db.get_connection()
        results = []

        def close_in_thread():
            with patch("builtins.print") as mock_print:
                db.close()
                results.append(mock_print.call_args[0][0])

        # Act
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=close_in_thread)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Assert
        expected_message = f"Closing connection: {connection_string}"
        for result in results:
            assert result == expected_message
        assert len(results) == 3

    def test_close_method_does_not_raise_exceptions(self):
        """Test that close method doesn't raise any exceptions"""
        # Arrange
        db = SingletonDatabase()

        # Act & Assert - should not raise any exceptions
        try:
            db.close()
        except Exception as e:
            pytest.fail(f"close method raised an exception: {e}")

    def test_close_method_return_value(self):
        """Test that close method returns None (implicitly)"""
        # Arrange
        db = SingletonDatabase()

        # Act
        result = db.close()

        # Assert
        assert result is None

    @patch("SingletonDatabase._instance", None)
    def test_close_on_fresh_instance(self):
        """Test close method on a freshly created instance"""
        # Arrange - Reset singleton and create new instance
        SingletonDatabase._instance = None
        db = SingletonDatabase()

        # Act & Assert
        with patch("builtins.print") as mock_print:
            db.close()
            mock_print.assert_called_once()
            # Should contain the connection string pattern
            assert "Closing connection: DBConnection_" in mock_print.call_args[0][0]
