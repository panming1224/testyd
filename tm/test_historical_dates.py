#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tm_chat_2 import TmallChatManager
import json
import time
from datetime import datetime, timedelta

def test_historical_dates():
    """测试历史日期范围，查找有数据的时间段"""
    
    print("=== 测试历史日期范围 ===")
    
    # 初始化管理器
    manager = TmallChatManager()
    
    # 加载cookies
    cookies_str = manager.load_cookies_from_file()
    if not cookies_str:
        print("无法加载cookies，退出")
        return
    
    results = []
    
    # 测试过去30天的日期
    base_date = datetime.now()
    
    print("开始测试过去30天的日期范围...")
    
    for days_back in range(0, 31):  # 从今天开始往前30天
        test_date = base_date - timedelta(days=days_back)
        date_str = test_date.strftime("%Y%m%d")
        
        print(f"\n--- 测试日期: {date_str} ({test_date.strftime('%Y-%m-%d')}) ---")
        
        start_time = time.time()
        
        try:
            # 调用API
            response = manager.get_customer_list(
                cookies_str, 
                begin_date=date_str, 
                end_date=date_str,
                page_size=10,
                page_index=1
            )
            
            duration = time.time() - start_time
            
            if response:
                result_count = 0
                if 'data' in response and 'result' in response['data']:
                    result_count = len(response['data']['result'])
                
                status = "SUCCESS" if response.get('ret', [''])[0].startswith('SUCCESS') else "ERROR"
                
                result = {
                    "date": date_str,
                    "readable_date": test_date.strftime('%Y-%m-%d'),
                    "days_back": days_back,
                    "status": status,
                    "result_count": result_count,
                    "duration": duration,
                    "has_data": result_count > 0,
                    "response_summary": {
                        "ret": response.get('ret', []),
                        "api": response.get('api', ''),
                        "traceId": response.get('traceId', '')
                    }
                }
                
                if result_count > 0:
                    print(f"✓ 找到数据！日期: {date_str}, 客户数量: {result_count}")
                    # 保存第一个有数据的响应详情
                    result["sample_customers"] = response['data']['result'][:3]  # 保存前3个客户样本
                else:
                    print(f"○ 无数据: {date_str}")
                
                results.append(result)
                
            else:
                print(f"✗ API调用失败: {date_str}")
                results.append({
                    "date": date_str,
                    "readable_date": test_date.strftime('%Y-%m-%d'),
                    "days_back": days_back,
                    "status": "FAILED",
                    "result_count": 0,
                    "duration": duration,
                    "has_data": False,
                    "error": "API调用返回空响应"
                })
        
        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ 异常: {date_str} - {str(e)}")
            results.append({
                "date": date_str,
                "readable_date": test_date.strftime('%Y-%m-%d'),
                "days_back": days_back,
                "status": "EXCEPTION",
                "result_count": 0,
                "duration": duration,
                "has_data": False,
                "error": str(e)
            })
        
        # 避免请求过快
        time.sleep(0.5)
    
    # 统计结果
    total_tests = len(results)
    successful_tests = len([r for r in results if r['status'] == 'SUCCESS'])
    tests_with_data = len([r for r in results if r['has_data']])
    
    summary = {
        "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "tests_with_data": tests_with_data,
        "date_range_tested": f"{(base_date - timedelta(days=30)).strftime('%Y-%m-%d')} 到 {base_date.strftime('%Y-%m-%d')}",
        "results": results
    }
    
    # 保存结果
    output_file = "d:/testyd/tm/historical_dates_test.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 测试完成 ===")
    print(f"总测试: {total_tests}")
    print(f"成功调用: {successful_tests}")
    print(f"有数据的日期: {tests_with_data}")
    
    if tests_with_data > 0:
        data_dates = [r['readable_date'] for r in results if r['has_data']]
        print(f"有数据的日期: {', '.join(data_dates)}")
    else:
        print("所有测试日期都没有数据")
    
    print(f"详细结果已保存到: {output_file}")

if __name__ == "__main__":
    test_historical_dates()