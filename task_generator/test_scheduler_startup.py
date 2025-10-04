# -*- coding: utf-8 -*-
"""
测试调度器启动问题
"""
import sys
sys.path.append(r'D:\testyd\task_generator')

print("=" * 80)
print("Step 1: 测试导入模块...")
print("=" * 80)

try:
    from prefect import serve
    from prefect.client.schemas.schedules import CronSchedule
    print("✓ Prefect 模块导入成功")
except Exception as e:
    print(f"✗ Prefect 模块导入失败: {e}")
    sys.exit(1)

try:
    from scheduler_flows import unified_task_generation_daily_flow
    print("✓ scheduler_flows 导入成功")
except Exception as e:
    print(f"✗ scheduler_flows 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("Step 2: 测试创建单个 deployment...")
print("=" * 80)

try:
    print("创建 deployment 对象...")
    deployment = unified_task_generation_daily_flow.to_deployment(
        name="测试任务",
        schedule=CronSchedule(cron="0 0 * * *", timezone="Asia/Shanghai"),
        description="测试任务描述",
        tags=["测试"]
    )
    print("✓ Deployment 创建成功")
    print(f"  名称: {deployment.name}")
except Exception as e:
    print(f"✗ Deployment 创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("Step 3: 测试 serve 函数（5秒后自动退出）...")
print("=" * 80)

import threading
import time

def timeout_exit():
    time.sleep(5)
    print("\n⏰ 5秒超时，强制退出")
    import os
    os._exit(0)

# 启动超时线程
timer = threading.Thread(target=timeout_exit, daemon=True)
timer.start()

try:
    print("调用 serve()...")
    serve(deployment, limit=1)
except KeyboardInterrupt:
    print("✓ 被中断（正常）")
except Exception as e:
    print(f"✗ serve() 执行失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

