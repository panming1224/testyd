# -*- coding: utf-8 -*-
"""
统一任务生成器
根据配置文件自动生成所有类型的任务
新增爬虫只需在 crawler_config.py 中添加配置即可
"""
import sys
from datetime import datetime

# 设置标准输出编码为UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 添加模块路径
sys.path.append(r'D:\testyd')
sys.path.append(r'D:\testyd\mysql')
sys.path.append(r'D:\testyd\pdd')

from crawler_db_interface import CrawlerDBInterface
from crawler_config import (
    CRAWLER_TASKS, DB_CONFIG, 
    get_enabled_tasks, get_daily_tasks, 
    get_task_date
)


def generate_tasks_by_schedule(schedule='daily', force_date=None):
    """
    根据调度类型生成任务
    
    Args:
        schedule: 调度类型 'daily'/'weekly'/'monthly'
        force_date: 强制指定日期（用于测试），格式如 '2025-10-02'
    
    Returns:
        dict: 各任务类型的创建结果
    """
    print("=" * 60)
    print(f"拼多多任务生成器 - {schedule.upper()}")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 初始化数据库接口
    db_interface = CrawlerDBInterface(**DB_CONFIG)
    
    # 筛选符合调度类型的任务
    tasks_to_generate = {
        k: v for k, v in get_enabled_tasks().items() 
        if v.get('schedule') == schedule
    }
    
    if not tasks_to_generate:
        print(f"\n⚠️  没有找到 {schedule} 类型的启用任务")
        return {}
    
    results = {}
    
    for task_key, task_config in tasks_to_generate.items():
        task_name = task_config['name']
        status_field = task_config['status_field']

        # 计算目标日期
        # 注意：即使指定了 force_date，也要根据任务的 date_offset 计算实际目标日期
        # 这样可以确保不同任务类型使用正确的日期
        target_date = get_task_date(task_config, base_date=force_date)
        
        print(f"\n{'='*60}")
        print(f"任务: {task_name}")
        print(f"状态字段: {status_field}")
        print(f"目标日期: {target_date}")
        print(f"{'='*60}")
        
        try:
            # 生成任务
            created_count = db_interface.generate_tasks(target_date, [status_field])
            results[task_key] = {
                'name': task_name,
                'status_field': status_field,
                'target_date': target_date,
                'created_count': created_count,
                'success': True
            }
            print(f"✓ 成功生成 {created_count} 个任务")
        except Exception as e:
            results[task_key] = {
                'name': task_name,
                'status_field': status_field,
                'target_date': target_date,
                'created_count': 0,
                'success': False,
                'error': str(e)
            }
            print(f"✗ 生成失败: {e}")
    
    return results


def print_summary(results):
    """打印任务生成摘要"""
    print("\n" + "=" * 60)
    print("任务生成完成")
    print("=" * 60)
    
    total_created = sum(r['created_count'] for r in results.values())
    success_count = sum(1 for r in results.values() if r['success'])
    
    print(f"\n总计: {len(results)} 个任务类型")
    print(f"成功: {success_count} 个")
    print(f"失败: {len(results) - success_count} 个")
    print(f"生成任务数: {total_created} 个")
    
    print("\n详细结果:")
    for task_key, result in results.items():
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {result['name']}")
        print(f"     - 状态字段: {result['status_field']}")
        print(f"     - 目标日期: {result['target_date']}")
        print(f"     - 生成数量: {result['created_count']}")
        if not result['success']:
            print(f"     - 错误: {result.get('error', '未知错误')}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='拼多多任务生成器')
    parser.add_argument(
        '--schedule', 
        choices=['daily', 'weekly', 'monthly', 'all'],
        default='daily',
        help='调度类型：daily(每日)/weekly(每周)/monthly(每月)/all(全部)'
    )
    parser.add_argument(
        '--date',
        help='强制指定日期（用于测试），格式：YYYY-MM-DD'
    )
    
    args = parser.parse_args()
    
    if args.schedule == 'all':
        # 生成所有类型的任务
        all_results = {}
        for schedule in ['daily', 'weekly', 'monthly']:
            results = generate_tasks_by_schedule(schedule, args.date)
            all_results.update(results)
        print_summary(all_results)
    else:
        # 生成指定类型的任务
        results = generate_tasks_by_schedule(args.schedule, args.date)
        print_summary(results)
    
    print("\n✓ 任务生成完成，可以开始执行各个爬虫程序")

