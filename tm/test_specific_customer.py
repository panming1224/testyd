#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特定客户的聊天消息获取
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2_cleaned import TmallChatManager

def test_specific_customer():
    """测试特定客户的聊天消息获取"""
    manager = TmallChatManager()
    
    # 加载cookies
    cookie_str = manager.load_cookies_from_file()
    if not cookie_str:
        print("无法加载cookies")
        return
    
    print("成功加载cookies")
    
    # 验证token
    token = manager.get_h5_token(cookie_str)
    if not token:
        print("Token验证失败")
        return
    
    print("[OK] Token仍然有效")
    
    # 使用用户提供的特定参数
    test_params = {
        "userNick": "cntaobao回力棉娅专卖店:可云",
        "cid": "2507486176.1-2219315280500.1#11001",  # 用户提供的特定cid
        "userId": "2219315280500"
    }
    
    print(f"\n=== 测试特定客户参数 ===")
    print(f"userNick: {test_params['userNick']}")
    print(f"cid: {test_params['cid']}")
    print(f"userId: {test_params['userId']}")
    
    # 构造客户数据
    customer_data = {
        "cid": {"appCid": test_params['cid']},
        "userID": {"appUid": test_params['userId']},
        "displayName": "测试客户"
    }
    
    # 调用聊天消息获取方法
    messages = manager.get_chat_messages_with_user_info(
        cookie_str, 
        test_params['userNick'], 
        customer_data
    )
    
    if messages:
        print(f"\n✅ 成功获取到 {len(messages)} 条消息")
        # 显示前几条消息的基本信息
        for i, msg in enumerate(messages[:3]):
            # 处理消息可能是字符串或字典的情况
            if isinstance(msg, dict):
                content = msg.get('content', {})
                if isinstance(content, dict):
                    text = content.get('text', 'N/A')
                else:
                    text = str(content)
                print(f"消息 {i+1}: {text[:50]}...")
            else:
                print(f"消息 {i+1}: {str(msg)[:50]}...")
    else:
        print("\n❌ 未获取到消息")


if __name__ == "__main__":
    test_specific_customer()