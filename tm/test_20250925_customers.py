#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2 import TmallChatManager
import json
import time
from datetime import datetime

def test_20250925_customers():
    """测试20250925日期前10个客户的消息拉取"""
    
    print("=== 测试20250925日期前10个客户的消息拉取 ===")
    
    # 初始化管理器
    manager = TmallChatManager()
    
    # 加载cookies
    cookies_str = manager.load_cookies_from_file()
    if not cookies_str:
        print("无法加载cookies，退出")
        return
    
    # 获取20250925的客户列表
    print("获取20250925的客户列表...")
    customer_response = manager.get_customer_list(
        cookies_str, 
        begin_date="20250925", 
        end_date="20250925",
        page_size=10,  # 只获取前10个
        page_index=1
    )
    
    if not customer_response:
        print("无法获取客户列表")
        return
    
    # 检查响应状态
    if 'ret' in customer_response:
        ret_status = customer_response['ret'][0] if customer_response['ret'] else 'UNKNOWN'
        print(f"API响应状态: {ret_status}")
        
        if not ret_status.startswith('SUCCESS'):
            print(f"API调用失败: {ret_status}")
            return
    
    # 提取客户数据
    customers = []
    if 'data' in customer_response and 'result' in customer_response['data']:
        customers = customer_response['data']['result']
    else:
        print("响应格式异常，无法提取客户列表")
        print(f"响应结构: {list(customer_response.keys()) if isinstance(customer_response, dict) else type(customer_response)}")
        return
    
    print(f"获取到 {len(customers)} 个客户")
    
    if len(customers) == 0:
        print("20250925日期没有客户数据")
        return
    
    # 测试结果记录
    test_results = {
        "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "test_date": "20250925",
        "total_customers": len(customers),
        "customer_tests": [],
        "summary": {
            "successful": 0,
            "failed": 0,
            "error": 0
        }
    }
    
    # 逐个测试前10个客户的消息拉取
    for i, customer in enumerate(customers[:10]):
        print(f"\n--- 测试第 {i+1} 个客户 ---")
        
        customer_nick = customer.get('nick', f'客户{i+1}')
        print(f"客户昵称: {customer_nick}")
        
        # 显示客户的基本信息
        print(f"客户数据结构: {list(customer.keys())}")
        
        start_time = time.time()
        
        try:
            # 尝试获取聊天消息
            chat_messages = manager.get_chat_messages_with_user_info(
                cookies_str, 
                customer_nick, 
                customer
            )
            
            duration = time.time() - start_time
            
            if chat_messages:
                # 检查消息数量
                message_count = 0
                if isinstance(chat_messages, dict) and 'data' in chat_messages:
                    if 'result' in chat_messages['data']:
                        message_count = len(chat_messages['data']['result'])
                    elif 'messages' in chat_messages['data']:
                        message_count = len(chat_messages['data']['messages'])
                elif isinstance(chat_messages, list):
                    message_count = len(chat_messages)
                
                print(f"✓ 成功获取消息，数量: {message_count}")
                
                test_results["customer_tests"].append({
                    "index": i + 1,
                    "customer_nick": customer_nick,
                    "status": "success",
                    "message_count": message_count,
                    "duration": duration,
                    "customer_data": customer,
                    "response_summary": {
                        "type": str(type(chat_messages)),
                        "keys": list(chat_messages.keys()) if isinstance(chat_messages, dict) else "not_dict"
                    }
                })
                
                test_results["summary"]["successful"] += 1
                
            else:
                print("✗ 获取消息失败，返回空结果")
                
                test_results["customer_tests"].append({
                    "index": i + 1,
                    "customer_nick": customer_nick,
                    "status": "failed",
                    "message_count": 0,
                    "duration": duration,
                    "customer_data": customer,
                    "error": "返回空结果"
                })
                
                test_results["summary"]["failed"] += 1
        
        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ 异常: {str(e)}")
            
            test_results["customer_tests"].append({
                "index": i + 1,
                "customer_nick": customer_nick,
                "status": "error",
                "message_count": 0,
                "duration": duration,
                "customer_data": customer,
                "error": str(e)
            })
            
            test_results["summary"]["error"] += 1
        
        # 避免请求过快
        time.sleep(1)
    
    # 保存测试结果
    output_file = "d:/testyd/tm/test_20250925_customers_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    # 输出测试总结
    print(f"\n=== 测试完成 ===")
    print(f"测试日期: 20250925")
    print(f"总客户数: {test_results['total_customers']}")
    print(f"测试客户数: {len(test_results['customer_tests'])}")
    print(f"成功: {test_results['summary']['successful']}")
    print(f"失败: {test_results['summary']['failed']}")
    print(f"异常: {test_results['summary']['error']}")
    
    if test_results['summary']['successful'] > 0:
        successful_customers = [t for t in test_results['customer_tests'] if t['status'] == 'success']
        total_messages = sum(t['message_count'] for t in successful_customers)
        print(f"总消息数: {total_messages}")
        
        print("\n成功的客户:")
        for test in successful_customers:
            print(f"  - {test['customer_nick']}: {test['message_count']} 条消息")
    
    print(f"\n详细结果已保存到: {output_file}")

if __name__ == "__main__":
    test_20250925_customers()