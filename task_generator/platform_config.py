# -*- coding: utf-8 -*-
"""
统一平台任务配置
所有平台的爬虫任务配置集中管理
新增平台或任务只需在这里添加配置即可
"""
from datetime import datetime, timedelta

# ==================== 拼多多平台配置 ====================
PDD_TASKS = {
    'badscore': {
        'name': '差评数据采集',
        'script': 'pdd/pdd_badscore.py',
        'status_field': 'badsscore_status',
        'schedule': 'daily',
        'date_offset': -1,  # T-1
        'minio_path': 'ods/pdd/pdd_badscore',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_badscore',
        'enabled': True
    },
    'quality': {
        'name': '产品质量数据采集',
        'script': 'pdd/pdd_quality.py',
        'status_field': 'quality_status',
        'schedule': 'daily',
        'date_offset': 0,  # T
        'minio_path': 'ods/pdd/pdd_quality',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_quality',
        'enabled': True
    },
    'kpi_days': {
        'name': '客服绩效数据采集（日度）',
        'script': 'pdd/pdd_kpi.py',
        'status_field': 'kpi_days_status',
        'schedule': 'daily',
        'date_offset': -3,  # T-3
        'minio_path': 'ods/pdd/pdd_kpi_days',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_kpi_days',
        'enabled': True
    },
    'chat': {
        'name': '聊天数据采集',
        'script': 'pdd/pdd_chat.py',
        'status_field': 'chat_status',
        'schedule': 'daily',
        'date_offset': -1,  # T-1
        'minio_path': 'ods/pdd/pdd_chat',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_chat',
        'enabled': True
    },
    'kpi_weekly': {
        'name': '客服绩效数据采集（周度）',
        'script': 'pdd/pdd_kpi_weekly.py',
        'status_field': 'kpi_weekly_status',
        'schedule': 'weekly',
        'date_range': (-9, -3),  # T-9 到 T-3（7天）
        'minio_path': 'ods/pdd/pdd_kpi_weekly',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_kpi_weekly',
        'enabled': True  # 已启用
    },
    'kpi_monthly': {
        'name': '客服绩效数据采集（月度）',
        'script': 'pdd/pdd_kpi_monthly.py',
        'status_field': 'kpi_monthly_status',
        'schedule': 'monthly',
        'date_range': 'last_month',  # 上个月
        'minio_path': 'ods/pdd/pdd_kpi_monthly',
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_kpi_monthly',
        'enabled': True  # 已启用
    }
}

# ==================== 天猫平台配置 ====================
TM_TASKS = {
    'cookie': {
        'name': 'Cookie获取',
        'script': 'tm/get_tm_cookies.py',
        'status_field': 'status',  # 修正：应该是 status 而不是 cookie_status
        'schedule': 'daily',
        'date_offset': 0,  # T（当天）
        'enabled': True,
        'is_shop_status': True  # 标记这是店铺状态任务，不是任务表任务
    },
    'badscore': {
        'name': '差评数据采集',
        'script': 'tm/tm_badscore.py',
        'status_field': 'badscore_status',
        'schedule': 'daily',
        'date_offset': -1,  # T-1
        'minio_path': 'ods/tm/tm_badscore',
        'dremio_table': 'minio.warehouse.ods.tm.tm_badscore',
        'enabled': True
    },
    'chat': {
        'name': '聊天数据采集',
        'script': 'tm/tm_chat.py',
        'status_field': 'chat_status',
        'schedule': 'daily',
        'date_offset': -1,  # T-1
        'minio_path': 'ods/tm/tm_chat',
        'dremio_table': 'minio.warehouse.ods.tm.tm_chat',
        'enabled': True
    },
    'kpi_self': {
        'name': '客服绩效自制报表',
        'script': 'tm/tm_kpi.py',
        'status_field': 'kpi_self_status',
        'schedule': 'daily',
        'date_offset': -4,  # T-4
        'minio_path': 'ods/tm/tm_kpi_self',
        'dremio_table': 'minio.warehouse.ods.tm.tm_kpi_self',
        'enabled': True
    },
    'kpi_official': {
        'name': '客服绩效官方报表',
        'script': 'tm/tm_kpi.py',
        'status_field': 'kpi_official_status',
        'schedule': 'daily',
        'date_offset': -4,  # T-4
        'minio_path': 'ods/tm/tm_kpi_official',
        'dremio_table': 'minio.warehouse.ods.tm.tm_kpi_official',
        'enabled': True
    },
    'kpi_weekly': {
        'name': '客服绩效数据采集（周度）',
        'script': 'tm/tm_kpi_weekly.py',
        'status_field': 'kpi_weekly_status',
        'schedule': 'weekly',
        'date_range': (-9, -3),  # T-9 到 T-3（7天）
        'minio_path': 'ods/tm/tm_kpi_weekly',
        'dremio_table': 'minio.warehouse.ods.tm.tm_kpi_weekly',
        'enabled': True  # 已启用
    },
    'kpi_monthly': {
        'name': '客服绩效数据采集（月度）',
        'script': 'tm/tm_kpi_monthly.py',
        'status_field': 'kpi_monthly_status',
        'schedule': 'monthly',
        'date_range': 'last_month',  # 上个月
        'minio_path': 'ods/tm/tm_kpi_monthly',
        'dremio_table': 'minio.warehouse.ods.tm.tm_kpi_monthly',
        'enabled': True  # 已启用
    }
}

