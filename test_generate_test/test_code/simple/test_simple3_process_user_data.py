# from advanced_functions import process_user_data, DataProcessingError, User
from typing import Dict, List

import pytest

from data.raw.simple.simple3 import DataProcessingError, User, process_user_data


class TestProcessUserData:
    """测试 process_user_data 函数"""

    def test_normal_case_with_active_users(self):
        """测试正常情况：包含活跃用户的不同余额分组"""
        users: List[User] = [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "balance": 1000.0,
                "is_active": True,
            },
            {
                "id": 2,
                "name": "Bob",
                "email": "bob@test.com",
                "balance": 500.0,
                "is_active": True,
            },
            {
                "id": 3,
                "name": "Charlie",
                "email": "charlie@test.com",
                "balance": 200.0,
                "is_active": True,
            },
        ]
        min_balance = 300.0

        result = process_user_data(users, min_balance)

        assert len(result["high_value_active"]) == 2  # Alice 和 Bob
        assert len(result["low_value_active"]) == 1  # Charlie
        assert len(result["inactive"]) == 0
        assert result["high_value_active"][0]["id"] == 1
        assert result["high_value_active"][1]["id"] == 2
        assert result["low_value_active"][0]["id"] == 3

    def test_with_inactive_users(self):
        """测试包含非活跃用户的情况"""
        users: List[User] = [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "balance": 1000.0,
                "is_active": True,
            },
            {
                "id": 2,
                "name": "Bob",
                "email": "bob@test.com",
                "balance": 500.0,
                "is_active": False,
            },
            {
                "id": 3,
                "name": "Charlie",
                "email": "charlie@test.com",
                "balance": 200.0,
                "is_active": False,
            },
        ]
        min_balance = 300.0

        result = process_user_data(users, min_balance)

        assert len(result["high_value_active"]) == 1  # Alice
        assert len(result["low_value_active"]) == 0
        assert len(result["inactive"]) == 2  # Bob 和 Charlie
        assert result["inactive"][0]["id"] == 2
        assert result["inactive"][1]["id"] == 3

    def test_empty_user_list(self):
        """测试空用户列表"""
        users: List[User] = []
        min_balance = 100.0

        result = process_user_data(users, min_balance)

        assert len(result["high_value_active"]) == 0
        assert len(result["low_value_active"]) == 0
        assert len(result["inactive"]) == 0

    def test_all_users_below_min_balance(self):
        """测试所有用户余额都低于阈值"""
        users: List[User] = [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "balance": 50.0,
                "is_active": True,
            },
            {
                "id": 2,
                "name": "Bob",
                "email": "bob@test.com",
                "balance": 99.0,
                "is_active": True,
            },
        ]
        min_balance = 100.0

        result = process_user_data(users, min_balance)

        assert len(result["high_value_active"]) == 0
        assert len(result["low_value_active"]) == 2
        assert len(result["inactive"]) == 0

    def test_all_users_above_min_balance(self):
        """测试所有用户余额都高于阈值"""
        users: List[User] = [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "balance": 200.0,
                "is_active": True,
            },
            {
                "id": 2,
                "name": "Bob",
                "email": "bob@test.com",
                "balance": 150.0,
                "is_active": True,
            },
        ]
        min_balance = 100.0

        result = process_user_data(users, min_balance)

        assert len(result["high_value_active"]) == 2
        assert len(result["low_value_active"]) == 0
        assert len(result["inactive"]) == 0

    def test_exactly_at_min_balance(self):
        """测试用户余额正好等于阈值的情况"""
        users: List[User] = [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "balance": 100.0,
                "is_active": True,
            },
        ]
        min_balance = 100.0

        result = process_user_data(users, min_balance)

        assert len(result["high_value_active"]) == 1  # 等于阈值应归为高价值
        assert len(result["low_value_active"]) == 0
        assert len(result["inactive"]) == 0

    def test_missing_balance_field(self):
        """测试用户数据缺少余额字段的情况"""
        users: List[User] = [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "is_active": True,
            },  # 缺少 balance
        ]
        min_balance = 100.0

        result = process_user_data(users, min_balance)

        # 缺少 balance 字段时使用默认值 0.0
        assert len(result["high_value_active"]) == 0
        assert len(result["low_value_active"]) == 1
        assert len(result["inactive"]) == 0

    def test_missing_is_active_field(self):
        """测试用户数据缺少 is_active 字段的情况"""
        users: List[User] = [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "balance": 100.0,
            },  # 缺少 is_active
        ]
        min_balance = 50.0

        result = process_user_data(users, min_balance)

        # 缺少 is_active 字段时使用默认值 False
        assert len(result["high_value_active"]) == 0
        assert len(result["low_value_active"]) == 0
        assert len(result["inactive"]) == 1

    def test_negative_min_balance(self):
        """测试负数的余额阈值"""
        users: List[User] = [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "balance": 100.0,
                "is_active": True,
            },
            {
                "id": 2,
                "name": "Bob",
                "email": "bob@test.com",
                "balance": -50.0,
                "is_active": True,
            },
        ]
        min_balance = -100.0

        result = process_user_data(users, min_balance)

        # 负余额阈值应能正确处理
        assert len(result["high_value_active"]) == 2  # 两个用户余额都大于 -100
        assert len(result["low_value_active"]) == 0
        assert len(result["inactive"]) == 0

    def test_invalid_user_data_type(self):
        """测试无效的用户数据类型"""
        users = [
            "invalid_user_data",  # 字符串而不是字典
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "balance": 100.0,
                "is_active": True,
            },
        ]
        min_balance = 50.0

        with pytest.raises(DataProcessingError) as exc_info:
            process_user_data(users, min_balance)

        assert "Invalid user data type" in str(exc_info.value)

    def test_none_user_in_list(self):
        """测试用户列表中包含 None 值"""
        users = [
            None,
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@test.com",
                "balance": 100.0,
                "is_active": True,
            },
        ]
        min_balance = 50.0

        with pytest.raises(DataProcessingError) as exc_info:
            process_user_data(users, min_balance)

        assert "Invalid user data type" in str(exc_info.value)

    def test_large_number_of_users(self):
        """测试大量用户数据的处理"""
        users: List[User] = []
        for i in range(1000):
            users.append(
                {
                    "id": i,
                    "name": f"User{i}",
                    "email": f"user{i}@test.com",
                    "balance": float(i * 10),
                    "is_active": i % 2 == 0,  # 一半用户活跃
                }
            )
        min_balance = 5000.0

        result = process_user_data(users, min_balance)
        # 验证分组数量正确
        high_value_count = len(
            [
                result
                for result in users
                if result["is_active"] and result.get("balance", 0.0) >= min_balance
            ]
        )
        low_value_count = len(
            [
                result
                for result in users
                if result["is_active"] and result.get("balance", 0.0) < min_balance
            ]
        )
        inactive_count = len([result for result in users if not result["is_active"]])
