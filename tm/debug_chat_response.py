# -*- coding: utf-8 -*-
"""
调试聊天消息API响应结构
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2 import TmallChatManager
import json
import requests
import time
import hashlib

def debug_chat_response():
    """调试聊天消息API响应"""
    print("=" * 60)
    print("调试聊天消息API响应结构")
    print("=" * 60)
    
    manager = TmallChatManager()
    
    # 加载cookies
    cookies_str = manager.load_cookies_from_file()
    if not cookies_str:
        print("❌ 无法加载cookies文件")
        return False
    
    print("✅ 成功加载cookies")
    
    # 获取客户列表
    print("\n1. 获取客户列表...")
    customer_data = manager.get_customer_list(
        cookies_str=cookies_str,
        begin_date="20250920",
        end_date="20250925",
        page_size=3,
        page_index=1
    )
    
    if not customer_data or 'data' not in customer_data:
        print("❌ 无法获取客户列表")
        return False
    
    customers = customer_data['data']['result']
    if not customers:
        print("❌ 客户列表为空")
        return False
    
    print(f"✅ 找到 {len(customers)} 个客户")
    
    # 提取用户信息
    user_info = manager.extract_user_info_from_cookie(cookies_str)
    if not user_info or 'userNick' not in user_info:
        print("❌ 无法提取用户昵称")
        return False
    
    user_nick = user_info['userNick']
    print(f"✅ 用户昵称: {user_nick}")
    
    # 测试第一个客户的聊天消息
    customer = customers[0]
    display_name = customer.get('displayName', '未知客户')
    print(f"\n2. 调试客户: {display_name}")
    
    # 显示客户的完整信息
    print(f"\n客户完整数据:")
    print(json.dumps(customer, ensure_ascii=False, indent=2))
    
    try:
        # 直接调用底层API方法来获取完整响应
        print(f"\n3. 调用聊天消息API...")
        
        # 提取客户信息
        actual_cid = None
        actual_user_id = None
        
        # 从客户数据中提取cid和userId
        if 'cid' in customer and 'appCid' in customer['cid']:
            actual_cid = customer['cid']['appCid']
        elif 'conversationId' in customer:
            actual_cid = customer['conversationId']
        
        if 'userID' in customer and 'appUid' in customer['userID']:
            actual_user_id = customer['userID']['appUid']
        elif 'userId' in customer:
            actual_user_id = customer['userId']
        elif 'buyerUserId' in customer:
            actual_user_id = customer['buyerUserId']
        
        if not actual_cid or not actual_user_id:
            print(f"❌ 无法提取cid或userId")
            return False
        
        print(f"提取的参数 - cid: {actual_cid}, userId: {actual_user_id}")
        
        # 手动构建请求来获取完整响应
        
        # 提取token
        token = manager.get_h5_token(cookies_str)
        if not token:
            print("无法提取token")
            return False
        
        # 生成时间戳
        timestamp = str(int(time.time() * 1000))
        
        # 构建请求数据
        request_data = {
            "userNick": user_nick,
            "cid": actual_cid,
            "userId": actual_user_id,
            "cursor": 1757520000000,
            "forward": True,
            "count": 100,
            "needRecalledContent": True
        }
        
        # 转换为JSON字符串
        data_str = json.dumps(request_data, separators=(',', ':'), ensure_ascii=False)
        
        # 生成签名
        sign_str = f"{token}&{timestamp}&12574478&{data_str}"
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        
        # 提取关键认证参数
        essential_cookies = manager.extract_essential_cookies(cookies_str)
        
        # 构建POST表单数据
        form_data = {
            'jsv': '2.6.2',
            'appKey': '12574478',
            't': timestamp,
            'sign': sign,
            'api': 'mtop.taobao.wireless.amp2.im.paas.message.list',
            'v': '1.0',
            'type': 'jsonp',
            'dataType': 'jsonp',
            'callback': 'mtopjsonp4',
            'data': data_str
        }
        
        # 设置请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": essential_cookies
        }
        
        # 发送请求
        response = requests.post("https://h5api.m.taobao.com/h5/mtop.taobao.wireless.amp2.im.paas.message.list/1.0/", 
                               data=form_data, headers=headers, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 处理JSONP响应
            response_text = response.text.strip()
            if response_text.startswith('mtopjsonp4(') and response_text.endswith(')'):
                # 提取JSON部分
                json_str = response_text[11:-1]
                chat_messages = json.loads(json_str)
            else:
                print("响应格式不是预期的JSONP格式")
                return False
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return False
        
        if chat_messages:
            print(f"✅ API调用成功，响应类型: {type(chat_messages)}")
            
            # 完整显示响应结构
            print(f"\n完整API响应:")
            print(json.dumps(chat_messages, ensure_ascii=False, indent=2))
            
            # 分析响应结构
            if isinstance(chat_messages, dict):
                print(f"\n响应顶级字段: {list(chat_messages.keys())}")
                
                # 检查ret字段
                if 'ret' in chat_messages:
                    ret_info = chat_messages['ret']
                    print(f"ret字段: {ret_info}")
                
                # 检查data字段
                if 'data' in chat_messages:
                    data = chat_messages['data']
                    print(f"data字段类型: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"data字段内容: {list(data.keys())}")
                        
                        # 递归显示data的所有内容
                        def show_nested_structure(obj, prefix=""):
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    print(f"{prefix}{key}: {type(value)}")
                                    if isinstance(value, (dict, list)) and len(str(value)) < 500:
                                        show_nested_structure(value, prefix + "  ")
                                    elif isinstance(value, str) and len(value) < 100:
                                        print(f"{prefix}  值: {value}")
                            elif isinstance(obj, list):
                                print(f"{prefix}列表长度: {len(obj)}")
                                if obj and len(str(obj[0])) < 500:
                                    print(f"{prefix}第一个元素类型: {type(obj[0])}")
                                    if isinstance(obj[0], dict):
                                        show_nested_structure(obj[0], prefix + "  ")
                        
                        print(f"\ndata详细结构:")
                        show_nested_structure(data, "  ")
                    else:
                        print(f"data内容: {data}")
                
                # 检查其他可能的消息字段
                possible_message_fields = ['messages', 'messageList', 'result', 'content', 'items']
                for field in possible_message_fields:
                    if field in chat_messages:
                        print(f"\n找到可能的消息字段 '{field}': {type(chat_messages[field])}")
                        if isinstance(chat_messages[field], list):
                            print(f"  列表长度: {len(chat_messages[field])}")
                            if chat_messages[field]:
                                print(f"  第一个元素: {chat_messages[field][0]}")
            
            return True
        else:
            print(f"❌ API调用失败，返回空结果")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_chat_response()