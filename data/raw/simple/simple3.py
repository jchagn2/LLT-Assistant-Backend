# advanced_functions.py

"""
一个包含20个高级复杂函数的集合，用于深度测试单测生成 agent 的能力。
涵盖了设计模式、缓存、上下文管理器、多线程、复杂数据处理等高级特性。
"""

import json
import re
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

# --- 1. 自定义异常和类型定义 ---


class InsufficientFundsError(Exception):
    """当账户余额不足时抛出的异常。"""

    pass


class DataProcessingError(Exception):
    """当数据处理失败时抛出的异常。"""

    pass


class User(TypedDict):
    """用户数据结构"""

    id: int
    name: str
    email: str
    balance: float
    is_active: bool


# --- 2. 设计模式 ---


class SingletonDatabase:
    """一个简单的单例模式数据库连接模拟类。"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    print("Creating new database connection...")
                    cls._instance = super(SingletonDatabase, cls).__new__(cls)
                    # 模拟连接数据库的耗时操作
                    time.sleep(0.1)
                    cls._instance.connection = f"DBConnection_{id(cls._instance)}"
        return cls._instance

    def get_connection(self) -> str:
        """获取数据库连接字符串。"""
        return self.connection

    def close(self):
        """模拟关闭连接（单例模式下此方法可能不常用）。"""
        print(f"Closing connection: {self.connection}")
        # 在单例模式中，我们通常不真正关闭，这里仅作演示
        # self._instance = None


def create_resource(resource_type: str, **kwargs) -> Dict[str, Any]:
    """
    一个简单的工厂模式函数，用于创建不同类型的资源。
    :param resource_type: 资源类型，如 'user', 'product'
    :param kwargs: 资源的属性
    :return: 创建的资源字典
    """
    if resource_type == "user":
        required_fields = ["id", "name", "email"]
        if not all(field in kwargs for field in required_fields):
            raise ValueError(
                f"Missing required fields for 'user': {', '.join(required_fields)}"
            )
        return User(
            id=kwargs["id"],
            name=kwargs["name"],
            email=kwargs["email"],
            balance=kwargs.get("balance", 0.0),
            is_active=kwargs.get("is_active", True),
        )
    elif resource_type == "product":
        return {
            "id": kwargs.get("id"),
            "name": kwargs.get("name"),
            "price": kwargs.get("price", 0.0),
            "category": kwargs.get("category", "uncategorized"),
        }
    else:
        raise ValueError(f"Unknown resource type: {resource_type}")


# --- 3. 缓存与性能 ---


def memoize(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """一个简单的记忆化（缓存）装饰器。"""
    cache = {}

    def wrapper(*args):
        if args in cache:
            return cache[args]
        result = func(*args)
        cache[args] = result
        return result

    return wrapper


@memoize
def fibonacci_memoized(n: int) -> int:
    """使用记忆化计算第n个斐波那契数。"""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci_memoized(n - 1) + fibonacci_memoized(n - 2)


# --- 4. 上下文管理器 ---


class TimedOperation:
    """一个用于测量代码块执行时间的上下文管理器。"""

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        print(f"Operation took {self.duration:.4f} seconds.")
        # 如果有异常，返回False以允许异常传播
        return False


# --- 5. 多线程与并发 ---


def worker_task(task_id: int, result_dict: Dict[int, str], delay: float):
    """一个简单的工作线程任务。"""
    print(f"Task {task_id} starting with delay {delay}s...")
    time.sleep(delay)
    result_dict[task_id] = f"Task {task_id} completed successfully."
    print(f"Task {task_id} finished.")


def run_concurrent_tasks(num_tasks: int) -> Dict[int, str]:
    """
    启动多个并发任务。
    :param num_tasks: 任务数量
    :return: 任务结果字典
    """
    results = {}
    threads = []
    for i in range(num_tasks):
        # 每个任务有不同的延迟
        thread = threading.Thread(target=worker_task, args=(i, results, (i + 1) * 0.1))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results


# --- 6. 复杂数据处理与算法 ---


def process_user_data(users: List[User], min_balance: float) -> Dict[str, List[User]]:
    """
    处理用户数据，按活跃度和余额进行分组。
    :param users: 用户列表
    :param min_balance: 最低余额阈值
    :return: 一个包含 'high_value_active', 'low_value_active', 'inactive' 键的字典
    """
    high_value_active = []
    low_value_active = []
    inactive = []

    for user in users:
        try:
            if not isinstance(user, dict):
                raise DataProcessingError(f"Invalid user data type: {type(user)}")

            is_active = user.get("is_active", False)
            balance = user.get("balance", 0.0)

            if not is_active:
                inactive.append(user)
            else:
                if balance >= min_balance:
                    high_value_active.append(user)
                else:
                    low_value_active.append(user)
        except Exception as e:
            raise DataProcessingError(
                f"Error processing user {user.get('id', 'Unknown')}: {e}"
            ) from e

    return {
        "high_value_active": high_value_active,
        "low_value_active": low_value_active,
        "inactive": inactive,
    }


def find_longest_palindromic_substring(s: str) -> str:
    """
    查找字符串中最长的回文子串（Manacher's 算法的简化思想）。
    :param s: 输入字符串
    :return: 最长的回文子串
    """
    if not s:
        return ""

    start = 0
    end = 0

    for i in range(len(s)):
        len1 = expand_around_center(s, i, i)  # 奇数长度
        len2 = expand_around_center(s, i, i + 1)  # 偶数长度
        max_len = max(len1, len2)
        if max_len > end - start:
            start = i - (max_len - 1) // 2
            end = i + max_len // 2
    return s[start : end + 1]


def expand_around_center(s: str, left: int, right: int) -> int:
    """辅助函数，用于查找回文子串。"""
    L, R = left, right
    while L >= 0 and R < len(s) and s[L] == s[R]:
        L -= 1
        R += 1
    return R - L - 1


# --- 7. 复杂字符串与正则 ---


def extract_and_validate_urls(text: str) -> List[Dict[str, str]]:
    """
    从文本中提取URL，并解析其组成部分。
    :param text: 包含URL的文本
    :return: 一个字典列表，每个字典包含 'url', 'protocol', 'domain'
    """
    # 一个相对复杂的URL匹配正则表达式
    url_pattern = r"https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:/[^\s]*)?"
    matches = re.findall(url_pattern, text)

    results = []
    for match in matches:
        # 这是一个简化的提取，实际情况更复杂
        protocol_match = re.match(r"(https?)://", match)
        protocol = protocol_match.group(1) if protocol_match else "http"

        # 移除协议和可能的www.来获取域名
        domain = re.sub(r"^https?://(www\.)?", "", match)
        domain = re.sub(r"/.*", "", domain)  # 移除路径部分

        results.append({"url": match, "protocol": protocol, "domain": domain})

    return results


# --- 8. 模拟外部系统交互 ---


def simulate_api_call(
    endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    模拟一个API调用。
    :param endpoint: API端点
    :param method: HTTP方法
    :param payload: 请求 payload (用于POST, PUT等)
    :return: API响应
    """
    print(f"Simulating API call to '{endpoint}' using {method}...")
    time.sleep(0.2)  # 模拟网络延迟

    if method not in ["GET", "POST", "PUT", "DELETE"]:
        return {"status": 400, "error": "Invalid method"}

    if endpoint == "/api/users":
        if method == "GET":
            return {
                "status": 200,
                "data": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            }
        elif method == "POST" and payload:
            new_user_id = 3  # 简单模拟
            return {"status": 201, "data": {"id": new_user_id, **payload}}
    elif endpoint == "/api/health":
        return {"status": 200, "data": {"status": "OK"}}
    else:
        return {"status": 404, "error": "Endpoint not found"}


