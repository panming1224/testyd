#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的cookie格式
"""

import sys
sys.path.append(r'D:\testyd\mysql')
from crawler_db_interface import CrawlerDBInterface

def check_cookies():
    db = CrawlerDBInterface('tm_shops', 'tm_tasks', 'tm', 'company')
    shops = db.get_all_shops()
    
    if shops:
        print(f'店铺数量: {len(shops)}')
        for i, shop in enumerate(shops[:3]):  # 只看前3个店铺
            print(f'\n店铺 {i+1}: {shop.get("shop_name", "未知")}')
            qncookie = shop.get('qncookie', '')
            print(f'qncookie长度: {len(qncookie) if qncookie else 0}')
            
            if qncookie:
                print(f'qncookie前100字符: {qncookie[:100]}')
                # 检查是否包含_m_h5_tk
                if '_m_h5_tk=' in qncookie:
                    print('✓ 包含_m_h5_tk token')
                    # 尝试提取token
                    for cookie in qncookie.split(';'):
                        if '_m_h5_tk=' in cookie:
                            token_value = cookie.split('_m_h5_tk=')[1].strip()
                            token = token_value.split('_')[0]
                            print(f'提取的token: {token[:20]}...')
                            break
                else:
                    print('✗ 不包含_m_h5_tk token')
                    # 检查其他可能的token格式
                    if 'token' in qncookie.lower():
                        print('包含其他token格式')
            else:
                print('qncookie为空')
            print('-' * 50)
    else:
        print('没有找到店铺信息')

if __name__ == "__main__":
    check_cookies()