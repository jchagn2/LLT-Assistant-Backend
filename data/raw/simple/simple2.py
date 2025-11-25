# complex_functions.py

"""
一个包含20个更复杂函数的集合，用于深度测试单测生成 agent。
涵盖了数据结构、算法、错误处理、正则、日期等多种特性。
"""

import re
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Union

# --- 1. 复杂数据结构操作 ---


def find_nested_value(data: Dict[str, Any], keys: List[str]) -> Any:
    """
    在嵌套的字典中根据一系列键查找值。
    如果任何一个键不存在，返回 None。
    :param data: 嵌套的字典
    :param keys: 键的列表，按层级顺序
    :return: 找到的值或 None
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def merge_and_deduplicate_lists(list1: List[Any], list2: List[Any]) -> List[Any]:
    """
    合并两个列表并去除重复元素，保持原始顺序（第一个出现的位置）。
    :param list1: 第一个列表
    :param list2: 第二个列表
    :return: 合并并去重后的新列表
    """
    seen = set()
    result = []
    for item in list1 + list2:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# --- 2. 模拟对象和业务逻辑 ---


def calculate_user_balance(users: List[Dict[str, Any]], user_id: int) -> float:
    """
    计算指定用户的账户余额。
    用户列表中每个用户是一个字典，包含 'id' 和 'transactions'。
    'transactions' 是一个字典列表，每个包含 'amount' (正数为收入，负数为支出)。
    :param users: 用户列表
    :param user_id: 要查询的用户ID
    :return: 账户余额，如果用户不存在则返回 -1.0
    """
    for user in users:
        if user.get("id") == user_id:
            transactions = user.get("transactions", [])
            balance = sum(t.get("amount", 0) for t in transactions)
            return round(balance, 2)
    return -1.0


# --- 3. 算法 ---


def custom_sort(lst: List[Union[int, str]]) -> List[Union[int, str]]:
    """
    自定义排序：先按类型（数字在前，字符串在后）排序，
    然后数字按升序，字符串按长度降序。
    :param lst: 包含整数和字符串的列表
    :return: 排序后的新列表
    """
    numbers = sorted([x for x in lst if isinstance(x, int)])
    strings = sorted(
        [x for x in lst if isinstance(x, str)], key=lambda s: len(s), reverse=True
    )
    return numbers + strings


def binary_search(sorted_list: List[int], target: int) -> int:
    """
    在有序整数列表中执行二分查找。
    :param sorted_list: 已排序的整数列表
    :param target: 要查找的整数
    :return: 目标的索引，如果找不到返回 -1
    """
    left, right = 0, len(sorted_list) - 1
    while left <= right:
        mid = (left + right) // 2
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


# --- 4. 错误处理和正则 ---


def extract_emails(text: str) -> List[str]:
    """
    使用正则表达式从文本中提取所有电子邮件地址。
    :param text: 包含可能电子邮件的文本
    :return: 提取到的电子邮件列表
    """
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    return re.findall(email_pattern, text)


def safe_convert_to_int(value: Any) -> int:
    """
    安全地将一个值转换为整数。
    如果转换失败（例如，值是None、非数字字符串），返回0并打印警告。
    :param value: 要转换的值
    :return: 转换后的整数或0
    """
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        print(f"Warning: Could not convert '{value}' to int. Error: {e}. Returning 0.")
        return 0


# --- 5. 日期时间处理 ---


def get_date_days_ago(days: int, date_str: str = None, format: str = "%Y-%m-%d") -> str:
    """
    计算并返回指定日期之前N天的日期字符串。
    如果不指定日期，则使用今天。
    :param days: 天数
    :param date_str: 参考日期字符串，如 "2023-10-27"
    :param format: 日期字符串的格式
    :return: 计算出的日期字符串
    """
    if date_str:
        try:
            base_date = datetime.strptime(date_str, format)
        except ValueError:
            raise ValueError(f"Invalid date string '{date_str}' for format '{format}'")
    else:
        base_date = datetime.now()

    target_date = base_date - timedelta(days=days)
    return target_date.strftime(format)


# --- 6. 高阶函数和文件操作 ---


def apply_function_to_items(items: List[Any], func: Callable[[Any], Any]) -> List[Any]:
    """
    将指定的函数应用于列表中的每一个元素，并返回结果列表。
    :param items: 元素列表
    :param func: 要应用的函数
    :return: 应用函数后的结果列表
    """
    return [func(item) for item in items]


def read_and_process_file(
    file_path: str, processor_func: Callable[[str], str]
) -> List[str]:
    """
    读取文件内容，对每一行应用处理函数，然后返回处理后的行列表。
    如果文件不存在，返回空列表。
    :param file_path: 文件路径
    :param processor_func: 处理每一行的函数
    :return: 处理后的行列表
    """
    processed_lines = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                processed_line = processor_func(line.strip())
                processed_lines.append(processed_line)
    except FileNotFoundError:
        print(f"Info: File '{file_path}' not found. Returning empty list.")
    return processed_lines


# --- 7. 更复杂的业务逻辑 ---


def generate_password(length: int = 12) -> str:
    """
    生成一个指定长度的随机密码。
    密码包含大小写字母、数字和特殊字符。
    :param length: 密码长度，至少8位
    :return: 生成的密码字符串
    """
    import random
    import string

    if length < 8:
        raise ValueError("Password length must be at least 8 characters.")

    all_chars = string.ascii_letters + string.digits + string.punctuation
    # 确保至少包含一种类型的字符
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice(string.punctuation),
    ]
    # 填充剩余长度
    password += [random.choice(all_chars) for _ in range(length - 4)]
    # 打乱顺序
    random.shuffle(password)
    return "".join(password)


def analyze_text_sentiment(text: str) -> Dict[str, Union[str, float]]:
    """
    一个简单的文本情感分析器。
    通过关键词匹配来判断文本的情感倾向。
    :param text: 要分析的文本
    :return: 包含情感标签('positive', 'negative', 'neutral')和置信度的字典
    """
    positive_words = {
        "good",
        "great",
        "excellent",
        "happy",
        "positive",
        "best",
        "love",
        "like",
    }
    negative_words = {
        "bad",
        "terrible",
        "awful",
        "sad",
        "negative",
        "worst",
        "hate",
        "dislike",
    }

    words = re.findall(r"\b\w+\b", text.lower())

    pos_count = sum(1 for word in words if word in positive_words)
    neg_count = sum(1 for word in words if word in negative_words)

    total = pos_count + neg_count
    if total == 0:
        return {"sentiment": "neutral", "confidence": 1.0}

    confidence = abs(pos_count - neg_count) / total
    if pos_count > neg_count:
        return {"sentiment": "positive", "confidence": confidence}
    elif neg_count > pos_count:
        return {"sentiment": "negative", "confidence": confidence}
    else:
        return {
            "sentiment": "neutral",
            "confidence": 1.0 - (confidence / 2),
        }  # 稍微降低置信度


# --- 8. 杂项复杂函数 ---


def solve_quadratic_equation(
    a: float, b: float, c: float
) -> List[Union[float, complex]]:
    """
    求解一元二次方程 ax^2 + bx + c = 0 的根。
    :param a: 二次项系数
    :param b: 一次项系数
    :param c: 常数项
    :return: 根的列表（可能包含复数）
    """
    if a == 0:
        raise ValueError("Coefficient 'a' cannot be zero.")

    discriminant = b**2 - 4 * a * c

    if discriminant > 0:
        root1 = (-b + discriminant**0.5) / (2 * a)
        root2 = (-b - discriminant**0.5) / (2 * a)
        return [root1, root2]
    elif discriminant == 0:
        root = -b / (2 * a)
        return [root]
    else:
        real_part = -b / (2 * a)
        imag_part = (-discriminant) ** 0.5 / (2 * a)
        return [complex(real_part, imag_part), complex(real_part, -imag_part)]


def group_by_key(
    items: List[Dict[str, Any]], key: str
) -> Dict[Any, List[Dict[str, Any]]]:
    """
    根据指定的键将字典列表分组。
    :param items: 字典列表
    :param key: 用于分组的键
    :return: 分组后的字典，键是分组依据的值，值是该组的字典列表
    """
    grouped = {}
    for item in items:
        group_key = item.get(key)
        if group_key not in grouped:
            grouped[group_key] = []
        grouped[group_key].append(item)
    return grouped


def is_valid_palindrome(s: str) -> bool:
    """
    判断一个字符串是否是有效的回文。
    只考虑字母和数字字符，忽略大小写和非字母数字字符。
    :param s: 输入字符串
    :return: 如果是有效回文则为 True，否则为 False
    """
    cleaned_s = re.sub(r"[^a-zA-Z0-9]", "", s).lower()
    return cleaned_s == cleaned_s[::-1]


def calculate_shipping_cost(
    weight: float, destination: str, is_express: bool = False
) -> float:
    """
    根据重量、目的地和是否加急计算运费。
    (这是一个模拟函数，使用虚构的费率)
    :param weight: 货物重量（公斤）
    :param destination: 目的地国家/地区
    :param is_express: 是否选择加急服务
    :return: 计算出的运费
    """
    base_rates = {"US": 5.0, "UK": 7.5, "China": 6.0, "Japan": 7.0, "Australia": 8.0}
    express_multiplier = 2.0
    weight_surcharge = 0.0

    if weight <= 0:
        raise ValueError("Weight must be positive.")

    if weight > 10:
        weight_surcharge = (weight - 10) * 2.5

    base_rate = base_rates.get(destination, 10.0)  # 默认费率
    total = base_rate + weight_surcharge

    if is_express:
        total *= express_multiplier

    return round(total, 2)


def flatten_nested_list(nested_list: List[Any]) -> List[Any]:
    """
    将一个可能包含嵌套列表的列表“扁平化”为一个一维列表。
    :param nested_list: 可能包含嵌套的列表
    :return: 扁平化后的一维列表
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_nested_list(item))
        else:
            result.append(item)
    return result


def find_common_elements(list_of_lists: List[List[Any]]) -> List[Any]:
    """
    找出多个列表中的所有共同元素。
    :param list_of_lists: 列表的列表
    :return: 所有列表都共有的元素列表
    """
    if not list_of_lists:
        return []

    # 使用第一个列表的元素作为初始候选
    common = set(list_of_lists[0])
    # 与后续每个列表求交集
    for lst in list_of_lists[1:]:
        common.intersection_update(lst)
        if not common:  # 提前退出，如果没有共同元素
            break
    return list(common)


print("'complex_functions.py' 模块加载完毕。")