# ==================== 平台数据库配置 ====================
PLATFORM_DB_CONFIG = {
    'pdd': {
        'platform': 'pdd',
        'shops_table': 'pdd_shops',
        'tasks_table': 'pdd_tasks',
        'database': 'company'
    },
    'tm': {
        'platform': 'tm',
        'shops_table': 'tm_shops',
        'tasks_table': 'tm_tasks',
        'database': 'company'
    }
}

# ==================== 所有平台任务配置 ====================
ALL_PLATFORMS = {
    'pdd': {
        'name': '拼多多',
        'tasks': PDD_TASKS,
        'db_config': PLATFORM_DB_CONFIG['pdd']
    },
    'tm': {
        'name': '天猫',
        'tasks': TM_TASKS,
        'db_config': PLATFORM_DB_CONFIG['tm']
    }
}


# ==================== 辅助函数 ====================

def get_all_platforms():
    """获取所有平台配置"""
    return ALL_PLATFORMS


def get_platform_config(platform_key):
    """获取指定平台的配置"""
    return ALL_PLATFORMS.get(platform_key)


def get_enabled_tasks(platform_key):
    """获取指定平台的所有启用任务"""
    platform = ALL_PLATFORMS.get(platform_key)
    if not platform:
        return {}
    return {k: v for k, v in platform['tasks'].items() if v.get('enabled', True)}


def get_tasks_by_schedule(platform_key, schedule):
    """获取指定平台指定调度类型的任务"""
    enabled_tasks = get_enabled_tasks(platform_key)
    return {k: v for k, v in enabled_tasks.items() if v.get('schedule') == schedule}


def get_all_enabled_tasks_by_schedule(schedule):
    """获取所有平台指定调度类型的任务"""
    result = {}
    for platform_key, platform_config in ALL_PLATFORMS.items():
        tasks = get_tasks_by_schedule(platform_key, schedule)
        if tasks:
            result[platform_key] = {
                'name': platform_config['name'],
                'db_config': platform_config['db_config'],
                'tasks': tasks
            }
    return result


def get_task_date(task_config, base_date=None):
    """
    根据任务配置计算目标日期
    
    Args:
        task_config: 任务配置字典
        base_date: 基准日期（可选），如果不指定则使用当前日期
    
    Returns:
        str: 日期字符串，如 '2025-10-02' 或 '2025-10-02_2025-10-08' 或 '2025-09'
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


def get_all_status_fields(platform_key):
    """获取指定平台所有任务的状态字段列表"""
    enabled_tasks = get_enabled_tasks(platform_key)
    return [task['status_field'] for task in enabled_tasks.values()]

