#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试失败客户的数据结构分析脚本
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2_cleaned import TmallChatManager

def analyze_customer_data():
    """分析客户数据结构，找出失败客户的特征"""
    
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
    
    print(f"总客户数: {len(customer_list)}")
    
    # 已知的失败客户名单（从之前的运行结果中提取）
    failed_customers = [
        "effie沫儿", "李丝丝李羽琪", "liuxf78", "东方龙魅", 
        "张喜军8858", "叠写凹陷", "华华的哇", "花落无声刘苗苗"
    ]
    
    # 已知的成功客户名单
    success_customers = [
        "tb950301045612", "tb5622336", "赤司akashisejuro", 
        "zhouming05128012345", "tb085292108", "zhoujin901008",
        "tb805582982", "tangweijia888", "kangjunru423", "钟杰zhongj"
    ]
    
    print("\n=== 分析失败客户数据结构 ===")
    failed_data = []
    for i, customer in enumerate(customer_list[:50]):  # 只分析前50个
        display_name = customer.get('displayName', '未知')
        if display_name in failed_customers:
            print(f"\n失败客户: {display_name}")
            print(f"完整数据: {json.dumps(customer, ensure_ascii=False, indent=2)}")
            failed_data.append(customer)
    
    print("\n=== 分析成功客户数据结构 ===")
    success_data = []
    for i, customer in enumerate(customer_list[:50]):  # 只分析前50个
        display_name = customer.get('displayName', '未知')
        if display_name in success_customers:
            print(f"\n成功客户: {display_name}")
            print(f"完整数据: {json.dumps(customer, ensure_ascii=False, indent=2)}")
            success_data.append(customer)
    
    # 对比分析
    print("\n=== 数据结构对比分析 ===")
    if failed_data and success_data:
        failed_keys = set()
        success_keys = set()
        
        for customer in failed_data:
            failed_keys.update(customer.keys())
        
        for customer in success_data:
            success_keys.update(customer.keys())
        
        print(f"失败客户字段: {sorted(failed_keys)}")
        print(f"成功客户字段: {sorted(success_keys)}")
        print(f"失败客户独有字段: {sorted(failed_keys - success_keys)}")
        print(f"成功客户独有字段: {sorted(success_keys - failed_keys)}")
        
        # 分析关键字段的值
        print("\n=== 关键字段值分析 ===")
        key_fields = ['cid', 'userID', 'userId', 'buyerId', 'customerId']
        
        for field in key_fields:
            print(f"\n字段 {field}:")
            print("失败客户:")
            for customer in failed_data:
                if field in customer:
                    print(f"  {customer.get('displayName')}: {customer[field]}")
            
            print("成功客户:")
            for customer in success_data:
                if field in customer:
                    print(f"  {customer.get('displayName')}: {customer[field]}")

if __name__ == "__main__":
    analyze_customer_data()