"""Prefect调度器配置 - 6个定时任务
拼多多质量数据、ERP门店数据、拼多多差评数据、京东门店数据、拼多多KPI数据、拼多多KPI周报
"""

from prefect import serve
from prefect.client.schemas.schedules import CronSchedule
from prefect_flows import (
    pdd_quality_flow,
    erp_store_flow,
    pdd_badscore_flow,
    jd_store_flow, 
    pdd_kpi_flow,
    pdd_kpi_weekly_flow
)
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('d:/testyd/prefect_scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_deployments():
    """创建Prefect部署配置 - 独立流程调度"""
    
    deployments = []
    
    # ==================== 定时调度任务 ====================
    
    # 1. 拼多多质量数据 - 每天08:00 (第一个执行)
    pdd_quality_deployment = pdd_quality_flow.to_deployment(
        name="拼多多质量数据-定时执行",
        schedule=CronSchedule(cron="0 8 * * *", timezone="Asia/Shanghai"),
        description="每天08:00执行拼多多质量数据拉取",
        tags=["数据拉取", "拼多多", "质量", "定时"]
    )
    deployments.append(pdd_quality_deployment)
    
    # 2. ERP门店数据 - 每天08:30 (第二个执行)
    erp_deployment = erp_store_flow.to_deployment(
        name="ERP门店数据-定时执行",
        schedule=CronSchedule(cron="30 8 * * *", timezone="Asia/Shanghai"),
        description="每天08:30执行ERP门店数据拉取",
        tags=["数据拉取", "ERP", "门店", "定时"]
    )
    deployments.append(erp_deployment)
    
    # 3. 拼多多差评数据 - 每天09:00 (第三个执行)
    pdd_badscore_deployment = pdd_badscore_flow.to_deployment(
        name="拼多多差评数据-定时执行",
        schedule=CronSchedule(cron="0 9 * * *", timezone="Asia/Shanghai"),
        description="每天09:00执行拼多多差评数据拉取",
        tags=["数据拉取", "拼多多", "差评", "定时"]
    )
    deployments.append(pdd_badscore_deployment)
    
    # 4. 京东门店数据 - 每天09:30
    jd_deployment = jd_store_flow.to_deployment(
        name="京东门店数据-定时执行",
        schedule=CronSchedule(cron="45 8 * * *", timezone="Asia/Shanghai"),
        description="每天08:45执行京东门店数据拉取",
        tags=["数据拉取", "京东", "门店", "定时"]
    )
    deployments.append(jd_deployment)
    
    # 5. 拼多多KPI数据 - 每天12:00
    pdd_kpi_deployment = pdd_kpi_flow.to_deployment(
        name="拼多多KPI数据-定时执行",
        schedule=CronSchedule(cron="0 12 * * *", timezone="Asia/Shanghai"),
        description="每天12:00执行拼多多KPI数据拉取",
        tags=["数据拉取", "拼多多", "KPI", "定时"]
    )
    deployments.append(pdd_kpi_deployment)
    
    # 6. 拼多多KPI周报数据 - 每周六11:00
    pdd_kpi_weekly_deployment = pdd_kpi_weekly_flow.to_deployment(
        name="拼多多KPI周报-定时执行",
        schedule=CronSchedule(cron="0 11 * * 6", timezone="Asia/Shanghai"),
        description="每周六11:00执行拼多多KPI周报数据拉取",
        tags=["数据拉取", "拼多多", "KPI", "周报", "定时"]
    )
    deployments.append(pdd_kpi_weekly_deployment)
    
    return deployments

def main():
    """启动Prefect调度服务"""
    logger.info("=" * 60)
    logger.info("Prefect 6个定时任务调度器启动")
    logger.info("=" * 60)
    
    # 创建部署
    deployments = create_deployments()
    
    logger.info("调度配置 (串行执行):")
    logger.info("  定时任务:")
    logger.info("    - 拼多多质量数据: 每天08:00 (第1个)")
    logger.info("    - ERP门店数据: 每天08:30 (第2个)")
    logger.info("    - 拼多多差评数据: 每天09:00 (第3个)")
    logger.info("    - 京东门店数据: 每天08:45 (第4个)")
    logger.info("    - 拼多多KPI数据: 每天12:00 (第5个)")
    logger.info("    - 拼多多KPI周报: 每周六11:00 (第6个)")
    logger.info("")
    logger.info("串行执行说明:")
    logger.info("  - 每个任务间隔30分钟，确保前一个任务完成后再执行下一个")
    logger.info("  - 避免资源冲突和数据竞争")
    logger.info("  - 可通过Prefect UI监控每个任务的执行状态")
    logger.info("")
    logger.info("可视化界面: http://127.0.0.1:4200")
    logger.info("=" * 60)
    
    try:
        # 启动服务
        serve(*deployments, limit=10)
    except KeyboardInterrupt:
        logger.info("Prefect调度器已停止")
    except Exception as e:
        logger.error(f"调度器运行异常: {str(e)}")
        import traceback
        logger.error(f"异常详情: {traceback.format_exc()}")

if __name__ == "__main__":
    main()