#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试目标appUid: 2220313775792 的聊天消息获取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2_cleaned import TmallChatManager

def test_target_appuid():
    """测试目标appUid的聊天消息获取"""
    print("开始测试目标appUid: 2220313775792...")
    
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
    
    # 查找目标appUid的客户
    target_appuid = "2220313775792"
    target_customers = []
    
    print(f"\n查找appUid为 {target_appuid} 的客户...")
    print("-" * 60)
    
    for customer in customers:
        user_id_data = customer.get('userID', {})
        if isinstance(user_id_data, dict) and user_id_data.get('appUid') == target_appuid:
            target_customers.append(customer)
            print(f"🎯 找到目标客户: {customer.get('displayName', 'Unknown')}")
            print(f"   cid: {customer.get('cid', 'N/A')}")
            print(f"   appUid: {user_id_data.get('appUid', 'N/A')}")
    
    if not target_customers:
        print(f"❌ 未找到appUid为 {target_appuid} 的客户")
        return
    
    print(f"\n✅ 找到 {len(target_customers)} 个目标客户")
    
    # 测试第一个目标客户的聊天消息获取
    target_customer = target_customers[0]
    print(f"\n测试客户: {target_customer.get('displayName', 'Unknown')}")
    print("-" * 60)
    
    try:
        # 获取聊天消息
        user_nick = "cntaobao回力棉娅专卖店:可云"  # 固定值
        
        # 打印详细的请求参数
        print(f"请求参数详情:")
        print(f"  userNick: {user_nick}")
        print(f"  客户displayName: {target_customer.get('displayName', 'Unknown')}")
        print(f"  客户cid: {target_customer.get('cid', {})}")
        print(f"  客户userID: {target_customer.get('userID', {})}")
        
        messages = manager.get_chat_messages_with_user_info(
            cookies_str, 
            user_nick, 
            target_customer
        )
        
        if messages:
            print(f"✅ 成功获取 {len(messages)} 条消息")
            if messages:
                print(f"第一条消息预览: {str(messages[0])[:200]}...")
        else:
            print("❌ 未获取到消息")
            
    except Exception as e:
        print(f"❌ 获取消息失败: {e}")
    
    print("\n" + "="*60)
    print("测试完成！")

if __name__ == "__main__":
    test_target_appuid()