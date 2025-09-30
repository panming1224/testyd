# -*- coding: utf-8 -*-
"""
调试天猫KPI任务状态和失败原因
"""

import sys
sys.path.append(r'D:\testyd')
sys.path.append(r'D:\testyd\mysql')

from crawler_db_interface import CrawlerDBInterface

def debug_tasks():
    """调试任务状态"""
    print("=== 调试天猫KPI任务状态 ===")
    
    try:
        # 初始化数据库接口
        db = CrawlerDBInterface(
            platform='tm',
            shops_table='tm_shops',
            tasks_table='tm_tasks',
            database='company'
        )
        print("✓ 数据库连接成功")
        
        # 检查2025-09-26的任务状态
        target_date = '2025-09-26'
        
        # 检查自制报表任务
        print(f"\n--- 检查 {target_date} 自制报表任务 ---")
        self_tasks = db.get_pending_tasks(target_date, 'kpi_self_status')
        print(f"待处理自制报表任务数量: {len(self_tasks) if self_tasks else 0}")
        
        if self_tasks:
            print("前5个待处理任务:")
            for i, task in enumerate(self_tasks[:5]):
                if isinstance(task, tuple):
                    shop_name = task[1] if len(task) > 1 else "未知店铺"
                    print(f"  {i+1}. 店铺: {shop_name}")
                else:
                    print(f"  {i+1}. 任务: {task}")
        
        # 检查售后解决分析任务
        print(f"\n--- 检查 {target_date} 售后解决分析任务 ---")
        official_tasks = db.get_pending_tasks(target_date, 'kpi_offical_status')
        print(f"待处理售后解决分析任务数量: {len(official_tasks) if official_tasks else 0}")
        
        if official_tasks:
            print("前5个待处理任务:")
            for i, task in enumerate(official_tasks[:5]):
                if isinstance(task, tuple):
                    shop_name = task[1] if len(task) > 1 else "未知店铺"
                    print(f"  {i+1}. 店铺: {shop_name}")
                else:
                    print(f"  {i+1}. 任务: {task}")
        
        # 检查所有店铺信息
        print(f"\n--- 检查店铺信息 ---")
        all_shops = db.get_all_shops()
        print(f"总店铺数量: {len(all_shops) if all_shops else 0}")
        
        if all_shops:
            print("店铺列表:")
            for i, shop in enumerate(all_shops[:10]):  # 只显示前10个
                if isinstance(shop, tuple):
                    shop_name = shop[1] if len(shop) > 1 else "未知店铺"
                    cookie_status = "有cookie" if (len(shop) > 8 and shop[8]) else "无cookie"
                    print(f"  {i+1}. {shop_name} - {cookie_status}")
                else:
                    print(f"  {i+1}. {shop}")
        
        # 检查任务统计
        print(f"\n--- 检查任务统计 ---")
        try:
            stats = db.get_task_statistics(target_date, ['kpi_self_status', 'kpi_offical_status'])
            if stats:
                for stat in stats:
                    print(f"  {stat}")
            else:
                print("  无统计数据")
        except Exception as e:
            print(f"  获取统计数据失败: {e}")
        
    except Exception as e:
        print(f"✗ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_tasks()