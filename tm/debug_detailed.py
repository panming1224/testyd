#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试脚本，查看具体的请求和响应
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2_cleaned import TmallChatManager
import json

def debug_single_customer():
    """调试单个客户的聊天消息获取"""
    manager = TmallChatManager()
    
    # 加载cookies
    try:
        with open('cookies.txt', 'r', encoding='utf-8') as f:
            cookies_str = f.read().strip()
        print(f"[OK] 从文件加载cookies成功，长度: {len(cookies_str)} 字符")
    except Exception as e:
        print(f"[ERROR] 加载cookies失败: {e}")
        return
    
    # 验证token
    token = manager.get_h5_token(cookies_str)
    if token:
        print("[OK] Token仍然有效")
    else:
        print("[ERROR] Token无效或过期")
        return
    
    # 获取客服列表
    customer_list_data = manager.get_customer_list(cookies_str)
    if not customer_list_data:
        print("[ERROR] 无法获取客服列表")
        return
    
    print("[OK] 成功获取客服列表数据")
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
    
    if not customers:
        print("[ERROR] 无法解析客户列表")
        print(f"完整数据: {json.dumps(customer_list_data, indent=2, ensure_ascii=False)}")
        return
    
    # 只处理前20个客户
    customers_to_process = customers[:20]
    print(f"将处理前 {len(customers_to_process)} 个客户")
    
    # 查找目标客户
    target_customer = None
    print(f"客户列表类型: {type(customers)}")
    print(f"客户列表长度: {len(customers) if customers else 0}")
    
    if customers:
        print("前3个客户数据:")
        for i, customer in enumerate(customers[:3]):
            print(f"  客户{i+1}: {type(customer)} - {customer}")
    
    for customer in customers_to_process:
        if isinstance(customer, dict) and customer.get('displayName') == 'effie沫儿':
            target_customer = customer
            break
    
    if not target_customer:
        print("[ERROR] 未找到目标客户 'effie沫儿'")
        return
    
    print("客户数据:")
    print(json.dumps(target_customer, indent=2, ensure_ascii=False))
    
    # 获取userNick
    user_nick = manager.get_user_nick_from_cookies(cookies_str)
    print(f"获取到的userNick: {user_nick}")
    
    # 验证token再次
    if manager.get_h5_token(cookies_str):
        print("[OK] Token仍然有效")
    else:
        print("[ERROR] Token在处理过程中失效")
        return
    
    # 尝试获取聊天消息，并打印详细的请求参数
    print("\n=== 开始获取聊天消息 ===")
    
    # 手动构建请求参数进行调试
    import time
    import requests
    
    # 解析客户数据
    cid_value = target_customer.get('cid', {})
    actual_cid = cid_value.get('appCid') if isinstance(cid_value, dict) else str(cid_value)
    
    user_id_value = target_customer.get('userID', {})
    actual_user_id = user_id_value.get('appUid') if isinstance(user_id_value, dict) else str(user_id_value)
    
    print(f"实际参数:")
    print(f"  userNick: {user_nick}")
    print(f"  cid: {actual_cid}")
    print(f"  userId: {actual_user_id}")
    
    # 构建请求数据
    current_time = int(time.time() * 1000)
    cursor_time = current_time - (24 * 60 * 60 * 1000)  # 24小时前
    
    request_data = {
        "userNick": user_nick,
        "cid": actual_cid,
        "userId": actual_user_id,
        "cursor": cursor_time,
        "forward": True,
        "count": 100,
        "needRecalledContent": True
    }
    
    print(f"请求数据:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    # 批量获取前20个客户的聊天消息
    print(f"\n=== 开始批量获取前20个客户的聊天消息 ===")
    successful_count = 0
    failed_count = 0
    
    for i, customer in enumerate(customers_to_process):
        print(f"\n--- 处理客户 {i+1}/20: {customer.get('displayName', 'Unknown')} ---")
        try:
            messages = manager.get_chat_messages_with_user_info(cookies_str, user_nick, customer)
            if messages and len(messages) > 0:
                print(f"✅ 成功获取 {len(messages)} 条消息")
                successful_count += 1
                # 显示第一条消息的简要信息
                first_msg = messages[0]
                if isinstance(first_msg, dict):
                    msg_content = str(first_msg)[:100] + "..." if len(str(first_msg)) > 100 else str(first_msg)
                    print(f"   首条消息: {msg_content}")
                else:
                    print(f"   首条消息: {str(first_msg)[:100]}...")
            else:
                print("❌ 未获取到消息")
                failed_count += 1
        except Exception as e:
            print(f"❌ 获取消息时出错: {str(e)}")
            failed_count += 1
    
    print(f"\n=== 批量处理完成 ===")
    print(f"成功: {successful_count} 个客户")
    print(f"失败: {failed_count} 个客户")
    print(f"总计: {successful_count + failed_count} 个客户")

if __name__ == "__main__":
    debug_single_customer()