#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from datetime import datetime, timedelta
from tm_chat_2 import TmallChatManager

def test_hourly_query():
    """测试按小时查询来避免数据量过多的问题"""
    print("=== 测试按小时查询聊天记录 ===")
    
    # 初始化管理器
    manager = TmallChatManager()
    cookies_str = manager.load_cookies_from_file()
    
    if not cookies_str:
        print("无法加载cookies")
        return
    
    # 测试今天的不同时间段
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 测试不同的时间范围
    time_ranges = [
        # 尝试更短的时间范围
        (today, today),  # 今天整天
        # 如果还是太多，可以尝试昨天
        ((datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), 
         (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')),
        # 前天
        ((datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'), 
         (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')),
    ]
    
    results = []
    
    for i, (begin_date, end_date) in enumerate(time_ranges):
        print(f"\n--- 测试时间范围 {i+1}: {begin_date} 到 {end_date} ---")
        
        # 尝试不同的页面大小
        for page_size in [1, 3, 5]:
            print(f"\n  测试页面大小: {page_size}")
            
            try:
                customer_response = manager.get_customer_list(
                    cookies_str=cookies_str,
                    begin_date=begin_date,
                    end_date=end_date,
                    customer_nick="",  # 不指定特定客户
                    page_size=page_size,
                    page_index=1
                )
                
                if not customer_response:
                    print(f"    无法获取客户列表")
                    results.append({
                        'begin_date': begin_date,
                        'end_date': end_date,
                        'page_size': page_size,
                        'result': 'FAILED',
                        'error': 'No response',
                        'customer_count': 0
                    })
                    continue
                
                # 检查返回结果
                ret_info = customer_response.get('ret', [])
                if ret_info and isinstance(ret_info, list) and len(ret_info) > 0:
                    ret_message = ret_info[0]
                    if 'APPLICATION_ERROR' in ret_message:
                        print(f"    API错误: {ret_message}")
                        results.append({
                            'begin_date': begin_date,
                            'end_date': end_date,
                            'page_size': page_size,
                            'result': 'API_ERROR',
                            'error': ret_message,
                            'customer_count': 0
                        })
                        continue
                
                # 成功获取数据
                customers = customer_response.get('data', {}).get('result', [])
                customer_count = len(customers)
                
                print(f"    成功! 获取到 {customer_count} 个客户")
                
                results.append({
                    'begin_date': begin_date,
                    'end_date': end_date,
                    'page_size': page_size,
                    'result': 'SUCCESS',
                    'error': None,
                    'customer_count': customer_count,
                    'customers': customers[:3] if customers else []  # 只保存前3个作为样本
                })
                
                # 如果成功了，尝试获取第一个客户的聊天记录
                if customers:
                    print(f"    尝试获取第一个客户的聊天记录...")
                    customer = customers[0]
                    cid = customer.get('cid', {})
                    display_name = customer.get('displayName', 'Unknown')
                    
                    try:
                        messages = manager.get_chat_messages_with_user_info(
                            cookies_str=cookies_str,
                            cid=cid,
                            user_nick=display_name
                        )
                        
                        if messages is None:
                            print(f"      聊天记录获取失败 (None响应)")
                        else:
                            message_count = len(messages) if isinstance(messages, list) else 1
                            print(f"      聊天记录获取成功! {message_count}条消息")
                            
                            # 更新结果
                            results[-1]['chat_test'] = {
                                'result': 'SUCCESS',
                                'message_count': message_count,
                                'customer_name': display_name
                            }
                    
                    except Exception as e:
                        print(f"      聊天记录获取错误: {e}")
                        results[-1]['chat_test'] = {
                            'result': 'ERROR',
                            'error': str(e),
                            'customer_name': display_name
                        }
                
                # 成功了就不需要测试更大的页面大小
                break
                
            except Exception as e:
                print(f"    请求异常: {e}")
                results.append({
                    'begin_date': begin_date,
                    'end_date': end_date,
                    'page_size': page_size,
                    'result': 'EXCEPTION',
                    'error': str(e),
                    'customer_count': 0
                })
            
            # 添加延迟
            time.sleep(1)
        
        # 如果这个时间范围成功了，就不需要测试其他时间范围
        if results and results[-1]['result'] == 'SUCCESS':
            print(f"  找到可用的时间范围: {begin_date} 到 {end_date}")
            break
    
    # 分析结果
    print("\n=== 测试结果汇总 ===")
    
    successful_queries = [r for r in results if r['result'] == 'SUCCESS']
    failed_queries = [r for r in results if r['result'] in ['FAILED', 'API_ERROR', 'EXCEPTION']]
    
    print(f"成功的查询: {len(successful_queries)}")
    print(f"失败的查询: {len(failed_queries)}")
    
    if successful_queries:
        print("\n成功的查询:")
        for r in successful_queries:
            chat_info = r.get('chat_test', {})
            chat_result = chat_info.get('result', 'NOT_TESTED')
            print(f"  - {r['begin_date']} (页面大小{r['page_size']}): {r['customer_count']}个客户, 聊天测试: {chat_result}")
    
    if failed_queries:
        print("\n失败的查询:")
        for r in failed_queries:
            print(f"  - {r['begin_date']} (页面大小{r['page_size']}): {r['error']}")
    
    # 保存详细结果
    result_data = {
        'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_queries': len(results),
        'successful_count': len(successful_queries),
        'failed_count': len(failed_queries),
        'results': results
    }
    
    with open('d:/testyd/tm/hourly_query_test.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细测试结果已保存到: d:/testyd/tm/hourly_query_test.json")

if __name__ == "__main__":
    test_hourly_query()