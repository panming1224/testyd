#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2 import TmallChatManager
import json
import time
from datetime import datetime

def debug_full_response():
    """调试完整的API响应，分析失败原因"""
    
    print("=== 调试完整API响应 ===")
    
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
        page_size=5,  # 只获取前5个进行详细调试
        page_index=1
    )
    
    if not customer_response:
        print("无法获取客户列表")
        return
    
    # 提取客户数据
    customers = []
    if 'data' in customer_response and 'result' in customer_response['data']:
        customers = customer_response['data']['result']
    else:
        print("响应格式异常，无法提取客户列表")
        return
    
    print(f"获取到 {len(customers)} 个客户，开始详细调试...")
    
    # 调试结果记录
    debug_results = {
        "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_debug": []
    }
    
    # 逐个调试前5个客户
    for i, customer in enumerate(customers[:5]):
        print(f"\n{'='*60}")
        print(f"调试第 {i+1} 个客户")
        print(f"{'='*60}")
        
        customer_nick = customer.get('displayName', f'客户{i+1}')
        print(f"客户昵称: {customer_nick}")
        print(f"客户完整数据:")
        print(json.dumps(customer, ensure_ascii=False, indent=2))
        
        # 记录客户基本信息
        customer_debug = {
            "index": i + 1,
            "customer_nick": customer_nick,
            "customer_data": customer,
            "api_calls": []
        }
        
        try:
            print(f"\n--- 开始调用聊天消息API ---")
            
            # 手动构造参数，模拟get_chat_messages_with_user_info的调用
            cid = customer.get('cid', {})
            user_id = customer.get('userID', {})
            
            print(f"CID: {cid}")
            print(f"UserID: {user_id}")
            
            # 构造请求参数
            if isinstance(cid, dict) and 'appCid' in cid:
                app_cid = cid['appCid']
            else:
                app_cid = str(cid) if cid else None
                
            if isinstance(user_id, dict) and 'appUid' in user_id:
                app_uid = user_id['appUid']
            else:
                app_uid = str(user_id) if user_id else None
            
            print(f"提取的appCid: {app_cid}")
            print(f"提取的appUid: {app_uid}")
            
            if not app_cid or not app_uid:
                print("❌ 缺少必要的CID或UserID参数")
                customer_debug["api_calls"].append({
                    "status": "error",
                    "error": "缺少必要的CID或UserID参数",
                    "app_cid": app_cid,
                    "app_uid": app_uid
                })
                continue
            
            # 调用聊天消息API
            start_time = time.time()
            
            print(f"\n--- 调用get_chat_messages_with_user_info ---")
            chat_response = manager.get_chat_messages_with_user_info(
                cookies_str, 
                customer_nick, 
                customer
            )
            
            duration = time.time() - start_time
            
            print(f"API调用耗时: {duration:.2f}秒")
            print(f"响应类型: {type(chat_response)}")
            
            if chat_response is None:
                print("❌ API返回None")
                customer_debug["api_calls"].append({
                    "status": "failed",
                    "error": "API返回None",
                    "duration": duration,
                    "response_type": str(type(chat_response))
                })
            elif isinstance(chat_response, list):
                print(f"✓ API返回列表，长度: {len(chat_response)}")
                print("完整响应内容:")
                print(json.dumps(chat_response, ensure_ascii=False, indent=2))
                
                customer_debug["api_calls"].append({
                    "status": "success",
                    "duration": duration,
                    "response_type": "list",
                    "response_length": len(chat_response),
                    "full_response": chat_response
                })
            elif isinstance(chat_response, dict):
                print(f"✓ API返回字典，键: {list(chat_response.keys())}")
                print("完整响应内容:")
                print(json.dumps(chat_response, ensure_ascii=False, indent=2))
                
                customer_debug["api_calls"].append({
                    "status": "success",
                    "duration": duration,
                    "response_type": "dict",
                    "response_keys": list(chat_response.keys()),
                    "full_response": chat_response
                })
            else:
                print(f"⚠️ API返回未知类型: {type(chat_response)}")
                print(f"响应内容: {chat_response}")
                
                customer_debug["api_calls"].append({
                    "status": "unknown",
                    "duration": duration,
                    "response_type": str(type(chat_response)),
                    "full_response": str(chat_response)
                })
        
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
            import traceback
            print("完整异常信息:")
            traceback.print_exc()
            
            customer_debug["api_calls"].append({
                "status": "exception",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
        
        debug_results["customer_debug"].append(customer_debug)
        
        # 避免请求过快
        print(f"\n等待1秒后继续下一个客户...")
        time.sleep(1)
    
    # 保存调试结果
    output_file = "d:/testyd/tm/debug_full_response_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(debug_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print("调试完成")
    print(f"详细结果已保存到: {output_file}")
    print(f"{'='*60}")

if __name__ == "__main__":
    debug_full_response()