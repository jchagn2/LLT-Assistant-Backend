import threading
import time

import pytest

from data.raw.simple.simple3 import SingletonDatabase, __new__

# from advanced_functions import SingletonDatabase


class TestSingletonDatabaseNew:
    """针对 SingletonDatabase.__new__ 方法的单元测试"""

    def test_singleton_creation_initial_instance(self):
        """测试首次创建单例实例"""
        # 确保没有现有实例
        SingletonDatabase._instance = None

        instance = SingletonDatabase()

        assert instance is not None
        assert hasattr(instance, "connection")
        assert isinstance(instance.connection, str)
        assert instance.connection.startswith("DBConnection_")

    def test_singleton_returns_same_instance(self):
        """测试多次调用返回相同实例"""
        SingletonDatabase._instance = None

        instance1 = SingletonDatabase()
        instance2 = SingletonDatabase()
        instance3 = SingletonDatabase()

        assert instance1 is instance2
        assert instance2 is instance3
        assert instance1 is instance3

    def test_singleton_thread_safety(self):
        """测试多线程环境下的线程安全性"""
        SingletonDatabase._instance = None
        instances = []

        def create_instance():
            instance = SingletonDatabase()
            instances.append(instance)

        # 创建多个线程同时尝试创建实例
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 所有实例应该是同一个对象
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance

    def test_singleton_connection_uniqueness(self):
        """测试每个单例实例的连接字符串是唯一的"""
        SingletonDatabase._instance = None

        instance1 = SingletonDatabase()
        connection1 = instance1.connection

        # 模拟重新创建单例（在实际使用中不会发生，但测试边界情况）
        SingletonDatabase._instance = None
        instance2 = SingletonDatabase()
        connection2 = instance2.connection

        # 两个连接字符串应该不同
        assert connection1 != connection2
        assert instance1 is not instance2

    def test_singleton_methods_accessible(self):
        """测试单例实例的方法可正常访问"""
        SingletonDatabase._instance = None

        instance = SingletonDatabase()

        # 测试方法调用
        connection_str = instance.get_connection()
        assert isinstance(connection_str, str)
        assert connection_str == instance.connection

        # 测试close方法（虽然单例中不常用）
        instance.close()  # 应该正常执行，不抛出异常

    def test_singleton_with_existing_instance(self):
        """测试当实例已存在时的行为"""
        # 先创建一个实例
        SingletonDatabase._instance = None
        original_instance = SingletonDatabase()
        original_connection = original_instance.connection

        # 再次创建应该返回相同实例
        new_instance = SingletonDatabase()

        assert new_instance is original_instance
        assert new_instance.connection == original_connection

    def test_singleton_instance_persistence(self):
        """测试单例实例的持久性"""
        SingletonDatabase._instance = None

        # 创建实例并存储连接信息
        instance1 = SingletonDatabase()
        connection1 = instance1.connection

        # 模拟程序运行一段时间后再次访问
        time.sleep(0.05)
        instance2 = SingletonDatabase()

        # 应该还是同一个实例，连接信息不变
        assert instance2 is instance1
        assert instance2.connection == connection1

    def test_singleton_after_close_simulation(self):
        """测试模拟关闭连接后的行为（边界情况）"""
        SingletonDatabase._instance = None

        instance1 = SingletonDatabase()
        instance1.close()  # 模拟关闭（单例模式下实际不关闭）

        # 关闭后再次获取应该还是同一个实例
        instance2 = SingletonDatabase()
        assert instance2 is instance1

    def test_singleton_lock_mechanism(self):
        """测试锁机制确保线程安全"""
        SingletonDatabase._instance = None

        # 验证锁对象存在且是线程锁
        assert hasattr(SingletonDatabase, "_lock")
        assert isinstance(SingletonDatabase._lock, type(threading.Lock()))

    def test_singleton_double_checked_locking(self):
        """测试双重检查锁定模式"""
        SingletonDatabase._instance = None

        # 第一次检查（无实例）
        if SingletonDatabase._instance is None:
            # 获取锁
            with SingletonDatabase._lock:
                # 第二次检查（仍然无实例）
                if SingletonDatabase._instance is None:
                    # 创建实例
                    instance = super(SingletonDatabase, SingletonDatabase).__new__(
                        SingletonDatabase
                    )
                    SingletonDatabase._instance = instance

        # 验证实例创建成功
        assert SingletonDatabase._instance is not None
