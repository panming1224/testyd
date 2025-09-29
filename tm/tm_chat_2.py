# -*- coding: utf-8 -*-
import requests
import json
import time
import hashlib
import os
from playwright.sync_api import sync_playwright

class TmallChatManager:
    def __init__(self):
        # API配置 - 修正API地址
        self.APP_KEY = "12574478"
        self.CUSTOMER_LIST_API = "https://h5api.m.taobao.com/h5/mtop.taobao.wireless.amp2.paas.conversation.list/1.0/"
        self.CHAT_MESSAGE_API = "https://h5api.m.taobao.com/h5/mtop.taobao.wireless.amp2.im.paas.message.list/1.0/"
        self.TARGET_URL = "https://myseller.taobao.com/home.htm/app-customer-service/toolpage/Message"
        
        # 浏览器配置
        self.USER_DATA_DIR = r"C:\Users\Administrator\AppData\Local\Google\Chrome\User Data"
        
        # Cookie缓存
        self._cached_cookies = None
        self._cached_token = None
        self._cache_timestamp = None
        self._cache_duration = 3600  # 缓存1小时
    
    def is_cache_valid(self):
        """检查缓存是否有效"""
        if not self._cached_cookies or not self._cache_timestamp:
            return False
        
        # 检查缓存时间
        current_time = time.time()
        if current_time - self._cache_timestamp > self._cache_duration:
            return False
        
        # 检查token是否过期
        if self._cached_token:
            token_info = self.get_h5_token(self._cached_cookies)
            if not token_info:
                return False
        
        return True
    
    def get_cached_cookies(self):
        """获取缓存的cookies"""
        if self.is_cache_valid():
            print("✓ 使用缓存的cookies")
            return self._cached_cookies
        else:
            print("⚠️ 缓存已过期或无效，需要重新获取")
            return None

    def get_cookies_from_browser(self):
        """动态从浏览器获取当前有效的cookies"""
        try:
            print("🔄 正在从浏览器获取最新cookies...")
            
            with sync_playwright() as p:
                # 启动浏览器，使用现有用户数据
                browser = p.chromium.launch_persistent_context(
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
                
                # 创建新页面
                page = browser.new_page()
                
                # 访问天猫商家后台
                print(f"📱 正在访问: {self.TARGET_URL}")
                page.goto(self.TARGET_URL, wait_until='networkidle')
                
                # 等待页面加载完成
                time.sleep(3)
                
                # 获取所有cookies
                cookies = page.context.cookies()
                print(f"✓ 获取到 {len(cookies)} 个cookies")
                
                # 转换为cookie字符串格式
                cookie_pairs = []
                for cookie in cookies:
                    cookie_pairs.append(f"{cookie['name']}={cookie['value']}")
                
                cookies_str = "; ".join(cookie_pairs)
                print(f"✓ Cookies字符串长度: {len(cookies_str)} 字符")
                
                # 验证关键cookies是否存在
                essential_cookies = ['_m_h5_tk', 't', '_tb_token_']
                missing_cookies = []
                for essential in essential_cookies:
                    if essential not in cookies_str:
                        missing_cookies.append(essential)
                
                if missing_cookies:
                    print(f"⚠️ 缺少关键cookies: {missing_cookies}")
                    print("请确保已登录天猫商家后台")
                    browser.close()
                    return None
                
                # 保存当前cookies
                self.current_cookies_str = cookies_str
                browser.close()
                
                print("✓ 成功获取浏览器cookies")
                return cookies_str
                
        except Exception as e:
            print(f"❌ 获取浏览器cookies失败: {e}")
            return None
    
    def get_cookies_from_file(self, file_path=None):
        """从文件获取cookies（备用方案）"""
        try:
            if file_path is None:
                file_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
            
            if not os.path.exists(file_path):
                print(f"⚠️ Cookies文件不存在: {file_path}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                cookies_str = f.read().strip()
                
            if cookies_str:
                print(f"✓ 从文件读取cookies，长度: {len(cookies_str)} 字符")
                self.current_cookies_str = cookies_str
                return cookies_str
            else:
                print("❌ Cookies文件为空")
                return None
                
        except Exception as e:
            print(f"❌ 从文件读取cookies失败: {e}")
            return None
    
    def save_cookies_to_file(self, cookies_str, file_path=None):
        """保存cookies到文件"""
        try:
            if file_path is None:
                file_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cookies_str)
                
            print(f"✓ Cookies已保存到: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 保存cookies失败: {e}")
            return False
    
    def get_current_cookies(self, force_refresh=False):
        """获取当前有效的cookies - 优先使用缓存"""
        if not force_refresh:
            cached = self.get_cached_cookies()
            if cached:
                return cached
        
        print("🔄 获取新的cookies...")
        
        # 尝试从文件获取
        cookies_str = self.get_cookies_from_file()
        if cookies_str:
            # 验证token有效性
            token_info = self.get_h5_token(cookies_str)
            if token_info:
                print("✓ 从文件获取到有效cookies")
                self._update_cache(cookies_str, token_info)
                return cookies_str
        
        # 从浏览器获取
        cookies_str = self.get_cookies_from_browser()
        if cookies_str:
            # 验证并缓存
            token_info = self.get_h5_token(cookies_str)
            if token_info:
                print("✓ 从浏览器获取到有效cookies")
                self._update_cache(cookies_str, token_info)
                # 保存到文件
                self.save_cookies_to_file(cookies_str)
                return cookies_str
        
        print("❌ 无法获取有效的cookies")
        return None
    
    def _update_cache(self, cookies_str, token_info):
        """更新缓存"""
        self._cached_cookies = cookies_str
        self._cached_token = token_info
        self._cache_timestamp = time.time()
        print(f"✓ 已更新cookie缓存，有效期: {self._cache_duration}秒")

    def get_h5_token(self, cookies_str):
        """从cookie字符串中提取h5 token"""
        try:
            print(f"正在从cookies中提取token...")
            print(f"Cookies长度: {len(cookies_str)} 字符")
            
            # 查找_m_h5_tk cookie
            for cookie in cookies_str.split(';'):
                cookie = cookie.strip()
                if '_m_h5_tk=' in cookie:
                    token_value = cookie.split('_m_h5_tk=')[1].strip()
                    print(f"找到_m_h5_tk: {token_value}")
                    
                    # token格式为: token_expireTime，我们只需要token部分
                    if '_' in token_value:
                        token_part = token_value.split('_')[0]
                        expire_time = token_value.split('_')[1] if len(token_value.split('_')) > 1 else None
                        
                        print(f"提取的token: {token_part}")
                        print(f"过期时间戳: {expire_time}")
                        
                        # 检查token是否过期
                        if expire_time:
                            try:
                                expire_timestamp = int(expire_time)
                                current_timestamp = int(time.time() * 1000)
                                print(f"当前时间戳: {current_timestamp}")
                                print(f"token过期时间戳: {expire_timestamp}")
                                
                                if current_timestamp > expire_timestamp:
                                    print("⚠️ Token已过期！")
                                    return None
                                else:
                                    print("✓ Token仍然有效")
                            except ValueError:
                                print("⚠️ 无法解析过期时间戳")
                        
                        return token_part
                    else:
                        print(f"Token格式异常，直接返回: {token_value}")
                        return token_value
            
            print("❌ 未找到_m_h5_tk cookie")
            return None
        except Exception as e:
            print(f"提取token失败: {e}")
            return None
    
    def generate_sign(self, token, timestamp, data):
        """生成签名 - 按照淘宝mtop API标准算法"""
        try:
            # 签名算法: md5(token + '&' + timestamp + '&' + appKey + '&' + data)
            sign_str = f"{token}&{timestamp}&{self.APP_KEY}&{data}"
            print(f"签名字符串: {sign_str}")
            
            # 计算MD5 - 转换为小写
            md5_hash = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
            print(f"生成的签名: {md5_hash}")
            return md5_hash
        except Exception as e:
            print(f"生成签名失败: {e}")
            return None
    
    def extract_essential_cookies(self, cookies_str):
        """提取关键认证cookie参数"""
        try:
            # 根据提供的cookie字符串，提取关键认证参数
            essential_params = [
                't',           # 用户认证token
                '_m_h5_tk',    # H5 token
                '_m_h5_tk_enc', # H5 token加密
                '_tb_token_',  # 淘宝token
                'cookie2',     # 基础认证cookie
                'sgcookie',    # 安全cookie
                'unb',         # 用户编号
                'csg',         # 客户端安全组
                'skt',         # 会话密钥token
                'tfstk'        # 防伪token
            ]
            
            essential_cookies = []
            
            for cookie in cookies_str.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    name = cookie.split('=')[0].strip()
                    if name in essential_params:
                        essential_cookies.append(cookie)
            
            result = '; '.join(essential_cookies)
            print(f"提取的关键cookie参数: {result[:200]}...")
            print(f"精简后cookie长度: {len(result)} 字符")
            
            return result
            
        except Exception as e:
            print(f"提取关键cookie参数失败: {e}")
            return cookies_str  # 失败时返回原始cookie
    
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
                # 访问天猫商家后台客服页面
                print(f"正在访问: {self.TARGET_URL}")
                page.goto(self.TARGET_URL, wait_until="domcontentloaded", timeout=30000)
                
                # 等待页面加载完成
                time.sleep(3)
                
                # 检查是否需要登录
                current_url = page.url
                page_title = page.title()
                print(f"当前页面URL: {current_url}")
                print(f"页面标题: {page_title}")
                
                if "login" in current_url.lower() or "登录" in page_title:
                    print("需要登录，请在浏览器中完成登录...")
                    input("登录完成后，请按回车键继续...")
                
                # 获取cookies
                cookies = context.cookies()
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
    
    def get_customer_list(self, cookies_str, begin_date="20250911", end_date="20250914"):
        """获取客户列表"""
        try:
            # 提取token
            token = self.get_h5_token(cookies_str)
            if not token:
                print("无法提取token")
                return None
            
            # 生成时间戳
            timestamp = str(int(time.time() * 1000))
            
            # 构建请求数据
            request_data = {
                "beginDate": begin_date,
                "endDate": end_date
            }
            
            # 转换为JSON字符串（用于签名计算）
            data_str = json.dumps(request_data, separators=(',', ':'), ensure_ascii=False)
            print(f"请求数据: {data_str}")
            
            # 生成签名
            sign = self.generate_sign(token, timestamp, data_str)
            if not sign:
                print("签名生成失败")
                return None
            
            # 构建POST表单数据
            form_data = {
                'jsv': '2.6.2',
                'appKey': self.APP_KEY,
                't': timestamp,
                'sign': sign,
                'api': 'mtop.taobao.wireless.amp2.paas.conversation.list',
                'v': '1.0',
                'type': 'jsonp',
                'dataType': 'jsonp',
                'callback': 'mtopjsonp3',
                'data': data_str  # 不进行URL编码，让requests自动处理
            }
            
            # 提取关键认证参数，避免HTTP 431错误
            essential_cookies = self.extract_essential_cookies(cookies_str)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": essential_cookies  # 使用精简的cookie参数
            }
            
            print(f"发送POST请求到: {self.CUSTOMER_LIST_API}")
            print(f"表单数据: {form_data}")
            print(f"请求头大小: {len(str(headers))} 字节")
            
            # 发送POST请求
            response = requests.post(self.CUSTOMER_LIST_API, data=form_data, headers=headers, timeout=30)
            
            print(f"响应状态码: {response.status_code}")
            print("=" * 50)
            print("完整响应内容:")
            print(response.text)
            print("=" * 50)
            
            if response.status_code == 200:
                # 处理JSONP响应
                response_text = response.text
                if response_text.startswith('mtopjsonp3(') and response_text.endswith(')'):
                    # 提取JSON部分
                    json_str = response_text[11:-1]  # 去掉 'mtopjsonp3(' 和 ')'
                    try:
                        data = json.loads(json_str)
                        print("✓ 成功获取客服列表数据")
                        return data
                    except json.JSONDecodeError as e:
                        print(f"JSON解析失败: {e}")
                        return None
                else:
                    print("响应格式不是预期的JSONP格式")
                    return None
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"获取客户列表失败: {e}")
            return None
    
    def get_chat_messages(self, cookies_str, conversation_id):
        """获取聊天消息 - 直接复制客户列表的成功逻辑"""
        try:
            # 提取token
            token = self.get_h5_token(cookies_str)
            if not token:
                print("无法提取token")
                return None
            
            # 生成时间戳
            timestamp = str(int(time.time() * 1000))
            
            # 构建请求数据 - 只修改data参数
            request_data = {
                "userNick": "cntaobao回力棉娅专卖店:可云",
                "cid": conversation_id,
                "userId": "2219368700744",
                "cursor": 1757520000000,
                "forward": True,
                "count": 100,
                "needRecalledContent": True
            }
            
            # 转换为JSON字符串（用于签名计算）
            data_str = json.dumps(request_data, separators=(',', ':'), ensure_ascii=False)
            print(f"请求数据: {data_str}")
            
            # 生成签名
            sign = self.generate_sign(token, timestamp, data_str)
            if not sign:
                print("签名生成失败")
                return None
            
            # 构建POST表单数据 - 完全复制客户列表的逻辑，只修改api和callback
            form_data = {
                'jsv': '2.6.2',
                'appKey': self.APP_KEY,
                't': timestamp,
                'sign': sign,
                'api': 'mtop.taobao.wireless.amp2.im.paas.message.list',  # 只修改这里
                'v': '1.0',
                'type': 'jsonp',
                'dataType': 'jsonp',
                'callback': 'mtopjsonp4',  # 修改callback
                'data': data_str
            }
            
            # 提取关键认证参数，避免HTTP 431错误
            essential_cookies = self.extract_essential_cookies(cookies_str)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": essential_cookies  # 使用精简的cookie参数
            }
            
            print(f"发送POST请求到: {self.CHAT_MESSAGE_API}")
            print(f"表单数据: {form_data}")
            print(f"请求头大小: {len(str(headers))} 字节")
            
            # 发送POST请求 - 完全复制客户列表的逻辑
            response = requests.post(self.CHAT_MESSAGE_API, data=form_data, headers=headers, timeout=30)
            
            print(f"响应状态码: {response.status_code}")
            print("=" * 50)
            print("完整响应内容:")
            print(response.text)
            print("=" * 50)
            
            if response.status_code == 200:
                # 处理JSONP响应
                response_text = response.text.strip()
                if response_text.startswith('mtopjsonp4(') and response_text.endswith(')'):
                    # 提取JSON部分
                    json_str = response_text[11:-1]  # 去掉 'mtopjsonp4(' 和 ')'
                    try:
                        data = json.loads(json_str)
                        print("✓ 成功获取聊天消息数据")
                        
                        # 检查返回状态
                        if 'ret' in data and data['ret'] and data['ret'][0].startswith('SUCCESS'):
                            print("✓ API调用成功")
                            if 'data' in data and 'messageList' in data['data']:
                                message_count = len(data['data']['messageList'])
                                print(f"📝 获取到 {message_count} 条聊天消息")
                            return data
                        else:
                            print(f"❌ API返回错误: {data.get('ret', ['未知错误'])}")
                            return data  # 仍然返回数据，让调用者处理
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON解析失败: {e}")
                        print(f"原始响应: {response_text[:200]}...")
                        return None
                else:
                    print("响应格式不是预期的JSONP格式")
                    print(f"响应开头: {response_text[:50]}...")
                    return None
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"获取聊天消息失败: {e}")
            return None
    
    def run_full_process(self):
        """运行完整的客服聊天数据获取流程"""
        print("=== 天猫客服聊天数据获取程序启动 ===")
        
        # 1. 登录并获取cookies
        cookie_str, page, context = self.login_and_get_cookies()
        if not cookie_str:
            print("获取cookies失败，程序退出")
            return
        
        try:
            # 2. 获取客服列表
            print("\n正在获取客服列表...")
            customer_list = self.get_customer_list(cookie_str)
            
            if customer_list:
                print(f"成功获取客服列表，共 {len(customer_list)} 个客服")
                
                # 3. 获取聊天消息（示例：获取第一个客服的消息）
                if customer_list:
                    first_customer = customer_list[0]
                    customer_id = first_customer.get('customerId', '')
                    print(f"\n正在获取客服 {customer_id} 的聊天消息...")
                    
                    chat_messages = self.get_chat_messages(cookie_str, customer_id)
                    
                    if chat_messages:
                        print(f"成功获取聊天消息，共 {len(chat_messages)} 条")
                        
                        # 4. 保存数据
                        self.save_to_excel(customer_list, chat_messages)
                    else:
                        print("获取聊天消息失败")
                else:
                    print("客服列表为空")
            else:
                print("获取客服列表失败")
        
        finally:
            # 清理资源
            if page:
                page.close()
            if context:
                context.close()
        
        print("=== 程序执行完成 ===")

def main():
    """主函数"""
    try:
        manager = TmallChatManager()
        success = manager.run_full_process()
        
        if success:
            print("\n程序执行完成")
        else:
            print("\n程序测试失败，请检查相关配置。")
            
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()