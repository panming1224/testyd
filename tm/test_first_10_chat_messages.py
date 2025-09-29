# -*- coding: utf-8 -*-
"""
测试前10条客户数据的实际聊天消息获取
"""
import json
from tm_chat_2_cleaned import TmallChatManager

def main():
    print("=== 测试前10条客户数据的实际聊天消息获取 ===\n")
    
    # 初始化管理器
    manager = TmallChatManager()
    
    # 读取cookies
    cookies_str = manager.load_cookies_from_file()
    if not cookies_str:
        print("❌ 无法加载cookies")
        return
    
    # 验证token
    token = manager.get_h5_token(cookies_str)
    if not token:
        print("❌ 无法提取token")
        return
    
    # 获取客户列表
    print("📋 获取客户列表...")
    customer_list_data = manager.get_customer_list(cookies_str)
    if not customer_list_data:
        print("❌ 无法获取客户列表")
        return
    
    # 解析客户列表
    customers = []
    if 'data' in customer_list_data:
        data = customer_list_data['data']
        if 'result' in data:
            customers = data['result']
        elif 'conversationList' in data:
            customers = data['conversationList']
        elif isinstance(data, list):
            customers = data
    
    if not customers:
        print("❌ 客户列表为空")
        return
    
    print(f"✅ 成功获取 {len(customers)} 个客户")
    
    # 测试前10个客户
    customers_to_test = customers[:10]
    print(f"\n🔍 测试前 {len(customers_to_test)} 个客户的聊天消息获取：\n")
    
    success_count = 0
    fail_count = 0
    
    for i, customer in enumerate(customers_to_test, 1):
        customer_name = customer.get('displayName', 'Unknown')
        print(f"客户 {i}: {customer_name}")
        print("-" * 60)
        
        try:
            # 获取聊天消息
            user_nick = "cntaobao回力棉娅专卖店:可云"  # 固定值
            messages = manager.get_chat_messages_with_user_info(
                cookies_str, 
                user_nick, 
                customer
            )
            
            if messages:
                success_count += 1
                print(f"✅ 成功获取 {len(messages)} 条消息")
                if messages:
                    # 显示第一条消息的简要信息
                    first_msg = messages[0]
                    msg_preview = str(first_msg)[:100] + "..." if len(str(first_msg)) > 100 else str(first_msg)
                    print(f"第一条消息预览: {msg_preview}")
            else:
                fail_count += 1
                print("❌ 未获取到消息")
                
        except Exception as e:
            fail_count += 1
            print(f"❌ 获取消息失败: {e}")
        
        print("\n" + "="*70 + "\n")
    
    # 汇总结果
    print(f"📊 测试结果汇总:")
    print(f"  总测试客户数: {len(customers_to_test)}")
    print(f"  成功获取消息: {success_count} 个客户")
    print(f"  获取失败: {fail_count} 个客户")
    print(f"  成功率: {success_count/len(customers_to_test)*100:.1f}%")

if __name__ == "__main__":
    main()