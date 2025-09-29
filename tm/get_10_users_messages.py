#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取10个用户的详细消息内容
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2 import TmallChatManager
import json

def get_10_users_messages():
    """获取10个用户的消息"""
    try:
        print("=== 获取10个用户的详细消息内容 ===")
        
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
        
        # 获取前10个客户的详细消息
        print(f"\n2. 获取前10个客户的详细消息...")
        all_messages = []
        
        for i, customer in enumerate(customers[:10]):
            customer_nick = customer.get('displayName', f'客户{i+1}')
            print(f"\n--- 客户 {i+1}: {customer_nick} ---")
            
            try:
                # 获取聊天消息
                chat_messages_data = manager.get_chat_messages_with_user_info(cookies_str, user_nick, customer)
                
                if chat_messages_data:
                    messages = []
                    # 根据修复后的逻辑处理消息数据
                    if isinstance(chat_messages_data, list):
                        messages = chat_messages_data
                        print(f"[OK] 获取到 {len(messages)} 条消息 (直接列表)")
                    elif isinstance(chat_messages_data, dict):
                        # 检查各种可能的消息字段
                        if 'userMessages' in chat_messages_data:
                            messages = chat_messages_data['userMessages']
                            print(f"[OK] 从userMessages字段获取 {len(messages)} 条消息")
                        elif 'messageList' in chat_messages_data:
                            messages = chat_messages_data['messageList']
                            print(f"[OK] 从messageList字段获取 {len(messages)} 条消息")
                        elif 'data' in chat_messages_data:
                            data_section = chat_messages_data['data']
                            if 'userMessages' in data_section:
                                messages = data_section['userMessages']
                                print(f"[OK] 从data.userMessages字段获取 {len(messages)} 条消息")
                            elif 'messageList' in data_section:
                                messages = data_section['messageList']
                                print(f"[OK] 从data.messageList字段获取 {len(messages)} 条消息")
                    
                    # 分析消息内容
                    if messages:
                        print(f"消息样本分析:")
                        for j, msg in enumerate(messages[:3]):  # 只显示前3条消息
                            print(f"  消息 {j+1}:")
                            print(f"    字段: {list(msg.keys()) if isinstance(msg, dict) else 'Not dict'}")
                            
                            if isinstance(msg, dict):
                                # 提取消息内容
                                content = ""
                                if 'content' in msg:
                                    try:
                                        content_data = json.loads(msg['content'])
                                        if isinstance(content_data, dict):
                                            content = content_data.get('text', content_data.get('summary', str(content_data)[:100]))
                                        else:
                                            content = str(content_data)[:100]
                                    except:
                                        content = str(msg['content'])[:100]
                                
                                print(f"    内容: {content}")
                                
                                # 显示其他重要字段
                                if 'msgType' in msg:
                                    print(f"    消息类型: {msg['msgType']}")
                                if 'sendTime' in msg:
                                    print(f"    发送时间: {msg['sendTime']}")
                                if 'ext' in msg:
                                    try:
                                        ext_data = json.loads(msg['ext'])
                                        sender = ext_data.get('senderNickName', ext_data.get('sender_nick', ''))
                                        if sender:
                                            print(f"    发送者: {sender}")
                                    except:
                                        pass
                        
                        # 添加客户信息到消息中
                        for msg in messages:
                            if isinstance(msg, dict):
                                msg['customer_nick'] = customer_nick
                                msg['customer_id'] = customer.get('cid', '')
                        
                        all_messages.extend(messages)
                    else:
                        print("[ERROR] 未找到消息数据")
                else:
                    print("[ERROR] 获取消息失败")
                    
            except Exception as e:
                print(f"[ERROR] 获取消息时发生异常: {e}")
        
        # 输出汇总信息
        print(f"\n=== 汇总信息 ===")
        print(f"总消息数: {len(all_messages)}")
        
        # 按客户分组统计
        customer_stats = {}
        for msg in all_messages:
            if isinstance(msg, dict) and 'customer_nick' in msg:
                nick = msg['customer_nick']
                if nick not in customer_stats:
                    customer_stats[nick] = 0
                customer_stats[nick] += 1
        
        print(f"按客户分组:")
        for nick, count in customer_stats.items():
            print(f"  {nick}: {count} 条消息")
        
        # 保存详细消息到文件
        output_file = "d:/testyd/tm/10_users_messages_detail.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_messages, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] 详细消息已保存到: {output_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 获取消息过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = get_10_users_messages()
    sys.exit(0 if success else 1)