"""
Prefect调度器清理脚本 - 只保留定时调度，移除手动执行
"""

import subprocess
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from prefect import flow, task, serve
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
        execution_time = (end_time - start_time).total_seconds()
        
        if result.returncode == 0:
            logger.info(f"{task_name} 执行成功，耗时 {execution_time:.2f} 秒")
            if result.stdout:
                logger.info(f"输出: {result.stdout}")
            return True
        else:
            logger.error(f"{task_name} 执行失败，返回码: {result.returncode}")
            if result.stderr:
                logger.error(f"错误输出: {result.stderr}")
            if result.stdout:
                logger.info(f"标准输出: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"{task_name} 执行超时 ({timeout/60} 分钟)")
        return False
    except Exception as e:
        logger.error(f"{task_name} 执行异常: {str(e)}")
        return False

# 定义各个数据流
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
    # 使用新的serve方法创建定时调度
    print("启动Prefect定时调度服务...")
    
    # 定义调度时间 - 使用Interval调度
    from datetime import timedelta, datetime
    from prefect.schedules import Interval
    
    # 创建serve配置
    serve_configs = []
    
    # ERP店铺数据 - 每天8:30
    serve_configs.append(
        erp_store_flow.to_deployment(
            name="ERP店铺数据-定时执行",
            schedule=Interval(
                timedelta(days=1),  # 第一个参数是interval
                anchor_date=datetime(2025, 1, 27, 8, 30),  # 今天8:30开始
                timezone="Asia/Shanghai"
            )
        )
    )
    
    # 京东门店数据 - 每天9:30
    serve_configs.append(
        jd_store_flow.to_deployment(
            name="京东门店数据-定时执行",
            schedule=Interval(
                timedelta(days=1),  # 第一个参数是interval
                anchor_date=datetime(2025, 1, 27, 9, 30),  # 今天9:30开始
                timezone="Asia/Shanghai"
            )
        )
    )
    
    # 拼多多KPI - 每天12:00
    serve_configs.append(
        pdd_kpi_flow.to_deployment(
            name="拼多多KPI-定时执行",
            schedule=Interval(
                timedelta(days=1),  # 第一个参数是interval
                anchor_date=datetime(2025, 1, 27, 12, 0),  # 今天12:00开始
                timezone="Asia/Shanghai"
            )
        )
    )
    
    # 拼多多质量数据 - 每天14:00
    serve_configs.append(
        pdd_quality_flow.to_deployment(
            name="拼多多质量数据-定时执行",
            schedule=Interval(
                timedelta(days=1),  # 第一个参数是interval
                anchor_date=datetime(2025, 1, 27, 14, 0),  # 今天14:00开始
                timezone="Asia/Shanghai"
            )
        )
    )
    
    # 拼多多差评数据 - 每天16:00
    serve_configs.append(
        pdd_badscore_flow.to_deployment(
            name="拼多多差评数据-定时执行",
            schedule=Interval(
                timedelta(days=1),  # 第一个参数是interval
                anchor_date=datetime(2025, 1, 27, 16, 0),  # 今天16:00开始
                timezone="Asia/Shanghai"
            )
        )
    )
    
    # 拼多多KPI周报 - 每周六10:00
    serve_configs.append(
        pdd_kpi_weekly_flow.to_deployment(
            name="拼多多KPI周报-定时执行",
            schedule=Interval(
                timedelta(weeks=1),  # 每周执行
                anchor_date=datetime(2025, 2, 1, 10, 0),  # 下个周六10:00开始
                timezone="Asia/Shanghai"
            )
        )
    )
    
    # 启动服务
    serve(*serve_configs)