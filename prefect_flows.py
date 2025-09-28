"""
Prefect工作流 - 数据拉取任务调度
每个Python脚本对应一个独立的flow，调度清晰，按时间执行
"""

import subprocess
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from prefect import flow, task
from prefect.task_runners import ConcurrentTaskRunner
from prefect.logging import get_run_logger
import sys
import os

# 设置编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

@task(name="执行脚本", retries=3, retry_delay_seconds=60)
def execute_script(script_path: str, task_name: str, timeout: int = 3600):
    """执行Python脚本任务"""
    logger = get_run_logger()
    
    if not Path(script_path).exists():
        logger.error(f"脚本文件不存在: {script_path}")
        raise FileNotFoundError(f"脚本文件不存在: {script_path}")
    
    logger.info(f"开始执行 {task_name}")
    logger.info(f"脚本路径: {script_path}")
    logger.info(f"超时设置: {timeout/60} 分钟")
    
    start_time = datetime.now()
    
    try:
        # 执行脚本，使用utf-8编码处理中文和Unicode字符
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',  # 使用utf-8编码处理中文和Unicode字符
            errors='replace',  # 替换无法编码的字符，避免程序崩溃
            timeout=timeout,
            cwd=Path(script_path).parent
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        if result.returncode == 0:
            logger.info(f"[成功] {task_name} 执行成功，耗时: {duration}")
            if result.stdout:
                logger.info(f"输出信息: {result.stdout[-500:]}")  # 只显示最后500字符
            return True
        else:
            logger.error(f"[错误] {task_name} 执行失败，返回码: {result.returncode}")
            if result.stderr:
                logger.error(f"错误输出: {result.stderr}")
            if result.stdout:
                logger.error(f"标准输出: {result.stdout}")
            raise RuntimeError(f"{task_name} 执行失败")
            
    except subprocess.TimeoutExpired:
        logger.error(f"[错误] {task_name} 执行超时（{timeout/60}分钟）")
        raise TimeoutError(f"{task_name} 执行超时")
    except Exception as e:
        logger.error(f"[错误] {task_name} 执行时发生异常: {str(e)}")
        raise

# ==================== 独立的数据流 ====================

@flow(name="拼多多质量数据流")
def pdd_quality_flow():
    """拼多多质量数据拉取流程"""
    logger = get_run_logger()
    logger.info("开始执行拼多多质量数据拉取任务")
    
    result = execute_script("pdd_quality.py", "拼多多质量数据拉取")
    
    if result:
        logger.info("拼多多质量数据拉取任务完成")
    else:
        logger.error("拼多多质量数据拉取任务失败")
    
    return result

@flow(name="ERP门店数据流")
def erp_store_flow():
    """ERP门店数据拉取流程"""
    logger = get_run_logger()
    logger.info("开始执行ERP门店数据拉取任务")
    
    result = execute_script("erp_store.py", "ERP门店数据拉取")
    
    if result:
        logger.info("ERP门店数据拉取任务完成")
    else:
        logger.error("ERP门店数据拉取任务失败")
    
    return result

@flow(name="拼多多差评数据流")
def pdd_badscore_flow():
    """拼多多差评数据拉取流程"""
    logger = get_run_logger()
    logger.info("开始执行拼多多差评数据拉取任务")
    
    result = execute_script("pdd_badscore.py", "拼多多差评数据拉取")
    
    if result:
        logger.info("拼多多差评数据拉取任务完成")
    else:
        logger.error("拼多多差评数据拉取任务失败")
    
    return result

@flow(name="京东门店数据流")
def jd_store_flow():
    """京东门店数据拉取流程"""
    logger = get_run_logger()
    logger.info("开始执行京东门店数据拉取任务")
    
    result = execute_script("jd_store.py", "京东门店数据拉取")
    
    if result:
        logger.info("京东门店数据拉取任务完成")
    else:
        logger.error("京东门店数据拉取任务失败")
    
    return result

@flow(name="拼多多KPI数据流")
def pdd_kpi_flow():
    """拼多多KPI数据拉取流程"""
    logger = get_run_logger()
    logger.info("开始执行拼多多KPI数据拉取任务")
    
    result = execute_script("pdd_kpi.py", "拼多多KPI数据拉取")
    
    if result:
        logger.info("拼多多KPI数据拉取任务完成")
    else:
        logger.error("拼多多KPI数据拉取任务失败")
    
    return result

@flow(name="拼多多聊天数据流")
def pdd_chat_flow():
    """拼多多聊天数据拉取流程"""
    logger = get_run_logger()
    logger.info("开始执行拼多多聊天数据拉取任务")
    
    result = execute_script("pdd_chat.py", "拼多多聊天数据拉取")
    
    if result:
        logger.info("拼多多聊天数据拉取任务完成")
    else:
        logger.error("拼多多聊天数据拉取任务失败")
    
    return result

@flow(name="拼多多KPI周报数据流")
def pdd_kpi_weekly_flow():
    """拼多多KPI周报数据拉取流程"""
    logger = get_run_logger()
    logger.info("开始执行拼多多KPI周报数据拉取任务")
    
    result = execute_script("pdd_kpi_weekly.py", "拼多多KPI周报数据拉取")
    
    if result:
        logger.info("拼多多KPI周报数据拉取任务完成")
    else:
        logger.error("拼多多KPI周报数据拉取任务失败")
    
    return result

if __name__ == "__main__":
    # 测试单个流程
    print("可用的数据流:")
    print("1. pdd_quality_flow() - 拼多多质量数据流")
    print("2. erp_store_flow() - ERP门店数据流")
    print("3. pdd_badscore_flow() - 拼多多差评数据流")
    print("4. jd_store_flow() - 京东门店数据流")
    print("5. pdd_kpi_flow() - 拼多多KPI数据流")
    print("6. pdd_chat_flow() - 拼多多聊天数据流")
    print("7. pdd_kpi_weekly_flow() - 拼多多KPI周报数据流")