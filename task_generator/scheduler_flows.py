# -*- coding: utf-8 -*-
"""
通用任务调度流 - 可扩展的Prefect工作流
支持所有数据拉取任务的调度和监控
"""

import subprocess
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from prefect import flow, task
from prefect.logging import get_run_logger
import sys
import os

# 设置编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

@task(name="执行脚本", retries=2, retry_delay_seconds=300)
def execute_script(script_path: str, task_name: str, timeout: int = 3600, cwd: str = None):
    """
    执行Python脚本任务
    
    Args:
        script_path: 脚本路径（相对于工作目录）
        task_name: 任务名称
        timeout: 超时时间（秒）
        cwd: 工作目录（默认为脚本所在目录）
    
    Returns:
        bool: 执行是否成功
    """
    logger = get_run_logger()
    
    # 确定工作目录
    if cwd is None:
        if os.path.isabs(script_path):
            cwd = str(Path(script_path).parent)
        else:
            cwd = str(Path('D:/testyd') / Path(script_path).parent)
    
    # 确定完整脚本路径
    if not os.path.isabs(script_path):
        full_script_path = str(Path('D:/testyd') / script_path)
    else:
        full_script_path = script_path
    
    if not Path(full_script_path).exists():
        logger.error(f"脚本文件不存在: {full_script_path}")
        raise FileNotFoundError(f"脚本文件不存在: {full_script_path}")
    
    logger.info(f"开始执行 {task_name}")
    logger.info(f"脚本路径: {full_script_path}")
    logger.info(f"工作目录: {cwd}")
    logger.info(f"超时设置: {timeout/60} 分钟")
    
    start_time = datetime.now()
    
    try:
        # 执行脚本，使用utf-8编码处理中文和Unicode字符
        result = subprocess.run(
            [sys.executable, full_script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            cwd=cwd
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        if result.returncode == 0:
            logger.info(f"[成功] {task_name} 执行成功，耗时: {duration}")
            if result.stdout:
                # 只显示最后1000字符
                output = result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout
                logger.info(f"输出信息: {output}")
            return True
        else:
            logger.error(f"[错误] {task_name} 执行失败，返回码: {result.returncode}")
            if result.stderr:
                logger.error(f"错误输出: {result.stderr[-1000:]}")
            if result.stdout:
                logger.error(f"标准输出: {result.stdout[-1000:]}")
            raise RuntimeError(f"{task_name} 执行失败")
            
    except subprocess.TimeoutExpired:
        logger.error(f"[错误] {task_name} 执行超时（{timeout/60}分钟）")
        raise TimeoutError(f"{task_name} 执行超时")
    except Exception as e:
        logger.error(f"[错误] {task_name} 执行时发生异常: {str(e)}")
        raise

# ==================== PDD任务流 ====================

@flow(name="统一任务生成流-每日")
def unified_task_generation_daily_flow():
    """统一任务生成流程（每日）- 每天00:05执行，为所有平台生成每日任务"""
    logger = get_run_logger()
    logger.info("开始执行统一任务生成（每日）")

    # 直接调用Python模块
    try:
        import sys
        sys.path.insert(0, 'D:/testyd')
        from task_generator.generate_all_tasks import generate_all_tasks_by_schedule, print_summary

        # 生成所有平台的每日任务
        results = generate_all_tasks_by_schedule('daily')

        # 统计成功数
        total_success = sum(
            1
            for platform_results in results.values()
            for r in platform_results.values()
            if r['success']
        )
        total_tasks = sum(len(platform_results) for platform_results in results.values())

        logger.info(f"统一任务生成完成（每日）: {total_success}/{total_tasks} 成功")

        return total_success == total_tasks

    except Exception as e:
        logger.error(f"统一任务生成失败（每日）: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

@flow(name="统一任务生成流-每周")
def unified_task_generation_weekly_flow():
    """统一任务生成流程（每周）- 每周六00:10执行，为所有平台生成周度任务"""
    logger = get_run_logger()
    logger.info("开始执行统一任务生成（每周）")

    try:
        import sys
        sys.path.insert(0, 'D:/testyd')
        from task_generator.generate_all_tasks import generate_all_tasks_by_schedule

        # 生成所有平台的周度任务
        results = generate_all_tasks_by_schedule('weekly')

        # 统计成功数
        total_success = sum(
            1
            for platform_results in results.values()
            for r in platform_results.values()
            if r['success']
        )
        total_tasks = sum(len(platform_results) for platform_results in results.values())

        logger.info(f"统一任务生成完成（每周）: {total_success}/{total_tasks} 成功")

        return total_success == total_tasks

    except Exception as e:
        logger.error(f"统一任务生成失败（每周）: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

@flow(name="统一任务生成流-每月")
def unified_task_generation_monthly_flow():
    """统一任务生成流程（每月）- 每月1号00:15执行，为所有平台生成月度任务"""
    logger = get_run_logger()
    logger.info("开始执行统一任务生成（每月）")

    try:
        import sys
        sys.path.insert(0, 'D:/testyd')
        from task_generator.generate_all_tasks import generate_all_tasks_by_schedule

        # 生成所有平台的月度任务
        results = generate_all_tasks_by_schedule('monthly')

        # 统计成功数
        total_success = sum(
            1
            for platform_results in results.values()
            for r in platform_results.values()
            if r['success']
        )
        total_tasks = sum(len(platform_results) for platform_results in results.values())

        logger.info(f"统一任务生成完成（每月）: {total_success}/{total_tasks} 成功")

        return total_success == total_tasks

    except Exception as e:
        logger.error(f"统一任务生成失败（每月）: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

@flow(name="PDD质量数据流")
def pdd_quality_flow():
    """PDD质量数据拉取流程 - 每天08:00执行"""
    logger = get_run_logger()
    logger.info("开始执行PDD质量数据拉取任务")
    
    result = execute_script(
        "pdd/pdd_quality.py",
        "PDD质量数据拉取",
        timeout=3600
    )
    
    if result:
        logger.info("PDD质量数据拉取任务完成")
    else:
        logger.error("PDD质量数据拉取任务失败")
    
    return result

@flow(name="PDD差评数据流")
def pdd_badscore_flow():
    """PDD差评数据拉取流程 - 每天08:30执行"""
    logger = get_run_logger()
    logger.info("开始执行PDD差评数据拉取任务")
    
    result = execute_script(
        "pdd/pdd_badscore.py",
        "PDD差评数据拉取",
        timeout=3600
    )
    
    if result:
        logger.info("PDD差评数据拉取任务完成")
    else:
        logger.error("PDD差评数据拉取任务失败")
    
    return result

@flow(name="PDD聊天数据流")
def pdd_chat_flow():
    """PDD聊天数据拉取流程 - 每天09:00执行"""
    logger = get_run_logger()
    logger.info("开始执行PDD聊天数据拉取任务")
    
    result = execute_script(
        "pdd/pdd_chat.py",
        "PDD聊天数据拉取",
        timeout=3600
    )
    
    if result:
        logger.info("PDD聊天数据拉取任务完成")
    else:
        logger.error("PDD聊天数据拉取任务失败")
    
    return result

@flow(name="PDDKPI数据流")
def pdd_kpi_flow():
    """PDDKPI数据拉取流程 - 每天11:00执行"""
    logger = get_run_logger()
    logger.info("开始执行PDDKPI数据拉取任务")
    
    result = execute_script(
        "pdd/pdd_kpi.py",
        "PDDKPI数据拉取",
        timeout=3600
    )
    
    if result:
        logger.info("PDDKPI数据拉取任务完成")
    else:
        logger.error("PDDKPI数据拉取任务失败")
    
    return result

@flow(name="PDDKPI周报数据流")
def pdd_kpi_weekly_flow():
    """PDDKPI周报数据拉取流程 - 每周六12:00执行"""
    logger = get_run_logger()
    logger.info("开始执行PDDKPI周报数据拉取任务")
    
    result = execute_script(
        "pdd/pdd_kpi_weekly.py",
        "PDDKPI周报数据拉取",
        timeout=3600
    )
    
    if result:
        logger.info("PDDKPI周报数据拉取任务完成")
    else:
        logger.error("PDDKPI周报数据拉取任务失败")
    
    return result

@flow(name="PDDKPI月报数据流")
def pdd_kpi_monthly_flow():
    """PDDKPI月报数据拉取流程 - 每月3号12:30执行"""
    logger = get_run_logger()
    logger.info("开始执行PDDKPI月报数据拉取任务")
    
    result = execute_script(
        "pdd/pdd_kpi_monthly.py",
        "PDDKPI月报数据拉取",
        timeout=3600
    )
    
    if result:
        logger.info("PDDKPI月报数据拉取任务完成")
    else:
        logger.error("PDDKPI月报数据拉取任务失败")
    
    return result

# ==================== 天猫平台任务流 ====================

@flow(name="天猫Cookie获取流")
def tm_cookie_flow():
    """天猫Cookie获取流程 - 每天07:00执行"""
    logger = get_run_logger()
    logger.info("开始执行天猫Cookie获取任务")

    result = execute_script(
        "tm/get_tm_cookies.py",
        "天猫Cookie获取",
        timeout=3600
    )

    if result:
        logger.info("天猫Cookie获取任务完成")
    else:
        logger.error("天猫Cookie获取任务失败")

    return result

@flow(name="天猫差评数据流")
def tm_badscore_flow():
    """天猫差评数据拉取流程 - 每天07:20执行"""
    logger = get_run_logger()
    logger.info("开始执行天猫差评数据拉取任务")

    result = execute_script(
        "tm/tm_badscore.py",
        "天猫差评数据拉取",
        timeout=3600
    )

    if result:
        logger.info("天猫差评数据拉取任务完成")
    else:
        logger.error("天猫差评数据拉取任务失败")

    return result

@flow(name="天猫聊天数据流")
def tm_chat_flow():
    """天猫聊天数据拉取流程 - 每天07:20执行"""
    logger = get_run_logger()
    logger.info("开始执行天猫聊天数据拉取任务")

    result = execute_script(
        "tm/tm_chat.py",
        "天猫聊天数据拉取",
        timeout=3600
    )

    if result:
        logger.info("天猫聊天数据拉取任务完成")
    else:
        logger.error("天猫聊天数据拉取任务失败")

    return result

@flow(name="天猫KPI数据流")
def tm_kpi_flow():
    """天猫KPI数据拉取流程 - 每天11:30执行"""
    logger = get_run_logger()
    logger.info("开始执行天猫KPI数据拉取任务")

    result = execute_script(
        "tm/tm_kpi.py",
        "天猫KPI数据拉取",
        timeout=3600
    )

    if result:
        logger.info("天猫KPI数据拉取任务完成")
    else:
        logger.error("天猫KPI数据拉取任务失败")

    return result

# ==================== 其他平台任务流 ====================

@flow(name="ERP门店数据流")
def erp_store_flow():
    """ERP门店数据拉取流程 - 每天07:00执行"""
    logger = get_run_logger()
    logger.info("开始执行ERP门店数据拉取任务")
    
    result = execute_script(
        "erp_store.py",
        "ERP门店数据拉取",
        timeout=3600
    )
    
    if result:
        logger.info("ERP门店数据拉取任务完成")
    else:
        logger.error("ERP门店数据拉取任务失败")
    
    return result

@flow(name="京东门店数据流")
def jd_store_flow():
    """京东门店数据拉取流程 - 每天07:30执行"""
    logger = get_run_logger()
    logger.info("开始执行京东门店数据拉取任务")
    
    result = execute_script(
        "jd_store.py",
        "京东门店数据拉取",
        timeout=3600
    )
    
    if result:
        logger.info("京东门店数据拉取任务完成")
    else:
        logger.error("京东门店数据拉取任务失败")
    
    return result

if __name__ == "__main__":
    # 测试单个流程
    print("可用的数据流:")
    print("1. pdd_generate_tasks_flow() - PDD任务生成流")
    print("2. pdd_quality_flow() - PDD质量数据流")
    print("3. pdd_badscore_flow() - PDD差评数据流")
    print("4. pdd_chat_flow() - PDD聊天数据流")
    print("5. pdd_kpi_flow() - PDDKPI数据流")
    print("6. pdd_kpi_weekly_flow() - PDDKPI周报数据流")
    print("7. pdd_kpi_monthly_flow() - PDDKPI月报数据流")
    print("8. erp_store_flow() - ERP门店数据流")
    print("9. jd_store_flow() - 京东门店数据流")

