#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的任务状态
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mysql'))

from crawler_db_interface import CrawlerDBInterface

def check_database_status():
    """检查数据库中的任务状态"""
    print("检查数据库中的任务状态...")
    
    try:
        # 创建数据库接口
        db_interface = CrawlerDBInterface('tm')
        
        # 检查所有店铺
        shops = db_interface.get_all_shops()
        print(f"数据库中共有 {len(shops)} 个店铺")
        
        # 检查2025-09-30的任务状态
        target_date = "2025-09-30"
        
        # 获取所有任务
        try:
            all_tasks = db_interface.get_all_tasks(target_date)
            print(f"日期 {target_date} 共有 {len(all_tasks)} 个任务")
            
            # 统计各种状态的任务
            status_count = {}
            for task in all_tasks:
                chat_status = task[4] if len(task) > 4 else None  # chat_status列
                if chat_status:
                    status_count[chat_status] = status_count.get(chat_status, 0) + 1
            
            print("任务状态统计:")
            for status, count in status_count.items():
                print(f"  {status}: {count} 个")
                
        except Exception as e:
            print(f"获取任务时出错: {e}")
        
        # 检查待处理的chat_status任务
        try:
            pending_tasks = db_interface.get_pending_tasks(target_date, 'chat_status')
            print(f"待处理的 chat_status 任务: {len(pending_tasks)} 个")
            
            if pending_tasks:
                print("待处理任务详情:")
                for i, task in enumerate(pending_tasks[:5]):  # 只显示前5个
                    shop_name = task[1] if len(task) > 1 else "未知"
                    print(f"  {i+1}. 店铺: {shop_name}")
                    
        except Exception as e:
            print(f"获取待处理任务时出错: {e}")
            
        # 手动重置一些任务状态为待处理
        print("\n尝试重置部分任务状态...")
        try:
            # 获取前3个店铺，重置其chat_status为待处理
            if shops:
                for i, shop in enumerate(shops[:3]):
                    shop_name = shop.get('shop_name', '')
                    if shop_name:
                        success = db_interface.update_task_status(target_date, shop_name, 'chat_status', '待处理')
                        print(f"重置店铺 {shop_name} 的chat_status: {'成功' if success else '失败'}")
                        
                # 重新检查待处理任务
                pending_tasks = db_interface.get_pending_tasks(target_date, 'chat_status')
                print(f"重置后待处理的 chat_status 任务: {len(pending_tasks)} 个")
                
        except Exception as e:
            print(f"重置任务状态时出错: {e}")
            
    except Exception as e:
        print(f"检查数据库状态时发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_status()