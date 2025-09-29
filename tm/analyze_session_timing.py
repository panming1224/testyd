#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from datetime import datetime
from tm_chat_2 import TmallChatManager

def analyze_session_timing():
    """分析会话时间和API错误的关系"""
    print("=== 分析会话时间和API错误的关系 ===")
    
    # 初始化管理器
    manager = TmallChatManager()
    cookies_str = manager.load_cookies_from_file()
    
    if not cookies_str:
        print("无法加载cookies")
        return
    
    # 获取客户列表 - 缩小时间范围避免数据量过多
    customer_response = manager.get_customer_list(
        cookies_str=cookies_str,
        begin_date="2025-09-29",
        end_date="2025-09-29",
        customer_nick="",
        page_size=20,
        page_index=1
    )
    
    if not customer_response or 'data' not in customer_response:
        print("无法获取客户列表")
        return
    
    customers = customer_response['data'].get('result', [])
    print(f"获取到 {len(customers)} 个客户")
    
    # 分析每个会话的时间特征
    session_analysis = []
    
    for i, customer in enumerate(customers[:30]):  # 分析前30个
        cid = customer.get('cid', {})
        user_id = customer.get('userID', {})
        create_time = customer.get('createTime', 0)
        display_name = customer.get('displayName', 'Unknown')
        
        # 转换时间戳
        create_datetime = datetime.fromtimestamp(int(create_time) / 1000)
        
        print(f"\n--- 测试会话 {i+1}: {display_name} ---")
        print(f"创建时间: {create_datetime}")
        print(f"CID: {cid}")
        print(f"UserID: {user_id}")
        
        # 尝试获取消息，记录详细信息
        start_time = time.time()
        try:
            messages = manager.get_chat_messages_with_user_info(
                cookies_str=cookies_str,
                cid=cid,
                user_nick=display_name
            )
            
            end_time = time.time()
            request_duration = end_time - start_time
            
            if messages is None:
                result = "FAILED"
                error_type = "None_response"
                message_count = 0
            else:
                result = "SUCCESS"
                error_type = None
                message_count = len(messages) if isinstance(messages, list) else 1
            
            print(f"结果: {result}")
            print(f"请求耗时: {request_duration:.2f}秒")
            print(f"消息数量: {message_count}")
            
        except Exception as e:
            end_time = time.time()
            request_duration = end_time - start_time
            result = "ERROR"
            error_type = str(e)
            message_count = 0
            print(f"结果: {result}")
            print(f"错误: {error_type}")
            print(f"请求耗时: {request_duration:.2f}秒")
        
        # 记录分析数据
        session_info = {
            'index': i + 1,
            'display_name': display_name,
            'create_time': create_time,
            'create_datetime': create_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'cid': cid,
            'user_id': user_id,
            'result': result,
            'error_type': error_type,
            'message_count': message_count,
            'request_duration': request_duration
        }
        
        session_analysis.append(session_info)
        
        # 添加延迟避免请求过快
        time.sleep(1)
    
    # 分析结果
    print("\n=== 分析结果 ===")
    
    successful_sessions = [s for s in session_analysis if s['result'] == 'SUCCESS']
    failed_sessions = [s for s in session_analysis if s['result'] == 'FAILED']
    error_sessions = [s for s in session_analysis if s['result'] == 'ERROR']
    
    print(f"成功会话: {len(successful_sessions)}")
    print(f"失败会话: {len(failed_sessions)}")
    print(f"错误会话: {len(error_sessions)}")
    
    if successful_sessions:
        success_times = [int(s['create_time']) for s in successful_sessions]
        success_durations = [s['request_duration'] for s in successful_sessions]
        print(f"成功会话平均创建时间: {datetime.fromtimestamp(sum(success_times) / len(success_times) / 1000)}")
        print(f"成功会话平均请求耗时: {sum(success_durations) / len(success_durations):.2f}秒")
    
    if failed_sessions:
        failed_times = [int(s['create_time']) for s in failed_sessions]
        failed_durations = [s['request_duration'] for s in failed_sessions]
        print(f"失败会话平均创建时间: {datetime.fromtimestamp(sum(failed_times) / len(failed_times) / 1000)}")
        print(f"失败会话平均请求耗时: {sum(failed_durations) / len(failed_durations):.2f}秒")
    
    # 保存详细分析结果
    result_data = {
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_sessions': len(session_analysis),
        'successful_count': len(successful_sessions),
        'failed_count': len(failed_sessions),
        'error_count': len(error_sessions),
        'sessions': session_analysis,
        'summary': {
            'success_rate': len(successful_sessions) / len(session_analysis) * 100 if session_analysis else 0,
            'avg_success_duration': sum([s['request_duration'] for s in successful_sessions]) / len(successful_sessions) if successful_sessions else 0,
            'avg_failed_duration': sum([s['request_duration'] for s in failed_sessions]) / len(failed_sessions) if failed_sessions else 0
        }
    }
    
    with open('d:/testyd/tm/session_timing_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细分析结果已保存到: d:/testyd/tm/session_timing_analysis.json")
    print(f"成功率: {result_data['summary']['success_rate']:.1f}%")

if __name__ == "__main__":
    analyze_session_timing()