#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie优化工具
用于清理和压缩过大的cookie，解决"Request Header Or Cookie Too Large"问题
"""

import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mysql'))
from crawler_db_interface import CrawlerDBInterface

class CookieOptimizer:
    """Cookie优化器"""
    
    def __init__(self):
        self.db = CrawlerDBInterface(platform='tm', shops_table='tm_shops', tasks_table='tm_tasks', database='company')
        
        # 定义关键cookie字段（保留这些，删除其他）
        self.essential_cookies = {
            'cna', 'isg', 'l', 'tfstk', 'x', 'cookie2', 'v', 't',
            'uc1', 'uc3', 'uc4', 'existShop', 'lgc', 'dnk', 'tracknick',
            'sn', 'unb', '_tb_token_', 'cookie1', 'csg', 'munb', 'thw',
            'JSESSIONID', '_m_h5_tk', '_m_h5_tk_enc', 'mt', 'swfstore',
            'x5sec', 'xlly_s', 'hng', 'enc', 'alitrackid', 'lastalitrackid'
        }
    
    def parse_cookie_string(self, cookie_string):
        """解析cookie字符串为字典"""
        if not cookie_string:
            return {}
        
        cookies = {}
        # 分割cookie字符串
        for item in cookie_string.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        return cookies
    
    def optimize_cookie(self, cookie_string, max_length=4000):
        """
        优化cookie字符串
        1. 保留关键cookie
        2. 删除重复和无用cookie
        3. 压缩到指定长度以内
        """
        if not cookie_string:
            return cookie_string
        
        # 解析cookie
        cookies = self.parse_cookie_string(cookie_string)
        
        # 第一步：保留关键cookie
        essential_cookies = {}
        for key, value in cookies.items():
            if key in self.essential_cookies:
                essential_cookies[key] = value
        
        # 第二步：如果关键cookie长度已经超标，进一步压缩
        essential_cookie_str = '; '.join([f"{k}={v}" for k, v in essential_cookies.items()])
        
        if len(essential_cookie_str) <= max_length:
            return essential_cookie_str
        
        # 第三步：如果还是太长，按优先级保留最重要的cookie
        priority_cookies = ['_tb_token_', 'cookie2', 'cna', 'isg', 'l', 'tfstk', 'x', 'v', 't']
        
        final_cookies = {}
        current_length = 0
        
        for cookie_name in priority_cookies:
            if cookie_name in essential_cookies:
                cookie_pair = f"{cookie_name}={essential_cookies[cookie_name]}"
                if current_length + len(cookie_pair) + 2 <= max_length:  # +2 for '; '
                    final_cookies[cookie_name] = essential_cookies[cookie_name]
                    current_length += len(cookie_pair) + 2
        
        # 添加其他关键cookie直到达到长度限制
        for key, value in essential_cookies.items():
            if key not in final_cookies:
                cookie_pair = f"{key}={value}"
                if current_length + len(cookie_pair) + 2 <= max_length:
                    final_cookies[key] = value
                    current_length += len(cookie_pair) + 2
        
        return '; '.join([f"{k}={v}" for k, v in final_cookies.items()])
    
    def optimize_shop_cookie(self, shop_name, max_length=4000):
        """优化指定店铺的cookie"""
        conn = self.db.pool.connection()
        try:
            cursor = conn.cursor()
            
            # 获取当前cookie
            cursor.execute('SELECT sycmcookie FROM tm_shops WHERE shop_name = %s', (shop_name,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                print(f"店铺 {shop_name} 没有找到cookie")
                return False
            
            original_cookie = result[0]
            original_length = len(original_cookie)
            
            # 优化cookie
            optimized_cookie = self.optimize_cookie(original_cookie, max_length)
            optimized_length = len(optimized_cookie)
            
            # 更新数据库
            cursor.execute('UPDATE tm_shops SET sycmcookie = %s WHERE shop_name = %s', 
                         (optimized_cookie, shop_name))
            conn.commit()
            
            print(f"店铺 {shop_name}:")
            print(f"  原始长度: {original_length} 字符")
            print(f"  优化后长度: {optimized_length} 字符")
            print(f"  压缩率: {((original_length - optimized_length) / original_length * 100):.1f}%")
            
            return True
            
        except Exception as e:
            print(f"优化店铺 {shop_name} cookie失败: {e}")
            return False
        finally:
            conn.close()
    
    def optimize_all_large_cookies(self, threshold=8000, max_length=4000):
        """优化所有过大的cookie"""
        conn = self.db.pool.connection()
        try:
            cursor = conn.cursor()
            
            # 查找所有cookie长度超过阈值的店铺
            cursor.execute('''
                SELECT shop_name, LENGTH(sycmcookie) as cookie_length 
                FROM tm_shops 
                WHERE sycmcookie IS NOT NULL 
                AND LENGTH(sycmcookie) > %s
                ORDER BY cookie_length DESC
            ''', (threshold,))
            
            large_cookie_shops = cursor.fetchall()
            
            if not large_cookie_shops:
                print(f"没有找到cookie长度超过 {threshold} 字符的店铺")
                return True
            
            print(f"找到 {len(large_cookie_shops)} 个cookie过大的店铺:")
            for shop_name, cookie_length in large_cookie_shops:
                print(f"  {shop_name}: {cookie_length} 字符")
            
            print("\n开始优化...")
            
            success_count = 0
            for shop_name, cookie_length in large_cookie_shops:
                if self.optimize_shop_cookie(shop_name, max_length):
                    success_count += 1
            
            print(f"\n优化完成: {success_count}/{len(large_cookie_shops)} 个店铺成功")
            return success_count == len(large_cookie_shops)
            
        except Exception as e:
            print(f"批量优化cookie失败: {e}")
            return False
        finally:
            conn.close()

def main():
    """主函数"""
    optimizer = CookieOptimizer()
    
    print("=== Cookie优化工具 ===")
    print("正在检查和优化过大的cookie...")
    
    # 优化所有长度超过8000字符的cookie，压缩到4000字符以内
    success = optimizer.optimize_all_large_cookies(threshold=8000, max_length=4000)
    
    if success:
        print("\n✓ Cookie优化完成！")
    else:
        print("\n✗ Cookie优化过程中出现错误")

if __name__ == "__main__":
    main()