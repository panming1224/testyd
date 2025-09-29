#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用tm_chat.py中的方法获取天猫商家后台cookies
"""

from playwright.sync_api import sync_playwright
import time

class SimpleCookieGetter:
    def __init__(self):
        self.USER_DATA_DIR = r"C:\Users\1\AppData\Local\Chromium\User Data"
        self.TARGET_URL = "https://myseller.taobao.com/home.htm/comment-manage/list"
        self.cookies_file = "cookies.txt"
        
    def get_cookies(self):
        """获取cookies并保存到文件"""
        print("正在启动浏览器并访问天猫商家后台...")
        
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
                current_url = page.url
                print(f"当前页面URL: {current_url}")
                
                if "login" in current_url.lower() or "登录" in page.title():
                    print("需要登录，请在浏览器中完成登录...")
                    input("登录完成后，请按回车键继续...")
                
                # 获取cookies
                cookies = context.cookies(self.TARGET_URL)
                if not cookies:
                    print("未获取到cookies")
                    return False
                    
                cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
                
                # 保存到文件
                with open(self.cookies_file, 'w', encoding='utf-8') as f:
                    f.write(cookie_str)
                
                print(f"✅ 成功获取并保存cookies到: {self.cookies_file}")
                print(f"📊 获取到 {len(cookies)} 个cookie")
                print(f"🔍 Cookie预览: {cookie_str[:100]}...")
                
                # 检查关键cookie
                key_cookies = ['_m_h5_tk', '_tb_token_', 'cookie2']
                print("\n🔍 关键Cookie检查:")
                for key in key_cookies:
                    if key in cookie_str:
                        print(f"  ✅ {key}: 存在")
                    else:
                        print(f"  ❌ {key}: 缺失")
                
                return True
                
            except Exception as e:
                print(f"获取cookies过程出错: {e}")
                return False
            
            finally:
                # 清理资源
                if page:
                    page.close()
                if context:
                    context.close()

def main():
    """主函数"""
    print("🎯 天猫商家后台Cookie获取工具")
    print("=" * 50)
    
    getter = SimpleCookieGetter()
    success = getter.get_cookies()
    
    if success:
        print("\n🎉 Cookie获取成功！")
        print("📝 接下来可以使用获取到的cookies进行API调用")
    else:
        print("\n❌ Cookie获取失败")

if __name__ == "__main__":
    main()