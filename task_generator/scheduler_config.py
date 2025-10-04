# -*- coding: utf-8 -*-
"""
任务调度配置 - 集中管理所有定时任务
新增任务只需在此文件添加配置即可
"""
import sys
sys.path.append(r'D:\testyd\task_generator')

from prefect import serve
from prefect.client.schemas.schedules import CronSchedule
from scheduler_flows import (
    unified_task_generation_daily_flow,
    unified_task_generation_weekly_flow,
    unified_task_generation_monthly_flow,
    pdd_quality_flow,
    pdd_badscore_flow,
    pdd_chat_flow,
    pdd_kpi_flow,
    pdd_kpi_weekly_flow,
    pdd_kpi_monthly_flow,
    tm_cookie_flow,
    tm_badscore_flow,
    tm_chat_flow,
    tm_kpi_flow,
    erp_store_flow,
    jd_store_flow
)
import logging

# 配置日志 - 确保日志文件可以正常写入
log_file = 'd:/testyd/task_generator/scheduler.log'
try:
    # 确保日志目录存在
    import os
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='a'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # 强制重新配置
    )
except Exception as e:
    print(f"警告: 无法配置日志文件 {log_file}: {e}")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )

logger = logging.getLogger(__name__)

# ==================== 任务配置 ====================

TASK_CONFIGS = [
    {
        'flow': unified_task_generation_daily_flow,
        'name': '统一任务生成-每日',
        'cron': '5 0 * * *',  # 每天00:05
        'description': '每天00:05为所有平台生成每日待执行任务',
        'tags': ['任务生成', '每日', '定时'],
        'enabled': True
    },
    {
        'flow': unified_task_generation_weekly_flow,
        'name': '统一任务生成-每周',
        'cron': '10 0 * * 6',  # 每周六00:10
        'description': '每周六00:10为所有平台生成周度待执行任务',
        'tags': ['任务生成', '每周', '定时'],
        'enabled': True
    },
    {
        'flow': unified_task_generation_monthly_flow,
        'name': '统一任务生成-每月',
        'cron': '15 0 1 * *',  # 每月1号00:15
        'description': '每月1号00:15为所有平台生成月度待执行任务',
        'tags': ['任务生成', '每月', '定时'],
        'enabled': True
    },
    {
        'flow': tm_cookie_flow,
        'name': '天猫Cookie获取-定时执行',
        'cron': '0 7 * * *',  # 每天07:00
        'description': '每天07:00执行天猫Cookie获取',
        'tags': ['天猫', 'Cookie', '定时'],
        'enabled': True
    },
    {
        'flow': erp_store_flow,
        'name': 'ERP门店数据-定时执行',
        'cron': '0 7 * * *',  # 每天07:00
        'description': '每天07:00执行ERP门店数据拉取',
        'tags': ['ERP', '门店', '定时'],
        'enabled': True
    },
    {
        'flow': tm_badscore_flow,
        'name': '天猫差评数据-定时执行',
        'cron': '20 7 * * *',  # 每天07:20
        'description': '每天07:20执行天猫差评数据拉取',
        'tags': ['天猫', '差评', '定时'],
        'enabled': True
    },
    {
        'flow': tm_chat_flow,
        'name': '天猫聊天数据-定时执行',
        'cron': '20 7 * * *',  # 每天07:20
        'description': '每天07:20执行天猫聊天数据拉取',
        'tags': ['天猫', '聊天', '定时'],
        'enabled': True
    },
    {
        'flow': jd_store_flow,
        'name': '京东门店数据-定时执行',
        'cron': '30 7 * * *',  # 每天07:30
        'description': '每天07:30执行京东门店数据拉取',
        'tags': ['京东', '门店', '定时'],
        'enabled': True
    },
    {
        'flow': pdd_quality_flow,
        'name': 'PDD质量数据-定时执行',
        'cron': '0 8 * * *',  # 每天08:00
        'description': '每天08:00执行PDD质量数据拉取',
        'tags': ['PDD', '质量', '定时'],
        'enabled': True
    },
    {
        'flow': pdd_badscore_flow,
        'name': 'PDD差评数据-定时执行',
        'cron': '30 8 * * *',  # 每天08:30
        'description': '每天08:30执行PDD差评数据拉取',
        'tags': ['PDD', '差评', '定时'],
        'enabled': True
    },
    {
        'flow': pdd_chat_flow,
        'name': 'PDD聊天数据-定时执行',
        'cron': '0 9 * * *',  # 每天09:00
        'description': '每天09:00执行PDD聊天数据拉取',
        'tags': ['PDD', '聊天', '定时'],
        'enabled': False  # 待实现，暂时禁用
    },
    {
        'flow': pdd_kpi_flow,
        'name': 'PDDKPI数据-定时执行',
        'cron': '0 11 * * *',  # 每天11:00
        'description': '每天11:00执行PDDKPI数据拉取',
        'tags': ['PDD', 'KPI', '定时'],
        'enabled': True
    },
    {
        'flow': tm_kpi_flow,
        'name': '天猫KPI数据-定时执行',
        'cron': '30 11 * * *',  # 每天11:30
        'description': '每天11:30执行天猫KPI数据拉取',
        'tags': ['天猫', 'KPI', '定时'],
        'enabled': True
    },
    {
        'flow': pdd_kpi_weekly_flow,
        'name': 'PDDKPI周报-定时执行',
        'cron': '0 12 * * 6',  # 每周六12:00
        'description': '每周六12:00执行PDDKPI周报数据拉取',
        'tags': ['PDD', 'KPI', '周报', '定时'],
        'enabled': True  # 已启用
    },
    {
        'flow': pdd_kpi_monthly_flow,
        'name': 'PDDKPI月报-定时执行',
        'cron': '30 12 3 * *',  # 每月3号12:30
        'description': '每月3号12:30执行PDDKPI月报数据拉取',
        'tags': ['PDD', 'KPI', '月报', '定时'],
        'enabled': True  # 已启用
    }
]

