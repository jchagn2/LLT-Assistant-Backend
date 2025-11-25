import ast
import http.client
import json
import os
import subprocess
import time

import tqdm

# [!] 请根据您的API文档修改此项！
# 上次失败的原因是这个URL不正确。您需要找到正确的URL来查询任务状态。
POLLING_ENDPOINT_TEMPLATE = "/tasks/{task_id}"
POLLING_INTERVAL_SECONDS = 10  # 轮询间隔
MAX_WAIT_SECONDS = 300  # 最长等待时间


def get_result_after_wait(task_id, host):
    """
    轮询指定的host，直到获取任务结果或超时。
    """
    print(f"    -- 已提交任务 {task_id}。将开始轮询结果...")
    start_time = time.time()

    while time.time() - start_time < MAX_WAIT_SECONDS:
        print(f"    -- 正在为任务 {task_id} 获取结果...")
        endpoint = POLLING_ENDPOINT_TEMPLATE.format(task_id=task_id)

        try:
            # 使用 HTTPSConnection
            conn = http.client.HTTPSConnection(host)
            conn.request("GET", endpoint)
            res = conn.getresponse()
            print(f"    -- HTTP 响应状态码: {res.status}")
            result_data = res.read().decode("utf-8")
            conn.close()

            result_info = json.loads(result_data)

            print(
                f"    -- 获取到的结果: {json.dumps(result_info, indent=2, ensure_ascii=False)}"
            )

            # 增加对 "Not Found" 错误的明确处理
            if res.status == 404:
                print(f"  -> 错误：获取结果失败 (HTTP 404 Not Found)。")
                print(
                    f"     请检查 POLLING_ENDPOINT_TEMPLATE 的值 ('{POLLING_ENDPOINT_TEMPLATE}') 是否正确。"
                )
                return None

            current_status = result_info.get("status")

            if current_status in ["completed", "successful", "succeeded"]:
                generated_code = result_info.get("result", {}).get("generated_code")
                if generated_code:
                    print(f"    -- 任务 {task_id} 已完成，成功获取测试代码。")
                    return generated_code
                else:
                    print(
                        f"  -> 错误：任务已完成，但响应中未找到生成的代码。完整响应: {result_data}"
                    )
                    return None
            else:
                print(
                    f"  -> 任务状态为 '{current_status}'。将在 {POLLING_INTERVAL_SECONDS} 秒后重试..."
                )

        except Exception as e:
            print(
                f"    -- 获取结果时出错: {e}。将在 {POLLING_INTERVAL_SECONDS} 秒后重试..."
            )

        time.sleep(POLLING_INTERVAL_SECONDS)

    print(
        f"  -> 错误：任务 {task_id} 超时。在 {MAX_WAIT_SECONDS} 秒内未获取到成功结果。"
    )
    return None


def generate_test_for_function(file_path, function_name):
    """
    为特定函数异步生成测试代码，并等待固定时间后获取结果。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    # 更新为新的URL
    host = "cs5351.efan.dev"
    try:
        # 使用 HTTPSConnection
        conn = http.client.HTTPSConnection(host)
        payload = json.dumps(
            {
                "source_code": source_code,
                "user_description": f"为函数 '{function_name}' 生成单元测试",
                "existing_test_code": "",
                "context": {"target_function": function_name, "mode": "new"},
            }
        )
        headers = {"Content-Type": "application/json"}
        # 创建任务的端点可能也需要修改，这里暂时保持不变
        conn.request("POST", "/workflows/generate-tests", payload, headers)
        res = conn.getresponse()
        initial_data = res.read().decode("utf-8")
        conn.close()

        task_info = json.loads(initial_data)
        task_id = task_info.get("task_id")

        if not task_id:
            print(f"  -> 错误：API响应中未找到 'task_id'。响应: {initial_data}")
            return None

        # 将host传递给等待函数
        return get_result_after_wait(task_id, host)

    except json.JSONDecodeError:
        print(f"  -> 错误：无法解析初始API响应。响应: {initial_data}")
        return None
    except ConnectionRefusedError:
        print(f"错误：到 {host} 的连接被拒绝。")
        return None
    except Exception as e:
        print(f"为函数 {function_name} 发起生成任务时发生意外错误: {e}")
        return None


def get_function_names(file_path):
    """
    解析一个Python文件，返回其中所有函数定义的名称列表。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
        return [
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        ]
    except SyntaxError as e:
        print(f"文件 {os.path.basename(file_path)} 存在语法错误，无法解析: {e}")
        return []


