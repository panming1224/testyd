# -*- coding: utf-8 -*-
"""
拼多多爬虫任务配置文件
新增爬虫只需在这里添加配置即可
"""
from datetime import datetime, timedelta

# 爬虫任务配置
CRAWLER_TASKS = {
    'badscore': {
        'name': '差评数据采集',
        'script': 'pdd_badscore.py',
        'status_field': 'badsscore_status',  # 注意：数据库字段名是两个s
        'schedule': 'daily',  # daily/weekly/monthly
        'date_offset': -1,  # T-1（昨天）
        'minio_path': 'ods/pdd/pdd_badscore',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_badscore',
        'enabled': True
    },
    'quality': {
        'name': '产品质量数据采集',
        'script': 'pdd_quality.py',
        'status_field': 'quality_status',
        'schedule': 'daily',
        'date_offset': 0,  # T（今天）
        'minio_path': 'ods/pdd/pdd_quality',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_quality',
        'enabled': True
    },
    'kpi_days': {
        'name': '客服绩效数据采集（日度）',
        'script': 'pdd_kpi.py',
        'status_field': 'kpi_days_status',
        'schedule': 'daily',
        'date_offset': -3,  # T-3（3天前）
        'minio_path': 'ods/pdd/pdd_kpi_days',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_kpi_days',
        'enabled': True
    },
    'chat': {
        'name': '聊天数据采集',
        'script': 'pdd_chat.py',
        'status_field': 'chat_status',
        'schedule': 'daily',
        'date_offset': -1,  # T-1（昨天）
        'minio_path': 'ods/pdd/pdd_chat',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_chat',
        'enabled': True
    },
    'kpi_weekly': {
        'name': '客服绩效数据采集（周度）',
        'script': 'pdd_kpi_weekly.py',
        'status_field': 'kpi_weekly_status',
        'schedule': 'weekly',  # 每周执行一次
        'date_range': (-9, -3),  # T-9 到 T-3（7天）
        'minio_path': 'ods/pdd/pdd_kpi_weekly',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_kpi_weekly',
        'enabled': True  # 已启用
    },
    'kpi_monthly': {
        'name': '客服绩效数据采集（月度）',
        'script': 'pdd_kpi_monthly.py',
        'status_field': 'kpi_monthly_status',
        'schedule': 'monthly',  # 每月执行一次
        'date_range': 'last_month',  # 上个月
        'minio_path': 'ods/pdd/pdd_kpi_monthly',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_kpi_monthly',
        'enabled': True  # 已启用
    }
}

# 数据库配置
DB_CONFIG = {
    'platform': 'pdd',
    'shops_table': 'pdd_shops',
    'tasks_table': 'pdd_tasks',
    'database': 'company'
}

# 文件存储配置
STORAGE_CONFIG = {
    'base_archive_dir': 'D:/pdd',
    'merged_files_dir': 'D:/pdd/合并文件'
}

# MinIO配置
MINIO_CONFIG = {
    'api_url': 'http://127.0.0.1:8009/api/upload',
    'bucket': 'warehouse'
}

# Dremio配置
DREMIO_CONFIG = {
    'api_url': 'http://localhost:8003/api'
}


def get_enabled_tasks():
    """获取所有启用的任务"""
    return {k: v for k, v in CRAWLER_TASKS.items() if v.get('enabled', True)}


def get_daily_tasks():
    """获取每日执行的任务"""
    return {k: v for k, v in CRAWLER_TASKS.items() 
            if v.get('enabled', True) and v.get('schedule') == 'daily'}


def get_weekly_tasks():
    """获取每周执行的任务"""
    return {k: v for k, v in CRAWLER_TASKS.items() 
            if v.get('enabled', True) and v.get('schedule') == 'weekly'}


def get_monthly_tasks():
    """获取每月执行的任务"""
    return {k: v for k, v in CRAWLER_TASKS.items() 
            if v.get('enabled', True) and v.get('schedule') == 'monthly'}


def get_task_date(task_config, base_date=None):
    """
    根据任务配置计算目标日期

    Args:
        task_config: 任务配置字典
        base_date: 基准日期（可选），如果不指定则使用当前日期

    Returns:
        str: 日期字符串，如 '2025-10-02'
    """
    schedule = task_config.get('schedule', 'daily')

    # 确定基准日期
    if base_date:
        if isinstance(base_date, str):
            base = datetime.strptime(base_date, '%Y-%m-%d').date()
        else:
            base = base_date
    else:
        base = datetime.now().date()

    if schedule == 'daily':
        offset = task_config.get('date_offset', -1)
        target_date = base + timedelta(days=offset)
        return target_date.strftime('%Y-%m-%d')

    elif schedule == 'weekly':
        # 周度任务：返回上周的日期范围
        date_range = task_config.get('date_range', (-9, -3))
        start_date = base + timedelta(days=date_range[0])
        end_date = base + timedelta(days=date_range[1])
        return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

    elif schedule == 'monthly':
        # 月度任务：返回上个月的年月
        first_day_this_month = base.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        return last_day_last_month.strftime('%Y-%m')
    
    return None


def get_all_status_fields():
    """获取所有任务的状态字段列表"""
    return [task['status_field'] for task in CRAWLER_TASKS.values() if task.get('enabled', True)]