# --- 9. 财务与交易逻辑 ---


def transfer_funds(from_user: User, to_user: User, amount: float) -> Dict[str, Any]:
    """
    在两个用户之间转移资金。
    :param from_user: 转出用户
    :param to_user: 转入用户
    :param amount: 转移金额
    :return: 交易结果
    """
    if not from_user.get("is_active") or not to_user.get("is_active"):
        raise ValueError("Both users must be active.")

    if amount <= 0:
        raise ValueError("Transfer amount must be positive.")

    if from_user.get("balance", 0.0) < amount:
        raise InsufficientFundsError(
            f"User {from_user.get('id')} has insufficient funds."
        )

    # 模拟数据库事务
    try:
        from_user["balance"] -= amount
        to_user["balance"] += amount
        return {
            "success": True,
            "from_user_id": from_user.get("id"),
            "to_user_id": to_user.get("id"),
            "amount": amount,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        # 在真实场景中，这里会有回滚逻辑
        raise DataProcessingError(f"Transaction failed: {e}") from e


# --- 10. 杂项高级函数 ---


def deep_copy_dict(obj: Any) -> Any:
    """
    一个简单的深拷贝函数（使用json作为辅助）。
    :param obj: 要拷贝的对象（应可被JSON序列化）
    :return: 深拷贝后的对象
    """
    try:
        return json.loads(json.dumps(obj))
    except (TypeError, ValueError) as e:
        raise DataProcessingError(f"Cannot deep copy object: {e}") from e


def parse_nested_json(json_str: str) -> Any:
    """
    解析一个可能包含嵌套JSON字符串的JSON。
    例如: '{"a": 1, "b": "{\"c\": 2}"}' -> {"a": 1, "b": {"c": 2}}
    :param json_str: 输入的JSON字符串
    :return: 解析后的Python对象
    """

    def _parse(obj: Any) -> Any:
        if isinstance(obj, str):
            try:
                return _parse(json.loads(obj))
            except json.JSONDecodeError:
                return obj
        elif isinstance(obj, dict):
            return {k: _parse(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_parse(item) for item in obj]
        else:
            return obj

    try:
        data = json.loads(json_str)
        return _parse(data)
    except json.JSONDecodeError as e:
        raise DataProcessingError(f"Invalid JSON string: {e}") from e


def calculate_complex_expression(expression: str, variables: Dict[str, float]) -> float:
    """
    计算一个包含变量的复杂数学表达式。
    (这是一个简化版本，使用eval，在生产环境中需谨慎使用)。
    :param expression: 数学表达式字符串，如 "a * (b + c)"
    :param variables: 变量字典，如 {'a': 2, 'b': 3, 'c': 4}
    :return: 计算结果
    """
    if not isinstance(expression, str) or not isinstance(variables, dict):
        raise ValueError("Invalid input types.")

    # 简单的安全检查：只允许字母、数字和指定运算符
    if not re.match(r"^[a-zA-Z0-9+\-*/().\s]+$", expression):
        raise ValueError("Expression contains invalid characters.")

    try:
        # 使用eval计算表达式，传入变量字典作为 locals
        result = eval(expression, {}, variables)
        if not isinstance(result, (int, float)):
            raise ValueError("Expression did not evaluate to a number.")
        return float(result)
    except SyntaxError:
        raise ValueError(f"Invalid expression syntax: {expression}") from None
    except NameError as e:
        raise ValueError(f"Undefined variable in expression: {e}") from None
    except Exception as e:
        raise ValueError(f"Error evaluating expression: {e}") from e


print("'advanced_functions.py' 模块加载完毕。")
