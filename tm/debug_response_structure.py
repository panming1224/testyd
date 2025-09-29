#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2 import TmallChatManager
import json

def debug_response_structure():
    """调试API响应结构"""
    
    print("=== 调试API响应结构 ===")
    
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
    
    print("=== API响应结构分析 ===")
    print(f"响应类型: {type(customer_response)}")
    
    if isinstance(customer_response, dict):
        print(f"顶级键: {list(customer_response.keys())}")
        
        for key, value in customer_response.items():
            print(f"\n键 '{key}':")
            print(f"  类型: {type(value)}")
            if isinstance(value, dict):
                print(f"  子键: {list(value.keys())}")
                if key == 'data':
                    print(f"  data详细结构:")
                    for sub_key, sub_value in value.items():
                        print(f"    {sub_key}: {type(sub_value)}")
                        if isinstance(sub_value, list) and len(sub_value) > 0:
                            print(f"      列表长度: {len(sub_value)}")
                            print(f"      第一个元素类型: {type(sub_value[0])}")
                            if isinstance(sub_value[0], dict):
                                print(f"      第一个元素键: {list(sub_value[0].keys())}")
            elif isinstance(value, list):
                print(f"  列表长度: {len(value)}")
                if len(value) > 0:
                    print(f"  第一个元素: {value[0]}")
            else:
                print(f"  值: {value}")
    
    # 保存完整响应到文件
    with open('d:/testyd/tm/api_response_debug.json', 'w', encoding='utf-8') as f:
        json.dump(customer_response, f, ensure_ascii=False, indent=2)
    
    print("\n完整响应已保存到: d:/testyd/tm/api_response_debug.json")

if __name__ == "__main__":
    debug_response_structure()