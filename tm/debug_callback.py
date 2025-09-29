#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试callback参数问题
"""

import re

# 模拟你的curl返回结果
curl_response = """mtopjsonp56({"api":"mtop.taobao.wireless.amp2.im.paas.message.list","data":{"hasMore":"false","nextCursor":"1758812571999","userMessages":[{"bizUnique":"4rtvZsz0Buv8b97919","cid":{"appCid":"2871415106.1-2219315280500.1#11001","domain":"cntaobao"},"content":"{\\"extensions\\":{\\"receiver_nick\\":\\"cntaobao花落无声刘苗苗\\",\\"sender_nick\\":\\"cntaobao回力棉娅专卖店:小余\\"},\\"text\\":\\"\\\\n💕回力女士双罗口中筒袜💕\\\\n┏━━━━━━━●○━┓\\\\n🌈采用新疆棉，柔软亲肤\\\\n🍄吸汗抗菌，有效防臭\\\\n🎮ins风设计，四季适配\\\\n┗━━●○━━━━━━┛\\\\n \\\\u0004\\"}","contentType":"1"}]}})"""

print("=== 调试callback参数问题 ===")
print(f"curl返回的响应开头: {curl_response[:50]}")

# 检查当前脚本的硬编码逻辑
if curl_response.startswith('mtopjsonp4('):
    print("✓ 匹配mtopjsonp4")
else:
    print("✗ 不匹配mtopjsonp4")

# 动态提取callback名称
callback_match = re.match(r'^(mtopjsonp\d+)\(', curl_response)
if callback_match:
    callback_name = callback_match.group(1)
    print(f"实际的callback名称: {callback_name}")
    
    # 动态解析JSON
    if curl_response.startswith(f'{callback_name}(') and curl_response.endswith(')'):
        json_str = curl_response[len(callback_name)+1:-1]
        print(f"提取的JSON长度: {len(json_str)}")
        print(f"JSON开头: {json_str[:100]}")
        
        import json
        try:
            data = json.loads(json_str)
            print("✓ JSON解析成功")
            print(f"API: {data.get('api', 'N/A')}")
            if 'data' in data and 'userMessages' in data['data']:
                messages = data['data']['userMessages']
                print(f"消息数量: {len(messages)}")
            else:
                print("未找到userMessages")
        except json.JSONDecodeError as e:
            print(f"✗ JSON解析失败: {e}")
else:
    print("✗ 无法提取callback名称")