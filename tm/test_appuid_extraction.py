#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试appUid提取功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2_cleaned import TmallChatManager

def test_appuid_extraction():
    """测试appUid提取功能"""
    print("开始测试appUid提取功能...")
    
    # 初始化管理器
    manager = TmallChatManager()
    
    # 读取cookies
    try:
        with open('cookies.txt', 'r', encoding='utf-8') as f:
            cookies_str = f.read().strip()
        print("✅ 成功读取cookies")
    except Exception as e:
        print(f"❌ 读取cookies失败: {e}")
        return
    
    # 验证token
    token = manager.get_h5_token(cookies_str)
    if not token:
        print("❌ Token验证失败")
        return
    print("✅ Token验证成功")
    
    # 获取客户列表
    print("\n获取客户列表...")
    customer_list_data = manager.get_customer_list(cookies_str)
    if not customer_list_data:
        print("❌ 获取客户列表失败")
        return
    
    print(f"客户列表数据类型: {type(customer_list_data)}")
    print(f"客户列表数据键: {customer_list_data.keys() if isinstance(customer_list_data, dict) else 'N/A'}")
    
    # 解析客户列表
    customers = None
    if isinstance(customer_list_data, dict):
        if 'data' in customer_list_data and 'result' in customer_list_data['data']:
            customers = customer_list_data['data']['result']
        elif 'data' in customer_list_data and 'conversationList' in customer_list_data['data']:
            customers = customer_list_data['data']['conversationList']
        elif 'data' in customer_list_data:
            customers = customer_list_data['data']
        else:
            customers = customer_list_data
    else:
        customers = customer_list_data
    
    if not customers:
        print("❌ 客户列表为空")
        return
    
    print(f"✅ 成功获取 {len(customers)} 个客户")
    
    # 测试前10个客户的appUid提取
    print("\n测试前10个客户的appUid提取:")
    print("-" * 60)
    
    for i, customer in enumerate(customers[:10]):
        print(f"\n客户 {i+1}: {customer.get('displayName', 'Unknown')}")
        
        # 显示原始userID数据
        user_id_data = customer.get('userID', {})
        print(f"  原始userID数据: {user_id_data}")
        
        # 提取appUid
        if isinstance(user_id_data, dict) and 'appUid' in user_id_data:
            app_uid = user_id_data['appUid']
            print(f"  ✅ 成功提取appUid: {app_uid}")
            
            # 验证是否为目标appUid
            if app_uid == "2220313775792":
                print(f"  🎯 找到目标appUid: {app_uid}")
        else:
            print(f"  ❌ 无法提取appUid")
    
    print("\n" + "="*60)
    print("测试完成！")

if __name__ == "__main__":
    test_appuid_extraction()