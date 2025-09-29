#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time

def analyze_success_failure_differences():
    """分析成功和失败用户的数据差异"""
    
    print("=== 分析成功和失败用户的数据差异 ===")
    
    # 读取分析结果
    try:
        with open('d:/testyd/tm/error_analysis_result.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"无法读取分析结果文件: {e}")
        return
    
    success_users = data.get('success_users', [])
    error_users = data.get('error_users', [])
    
    print(f"成功用户数: {len(success_users)}")
    print(f"失败用户数: {len(error_users)}")
    
    # 分析成功用户的特征
    print("\n=== 成功用户特征分析 ===")
    success_features = {
        'cid_domains': [],
        'user_domains': [],
        'cid_patterns': [],
        'user_id_patterns': [],
        'display_names': [],
        'biz_types': [],
        'create_times': [],
        'message_counts': []
    }
    
    for user in success_users:
        customer_data = user.get('customer_data', {})
        
        # 提取cid信息
        cid = customer_data.get('cid', {})
        if isinstance(cid, dict):
            success_features['cid_domains'].append(cid.get('domain', ''))
            app_cid = cid.get('appCid', '')
            success_features['cid_patterns'].append(app_cid)
        
        # 提取userID信息
        user_id = customer_data.get('userID', {})
        if isinstance(user_id, dict):
            success_features['user_domains'].append(user_id.get('domain', ''))
            app_uid = user_id.get('appUid', '')
            success_features['user_id_patterns'].append(app_uid)
        
        # 其他信息
        success_features['display_names'].append(customer_data.get('displayName', ''))
        success_features['biz_types'].append(customer_data.get('bizType', ''))
        success_features['create_times'].append(customer_data.get('createTime', ''))
        success_features['message_counts'].append(user.get('message_count', 0))
    
    # 分析失败用户的特征
    print("\n=== 失败用户特征分析 ===")
    failure_features = {
        'cid_domains': [],
        'user_domains': [],
        'cid_patterns': [],
        'user_id_patterns': [],
        'display_names': [],
        'biz_types': [],
        'create_times': [],
        'error_types': []
    }
    
    for user in error_users:
        customer_data = user.get('customer_data', {})
        
        # 提取cid信息
        cid = customer_data.get('cid', {})
        if isinstance(cid, dict):
            failure_features['cid_domains'].append(cid.get('domain', ''))
            app_cid = cid.get('appCid', '')
            failure_features['cid_patterns'].append(app_cid)
        
        # 提取userID信息
        user_id = customer_data.get('userID', {})
        if isinstance(user_id, dict):
            failure_features['user_domains'].append(user_id.get('domain', ''))
            app_uid = user_id.get('appUid', '')
            failure_features['user_id_patterns'].append(app_uid)
        
        # 其他信息
        failure_features['display_names'].append(customer_data.get('displayName', ''))
        failure_features['biz_types'].append(customer_data.get('bizType', ''))
        failure_features['create_times'].append(customer_data.get('createTime', ''))
        failure_features['error_types'].append(user.get('error_type', ''))
    
    # 对比分析
    print("\n=== 对比分析结果 ===")
    
    # 域名对比
    success_cid_domains = set(success_features['cid_domains'])
    failure_cid_domains = set(failure_features['cid_domains'])
    print(f"成功用户CID域名: {success_cid_domains}")
    print(f"失败用户CID域名: {failure_cid_domains}")
    print(f"CID域名差异: {failure_cid_domains - success_cid_domains}")
    
    success_user_domains = set(success_features['user_domains'])
    failure_user_domains = set(failure_features['user_domains'])
    print(f"成功用户ID域名: {success_user_domains}")
    print(f"失败用户ID域名: {failure_user_domains}")
    print(f"用户ID域名差异: {failure_user_domains - success_user_domains}")
    
    # bizType对比
    success_biz_types = set(success_features['biz_types'])
    failure_biz_types = set(failure_features['biz_types'])
    print(f"成功用户bizType: {success_biz_types}")
    print(f"失败用户bizType: {failure_biz_types}")
    print(f"bizType差异: {failure_biz_types - success_biz_types}")
    
    # 时间分析
    success_times = [int(t) for t in success_features['create_times'] if t]
    failure_times = [int(t) for t in failure_features['create_times'] if t]
    
    if success_times and failure_times:
        success_avg_time = sum(success_times) / len(success_times)
        failure_avg_time = sum(failure_times) / len(failure_times)
        
        print(f"成功用户平均创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(success_avg_time/1000))}")
        print(f"失败用户平均创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(failure_avg_time/1000))}")
        
        success_min_time = min(success_times)
        success_max_time = max(success_times)
        failure_min_time = min(failure_times)
        failure_max_time = max(failure_times)
        
        print(f"成功用户时间范围: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(success_min_time/1000))} ~ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(success_max_time/1000))}")
        print(f"失败用户时间范围: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(failure_min_time/1000))} ~ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(failure_max_time/1000))}")
    
    # 消息数量分析
    if success_features['message_counts']:
        avg_messages = sum(success_features['message_counts']) / len(success_features['message_counts'])
        print(f"成功用户平均消息数: {avg_messages:.2f}")
    
    # 用户ID模式分析
    print(f"\n=== 用户ID模式分析 ===")
    success_uids = set(success_features['user_id_patterns'])
    failure_uids = set(failure_features['user_id_patterns'])
    
    print(f"成功用户的唯一用户ID数量: {len(success_uids)}")
    print(f"失败用户的唯一用户ID数量: {len(failure_uids)}")
    
    common_uids = success_uids & failure_uids
    if common_uids:
        print(f"同时出现在成功和失败中的用户ID: {common_uids}")
        print("这表明同一个用户可能有些消息能获取，有些不能获取")
    
    # 保存详细对比结果
    comparison_result = {
        'success_features': success_features,
        'failure_features': failure_features,
        'comparison': {
            'cid_domain_diff': list(failure_cid_domains - success_cid_domains),
            'user_domain_diff': list(failure_user_domains - success_user_domains),
            'biz_type_diff': list(failure_biz_types - success_biz_types),
            'common_user_ids': list(common_uids) if common_uids else []
        },
        'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('d:/testyd/tm/success_failure_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(comparison_result, f, ensure_ascii=False, indent=2)
    
    print("\n详细对比结果已保存到: d:/testyd/tm/success_failure_comparison.json")

if __name__ == "__main__":
    analyze_success_failure_differences()