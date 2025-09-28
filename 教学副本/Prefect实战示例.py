#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prefect 实战示例
================

这个文件包含了完整的 Prefect 使用示例，从基础到高级用法。

运行方式:
1. 直接运行: python Prefect实战示例.py
2. 部署运行: 先运行创建部署，再通过 UI 或命令行执行
"""

from prefect import task, flow, get_run_logger
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from prefect.exceptions import SKIP, FAIL
import subprocess
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
import json

# ============================================================================
# 基础示例：Task 和 Flow 的使用
# ============================================================================

@task(
    name="问候任务",
    description="向指定用户问候",
    tags=["基础", "示例"],
    retries=2,
    retry_delay_seconds=5
)
def greet_user(name: str, greeting: str = "Hello") -> str:
    """基础任务示例：问候用户"""
    logger = get_run_logger()
    
    logger.info(f"开始问候用户: {name}")
    
    # 模拟可能的失败（10% 概率）
    if random.random() < 0.1:
        logger.error("随机失败，将会重试")
        raise Exception("随机失败")
    
    message = f"{greeting}, {name}! 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    logger.info(f"问候完成: {message}")
    
    return message

@task(
    name="数据处理任务",
    description="处理数字列表",
    timeout_seconds=30
)
def process_numbers(numbers: list) -> dict:
    """数据处理任务示例"""
    logger = get_run_logger()
    
    logger.info(f"开始处理 {len(numbers)} 个数字")
    
    # 模拟处理时间
    time.sleep(1)
    
    result = {
        "count": len(numbers),
        "sum": sum(numbers),
        "average": sum(numbers) / len(numbers) if numbers else 0,
        "max": max(numbers) if numbers else None,
        "min": min(numbers) if numbers else None
    }
    
    logger.info(f"处理完成: {result}")
    return result

@flow(
    name="基础示例流程",
    description="演示基础 Task 和 Flow 用法",
    tags=["示例", "教学"]
)
def basic_example_flow():
    """基础示例流程"""
    logger = get_run_logger()
    logger.info("🚀 开始执行基础示例流程")
    
    # 串行执行任务
    greeting1 = greet_user("Alice", "Hi")
    greeting2 = greet_user("Bob", "Hello")
    
    # 处理数据
    numbers = [1, 2, 3, 4, 5, 10, 20, 30]
    stats = process_numbers(numbers)
    
    result = {
        "greetings": [greeting1, greeting2],
        "statistics": stats,
        "execution_time": datetime.now().isoformat()
    }
    
    logger.info("✅ 基础示例流程执行完成")
    return result

# ============================================================================
# 中级示例：并行执行和条件逻辑
# ============================================================================

@task
def check_file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    logger = get_run_logger()
    exists = Path(file_path).exists()
    logger.info(f"文件 {file_path} {'存在' if exists else '不存在'}")
    return exists

@task
def create_sample_file(file_path: str) -> str:
    """创建示例文件"""
    logger = get_run_logger()
    
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"示例文件\n创建时间: {datetime.now()}\n")
    
    logger.info(f"创建文件: {file_path}")
    return file_path

@task
def read_file_content(file_path: str) -> str:
    """读取文件内容"""
    logger = get_run_logger()
    
    if not Path(file_path).exists():
        logger.warning(f"文件不存在: {file_path}")
        raise SKIP(f"文件不存在，跳过读取: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    logger.info(f"读取文件成功: {len(content)} 字符")
    return content

@task
def parallel_processing_task(task_id: int, duration: int = 2) -> dict:
    """并行处理任务"""
    logger = get_run_logger()
    
    logger.info(f"任务 {task_id} 开始执行，预计耗时 {duration} 秒")
    time.sleep(duration)
    
    result = {
        "task_id": task_id,
        "duration": duration,
        "completed_at": datetime.now().isoformat(),
        "random_value": random.randint(1, 100)
    }
    
    logger.info(f"任务 {task_id} 执行完成")
    return result

@flow(
    name="中级示例流程",
    description="演示并行执行和条件逻辑",
    tags=["中级", "并行", "条件"]
)
def intermediate_example_flow():
    """中级示例流程"""
    logger = get_run_logger()
    logger.info("🚀 开始执行中级示例流程")
    
    # 条件逻辑示例
    test_file = "temp/test_file.txt"
    
    file_exists = check_file_exists(test_file)
    
    if not file_exists:
        logger.info("文件不存在，创建新文件")
        create_sample_file(test_file)
    
    # 读取文件内容
    content = read_file_content(test_file)
    
    # 并行执行示例
    logger.info("开始并行执行任务")
    parallel_tasks = []
    
    for i in range(5):
        # 使用 submit 方法并行执行
        task_future = parallel_processing_task.submit(
            task_id=i, 
            duration=random.randint(1, 3)
        )
        parallel_tasks.append(task_future)
    
    # 等待所有并行任务完成
    parallel_results = []
    for task_future in parallel_tasks:
        result = task_future.result()
        parallel_results.append(result)
    
    final_result = {
        "file_content": content,
        "parallel_results": parallel_results,
        "total_tasks": len(parallel_results),
        "execution_time": datetime.now().isoformat()
    }
    
    logger.info("✅ 中级示例流程执行完成")
    return final_result

# ============================================================================
# 高级示例：脚本执行和错误处理
# ============================================================================

@task(
    name="执行Python脚本",
    retries=2,
    retry_delay_seconds=30,
    timeout_seconds=300
)
def execute_python_script(script_path: str, args: list = None) -> dict:
    """执行Python脚本的高级任务"""
    logger = get_run_logger()
    
    if not Path(script_path).exists():
        logger.error(f"脚本文件不存在: {script_path}")
        raise FAIL(f"脚本文件不存在: {script_path}")
    
    # 构建命令
    cmd = ["python", script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"执行命令: {' '.join(cmd)}")
    
    try:
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(script_path).parent,
            timeout=300
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✅ 脚本执行成功，耗时 {execution_time:.2f} 秒")
            return {
                "success": True,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time
            }
        else:
            logger.error(f"❌ 脚本执行失败，返回码: {result.returncode}")
            logger.error(f"错误输出: {result.stderr}")
            raise Exception(f"脚本执行失败: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error(f"脚本执行超时: {script_path}")
        raise Exception(f"脚本执行超时: {script_path}")
    except Exception as e:
        logger.error(f"脚本执行异常: {str(e)}")
        raise

@task
def validate_script_output(script_result: dict) -> bool:
    """验证脚本输出"""
    logger = get_run_logger()
    
    if not script_result.get("success", False):
        logger.error("脚本执行失败，验证不通过")
        return False
    
    # 检查执行时间
    execution_time = script_result.get("execution_time", 0)
    if execution_time > 60:  # 超过1分钟
        logger.warning(f"脚本执行时间较长: {execution_time:.2f} 秒")
    
    # 检查输出内容
    stdout = script_result.get("stdout", "")
    if "error" in stdout.lower() or "exception" in stdout.lower():
        logger.warning("输出中包含错误关键词")
    
    logger.info("✅ 脚本输出验证通过")
    return True

@flow(
    name="高级示例流程",
    description="演示脚本执行和错误处理",
    tags=["高级", "脚本执行", "错误处理"]
)
def advanced_example_flow():
    """高级示例流程"""
    logger = get_run_logger()
    logger.info("🚀 开始执行高级示例流程")
    
    # 创建一个简单的测试脚本
    test_script_path = "temp/test_script.py"
    Path(test_script_path).parent.mkdir(parents=True, exist_ok=True)
    
    test_script_content = '''
import sys
import time
import random

print("测试脚本开始执行")
print(f"参数: {sys.argv[1:] if len(sys.argv) > 1 else '无参数'}")

# 模拟处理时间
time.sleep(random.uniform(0.5, 2.0))

# 模拟随机成功/失败
if random.random() < 0.8:  # 80% 成功率
    print("✅ 测试脚本执行成功")
    print("处理了一些数据...")
    sys.exit(0)
else:
    print("❌ 测试脚本执行失败")
    sys.exit(1)
'''
    
    with open(test_script_path, 'w', encoding='utf-8') as f:
        f.write(test_script_content)
    
    logger.info(f"创建测试脚本: {test_script_path}")
    
    # 执行脚本
    try:
        script_result = execute_python_script(
            script_path=test_script_path,
            args=["--test", "参数"]
        )
        
        # 验证输出
        is_valid = validate_script_output(script_result)
        
        result = {
            "script_execution": script_result,
            "validation_passed": is_valid,
            "execution_time": datetime.now().isoformat()
        }
        
        logger.info("✅ 高级示例流程执行完成")
        return result
        
    except Exception as e:
        logger.error(f"流程执行失败: {str(e)}")
        return {
            "error": str(e),
            "execution_time": datetime.now().isoformat()
        }

# ============================================================================
# 部署配置
# ============================================================================

def create_example_deployments():
    """创建示例部署"""
    deployments = []
    
    # 基础示例 - 手动执行
    basic_manual = Deployment.build_from_flow(
        flow=basic_example_flow,
        name="基础示例-手动执行",
        description="手动执行基础示例流程",
        tags=["示例", "手动", "基础"]
    )
    deployments.append(basic_manual)
    
    # 中级示例 - 定时执行（每小时）
    intermediate_scheduled = Deployment.build_from_flow(
        flow=intermediate_example_flow,
        name="中级示例-定时执行",
        description="每小时执行中级示例流程",
        tags=["示例", "定时", "中级"],
        schedule=CronSchedule(
            cron="0 * * * *",  # 每小时执行
            timezone="Asia/Shanghai"
        )
    )
    deployments.append(intermediate_scheduled)
    
    # 高级示例 - 手动执行
    advanced_manual = Deployment.build_from_flow(
        flow=advanced_example_flow,
        name="高级示例-手动执行",
        description="手动执行高级示例流程",
        tags=["示例", "手动", "高级"]
    )
    deployments.append(advanced_manual)
    
    return deployments

def deploy_examples():
    """部署所有示例"""
    print("🚀 开始部署 Prefect 示例...")
    
    deployments = create_example_deployments()
    
    for deployment in deployments:
        try:
            deployment.apply()
            print(f"✅ 部署成功: {deployment.name}")
        except Exception as e:
            print(f"❌ 部署失败: {deployment.name} - {str(e)}")
    
    print("🎉 示例部署完成!")
    print("\n📋 可用的部署:")
    for deployment in deployments:
        print(f"  - {deployment.name}")
    
    print("\n🌐 访问 UI: http://127.0.0.1:4200")
    print("📝 手动执行命令示例:")
    print('  python -m prefect deployment run "基础示例流程/基础示例-手动执行"')

# ============================================================================
# 主程序
# ============================================================================

def main():
    """主程序"""
    print("=" * 60)
    print("🎓 Prefect 实战示例")
    print("=" * 60)
    
    print("\n选择运行模式:")
    print("1. 本地测试运行")
    print("2. 创建部署")
    print("3. 运行所有示例")
    
    try:
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            print("\n🧪 本地测试运行...")
            
            print("\n--- 基础示例 ---")
            result1 = basic_example_flow()
            print(f"结果: {json.dumps(result1, indent=2, ensure_ascii=False)}")
            
            print("\n--- 中级示例 ---")
            result2 = intermediate_example_flow()
            print(f"结果: {json.dumps(result2, indent=2, ensure_ascii=False)}")
            
            print("\n--- 高级示例 ---")
            result3 = advanced_example_flow()
            print(f"结果: {json.dumps(result3, indent=2, ensure_ascii=False)}")
            
        elif choice == "2":
            print("\n📋 创建部署...")
            deploy_examples()
            
        elif choice == "3":
            print("\n🚀 运行所有示例...")
            
            # 先创建部署
            deploy_examples()
            
            print("\n等待 5 秒后开始本地测试...")
            time.sleep(5)
            
            # 再运行本地测试
            print("\n🧪 本地测试运行...")
            basic_example_flow()
            intermediate_example_flow()
            advanced_example_flow()
            
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 执行出错: {str(e)}")

if __name__ == "__main__":
    main()