def create_deployments():
    """
    创建Prefect部署配置

    Returns:
        list: 部署配置列表
    """
    deployments = []

    for config in TASK_CONFIGS:
        if not config.get('enabled', True):
            logger.info(f"跳过禁用的任务: {config['name']}")
            continue

        try:
            deployment = config['flow'].to_deployment(
                name=config['name'],
                schedule=CronSchedule(cron=config['cron'], timezone="Asia/Shanghai"),
                description=config['description'],
                tags=config['tags']
                # 移除 work_pool_name 参数，served deployments 不需要它
            )
            deployments.append(deployment)
            logger.info(f"✓ 添加任务: {config['name']} - {config['cron']}")
        except Exception as e:
            logger.error(f"✗ 创建任务失败 {config['name']}: {e}")
            import traceback
            logger.error(traceback.format_exc())

    return deployments

def print_schedule_info():
    """打印调度信息"""
    logger.info("=" * 80)
    logger.info("任务调度系统启动")
    logger.info("=" * 80)
    logger.info("")
    logger.info("已启用的定时任务:")
    logger.info("")
    
    enabled_tasks = [c for c in TASK_CONFIGS if c.get('enabled', True)]
    
    for i, config in enumerate(enabled_tasks, 1):
        logger.info(f"  {i}. {config['name']}")
        logger.info(f"     调度时间: {config['cron']}")
        logger.info(f"     说明: {config['description']}")
        logger.info("")
    
    logger.info(f"总计: {len(enabled_tasks)} 个启用任务")
    logger.info("")
    logger.info("禁用的任务:")
    
    disabled_tasks = [c for c in TASK_CONFIGS if not c.get('enabled', True)]
    for config in disabled_tasks:
        logger.info(f"  - {config['name']} (待实现)")
    
    logger.info("")
    logger.info("可视化界面: http://127.0.0.1:4200")
    logger.info("日志文件: d:/testyd/task_generator/scheduler.log")
    logger.info("=" * 80)

def main():
    """启动Prefect调度服务"""
    try:
        logger.info("=" * 80)
        logger.info("🚀 任务调度系统正在启动...")
        logger.info("=" * 80)

        # 打印调度信息
        print_schedule_info()

        # 创建部署
        logger.info("📋 正在创建任务部署...")
        deployments = create_deployments()

        if not deployments:
            logger.error("❌ 没有启用的任务，退出")
            return

        logger.info(f"✓ 成功创建 {len(deployments)} 个任务部署")
        logger.info("")

        # 启动服务
        logger.info("🔄 正在启动调度服务...")
        logger.info("   服务将在后台持续运行，按 Ctrl+C 可停止")
        logger.info("=" * 80)
        logger.info("")

        # 刷新输出缓冲区
        sys.stdout.flush()
        sys.stderr.flush()

        serve(*deployments, limit=10)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 80)
        logger.info("⏹️  调度器已停止（用户中断）")
        logger.info("=" * 80)
    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error(f"❌ 调度器运行异常: {str(e)}")
        logger.error("=" * 80)
        import traceback
        logger.error(f"异常详情:\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()

