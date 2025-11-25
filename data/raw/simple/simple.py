# math_functions.py

"""
一个包含多种简单函数的集合，用于测试单测生成 agent。
"""

# --- 1. 基本数学运算 ---


def add(a: int, b: int) -> int:
    """返回两个整数的和。"""
    return a + b


def subtract(a: int, b: int) -> int:
    """返回两个整数的差 (a - b)。"""
    return a - b


def multiply(a: int, b: int) -> int:
    """返回两个整数的积。"""
    return a * b


def divide(a: int, b: int) -> float:
    """返回两个整数的商 (a / b)。假设 b 不为零。"""
    return a / b


# --- 2. 字符串操作 ---


def greet(name: str) -> str:
    """返回一个问候字符串。"""
    return f"Hello, {name}!"


def reverse_string(s: str) -> str:
    """返回反转后的字符串。"""
    return s[::-1]


def is_palindrome(s: str) -> bool:
    """判断一个字符串是否是回文（忽略大小写）。"""
    cleaned_s = s.lower().replace(" ", "")
    return cleaned_s == cleaned_s[::-1]


# --- 3. 列表操作 ---


def find_max(numbers: list[int]) -> int:
    """返回列表中的最大值。假设列表非空。"""
    return max(numbers)


def sum_list(numbers: list[int]) -> int:
    """返回列表中所有元素的总和。"""
    total = 0
    for num in numbers:
        total += num
    return total


def filter_even(numbers: list[int]) -> list[int]:
    """返回一个只包含原列表中偶数的新列表。"""
    return [num for num in numbers if num % 2 == 0]


# --- 4. 条件判断与循环 ---


def is_prime(n: int) -> bool:
    """判断一个大于1的整数是否为质数。"""
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def factorial(n: int) -> int:
    """计算一个非负整数的阶乘。"""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result


def fibonacci(n: int) -> list[int]:
    """返回包含前 n 个斐波那契数的列表。n 应大于0。"""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    sequence = [0, 1]
    while len(sequence) < n:
        next_num = sequence[-1] + sequence[-2]
        sequence.append(next_num)
    return sequence


# --- 5. 复杂逻辑与默认参数 ---


def calculate_discount(price: float, discount_percent: float = 0.0) -> float:
    """
    计算打折后的价格。
    :param price: 原价
    :param discount_percent: 折扣百分比 (例如 10 表示 10%)，默认为 0
    :return: 折后价格
    """
    if discount_percent < 0:
        discount_percent = 0
    if discount_percent > 100:
        discount_percent = 100
    return price * (1 - discount_percent / 100)


def get_grade(score: int) -> str:
    """
    根据分数返回等级。
    90-100: 'A'
    80-89: 'B'
    70-79: 'C'
    60-69: 'D'
    低于60: 'F'
    """
    if not (0 <= score <= 100):
        raise ValueError("Score must be between 0 and 100.")
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def count_vowels(s: str) -> int:
    """计算字符串中元音字母（a, e, i, o, u，不区分大小写）的数量。"""
    vowels = {"a", "e", "i", "o", "u"}
    count = 0
    for char in s.lower():
        if char in vowels:
            count += 1
    return count


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    合并两个字典。如果有相同的键，dict2 的值会覆盖 dict1 的值。
    返回一个新的合并后的字典。
    """
    merged = dict1.copy()
    merged.update(dict2)
    return merged


# --- 6. 简单的无参函数 ---


def get_current_year() -> int:
    """返回当前的年份（一个固定值，用于测试）。"""
    return 2024


print("'math_functions.py' 模块加载完毕。")
