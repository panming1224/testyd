#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from datetime import datetime
from tm_chat_2 import TmallChatManager

def debug_api_params():
    """调试API参数传递问题"""
    print("=== 调试API参数传递问题 ===")
    
    # 初始化管理器
    manager = TmallChatManager()
    cookies_str = manager.load_cookies_from_file()
    
    if not cookies_str:
        print("无法加载cookies")
        return
    
    # 测试不同的参数组合
    test_cases = [
        {
            "name": "不指定客户昵称",
            "params": {
                "begin_date": "20250929",
                "end_date": "20250929",
                "page_size": 1,
                "page_index": 1
            }
        },
        {
            "name": "指定客户昵称",
            "params": {
                "begin_date": "20250929", 
                "end_date": "20250929",
                "customer_nick": "花落无声刘苗苗",
                "page_size": 1,
                "page_index": 1
            }
        },
        {
            "name": "更短时间范围",
            "params": {
                "begin_date": "20250930",
                "end_date": "20250930", 
                "page_size": 1,
                "page_index": 1
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- 测试用例 {i+1}: {test_case['name']} ---")
        print(f"参数: {test_case['params']}")
        
        start_time = time.time()
        
        try:
            response = manager.get_customer_list(
                cookies_str=cookies_str,
                **test_case['params']
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response:
                # 分析响应结构
                print(f"✅ 请求成功，耗时: {duration:.2f}秒")
                print(f"响应类型: {type(response)}")
                
                if isinstance(response, dict):
                    print(f"响应键: {list(response.keys())}")
                    
                    # 检查是否有错误信息
                    if 'ret' in response:
                        ret_info = response['ret']
                        print(f"返回状态: {ret_info}")
                        
                        if isinstance(ret_info, list) and len(ret_info) > 0:
                            error_code = ret_info[0]
                            if error_code != "SUCCESS::调用成功":
                                print(f"❌ API错误: {error_code}")
                    
                    # 检查数据部分
                    if 'data' in response:
                        data = response['data']
                        print(f"数据类型: {type(data)}")
                        
                        if isinstance(data, dict):
                            print(f"数据键: {list(data.keys())}")
                            
                            if 'result' in data:
                                result = data['result']
                                if isinstance(result, list):
                                    print(f"结果数量: {len(result)}")
                                else:
                                    print(f"结果类型: {type(result)}")
                                    print(f"结果内容: {result}")
                
                results.append({
                    'test_case': test_case['name'],
                    'params': test_case['params'],
                    'success': True,
                    'duration': duration,
                    'response_summary': {
                        'type': str(type(response)),
                        'keys': list(response.keys()) if isinstance(response, dict) else None,
                        'has_data': 'data' in response if isinstance(response, dict) else False
                    },
                    'full_response': response
                })
                
            else:
                end_time = time.time()
                duration = end_time - start_time
                print(f"❌ 请求失败，耗时: {duration:.2f}秒")
                
                results.append({
                    'test_case': test_case['name'],
                    'params': test_case['params'],
                    'success': False,
                    'duration': duration,
                    'response_summary': None,
                    'full_response': None
                })
        
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"💥 请求异常: {e}，耗时: {duration:.2f}秒")
            
            results.append({
                'test_case': test_case['name'],
                'params': test_case['params'],
                'success': False,
                'duration': duration,
                'error': str(e),
                'response_summary': None,
                'full_response': None
            })
        
        # 添加延迟
        time.sleep(3)
    
    # 保存调试结果
    debug_data = {
        'debug_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_tests': len(test_cases),
        'results': results
    }
    
    with open('d:/testyd/tm/api_params_debug.json', 'w', encoding='utf-8') as f:
        json.dump(debug_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 调试结果汇总 ===")
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"成功测试: {len(successful_tests)}")
    print(f"失败测试: {len(failed_tests)}")
    
    if successful_tests:
        print("\n成功的测试:")
        for r in successful_tests:
            print(f"  - {r['test_case']}: {r['duration']:.2f}秒")
    
    if failed_tests:
        print("\n失败的测试:")
        for r in failed_tests:
            error_info = r.get('error', '未知错误')
            print(f"  - {r['test_case']}: {error_info}")
    
    print(f"\n详细调试结果已保存到: d:/testyd/tm/api_params_debug.json")

if __name__ == "__main__":
    debug_api_params()