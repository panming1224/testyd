# -*- coding: utf-8 -*-
"""
测试前10条客户数据的appCid和appUid提取
"""
import json
from tm_chat_2_cleaned import TmallChatManager

def main():
    print("=== 测试前10条客户数据的appCid和appUid提取 ===\n")
    
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
    print(f"\n🔍 测试前 {len(customers_to_test)} 个客户的参数提取：\n")
    
    for i, customer in enumerate(customers_to_test, 1):
        print(f"客户 {i}: {customer.get('displayName', 'Unknown')}")
        print("-" * 50)
        
        # 显示原始数据结构
        print("原始客户数据:")
        print(f"  cid: {customer.get('cid', {})}")
        print(f"  userID: {customer.get('userID', {})}")
        
        # 提取appCid
        actual_cid = None
        if 'cid' in customer:
            cid_value = customer['cid']
            if isinstance(cid_value, dict) and 'appCid' in cid_value:
                actual_cid = cid_value['appCid']
        
        # 提取appUid
        actual_user_id = None
        if 'userID' in customer:
            user_id_value = customer['userID']
            if isinstance(user_id_value, dict) and 'appUid' in user_id_value:
                actual_user_id = user_id_value['appUid']
        
        print(f"提取结果:")
        print(f"  实际appCid: {actual_cid}")
        print(f"  实际appUid: {actual_user_id}")
        
        # 测试聊天消息获取（只显示请求参数，不实际发送请求）
        if actual_cid and actual_user_id:
            print(f"✅ 参数提取成功")
            print(f"将用于请求的参数:")
            print(f"  cid: {actual_cid}")
            print(f"  userId: {actual_user_id}")
        else:
            print(f"❌ 参数提取失败")
            if not actual_cid:
                print("  - 缺少appCid")
            if not actual_user_id:
                print("  - 缺少appUid")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()