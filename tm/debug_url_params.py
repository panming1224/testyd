#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比用户成功URL参数与脚本生成参数的调试脚本
"""

import json
import urllib.parse
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2_cleaned import TmallChatManager

def parse_user_url():
    """解析用户提供的成功URL"""
    user_url = "https://h5api.m.taobao.com/h5/mtop.taobao.wireless.amp2.im.paas.message.list/1.0/?jsv=2.6.2&appKey=12574478&t=1759160165675&sign=2c87f4a0b839c09029eae668e3e770cf&api=mtop.taobao.wireless.amp2.im.paas.message.list&v=1.0&type=jsonp&dataType=jsonp&callback=mtopjsonp57&data=%7B%22userNick%22%3A%22cntaobao%E5%9B%9E%E5%8A%9B%E6%A3%89%E5%A8%85%E4%B8%93%E5%8D%96%E5%BA%97%3A%E5%8F%AF%E4%BA%91%22%2C%22cid%22%3A%222032298289.1-2219315280500.1%2311001%22%2C%22userId%22%3A%222219315280500%22%2C%22cursor%22%3A1758729600000%2C%22forward%22%3Atrue%2C%22count%22%3A100%2C%22needRecalledContent%22%3Atrue%7D"
    
    # 解析URL参数
    parsed_url = urllib.parse.urlparse(user_url)
    params = urllib.parse.parse_qs(parsed_url.query)
    
    # 将参数转换为单值字典
    user_params = {}
    for key, value_list in params.items():
        user_params[key] = value_list[0] if value_list else ""
    
    # 解码data参数
    if 'data' in user_params:
        decoded_data = urllib.parse.unquote(user_params['data'])
        user_params['data_decoded'] = decoded_data
        try:
            user_params['data_json'] = json.loads(decoded_data)
        except:
            user_params['data_json'] = "解析失败"
    
    return user_params

def generate_script_params():
    """生成脚本的参数（模拟effie沫儿客户）"""
    manager = TmallChatManager()
    
    # 加载cookies
    cookie_str = manager.load_cookies_from_file()
    if not cookie_str:
        print("无法加载cookies")
        return None
    
    # 获取客户列表
    customer_list_data = manager.get_customer_list(cookie_str)
    if not customer_list_data or 'data' not in customer_list_data:
        print("无法获取客户列表")
        return None
    
    data_section = customer_list_data['data']
    if 'result' in data_section:
        customer_list = data_section['result']
    elif 'conversationList' in data_section:
        customer_list = data_section['conversationList']
    else:
        print("无法解析客户列表")
        return None
    
    # 找到effie沫儿客户
    effie_customer = None
    for customer in customer_list:
        if customer.get('displayName') == 'effie沫儿':
            effie_customer = customer
            break
    
    if not effie_customer:
        print("未找到effie沫儿客户")
        return None
    
    print(f"找到effie沫儿客户数据: {json.dumps(effie_customer, ensure_ascii=False, indent=2)}")
    
    # 模拟脚本生成参数的过程
    import time
    import ast
    
    # 解析cid
    cid_value = effie_customer.get('cid', '')
    if isinstance(cid_value, dict) and 'appCid' in cid_value:
        actual_cid = cid_value['appCid']
    elif isinstance(cid_value, str):
        try:
            cid_dict = ast.literal_eval(cid_value)
            if isinstance(cid_dict, dict) and 'appCid' in cid_dict:
                actual_cid = cid_dict['appCid']
            else:
                actual_cid = cid_value
        except:
            actual_cid = cid_value
    else:
        actual_cid = str(cid_value)
    
    if not actual_cid:
        actual_cid = "2215831800345.1-2219315280500.1#11001"
    
    # 解析userId
    actual_user_id = None
    if 'userID' in effie_customer:
        user_id_value = effie_customer['userID']
        if isinstance(user_id_value, dict) and 'appUid' in user_id_value:
            actual_user_id = user_id_value['appUid']
        elif isinstance(user_id_value, str):
            try:
                user_id_dict = ast.literal_eval(user_id_value)
                if isinstance(user_id_dict, dict) and 'appUid' in user_id_dict:
                    actual_user_id = user_id_dict['appUid']
                else:
                    actual_user_id = user_id_value
            except:
                actual_user_id = user_id_value
        else:
            actual_user_id = str(user_id_value)
    
    if not actual_user_id:
        actual_user_id = "2219315280500"
    
    # 使用客户的displayName作为userNick
    actual_user_nick = effie_customer.get('displayName', 'effie沫儿')
    
    # 提取token
    token = manager.get_h5_token(cookie_str)
    if not token:
        print("无法提取token")
        return None
    
    # 生成时间戳
    timestamp = str(int(time.time() * 1000))
    
    # 构建请求数据
    request_data = {
        "userNick": actual_user_nick,
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
    sign = manager.generate_sign(token, timestamp, data_str)
    
    # 构建POST表单数据
    script_params = {
        'jsv': '2.6.2',
        'appKey': manager.APP_KEY,
        't': timestamp,
        'sign': sign,
        'api': 'mtop.taobao.wireless.amp2.im.paas.message.list',
        'v': '1.0',
        'type': 'jsonp',
        'dataType': 'jsonp',
        'callback': 'mtopjsonp4',
        'data': data_str,
        'data_json': request_data
    }
    
    return script_params

def compare_params():
    """对比用户URL参数与脚本生成的参数"""
    print("=== 解析用户成功URL参数 ===")
    user_params = parse_user_url()
    print(json.dumps(user_params, ensure_ascii=False, indent=2))
    
    print("\n=== 生成脚本参数 ===")
    script_params = generate_script_params()
    if not script_params:
        return
    
    print(json.dumps(script_params, ensure_ascii=False, indent=2))
    
    print("\n=== 参数对比分析 ===")
    
    # 对比关键参数
    key_params = ['jsv', 'appKey', 'api', 'v', 'type', 'dataType', 'callback']
    
    for param in key_params:
        user_val = user_params.get(param, "缺失")
        script_val = script_params.get(param, "缺失")
        match = "✓" if user_val == script_val else "✗"
        print(f"{param}: 用户={user_val}, 脚本={script_val} {match}")
    
    # 对比data内容
    print("\n=== data参数对比 ===")
    user_data = user_params.get('data_json', {})
    script_data = script_params.get('data_json', {})
    
    if isinstance(user_data, dict) and isinstance(script_data, dict):
        for key in set(list(user_data.keys()) + list(script_data.keys())):
            user_val = user_data.get(key, "缺失")
            script_val = script_data.get(key, "缺失")
            match = "✓" if user_val == script_val else "✗"
            print(f"{key}: 用户={user_val}, 脚本={script_val} {match}")
    else:
        print(f"用户data: {user_data}")
        print(f"脚本data: {script_data}")

if __name__ == "__main__":
    compare_params()