def run_tests(test_dir):
    """
    在指定目录上运行 pytest 并保存报告。
    """
    # 检查测试目录是否为空
    if not os.listdir(test_dir):
        print("测试目录为空，跳过测试执行。")
        return "No tests to run."

    report_path = os.path.join(os.path.dirname(test_dir), "simple_test_report.html")
    command = ["pytest", test_dir, f"--html={report_path}"]

    print(f"使用命令运行测试: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print("所有测试成功通过。")
        else:
            print("测试执行期间存在失败或错误。")
        return result.stdout + result.stderr
    except FileNotFoundError:
        return "错误: 未找到 'pytest' 命令。请确保 pytest 已安装 (pip install pytest) 并在您的 PATH 环境变量中。"
    except Exception as e:
        return f"运行测试时发生意外错误: {e}"


def main():
    """
    主函数，用于编排测试生成和执行。
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    code_dir = os.path.join(base_dir, "../data/raw/simple")
    test_dir = os.path.join(base_dir, "test_code/simple")

    print(f"基础目录: {base_dir}")
    print(f"源代码目录: {code_dir}")
    print(f"测试代码目录: {test_dir}\n")

    if not os.path.exists(code_dir):
        print(f"未找到源代码目录: {code_dir}")
        return

    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"已创建测试目录: {test_dir}")

    print(f"正在扫描Python文件于: {code_dir}")
    for root, _, files in os.walk(code_dir):
        for file in files:
            file_name = file.split("/")[-1]

            if file == "__init__.py":
                continue
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                # print(f"处理文件: {file_path}")

                function_names = get_function_names(file_path)
                if not function_names:
                    print(f"  -> 在 {file} 中未找到函数定义，跳过。")
                    continue

                print(f"  -> 找到函数: {', '.join(function_names)}")

                all_tests_for_file = []
                for func_name in tqdm.tqdm(function_names, desc=f"处理 {file}"):
                    print(f"    -- 为函数 '{func_name}' 生成测试...")
                    generated_test_code = generate_test_for_function(
                        file_path, func_name
                    )
                    print(f"    -- 生成的测试代码:\n{generated_test_code}\n")
                    if generated_test_code:
                        if generated_test_code.strip().startswith("```python"):
                            generated_test_code = generated_test_code.strip()[
                                9:
                            ].strip()
                        if generated_test_code.strip().endswith("```"):
                            generated_test_code = generated_test_code.strip()[
                                :-3
                            ].strip()
                        # all_tests_for_file.append(generated_test_code)

                    if generated_test_code:
                        test_file_name = "test_{}_{}.py".format(
                            file.split(".")[0], func_name
                        )
                        test_file_path = os.path.join(test_dir, test_file_name)

                        imports = set()
                        imports.add(
                            "from data.raw.simple.{file_name} import {func_name}".format(
                                file_name=file_name.split(".")[0], func_name=func_name
                            )
                        )
                        test_functions = []
                        for code in generated_test_code.split("\n\n"):
                            lines = code.split("\n")
                            for line in lines:
                                if line.strip().startswith(
                                    "import "
                                ) or line.strip().startswith("from "):
                                    imports.add(line)
                                else:
                                    test_functions.append(line)

                        final_test_code = (
                            "\n".join(sorted(list(imports)))
                            + "\n\n"
                            + "\n".join(test_functions)
                        )

                        with open(test_file_path, "w", encoding="utf-8") as f:
                            f.write(final_test_code)
                        print(
                            f"  -> 已为 {file}-{func_name} 生成所有测试并合并保存到 {test_file_path}"
                        )

    print("\n--- 正在运行生成的测试 ---")
    test_report = run_tests(test_dir)
    print("\n--- 测试执行摘要 ---")
    print(test_report)
    report_file = os.path.join(base_dir, "test_report.xml")
    print(f"\n测试报告已保存到 {report_file}")


if __name__ == "__main__":
    main()
