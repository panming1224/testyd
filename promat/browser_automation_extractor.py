#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多 anti-content 参数浏览器自动化提取脚本
使用Selenium自动化浏览器来提取真实的anti-content参数
"""

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests

class PddAntiContentExtractor:
    """拼多多anti-content参数提取器"""
    
    def __init__(self):
        self.driver = None
        self.extracted_params = []
        
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        print("设置Chrome浏览器...")
        
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
        
        # 启用网络日志
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("Chrome浏览器启动成功")
            return True
        except Exception as e:
            print(f"Chrome浏览器启动失败: {e}")
            return False
    
    def extract_network_requests(self):
        """提取网络请求中的anti-content参数"""
        print("提取网络请求...")
        
        # 获取性能日志
        logs = self.driver.get_log('performance')
        
        anti_content_params = []
        
        for log in logs:
            message = json.loads(log['message'])
            
            if message['message']['method'] == 'Network.requestWillBeSent':
                request = message['message']['params']['request']
                url = request.get('url', '')
                
                # 检查URL中的anti-content参数
                if 'anti-content' in url:
                    match = re.search(r'anti-content=([^&]+)', url)
                    if match:
                        anti_content = match.group(1)
                        anti_content_params.append({
                            'url': url,
                            'anti_content': anti_content,
                            'timestamp': time.time(),
                            'method': request.get('method', 'GET'),
                            'headers': request.get('headers', {})
                        })
                        print(f"发现anti-content参数: {anti_content[:50]}...")
                
                # 检查POST请求体中的anti-content
                if request.get('postData'):
                    post_data = request['postData']
                    if 'anti-content' in post_data:
                        match = re.search(r'anti-content["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', post_data)
                        if match:
                            anti_content = match.group(1)
                            anti_content_params.append({
                                'url': url,
                                'anti_content': anti_content,
                                'timestamp': time.time(),
                                'method': 'POST',
                                'post_data': post_data[:200]  # 只保存前200个字符
                            })
                            print(f"发现POST中的anti-content参数: {anti_content[:50]}...")
        
        return anti_content_params
    
    def visit_pdd_pages(self):
        """访问拼多多相关页面"""
        print("访问拼多多页面...")
        
        pages = [
            'https://mms.pinduoduo.com/',
            'https://mms.pinduoduo.com/mms-chat/search?msfrom=mms_sidenav',
            'https://mobile.yangkeduo.com/',
        ]
        
        all_params = []
        
        for page_url in pages:
            try:
                print(f"访问页面: {page_url}")
                self.driver.get(page_url)
                
                # 等待页面加载
                time.sleep(3)
                
                # 尝试触发一些交互
                try:
                    # 滚动页面
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(1)
                    
                    # 查找搜索框并输入
                    search_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"], input[placeholder*="搜索"], input[placeholder*="search"]')
                    if search_inputs:
                        search_inputs[0].click()
                        search_inputs[0].send_keys("测试商品")
                        time.sleep(1)
                    
                except Exception as e:
                    print(f"页面交互失败: {e}")
                
                # 提取网络请求
                params = self.extract_network_requests()
                all_params.extend(params)
                
                time.sleep(2)
                
            except Exception as e:
                print(f"访问页面 {page_url} 失败: {e}")
        
        return all_params
    
    def extract_js_generation_logic(self):
        """尝试提取JavaScript中的anti-content生成逻辑"""
        print("提取JavaScript生成逻辑...")
        
        try:
            # 执行JavaScript来查找anti-content相关函数
            js_code = """
            var antiContentFunctions = [];
            
            // 搜索全局对象中的相关函数
            function searchAntiContentFunctions(obj, path = '') {
                try {
                    for (let key in obj) {
                        if (typeof obj[key] === 'function') {
                            let funcStr = obj[key].toString();
                            if (funcStr.includes('anti-content') || 
                                funcStr.includes('antiContent') || 
                                funcStr.includes('anti_content')) {
                                antiContentFunctions.push({
                                    path: path + '.' + key,
                                    function: funcStr.substring(0, 500)
                                });
                            }
                        } else if (typeof obj[key] === 'object' && obj[key] !== null && path.split('.').length < 3) {
                            searchAntiContentFunctions(obj[key], path + '.' + key);
                        }
                    }
                } catch (e) {
                    // 忽略访问错误
                }
            }
            
            // 搜索window对象
            searchAntiContentFunctions(window, 'window');
            
            return antiContentFunctions;
            """
            
            functions = self.driver.execute_script(js_code)
            
            if functions:
                print(f"找到 {len(functions)} 个相关函数")
                for func in functions:
                    print(f"函数路径: {func['path']}")
                    print(f"函数内容: {func['function'][:100]}...")
            else:
                print("未找到相关的JavaScript函数")
            
            return functions
            
        except Exception as e:
            print(f"JavaScript提取失败: {e}")
            return []
    
    def save_extracted_data(self, params, js_functions):
        """保存提取的数据"""
        data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'extracted_params': params,
            'js_functions': js_functions,
            'total_params': len(params),
            'unique_params': len(set(p['anti_content'] for p in params))
        }
        
        output_file = 'd:\\testyd\\promat\\extracted_anti_content.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"提取数据已保存到: {output_file}")
        return output_file
    
    def run_extraction(self):
        """运行完整的提取流程"""
        print("拼多多 anti-content 参数提取")
        print("=" * 50)
        
        try:
            # 1. 设置浏览器
            if not self.setup_driver():
                return None
            
            # 2. 访问页面并提取参数
            params = self.visit_pdd_pages()
            
            # 3. 提取JavaScript逻辑
            js_functions = self.extract_js_generation_logic()
            
            # 4. 保存数据
            output_file = self.save_extracted_data(params, js_functions)
            
            # 5. 分析结果
            print(f"\n提取完成!")
            print(f"总共提取到 {len(params)} 个anti-content参数")
            print(f"唯一参数数量: {len(set(p['anti_content'] for p in params))}")
            
            if params:
                print("\n样本参数:")
                for i, param in enumerate(params[:3]):
                    print(f"{i+1}. {param['anti_content'][:80]}...")
            
            return {
                'params': params,
                'js_functions': js_functions,
                'output_file': output_file
            }
            
        except Exception as e:
            print(f"提取过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            if self.driver:
                self.driver.quit()
                print("浏览器已关闭")

class AntiContentValidator:
    """anti-content参数验证器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        })
    
    def validate_anti_content(self, anti_content, test_url):
        """验证anti-content参数的有效性"""
        print(f"验证anti-content参数: {anti_content[:50]}...")
        
        try:
            # 构造测试请求
            test_params = {
                'anti-content': anti_content,
                'q': '测试商品',
                'page': 1
            }
            
            response = self.session.get(test_url, params=test_params, timeout=10)
            
            result = {
                'anti_content': anti_content,
                'status_code': response.status_code,
                'valid': response.status_code == 200,
                'response_length': len(response.text),
                'contains_error': 'error' in response.text.lower() or 'forbidden' in response.text.lower()
            }
            
            print(f"验证结果: 状态码={result['status_code']}, 有效={result['valid']}")
            return result
            
        except Exception as e:
            print(f"验证失败: {e}")
            return {
                'anti_content': anti_content,
                'error': str(e),
                'valid': False
            }

def main():
    """主函数"""
    print("开始拼多多anti-content参数提取...")
    
    # 1. 提取参数
    extractor = PddAntiContentExtractor()
    results = extractor.run_extraction()
    
    if not results or not results['params']:
        print("未能提取到anti-content参数")
        return
    
    # 2. 验证参数
    print("\n开始验证提取的参数...")
    validator = AntiContentValidator()
    
    validation_results = []
    test_url = 'https://mms.pinduoduo.com/mms-chat/search'
    
    for param in results['params'][:3]:  # 只验证前3个参数
        result = validator.validate_anti_content(param['anti_content'], test_url)
        validation_results.append(result)
    
    # 3. 保存验证结果
    final_results = {
        'extraction_results': results,
        'validation_results': validation_results,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    output_file = 'd:\\testyd\\promat\\anti_content_final_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n最终结果已保存到: {output_file}")
    
    # 4. 总结
    valid_params = [r for r in validation_results if r.get('valid', False)]
    print(f"\n总结:")
    print(f"提取参数数量: {len(results['params'])}")
    print(f"验证参数数量: {len(validation_results)}")
    print(f"有效参数数量: {len(valid_params)}")

if __name__ == "__main__":
    main()