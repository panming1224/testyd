# -*- coding: utf-8 -*-
"""
简化测试：获取客户列表数据并分析结构
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from tm_chat_2 import TmallChatManager
import json

def main():
    try:
        print("=" * 50)
        print("开始分析客户列表数据")
        print("=" * 50)
        
        # 初始化管理器
        manager = TmallChatManager()
        
        # 获取cookies
        print("1. 获取cookies...")
        cookies_str = manager.get_cookies_from_file()
        
        if not cookies_str:
            print("❌ 获取cookies失败")
            return
            
        print(f"✓ 成功获取cookies，长度: {len(cookies_str)}")
        
        # 获取客户列表
        print("\n2. 获取客户列表...")
        result = manager.get_customer_list(cookies_str)
        
        if not result:
            print("❌ 获取数据失败")
            return
            
        print("✓ 成功获取数据")
        print(f"数据类型: {type(result)}")
        
        # 保存完整数据到文件以便分析
        try:
            with open('customer_data.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print("✓ 数据已保存到 customer_data.json")
        except Exception as e:
            print(f"保存文件失败: {e}")
        
        # 分析数据结构
        print("\n3. 分析数据结构...")
        print(f"响应包含的顶级字段: {list(result.keys()) if isinstance(result, dict) else '非字典类型'}")
        
        if 'data' in result:
            data = result['data']
            print(f"data字段类型: {type(data)}")
            
            if isinstance(data, dict):
                print(f"data包含的字段: {list(data.keys())}")
                
                if 'conversationList' in data:
                    conversations = data['conversationList']
                    print(f"✓ 找到 {len(conversations)} 个对话")
                    
                    if conversations and len(conversations) > 0:
                        first = conversations[0]
                        print("\n4. 第一个客户的详细信息:")
                        print(json.dumps(first, indent=2, ensure_ascii=False))
                        
                        print("\n5. 提取关键字段:")
                        # 提取可能需要的字段
                        key_fields = ['cid', 'userId', 'userNick', 'conversationId', 'buyerId', 'buyerNick']
                        extracted_data = {}
                        
                        for field in key_fields:
                            if field in first:
                                extracted_data[field] = first[field]
                                print(f"  ✓ {field}: {first[field]}")
                            else:
                                print(f"  ✗ {field}: 未找到")
                        
                        # 检查嵌套对象
                        if 'buyer' in first:
                            buyer = first['buyer']
                            print(f"\n  buyer信息 ({type(buyer)}): {buyer}")
                            if isinstance(buyer, dict):
                                for k, v in buyer.items():
                                    print(f"    buyer.{k}: {v}")
                                    
                        if 'conversation' in first:
                            conversation = first['conversation']
                            print(f"\n  conversation信息 ({type(conversation)}): {conversation}")
                            if isinstance(conversation, dict):
                                for k, v in conversation.items():
                                    print(f"    conversation.{k}: {v}")
                        
                        print("\n6. 用于聊天消息请求的参数:")
                        print("=" * 30)
                        
                        # 构建聊天消息请求需要的参数
                        chat_params = {}
                        
                        # 从第一个客户记录中提取参数
                        if 'cid' in first:
                            chat_params['cid'] = first['cid']
                        elif 'conversation' in first and isinstance(first['conversation'], dict) and 'cid' in first['conversation']:
                            chat_params['cid'] = first['conversation']['cid']
                            
                        if 'buyer' in first and isinstance(first['buyer'], dict):
                            if 'userId' in first['buyer']:
                                chat_params['userId'] = first['buyer']['userId']
                            if 'userNick' in first['buyer']:
                                chat_params['userNick'] = first['buyer']['userNick']
                        
                        for key, value in chat_params.items():
                            print(f"  {key}: {value}")
                            
                        return chat_params
                    else:
                        print("❌ 客户列表为空")
                else:
                    print("❌ 未找到conversationList字段")
                    print(f"data字段内容: {data}")
            else:
                print(f"❌ data字段不是字典类型: {data}")
        else:
            print("❌ 响应中没有data字段")
            print(f"响应内容: {result}")
            
    except Exception as e:
        print(f"❌ 执行过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()