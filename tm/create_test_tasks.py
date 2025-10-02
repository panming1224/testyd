#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试任务，用于验证修改后的功能
"""

import sys
import os
from datetime import datetime, timedelta

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawler_db_interface import CrawlerDBInterface

def create_test_tasks():
    """创建测试任务"""
    print("=== 创建测试任务 ===")
    
    # 初始化数据库接口
    db_interface = CrawlerDBInterface(
        platform='tm',
        shops_table='tm_shops',
        tasks_table='tm_tasks',
        database='company'
    )
    
    # 获取昨天的日期
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    print(f"目标日期: {yesterday_str}")
    
    try:
        # 获取所有店铺
        shops = db_interface.get_all_shops()
        print(f"找到 {len(shops)} 个店铺")
        
        if not shops:
            print("没有找到店铺，无法创建测试任务")
            return
        
        # 为前3个店铺创建测试任务
        test_shops = shops[:3]
        
        for shop in test_shops:
            shop_name = shop.get('shop_name', '')
            if not shop_name:
                continue
                
            print(f"为店铺 {shop_name} 创建测试任务...")
            
            # 检查是否已存在任务
            existing_task = db_interface.get_task_status(yesterday_str, shop_name, 'chat_status')
            
            if existing_task:
                # 更新现有任务状态为待处理
                db_interface.update_task_status(yesterday_str, shop_name, 'chat_status', '待处理')
                print(f"  ✓ 更新现有任务状态为待处理")
            else:
                # 创建新任务
                db_interface.create_task(yesterday_str, shop_name, 'chat_status', '待处理')
                print(f"  ✓ 创建新任务")
        
        # 验证创建的任务
        print("\n=== 验证创建的任务 ===")
        pending_tasks = []
        
        for shop in test_shops:
            shop_name = shop.get('shop_name', '')
            if not shop_name:
                continue
                
            task_status = db_interface.get_task_status(yesterday_str, shop_name, 'chat_status')
            if task_status == '待处理':
                pending_tasks.append(shop_name)
                print(f"✓ {shop_name}: 待处理")
            else:
                print(f"✗ {shop_name}: {task_status}")
        
        print(f"\n总共创建了 {len(pending_tasks)} 个待处理任务")
        
    except Exception as e:
        print(f"创建测试任务时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_tasks()