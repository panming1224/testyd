#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用爬虫数据库接口使用示例 - 简化版本
演示如何使用简化后的 CrawlerDBInterface 进行任务管理
支持动态列名传入，任务状态简化为null和已完成两种
"""

from crawler_db_interface import CrawlerDBInterface, TaskStatus
from datetime import datetime

def main():
    """使用示例主函数"""
    
    # 1. 初始化数据库接口（单例模式，全局只有一个实例）
    # 使用默认的company数据库
    db = CrawlerDBInterface()
    print("✓ 数据库接口初始化完成")
    
    # 2. 导入店铺信息示例（支持文件夹字段）
    # 创建示例店铺数据并直接插入数据库
    shop_data = [
        {'shop_name': '测试店铺A', 'folder_path': 'D:/company_data/shop_a'},
        {'shop_name': '测试店铺B', 'folder_path': 'D:/company_data/shop_b'},
        {'shop_name': '测试店铺C', 'folder_path': 'D:/company_data/shop_c'}
    ]
    
    imported_count = 0
    for shop in shop_data:
        # 检查店铺是否已存在
        existing_shop = db.get_shop_by_name(shop['shop_name'])
        if existing_shop:
            # 更新现有店铺的文件夹路径
            success = db.update_record('shops', {'folder_path': shop['folder_path']}, 
                                     'shop_name = %s', (shop['shop_name'],))
            if success:
                imported_count += 1
        else:
            # 插入新店铺
            success = db.insert_record('shops', shop)
            if success:
                imported_count += 1
    
    print(f"✓ 成功导入/更新 {imported_count} 个店铺")
    
    # 3. 生成今日任务（支持自定义任务列）
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 定义自定义任务类型（动态列名）
    custom_tasks = [
        'chat_status',          # 客服聊天记录
        'quality_status',       # 产品质量下载
        'badreview_status',     # 差评下载
        'kpi_status',          # 客服绩效下载
        'promotion_status',     # 推广数据下载（新增）
        'inventory_status'      # 库存数据下载（新增）
    ]
    
    created_count = db.generate_tasks(today, custom_tasks)
    print(f"✓ 为日期 {today} 创建了 {created_count} 个新任务")
    
    # 4. 获取待处理的差评任务（使用动态列名）
    # 待处理状态为null或空字符串
    pending_tasks = db.get_pending_tasks(today, 'badreview_status', limit=5)
    print(f"✓ 获取到 {len(pending_tasks)} 个待处理的差评任务")
    
    # 5. 处理任务示例
    if pending_tasks:
        for task in pending_tasks[:2]:  # 处理前2个任务
            # 处理元组格式的返回数据
            if isinstance(task, tuple):
                # 假设返回格式为 (time_period, shop_name, shop_data...)
                shop_name = task[1]
                # 获取店铺详细信息
                shop_info = db.get_shop_by_name(shop_name)
                cookie = shop_info.get('cookie', '') if shop_info else ''
                folder_path = shop_info.get('folder_path', '') if shop_info else ''
            else:
                shop_name = task['shop_name']
                cookie = task['cookie']
                folder_path = task['folder_path']
            
            print(f"\n开始处理店铺: {shop_name}")
            print(f"  - 文件夹路径: {folder_path}")
            print(f"  - 当前状态: null（待处理）")
            
            # 这里可以添加实际的爬虫逻辑
            # 例如：使用cookie和文件夹路径进行数据抓取
            print(f"  - 使用Cookie进行数据抓取...")
            print(f"  - Cookie: {cookie[:50]}..." if cookie else "  - 无Cookie")
            print(f"  - 数据将保存到: {folder_path}")
            
            # 模拟处理完成，更新状态为已完成
            db.update_task_status(today, shop_name, 'badreview_status', TaskStatus.COMPLETED)
            print(f"  - 任务完成，状态更新为: {TaskStatus.COMPLETED}")
    
    # 6. Cookie和文件夹管理示例
    if pending_tasks:
        first_task = pending_tasks[0]
        # 处理元组格式的返回数据
        if isinstance(first_task, tuple):
            shop_name = first_task[1]
        else:
            shop_name = first_task['shop_name']
        
        # 更新Cookie
        new_cookie = "new_cookie_value_example_12345"
        success = db.update_shop_cookie(shop_name, new_cookie)
        if success:
            print(f"✓ 店铺 {shop_name} 的Cookie已更新")
        
        # 获取Cookie
        current_cookie = db.get_shop_cookie(shop_name)
        print(f"✓ 当前Cookie: {current_cookie[:30]}..." if current_cookie else "无Cookie")
        
        # 更新文件夹路径
        new_folder = f"D:/company_data/{shop_name.replace('店铺', 'shop')}"
        success = db.update_shop_folder(shop_name, new_folder)
        if success:
            print(f"✓ 店铺 {shop_name} 的文件夹路径已更新为: {new_folder}")
        
        # 获取文件夹路径
        current_folder = db.get_shop_folder(shop_name)
        print(f"✓ 当前文件夹路径: {current_folder}")
    
    # 7. 演示不同任务类型的处理（动态列名）
    print("\n=== 演示不同任务类型处理 ===")
    task_types = ['chat_status', 'quality_status', 'kpi_status']
    
    for task_type in task_types:
        pending = db.get_pending_tasks(today, task_type, limit=1)
        if pending:
            task = pending[0]
            shop_name = task['shop_name']
            print(f"处理 {task_type} 任务 - 店铺: {shop_name}")
            
            # 直接标记为完成（简化流程）
            db.update_task_status(today, shop_name, task_type, TaskStatus.COMPLETED)
            print(f"  - {task_type} 任务已完成")
    
    # 8. 批量处理示例
    print("\n=== 批量处理示例 ===")
    all_pending = db.get_pending_tasks(today, 'promotion_status')
    print(f"待处理的推广数据任务: {len(all_pending)} 个")
    
    for task in all_pending:
        shop_name = task['shop_name']
        # 批量标记为完成
        db.update_task_status(today, shop_name, 'promotion_status', TaskStatus.COMPLETED)
        print(f"  - 店铺 {shop_name} 的推广数据任务已完成")
    
    print("\n✓ 所有示例执行完成")
    print("✓ 任务状态简化：null（待处理）→ 已完成")
    print("✓ 支持动态列名传入，无需固定枚举类型")
    
    # 清理临时文件
    import os
    if os.path.exists('temp_shops.csv'):
        os.remove('temp_shops.csv')
        print("✓ 临时文件已清理")

if __name__ == "__main__":
    main()