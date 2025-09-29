#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2 import TmallChatManager
import json
import time

def analyze_specific_errors():
    """分析具体哪些用户返回APPLICATION_ERROR"""
    
    print("=== 开始分析具体用户的APPLICATION_ERROR ===")
    
    # 初始化管理器
    manager = TmallChatManager()
    
    # 加载cookies
    cookies_str = manager.load_cookies_from_file()
    if not cookies_str:
        print("无法加载cookies，退出")
        return
    
    # 获取客户列表
    print("获取客户列表...")
    customer_response = manager.get_customer_list(cookies_str)
    if not customer_response:
        print("无法获取客户列表")
        return
    
    # 从响应中提取客户数据
    customers = []
    if 'data' in customer_response and 'result' in customer_response['data']:
        customers = customer_response['data']['result']
    else:
        print("响应格式异常，无法提取客户列表")
        print(f"响应结构: {list(customer_response.keys()) if isinstance(customer_response, dict) else type(customer_response)}")
        return
    
    print(f"总共获取到 {len(customers)} 个客户")
    
    success_users = []
    error_users = []
    
    # 分析前20个用户
    for i, customer in enumerate(customers[:20]):
        print(f"\n--- 分析第 {i+1} 个用户 ---")
        
        # 提取用户信息
        user_nick = customer.get('userNick', 'Unknown')
        print(f"用户昵称: {user_nick}")
        
        # 检查cid和userID的原始数据
        cid_raw = customer.get('cid', '')
        user_id_raw = customer.get('userID', '')
        
        print(f"原始cid: {cid_raw}")
        print(f"原始userID: {user_id_raw}")
        print(f"cid类型: {type(cid_raw)}")
        print(f"userID类型: {type(user_id_raw)}")
        
        # 尝试获取聊天消息
        try:
            messages = manager.get_chat_messages_with_user_info(cookies_str, user_nick, customer)
            
            if messages is None:
                print(f"❌ 用户 {user_nick} 返回None")
                error_users.append({
                    'user_nick': user_nick,
                    'cid_raw': cid_raw,
                    'user_id_raw': user_id_raw,
                    'cid_type': str(type(cid_raw)),
                    'user_id_type': str(type(user_id_raw)),
                    'error_type': 'None_response',
                    'customer_data': customer
                })
            elif isinstance(messages, dict) and 'error' in messages:
                print(f"❌ 用户 {user_nick} 返回错误: {messages}")
                error_users.append({
                    'user_nick': user_nick,
                    'cid_raw': cid_raw,
                    'user_id_raw': user_id_raw,
                    'cid_type': str(type(cid_raw)),
                    'user_id_type': str(type(user_id_raw)),
                    'error_type': 'API_error',
                    'error_details': messages,
                    'customer_data': customer
                })
            else:
                print(f"✅ 用户 {user_nick} 成功获取 {len(messages) if messages else 0} 条消息")
                success_users.append({
                    'user_nick': user_nick,
                    'cid_raw': cid_raw,
                    'user_id_raw': user_id_raw,
                    'cid_type': str(type(cid_raw)),
                    'user_id_type': str(type(user_id_raw)),
                    'message_count': len(messages) if messages else 0,
                    'customer_data': customer
                })
                
        except Exception as e:
            print(f"❌ 用户 {user_nick} 发生异常: {str(e)}")
            error_users.append({
                'user_nick': user_nick,
                'cid_raw': cid_raw,
                'user_id_raw': user_id_raw,
                'cid_type': str(type(cid_raw)),
                'user_id_type': str(type(user_id_raw)),
                'error_type': 'Exception',
                'error_details': str(e),
                'customer_data': customer
            })
        
        # 添加延迟避免请求过快
        time.sleep(0.5)
    
    # 保存分析结果
    analysis_result = {
        'success_count': len(success_users),
        'error_count': len(error_users),
        'success_users': success_users,
        'error_users': error_users,
        'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('d:/testyd/tm/error_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 分析结果汇总 ===")
    print(f"成功用户数: {len(success_users)}")
    print(f"失败用户数: {len(error_users)}")
    
    if error_users:
        print(f"\n=== 失败用户详情 ===")
        for user in error_users:
            print(f"用户: {user['user_nick']}")
            print(f"  错误类型: {user['error_type']}")
            print(f"  cid类型: {user['cid_type']}")
            print(f"  userID类型: {user['user_id_type']}")
            if 'error_details' in user:
                print(f"  错误详情: {user['error_details']}")
            print()
    
    print("详细结果已保存到: d:/testyd/tm/error_analysis_result.json")

if __name__ == "__main__":
    analyze_specific_errors()