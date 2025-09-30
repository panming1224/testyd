# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import time
import json
import requests
import hashlib
import os
import pandas as pd
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 配置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 添加merge_excel_files模块路径
sys.path.append(r'D:\testyd')
try:
    from merge_excel_files import ExcelMerger
except ImportError:
    print("警告：无法导入merge_excel_files模块")

class TmallCommentManager:
    def __init__(self):
        self.USER_DATA_DIR = r"C:\Users\1\AppData\Local\Chromium\User Data"
        self.TARGET_URL = "https://myseller.taobao.com/home.htm/comment-manage/list"
        self.API_URL = "https://h5api.m.taobao.com/h5/mtop.rm.sellercenter.list.data.pc/1.0/"
        self.APP_KEY = "12574478"
        self.cookies = {}
        
    def get_h5_token(self, cookies_str):
        """从cookie字符串中提取h5 token"""
        try:
            for cookie in cookies_str.split(';'):
                if '_m_h5_tk=' in cookie:
                    token_value = cookie.split('_m_h5_tk=')[1].strip()
                    # token格式为: token_expireTime，我们只需要token部分
                    return token_value.split('_')[0]
            return None
        except Exception as e:
            print(f"提取token失败: {e}")
            return None
    
    def generate_sign(self, token, timestamp, data):
        """生成签名 - 按照淘宝mtop API标准算法"""
        try:
            # 签名算法: md5(token + '&' + timestamp + '&' + appKey + '&' + data)
            # 注意：这里的data应该是JSON字符串，不需要额外编码
            sign_str = f"{token}&{timestamp}&{self.APP_KEY}&{data}"
            print(f"签名字符串: {sign_str}")
            
            # 计算MD5 - 转换为小写（根据搜索结果，淘宝API使用小写）
            md5_hash = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
            print(f"生成的签名: {md5_hash}")
            return md5_hash
        except Exception as e:
            print(f"生成签名失败: {e}")
            return None
    
    def login_and_get_cookies(self):
        """登录并获取cookies"""
        print("正在启动浏览器并登录天猫商家后台...")
        
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.USER_DATA_DIR,
                headless=False,
                args=[
                    "--start-maximized",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--profile-directory=Default",
                ],
                no_viewport=True,
                ignore_https_errors=True
            )
            
            page = context.new_page()
            
            try:
                # 访问天猫商家后台
                print(f"正在访问: {self.TARGET_URL}")
                page.goto(self.TARGET_URL, wait_until="domcontentloaded", timeout=30000)
                
                # 等待页面加载完成
                time.sleep(3)
                
                # 检查是否需要登录
                if "login" in page.url.lower() or "登录" in page.title():
                    print("需要登录，请在浏览器中完成登录...")
                    input("登录完成后，请按回车键继续...")
                
                # 获取cookies
                cookies = context.cookies(self.TARGET_URL)
                cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
                print(f"获取到cookies: {cookie_str[:100]}...")
                
                return cookie_str, page, context
                
            except Exception as e:
                print(f"登录过程出错: {e}")
                # 清理资源
                if 'page' in locals() and page:
                    try:
                        page.close()
                    except:
                        pass
                if 'context' in locals() and context:
                    try:
                        context.close()
                    except:
                        pass
                return None, None, None
    
    def fetch_comments(self, cookies_str, start_date="20250924", end_date="20250926", page_num=1, page_size=20):
        """获取评价数据"""
        try:
            # 提取token
            token = self.get_h5_token(cookies_str)
            if not token:
                print("无法提取token，请检查cookies")
                return None
            
            print(f"提取到token: {token}")
            
            # 生成时间戳
            timestamp = str(int(time.time() * 1000))
            print(f"时间戳: {timestamp}")
            
            # 构造请求数据 - 按照天猫提示词文档的格式
            json_body = {
                "pageType": "rateWait4PC",
                "pagination": {
                    "current": page_num,
                    "pageSize": page_size
                },
                "dateRange": [start_date, end_date]
            }
            
            # 将jsonBody转换为字符串用于签名计算
            json_body_str = json.dumps(json_body, separators=(',', ':'))
            
            # 构造完整的请求数据结构
            request_data = {
                "jsonBody": json_body_str
            }
            
            data_str = json.dumps(request_data, separators=(',', ':'))
            print(f"请求数据: {data_str}")
            
            # 生成签名
            sign = self.generate_sign(token, timestamp, data_str)
            if not sign:
                print("签名生成失败")
                return None
            
            # 构造完整的URL - 按照用户提供的格式添加v和syncCookieMode参数
            params = {
                'jsv': '2.6.1',
                'appKey': self.APP_KEY,
                't': timestamp,
                'sign': sign,
                'api': 'mtop.rm.sellercenter.list.data.pc',
                'v': '1.0',
                'syncCookieMode': 'true',
                'type': 'originaljson',
                'dataType': 'json'
            }
            
            # 构造请求头 - 按照天猫提示词文档的格式
            headers = {
                'Cookie': cookies_str,
                'origin': 'https://myseller.taobao.com',
                'referer': 'https://myseller.taobao.com/home.htm/comment-manage/list/rateWait4PC?current=1&pageSize=20&dateRange=20250924%2C20250926',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'accept': 'application/json',
                'accept-language': 'zh-CN,zh;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded',
                'priority': 'u=1, i',
                'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site'
            }
            
            # 构造POST数据 - 按照mtop API标准格式
            # 直接使用JSON字符串作为data参数值，不需要URL编码
            post_data = f'data={data_str}'
            
            print(f"请求URL: {self.API_URL}")
            print(f"请求参数: {params}")
            print(f"POST数据: {post_data}")
            
            # 发送请求
            response = requests.post(
                self.API_URL,
                params=params,
                headers=headers,
                data=post_data,
                timeout=30
            )
            
            print(f"响应状态码: {response.status_code}")
            print("=" * 50)
            print("完整响应内容:")
            print(response.text)
            print("=" * 50)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("[OK] 成功获取评价数据")
                    print(f"响应数据类型: {type(data)}")
                    print(f"响应键: {list(data.keys())}")
                    
                    # 打印详细的数据结构
                    print("\n详细数据结构:")
                    if 'data' in data:
                        print(f"data字段内容: {json.dumps(data['data'], indent=2, ensure_ascii=False)}")
                    if 'ret' in data:
                        print(f"ret字段内容: {data['ret']}")
                    
                    return data
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
                    return None
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"获取评价数据失败: {e}")
            return None
    
    def process_comments_data(self, data):
        """处理评价数据"""
        try:
            if isinstance(data, dict) and 'data' in data:
                comments = data['data'].get('result', {}).get('list', [])
                processed_data = []
                
                for comment in comments:
                    processed_comment = {
                        '评价ID': comment.get('id', ''),
                        '商品标题': comment.get('itemTitle', ''),
                        '买家昵称': comment.get('buyerNick', ''),
                        '评价内容': comment.get('content', ''),
                        '评价时间': comment.get('createTime', ''),
                        '评分': comment.get('rate', ''),
                        '订单号': comment.get('orderId', ''),
                        '商品ID': comment.get('itemId', ''),
                    }
                    processed_data.append(processed_comment)
                
                return processed_data
            else:
                print("数据格式不正确")
                return []
                
        except Exception as e:
            print(f"处理评价数据失败: {e}")
            return []
    
    def save_to_excel(self, data, filename=None):
        """保存数据到Excel"""
        try:
            if not data:
                print("没有数据可保存")
                return False
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"天猫评价数据_{timestamp}.xlsx"
            
            # 确保保存目录存在
            save_dir = Path("d:/testyd/tm")
            save_dir.mkdir(exist_ok=True)
            
            filepath = save_dir / filename
            
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            print(f"数据已保存到: {filepath}")
            return True
            
        except Exception as e:
            print(f"保存Excel文件失败: {e}")
            return False
    
    def login(self):
        """简化的登录方法，返回cookie字符串"""
        cookie_str, page, context = self.login_and_get_cookies()
        
        # 清理资源
        if page:
            page.close()
        if context:
            context.close()
            
        return cookie_str
    
    def run(self):
        """主运行函数"""
        print("=== 天猫评价管理程序启动 ===")
        
        # 1. 登录并获取cookies
        cookie_str, page, context = self.login_and_get_cookies()
        if not cookie_str:
            print("获取cookies失败，程序退出")
            return
        
        try:
            # 2. 获取评价数据
            print("\n正在获取评价数据...")
            comments_data = self.fetch_comments(cookie_str)
            
            if comments_data:
                print("成功获取评价数据")
                
                # 3. 处理数据
                processed_data = self.process_comments_data(comments_data)
                
                if processed_data:
                    print(f"处理了 {len(processed_data)} 条评价数据")
                    
                    # 4. 保存到Excel
                    if self.save_to_excel(processed_data):
                        print("数据保存成功")
                    else:
                        print("数据保存失败")
                else:
                    print("没有处理到有效数据")
            else:
                print("获取评价数据失败")
        
        finally:
            # 清理资源
            if page:
                page.close()
            if context:
                context.close()
        
        print("=== 程序执行完成 ===")

def main():
    """主函数"""
    manager = TmallCommentManager()
    manager.run()

if __name__ == "__main__":
    main()