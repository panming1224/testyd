#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的脚本，专门测试之前失败的客户
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2_cleaned import TmallChatManager

def test_failed_customers():
    """测试之前失败的客户"""
    # 之前失败的客户列表
    failed_customers = [
        "effie沫儿", "李丝丝李羽琪", "liuxf78", "东方龙魅", 
        "张喜军8858", "叠写凹陷", "华华的哇", "花落无声刘苗苗"
    ]
    
    manager = TmallChatManager()
    
    # 加载cookies
    cookie_str = manager.load_cookies_from_file()
    if not cookie_str:
        print("无法加载cookies")
        return
    
    # 获取客户列表
    customer_list_data = manager.get_customer_list(cookie_str)
    if not customer_list_data or 'data' not in customer_list_data:
        print("无法获取客户列表")
        return
    
    data_section = customer_list_data['data']
    if 'result' in data_section:
        customer_list = data_section['result']
    elif 'conversationList' in data_section:
        customer_list = data_section['conversationList']
    else:
        print("无法解析客户列表")
        return
    
    print(f"总共获取到 {len(customer_list)} 个客户")
    
    # 测试失败的客户
    success_count = 0
    fail_count = 0
    
    for customer in customer_list:
        display_name = customer.get('displayName', '')
        if display_name in failed_customers:
            print(f"\n=== 测试客户: {display_name} ===")
            
            # 获取聊天记录
            chat_messages = manager.get_chat_messages_with_user_info(cookie_str, display_name, customer)
            
            if chat_messages:
                print(f"✓ 成功获取 {len(chat_messages)} 条聊天记录")
                success_count += 1
                
                # 显示前3条消息
                for i, msg in enumerate(chat_messages[:3]):
                    print(f"  消息{i+1}: {msg.get('content', '')[:100]}...")
            else:
                print("✗ 获取聊天记录失败")
                fail_count += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"总计: {success_count + fail_count}")

if __name__ == "__main__":
    test_failed_customers()