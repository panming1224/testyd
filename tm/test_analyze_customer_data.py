# -*- coding: utf-8 -*-
"""
测试脚本：分析客户列表数据结构，为整合两个API做准备
"""
import json
from tm_chat_2 import TmallChatManager

def analyze_customer_data():
    """分析客户列表数据结构"""
    print("=" * 60)
    print("开始分析客户列表数据结构")
    print("=" * 60)
    
    # 初始化管理器
    manager = TmallChatManager()
    
    # 获取cookies
    cookies_str = manager.get_cookies_from_file()
    if not cookies_str:
        print("❌ 无法获取cookies")
        return
    
    print("✓ 成功获取cookies")
    
    # 获取客户列表
    print("\n🔄 正在获取客户列表...")
    customer_data = manager.get_customer_list(cookies_str)
    
    if not customer_data:
        print("❌ 无法获取客户列表数据")
        return
    
    print("✓ 成功获取客户列表数据")
    
    # 分析数据结构
    print("\n" + "=" * 40)
    print("数据结构分析:")
    print("=" * 40)
    
    # 打印完整数据结构
    print("完整响应数据:")
    print(json.dumps(customer_data, indent=2, ensure_ascii=False))
    
    # 检查关键字段
    print("\n" + "-" * 40)
    print("关键字段分析:")
    print("-" * 40)
    
    if 'data' in customer_data:
        data = customer_data['data']
        print(f"data字段类型: {type(data)}")
        
        if isinstance(data, dict):
            print("data字段包含的键:")
            for key in data.keys():
                print(f"  - {key}: {type(data[key])}")
            
            # 查找客户列表
            if 'conversationList' in data:
                conversations = data['conversationList']
                print(f"\nconversationList长度: {len(conversations)}")
                
                if conversations and len(conversations) > 0:
                    print("\n第一条客户记录详细信息:")
                    first_customer = conversations[0]
                    print(json.dumps(first_customer, indent=2, ensure_ascii=False))
                    
                    # 提取关键信息
                    print("\n" + "-" * 30)
                    print("提取的关键信息:")
                    print("-" * 30)
                    
                    # 查找需要的字段
                    key_fields = ['cid', 'userId', 'userNick', 'conversationId', 'buyerId', 'buyerNick']
                    for field in key_fields:
                        if field in first_customer:
                            print(f"{field}: {first_customer[field]}")
                    
                    # 查找嵌套字段
                    if 'buyer' in first_customer:
                        buyer = first_customer['buyer']
                        print(f"buyer信息: {buyer}")
                        if isinstance(buyer, dict):
                            for key, value in buyer.items():
                                print(f"  buyer.{key}: {value}")
                    
                    if 'conversation' in first_customer:
                        conversation = first_customer['conversation']
                        print(f"conversation信息: {conversation}")
                        if isinstance(conversation, dict):
                            for key, value in conversation.items():
                                print(f"  conversation.{key}: {value}")
                    
                    return first_customer
                else:
                    print("❌ 客户列表为空")
            else:
                print("❌ 未找到conversationList字段")
        else:
            print(f"data字段不是字典类型: {data}")
    else:
        print("❌ 响应中没有data字段")
    
    return None

if __name__ == "__main__":
    analyze_customer_data()