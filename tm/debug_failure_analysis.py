#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析用户消息获取失败的原因
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2 import TmallChatManager
import json

def analyze_failure_reasons():
    """分析失败原因"""
    try:
        print("=== 分析用户消息获取失败原因 ===")
        
        # 初始化管理器
        manager = TmallChatManager()
        
        # 加载cookies
        cookies_str = manager.load_cookies_from_file()
        if not cookies_str:
            print("[ERROR] 无法加载cookies")
            return False
        
        # 获取客户列表
        print("\n1. 获取客户列表...")
        customer_data = manager.get_customer_list(cookies_str)
        if not customer_data:
            print("[ERROR] 无法获取客户列表")
            return False
        
        # 提取客户列表
        customers = customer_data.get('data', {}).get('result', [])
        if not customers:
            print("[ERROR] 客户列表为空")
            return False
        
        print(f"[OK] 获取到 {len(customers)} 个客户")
        
        # 提取用户信息
        user_info = manager.extract_user_info_from_cookie(cookies_str)
        user_nick = user_info.get('nick', 'unknown') if user_info else 'unknown'
        
        # 分析前10个客户的消息获取情况
        print(f"\n2. 分析前10个客户的消息获取情况...")
        success_count = 0
        failure_count = 0
        failure_details = []
        
        for i, customer in enumerate(customers[:10]):
            customer_nick = customer.get('displayName', f'客户{i+1}')
            print(f"\n--- 分析客户 {i+1}: {customer_nick} ---")
            
            # 打印客户数据结构
            print(f"客户数据字段: {list(customer.keys())}")
            
            try:
                # 尝试获取聊天消息
                chat_messages_data = manager.get_chat_messages_with_user_info(cookies_str, user_nick, customer)
                
                if chat_messages_data:
                    # 检查返回的数据结构
                    if isinstance(chat_messages_data, list):
                        message_count = len(chat_messages_data)
                        print(f"[OK] 成功获取 {message_count} 条消息 (直接列表)")
                        success_count += 1
                    elif isinstance(chat_messages_data, dict):
                        print(f"返回数据字段: {list(chat_messages_data.keys())}")
                        
                        # 检查各种可能的消息字段
                        messages = []
                        if 'userMessages' in chat_messages_data:
                            messages = chat_messages_data['userMessages']
                            print(f"[OK] 从userMessages字段获取 {len(messages)} 条消息")
                        elif 'messageList' in chat_messages_data:
                            messages = chat_messages_data['messageList']
                            print(f"[OK] 从messageList字段获取 {len(messages)} 条消息")
                        elif 'data' in chat_messages_data:
                            data_section = chat_messages_data['data']
                            if isinstance(data_section, dict):
                                if 'userMessages' in data_section:
                                    messages = data_section['userMessages']
                                    print(f"[OK] 从data.userMessages字段获取 {len(messages)} 条消息")
                                elif 'messageList' in data_section:
                                    messages = data_section['messageList']
                                    print(f"[OK] 从data.messageList字段获取 {len(messages)} 条消息")
                        
                        if messages:
                            success_count += 1
                        else:
                            print("[ERROR] 未找到消息数据")
                            failure_count += 1
                            failure_details.append({
                                'customer': customer_nick,
                                'reason': '未找到消息数据',
                                'data_fields': list(chat_messages_data.keys())
                            })
                    else:
                        print(f"[ERROR] 未知的返回数据类型: {type(chat_messages_data)}")
                        failure_count += 1
                        failure_details.append({
                            'customer': customer_nick,
                            'reason': f'未知数据类型: {type(chat_messages_data)}',
                            'data': str(chat_messages_data)[:200]
                        })
                else:
                    print("[ERROR] 获取消息失败，返回None")
                    failure_count += 1
                    failure_details.append({
                        'customer': customer_nick,
                        'reason': '获取消息失败，返回None',
                        'customer_data': {k: str(v)[:100] for k, v in customer.items()}
                    })
                    
            except Exception as e:
                print(f"[ERROR] 获取消息时发生异常: {e}")
                failure_count += 1
                failure_details.append({
                    'customer': customer_nick,
                    'reason': f'异常: {str(e)}',
                    'customer_data': {k: str(v)[:100] for k, v in customer.items()}
                })
        
        # 输出分析结果
        print(f"\n=== 分析结果 ===")
        print(f"成功获取消息: {success_count}/10")
        print(f"获取失败: {failure_count}/10")
        print(f"成功率: {success_count/10*100:.1f}%")
        
        if failure_details:
            print(f"\n=== 失败详情 ===")
            for i, detail in enumerate(failure_details, 1):
                print(f"\n失败 {i}: {detail['customer']}")
                print(f"原因: {detail['reason']}")
                if 'data_fields' in detail:
                    print(f"返回数据字段: {detail['data_fields']}")
                if 'customer_data' in detail:
                    print(f"客户数据: {detail['customer_data']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 分析过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = analyze_failure_reasons()
    sys.exit(0 if success else 1)