import re
import threading

import pytest

from data.raw.simple.simple3 import SingletonDatabase

# from advanced_functions import SingletonDatabase


class TestGetConnection:
    """Test cases for the get_connection method of SingletonDatabase class."""

    def test_get_connection_returns_string(self):
        """Test that get_connection returns a string connection identifier."""
        # Arrange
        db = SingletonDatabase()

        # Act
        connection = db.get_connection()

        # Assert
        assert isinstance(connection, str)
        assert connection.startswith("DBConnection_")

    def test_get_connection_same_instance_returns_same_connection(self):
        """Test that multiple calls to get_connection on same instance return same connection string."""
        # Arrange
        db = SingletonDatabase()
        first_connection = db.get_connection()

        # Act
        second_connection = db.get_connection()
        third_connection = db.get_connection()

        # Assert
        assert first_connection == second_connection == third_connection

    def test_get_connection_different_instances_return_same_connection(self):
        """Test that get_connection returns same connection string for different SingletonDatabase instances."""
        # Arrange & Act
        db1 = SingletonDatabase()
        db2 = SingletonDatabase()
        db3 = SingletonDatabase()

        connection1 = db1.get_connection()
        connection2 = db2.get_connection()
        connection3 = db3.get_connection()

        # Assert
        assert connection1 == connection2 == connection3

    def test_get_connection_after_close_still_returns_connection(self):
        """Test that get_connection still works after calling close method."""
        # Arrange
        db = SingletonDatabase()
        original_connection = db.get_connection()

        # Act
        db.close()  # This doesn't actually reset the singleton in the current implementation
        connection_after_close = db.get_connection()

        # Assert
        assert connection_after_close == original_connection

    def test_get_connection_thread_safety(self):
        """Test that get_connection is thread-safe and returns consistent results."""
        # Arrange
        results = []

        def get_connection_in_thread():
            db = SingletonDatabase()
            results.append(db.get_connection())

        # Act
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=get_connection_in_thread)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Assert
        assert len(results) == 5
        assert all(conn == results[0] for conn in results)

    def test_get_connection_format_consistent(self):
        """Test that the connection string format is consistent across calls."""
        # Arrange
        db = SingletonDatabase()

        # Act
        connection = db.get_connection()

        # Assert
        # Should match pattern: DBConnection_ followed by a number (memory address)
        assert re.match(r"^DBConnection_\d+$", connection)

    def test_get_connection_multiple_instances_same_thread(self):
        """Test get_connection behavior when creating multiple instances in same thread."""
        # Arrange & Act
        connections = []
        for _ in range(3):
            db = SingletonDatabase()
            connections.append(db.get_connection())

        # Assert
        assert len(set(connections)) == 1  # All should be identical
        assert connections[0] == connections[1] == connections[2]

    def test_get_connection_persistence(self):
        """Test that connection string persists across multiple instance creations."""
        # Arrange
        db1 = SingletonDatabase()
        original_connection = db1.get_connection()

        # Act - Create new instances and verify connection remains the same
        db2 = SingletonDatabase()
        db3 = SingletonDatabase()

        # Assert
        assert db2.get_connection() == original_connection
        assert db3.get_connection() == original_connection

    def test_get_connection_not_none(self):
        """Test that get_connection never returns None."""
        # Arrange
        db = SingletonDatabase()

        # Act
        connection = db.get_connection()

        # Assert
        assert connection is not None
        assert connection != ""

    def test_get_connection_immutable(self):
        """Test that the returned connection string cannot be modified to affect other instances."""
        # Arrange
        db1 = SingletonDatabase()
        db2 = SingletonDatabase()

        # Act
        connection1 = db1.get_connection()
        connection2 = db2.get_connection()

        # Attempt to modify (this shouldn't affect the singleton's internal state)
        original_connection = connection1
        connection1 = "modified_string"  # This is just reassigning the variable

        # Assert
        assert db1.get_connection() == original_connection
        assert db2.get_connection() == original_connection
        assert connection1 == "modified_string"  # Only the local variable changed
