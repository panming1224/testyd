#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多 anti-content 参数浏览器自动化获取方案
使用Selenium或Playwright来获取真实的anti-content参数
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class PddAntiContentExtractor:
    """拼多多 anti-content 参数提取器"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.intercepted_requests = []
        
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            
        # 设置用户代理
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
        
        # 禁用图片加载以提高速度
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')  # 我们需要JavaScript来生成anti-content
        
        # 启用网络日志
        caps = DesiredCapabilities.CHROME
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)
            print("Chrome浏览器驱动初始化成功")
            return True
        except Exception as e:
            print(f"Chrome浏览器驱动初始化失败: {e}")
            return False
    
    def extract_from_network_logs(self):
        """从网络日志中提取anti-content参数"""
        print("从网络日志中提取anti-content参数...")
        
        logs = self.driver.get_log('performance')
        anti_content_values = []
        
        for log in logs:
            message = json.loads(log['message'])
            
            if message['message']['method'] == 'Network.requestWillBeSent':
                request = message['message']['params']['request']
                
                # 检查请求头中的anti-content
                if 'headers' in request and 'anti-content' in request['headers']:
                    anti_content = request['headers']['anti-content']
                    anti_content_values.append({
                        'url': request['url'],
                        'anti_content': anti_content,
                        'timestamp': time.time(),
                        'method': request['method']
                    })
                    print(f"发现anti-content: {anti_content[:50]}...")
        
        return anti_content_values
    
    def simulate_pdd_request(self, cookies_dict=None):
        """模拟拼多多请求过程"""
        print("开始模拟拼多多请求过程...")
        
        if not self.setup_driver():
            return None
            
        try:
            # 访问拼多多商家后台登录页
            login_url = "https://mms.pinduoduo.com"
            print(f"访问登录页面: {login_url}")
            self.driver.get(login_url)
            
            # 如果提供了cookies，设置cookies
            if cookies_dict:
                for name, value in cookies_dict.items():
                    self.driver.add_cookie({'name': name, 'value': value})
                print("已设置cookies")
                
            # 等待页面加载
            time.sleep(3)
            
            # 访问目标页面
            target_url = "https://mms.pinduoduo.com/mms-chat/search?msfrom=mms_sidenav"
            print(f"访问目标页面: {target_url}")
            self.driver.get(target_url)
            
            # 等待页面完全加载
            time.sleep(5)
            
            # 模拟用户操作来触发anti-content生成
            self.simulate_user_actions()
            
            # 提取anti-content参数
            anti_content_values = self.extract_from_network_logs()
            
            return anti_content_values
            
        except Exception as e:
            print(f"模拟请求过程出错: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
    
    def simulate_user_actions(self):
        """模拟用户操作"""
        print("模拟用户操作...")
        
        try:
            # 等待页面元素加载
            wait = WebDriverWait(self.driver, 10)
            
            # 尝试找到搜索框或其他交互元素
            search_elements = self.driver.find_elements(By.TAG_NAME, "input")
            if search_elements:
                search_box = search_elements[0]
                search_box.click()
                search_box.send_keys("test")
                time.sleep(2)
                print("已输入搜索关键词")
            
            # 模拟滚动操作
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # 尝试点击按钮或链接
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            if buttons:
                try:
                    buttons[0].click()
                    time.sleep(2)
                    print("已点击按钮")
                except:
                    pass
                    
        except Exception as e:
            print(f"模拟用户操作出错: {e}")
    
    def extract_js_anti_content_function(self):
        """尝试从页面JavaScript中提取anti-content生成函数"""
        print("尝试提取JavaScript中的anti-content生成函数...")
        
        try:
            # 获取所有script标签的内容
            scripts = self.driver.find_elements(By.TAG_NAME, "script")
            
            for i, script in enumerate(scripts):
                script_content = script.get_attribute('innerHTML')
                if script_content and 'anti' in script_content.lower():
                    print(f"在第{i+1}个script标签中发现可能相关的代码")
                    
                    # 保存到文件以便分析
                    with open(f'd:\\testyd\\promat\\pdd_script_{i}.js', 'w', encoding='utf-8') as f:
                        f.write(script_content)
                    
                    # 查找anti-content相关的函数
                    if 'anti_content' in script_content or 'anticontent' in script_content:
                        print(f"发现anti-content相关代码片段")
                        return script_content
            
            # 尝试执行JavaScript来获取anti-content
            js_code = """
            // 尝试调用可能的anti-content生成函数
            var result = {};
            try {
                if (typeof window.generateAntiContent === 'function') {
                    result.method1 = window.generateAntiContent();
                }
                if (typeof window.getAntiContent === 'function') {
                    result.method2 = window.getAntiContent();
                }
                // 查找全局对象中的相关函数
                for (var key in window) {
                    if (key.toLowerCase().includes('anti') && typeof window[key] === 'function') {
                        try {
                            result[key] = window[key]();
                        } catch(e) {}
                    }
                }
            } catch(e) {
                result.error = e.toString();
            }
            return result;
            """
            
            js_result = self.driver.execute_script(js_code)
            print(f"JavaScript执行结果: {js_result}")
            
            return js_result
            
        except Exception as e:
            print(f"提取JavaScript函数出错: {e}")
            return None

class PddRequestTester:
    """拼多多请求测试器"""
    
    def __init__(self):
        self.session = requests.Session()
        
    def test_anti_content(self, anti_content, cookies_dict):
        """测试anti-content参数是否有效"""
        print(f"测试anti-content参数: {anti_content[:50]}...")
        
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "anti-content": anti_content,
            "cache-control": "max-age=0",
            "content-type": "application/json",
            "origin": "https://mms.pinduoduo.com",
            "referer": "https://mms.pinduoduo.com/mms-chat/search?msfrom=mms_sidenav",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }
        
        url = "https://mms.pinduoduo.com/latitude/search/message/getMessagesUsers"
        data = {
            "pageNum": 1,
            "pageSize": 25,
            "startTime": 1758816000,
            "endTime": 1759420799,
            "keywords": ""
        }
        
        try:
            response = self.session.post(
                url, 
                headers=headers, 
                cookies=cookies_dict, 
                json=data,
                timeout=10
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    if 'success' in json_response and json_response['success']:
                        print("✓ anti-content参数有效！")
                        return True
                    else:
                        print("✗ 请求被拒绝，anti-content可能无效")
                        return False
                except:
                    print("✗ 响应不是有效的JSON格式")
                    return False
            else:
                print("✗ 请求失败")
                return False
                
        except Exception as e:
            print(f"请求测试出错: {e}")
            return False

def main():
    """主函数"""
    print("拼多多 Anti-Content 参数浏览器自动化获取")
    print("=" * 60)
    
    # 从原始文件中提取cookies
    cookies_dict = {
        "api_uid": "CiDokWjR7OB0rQCRCs1zAg==",
        "_nano_fp": "Xpmyl0dJl0gxlpPJno_5_o4j1sC5SRUOQNMb94iP",
        "rckk": "ZMKsB5nx9K69OmMPxs7ZoA1Rh5zy791X",
        "_bee": "ZMKsB5nx9K69OmMPxs7ZoA1Rh5zy791X",
        "PASS_ID": "1-IJpazeqwLDdGAe7CJhk5erhTM5sa223hL9f4THT00dctCkt3j+1hQbtj2gTQ3Hg6aIAa9H/t7RniQ0Id0JdW5g_360624906_172053760",
        "JSESSIONID": "627EB3A27CD8C6A6E341C6F4B75F0E0A"
    }
    
    # 创建提取器
    extractor = PddAntiContentExtractor(headless=False)  # 设置为False以便观察过程
    
    # 提取anti-content参数
    anti_content_values = extractor.simulate_pdd_request(cookies_dict)
    
    if anti_content_values:
        print(f"成功提取到 {len(anti_content_values)} 个anti-content参数")
        
        # 测试每个参数的有效性
        tester = PddRequestTester()
        for item in anti_content_values:
            print(f"\n测试URL: {item['url']}")
            is_valid = tester.test_anti_content(item['anti_content'], cookies_dict)
            item['is_valid'] = is_valid
        
        # 保存结果
        with open('d:\\testyd\\promat\\extracted_anti_content.json', 'w', encoding='utf-8') as f:
            json.dump(anti_content_values, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存到: d:\\testyd\\promat\\extracted_anti_content.json")
        
    else:
        print("未能提取到anti-content参数")
        print("\n建议:")
        print("1. 检查网络连接")
        print("2. 确认cookies是否有效")
        print("3. 检查拼多多网站是否有变化")
        print("4. 尝试手动登录后再运行脚本")

if __name__ == "__main__":
    main()