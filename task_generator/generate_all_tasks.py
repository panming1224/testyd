# -*- coding: utf-8 -*-
"""
统一任务生成器 - 所有平台
每天统一生成所有平台的任务
新增平台只需在 platform_config.py 中添加配置即可
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
sys.path.append(r'D:\testyd\task_generator')

from crawler_db_interface import CrawlerDBInterface
from platform_config import (
    get_all_platforms,
    get_all_enabled_tasks_by_schedule,
    get_task_date
)


def generate_tasks_for_platform(platform_key, platform_name, db_config, tasks, schedule, force_date=None):
    """
    为指定平台生成任务
    
    Args:
        platform_key: 平台键名，如 'pdd', 'tm'
        platform_name: 平台显示名称
        db_config: 数据库配置
        tasks: 任务配置字典
        schedule: 调度类型 'daily'/'weekly'/'monthly'
        force_date: 强制指定日期（用于测试）
    
    Returns:
        dict: 任务生成结果
    """
    print(f"\n{'='*60}")
    print(f"平台: {platform_name} ({platform_key.upper()})")
    print(f"{'='*60}")
    
    # 初始化数据库接口
    db_interface = CrawlerDBInterface(**db_config)
    
    results = {}
    
    for task_key, task_config in tasks.items():
        task_name = task_config['name']
        status_field = task_config['status_field']
        is_shop_status = task_config.get('is_shop_status', False)  # 是否是店铺状态任务

        # 计算目标日期
        target_date = get_task_date(task_config, base_date=force_date)

        print(f"\n  任务: {task_name}")
        print(f"  状态字段: {status_field}")
        print(f"  目标日期: {target_date}")

        try:
            if is_shop_status:
                # 店铺状态任务：重置所有店铺的status字段为NULL（待执行）
                reset_count = db_interface.check_and_reset_daily_status()
                results[task_key] = {
                    'platform': platform_name,
                    'name': task_name,
                    'status_field': status_field,
                    'target_date': target_date,
                    'created_count': reset_count,
                    'success': True
                }
                print(f"  ✓ 成功重置 {reset_count} 个店铺状态为待执行")
            else:
                # 普通任务：在任务表中生成任务
                created_count = db_interface.generate_tasks(target_date, [status_field])
                results[task_key] = {
                    'platform': platform_name,
                    'name': task_name,
                    'status_field': status_field,
                    'target_date': target_date,
                    'created_count': created_count,
                    'success': True
                }
                print(f"  ✓ 成功生成 {created_count} 个任务")
        except Exception as e:
            results[task_key] = {
                'platform': platform_name,
                'name': task_name,
                'status_field': status_field,
                'target_date': target_date,
                'created_count': 0,
                'success': False,
                'error': str(e)
            }
            print(f"  ✗ 生成失败: {e}")
    
    return results


def generate_all_tasks_by_schedule(schedule='daily', platforms=None, force_date=None):
    """
    为所有平台生成指定调度类型的任务
    
    Args:
        schedule: 调度类型 'daily'/'weekly'/'monthly'
        platforms: 指定平台列表，如 ['pdd', 'tm']，None表示所有平台
        force_date: 强制指定日期（用于测试），格式如 '2025-10-02'
    
    Returns:
        dict: 所有平台的任务生成结果
    """
    print("=" * 80)
    print(f"统一任务生成器 - {schedule.upper()}")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 获取所有平台的指定调度类型任务
    all_platform_tasks = get_all_enabled_tasks_by_schedule(schedule)
    
    if not all_platform_tasks:
        print(f"\n⚠️  没有找到 {schedule} 类型的启用任务")
        return {}
    
    # 如果指定了平台，则只处理指定平台
    if platforms:
        all_platform_tasks = {
            k: v for k, v in all_platform_tasks.items() 
            if k in platforms
        }
    
    all_results = {}
    
    # 遍历每个平台
    for platform_key, platform_data in all_platform_tasks.items():
        platform_name = platform_data['name']
        db_config = platform_data['db_config']
        tasks = platform_data['tasks']
        
        # 为该平台生成任务
        platform_results = generate_tasks_for_platform(
            platform_key,
            platform_name,
            db_config,
            tasks,
            schedule,
            force_date
        )
        
        all_results[platform_key] = platform_results
    
    return all_results


def print_summary(all_results):
    """打印任务生成摘要"""
    print("\n" + "=" * 80)
    print("任务生成完成")
    print("=" * 80)
    
    # 统计总数
    total_platforms = len(all_results)
    total_tasks = sum(len(results) for results in all_results.values())
    total_created = sum(
        r['created_count'] 
        for results in all_results.values() 
        for r in results.values()
    )
    total_success = sum(
        1 
        for results in all_results.values() 
        for r in results.values() 
        if r['success']
    )
    total_failed = total_tasks - total_success
    
    print(f"\n总计:")
    print(f"  平台数: {total_platforms}")
    print(f"  任务类型数: {total_tasks}")
    print(f"  成功: {total_success}")
    print(f"  失败: {total_failed}")
    print(f"  生成任务数: {total_created}")
    
    # 按平台显示详细结果
    print(f"\n详细结果:")
    for platform_key, results in all_results.items():
        print(f"\n  【{results[list(results.keys())[0]]['platform']}】")
        for task_key, result in results.items():
            status = "✓" if result['success'] else "✗"
            print(f"    {status} {result['name']}")
            print(f"       状态字段: {result['status_field']}")
            print(f"       目标日期: {result['target_date']}")
            print(f"       生成数量: {result['created_count']}")
            if not result['success']:
                print(f"       错误: {result.get('error', '未知错误')}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='统一任务生成器 - 所有平台')
    parser.add_argument(
        '--schedule',
        choices=['daily', 'weekly', 'monthly', 'all'],
        default='daily',
        help='调度类型：daily(每日)/weekly(每周)/monthly(每月)/all(全部)'
    )
    parser.add_argument(
        '--platforms',
        nargs='+',
        choices=['pdd', 'tm'],
        help='指定平台：pdd tm，不指定则生成所有平台'
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
            results = generate_all_tasks_by_schedule(schedule, args.platforms, args.date)
            for platform_key, platform_results in results.items():
                if platform_key not in all_results:
                    all_results[platform_key] = {}
                all_results[platform_key].update(platform_results)
        print_summary(all_results)
    else:
        # 生成指定类型的任务
        results = generate_all_tasks_by_schedule(args.schedule, args.platforms, args.date)
        print_summary(results)

