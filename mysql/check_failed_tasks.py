# -*- coding: utf-8 -*-
"""
检查失败任务的具体原因
"""

import sys
sys.path.append(r'D:\testyd')
sys.path.append(r'D:\testyd\mysql')

from crawler_db_interface import CrawlerDBInterface
import pymysql

def check_failed_tasks():
    """检查失败任务的具体原因"""
    print("=== 检查失败任务详情 ===")
    
    try:
        # 初始化数据库接口
        db = CrawlerDBInterface(
            platform='tm',
            shops_table='tm_shops',
            tasks_table='tm_tasks',
            database='company'
        )
        print("✓ 数据库连接成功")
        
        # 直接查询数据库获取任务详情
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='admin123',
            database='company',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 查询2025-09-26的所有任务
        query = """
        SELECT 
            shop_name, time_period, 
            kpi_self_status, kpi_offical_status,
            create_time, update_time
        FROM tm_tasks 
        WHERE time_period = '2025-09-26'
        ORDER BY shop_name
        """
        
        cursor.execute(query)
        tasks = cursor.fetchall()
        
        print(f"\n总任务数: {len(tasks)}")
        
        # 统计任务状态
        self_status_count = {}
        official_status_count = {}
        failed_tasks = []
        
        for task in tasks:
            shop_name, time_period, kpi_self_status, kpi_offical_status, create_time, update_time = task
            
            # 统计自制报表状态
            if kpi_self_status not in self_status_count:
                self_status_count[kpi_self_status] = 0
            self_status_count[kpi_self_status] += 1
            
            # 统计售后解决分析状态
            if kpi_offical_status not in official_status_count:
                official_status_count[kpi_offical_status] = 0
            official_status_count[kpi_offical_status] += 1
            
            # 收集失败任务（状态为None表示待处理，其他非"已完成"状态可能是失败）
            if (kpi_self_status and kpi_self_status != '已完成') or (kpi_offical_status and kpi_offical_status != '已完成'):
                failed_tasks.append(task)
        
        print("\n--- 自制报表任务状态统计 ---")
        for status, count in self_status_count.items():
            status_name = status if status else "待处理"
            print(f"  {status_name}: {count}")
            
        print("\n--- 售后解决分析任务状态统计 ---")
        for status, count in official_status_count.items():
            status_name = status if status else "待处理"
            print(f"  {status_name}: {count}")
        
        print(f"\n--- 异常任务详情 ({len(failed_tasks)}个) ---")
        for i, task in enumerate(failed_tasks):
            shop_name, time_period, kpi_self_status, kpi_offical_status, create_time, update_time = task
            print(f"\n{i+1}. 店铺: {shop_name}")
            print(f"   时间周期: {time_period}")
            print(f"   自制报表状态: {kpi_self_status}")
            print(f"   售后解决分析状态: {kpi_offical_status}")
            print(f"   更新时间: {update_time}")
        
        # 检查成功任务的情况
        success_tasks = [task for task in tasks if task[2] == '已完成' and task[3] == '已完成']
        print(f"\n--- 完全成功任务详情 ({len(success_tasks)}个) ---")
        for i, task in enumerate(success_tasks[:5]):  # 只显示前5个
            shop_name, time_period, kpi_self_status, kpi_offical_status, create_time, update_time = task
            print(f"{i+1}. 店铺: {shop_name}, 完成时间: {update_time}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_failed_tasks()