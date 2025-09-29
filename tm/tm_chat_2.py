# -*- coding: utf-8 -*-
import os
import json
import time
import hashlib
import requests
import pandas as pd
import urllib.parse
from datetime import datetime

class TmallChatManager:
    """天猫客服聊天数据管理器"""
    
    def __init__(self):
        # API配置
        self.APP_KEY = "12574478"
        self.CUSTOMER_LIST_API = "https://h5api.m.taobao.com/h5/mtop.taobao.wireless.amp2.paas.conversation.list/1.0/"
        self.CHAT_MESSAGE_API = "https://h5api.m.taobao.com/h5/mtop.taobao.wireless.amp2.im.paas.message.list/1.0/"
        
        # 文件路径
        self.COOKIE_FILE = "d:/testyd/tm/cookies.txt"
        
        # 文件路径
        self.COOKIE_FILE = "d:/testyd/tm/cookies.txt"
        
        # 缓存相关
        self._cached_cookies = None
        self._cached_token = None
        self._cache_timestamp = 0
        self._cache_duration = 1800  # 30分钟缓存
    
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
            sign_str = f"{token}&{timestamp}&{self.APP_KEY}&{data}"
            return hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"生成签名失败: {e}")
            return None
    
    def get_user_nick_from_cookies(self, cookies_str):
        """从cookies中提取用户昵称"""
        try:
            for cookie in cookies_str.split(';'):
                if 'sn=' in cookie:
                    user_nick = cookie.split('sn=')[1].strip()
                    # URL解码
                    user_nick = urllib.parse.unquote(user_nick)
                    print(f"从cookie中获取到userNick: {user_nick}")
                    return user_nick
            
            # 如果没有找到sn，尝试其他可能的字段
            print("警告：无法从cookie中获取userNick，使用默认值")
            return "cntaobao回力棉娅专卖店:客服"
        except Exception as e:
            print(f"从cookie提取userNick失败: {e}")
            return "cntaobao回力棉娅专卖店:客服"
    
    def load_cookies_from_file(self):
        """从文件加载cookies"""
        try:
            with open(self.COOKIE_FILE, 'r', encoding='utf-8') as f:
                cookie_str = f.read().strip()
                if cookie_str:
                    print("✅ 成功加载cookies")
                    return cookie_str
                else:
                    print("❌ cookies文件为空")
                    return None
        except FileNotFoundError:
            print(f"❌ cookies文件不存在: {self.COOKIE_FILE}")
            return None
        except Exception as e:
            print(f"❌ 读取cookies文件失败: {e}")
            return None
    
    def get_customer_list(self, cookies_str):
        """获取客户列表 - 使用会话列表API获取客户信息"""
        try:
            # 提取token
            token = self.get_h5_token(cookies_str)
            if not token:
                print("无法提取token")
                return None
            
            # 生成时间戳
            timestamp = str(int(time.time() * 1000))
            
            # 构建请求数据 - 使用会话列表API的正确参数
            data = json.dumps({
                "beginDate": "2025-09-25",
                "endDate": "2025-09-25",
                "pageSize": 10,
                "pageNum": 1
            }, separators=(',', ':'))
            
            # 生成签名
            sign = self.generate_sign(token, timestamp, data)
            if not sign:
                print("无法生成签名")
                return None
            
            # 构建请求参数 - 使用正确的会话列表API
            params = {
                'jsv': '2.6.2',
                'appKey': self.APP_KEY,
                't': timestamp,
                'sign': sign,
                'api': 'mtop.taobao.wireless.amp2.paas.conversation.list',  # 使用会话列表API
                'v': '1.0',
                'type': 'jsonp',
                'dataType': 'jsonp',
                'callback': 'mtopjsonp41',
                'data': data
            }
            
            # 设置请求头
            headers = {
                'Cookie': cookies_str,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'Referer': 'https://market.m.taobao.com/',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Sec-Ch-Ua': '"Chromium";v="140", "Google Chrome";v="140", "Not?A_Brand";v="99"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'script',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            print(f"正在获取客户列表...")
            response = requests.get(self.CUSTOMER_LIST_API, params=params, headers=headers)
            
            if response.status_code == 200:
                # 处理JSONP响应
                response_text = response.text.strip()
                
                # 使用正则表达式匹配JSONP格式
                import re
                match = re.match(r'^(\w+)\((.*)\)$', response_text)
                if match:
                    callback_name = match.group(1)
                    json_str = match.group(2)
                    print(f"[OK] 找到JSONP回调函数: {callback_name}")
                    
                    try:
                        data = json.loads(json_str)
                        print("[OK] 成功获取客户列表数据")
                        return data
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] JSON解析失败: {e}")
                        return None
                else:
                    print("[ERROR] 响应格式不是预期的JSONP格式")
                    print(f"响应开头: {response_text[:100]}")
                    return None
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"获取客户列表失败: {e}")
            return None
    
    def get_chat_messages_with_user_info(self, cookies_str, user_nick, customer_data):
        """获取聊天消息，使用从客户数据中解析的参数"""
        try:
            # 从客户数据中解析实际的cid和userId
            actual_cid = None
            if 'cid' in customer_data:
                cid_value = customer_data['cid']
                if isinstance(cid_value, dict) and 'appCid' in cid_value:
                    actual_cid = cid_value['appCid']
                elif isinstance(cid_value, str):
                    # 尝试解析字符串格式的字典
                    try:
                        import ast
                        cid_dict = ast.literal_eval(cid_value)
                        if isinstance(cid_dict, dict) and 'appCid' in cid_dict:
                            actual_cid = cid_dict['appCid']
                        else:
                            actual_cid = cid_value
                    except:
                        actual_cid = cid_value
                else:
                    actual_cid = str(cid_value)
            
            if not actual_cid:
                actual_cid = "2215831800345.1-2219315280500.1#11001"  # 默认值
            
            # 解析userId，支持多种可能的字段名和格式
            actual_user_id = None
            if 'userID' in customer_data:
                user_id_value = customer_data['userID']
                if isinstance(user_id_value, dict) and 'appUid' in user_id_value:
                    actual_user_id = user_id_value['appUid']
                elif isinstance(user_id_value, str):
                    # 尝试解析字符串格式的字典
                    try:
                        import ast
                        user_id_dict = ast.literal_eval(user_id_value)
                        if isinstance(user_id_dict, dict) and 'appUid' in user_id_dict:
                            actual_user_id = user_id_dict['appUid']
                        else:
                            actual_user_id = user_id_value
                    except:
                        actual_user_id = user_id_value
                else:
                    actual_user_id = str(user_id_value)
            elif 'userId' in customer_data:
                actual_user_id = str(customer_data['userId'])
            elif 'buyerId' in customer_data:
                actual_user_id = str(customer_data['buyerId'])
            elif 'customerId' in customer_data:
                actual_user_id = str(customer_data['customerId'])
            
            if not actual_user_id:
                actual_user_id = "2219315280500"  # 默认值
            
            # 使用客户的displayName作为userNick，而不是从cookie中提取的用户昵称
            actual_user_nick = customer_data.get('displayName', user_nick)
            print(f"使用客户displayName作为userNick: {actual_user_nick}")
            print(f"使用解析的参数 - cid: {actual_cid}, userId: {actual_user_id}")
            
            # 提取token
            token = self.get_h5_token(cookies_str)
            if not token:
                print("无法提取token")
                return None
            
            # 生成时间戳
            timestamp = str(int(time.time() * 1000))
            
            # 构建请求数据 - 使用你提供的成功请求的确切参数
            data = json.dumps({
                "cid": actual_cid,
                "userId": actual_user_id,
                "cursor": 1758729600000,  # 使用固定的cursor时间戳
                "forward": True,
                "count": 100,
                "needRecalledContent": True
            }, separators=(',', ':'))
            
            # 生成签名
            sign = self.generate_sign(token, timestamp, data)
            if not sign:
                print("无法生成签名")
                return None
            
            # 构建请求参数
            params = {
                'jsv': '2.6.2',
                'appKey': self.APP_KEY,
                't': timestamp,
                'sign': sign,
                'api': 'mtop.taobao.wireless.amp2.im.paas.message.list',
                'v': '1.0',
                'type': 'jsonp',
                'dataType': 'jsonp',
                'callback': 'mtopjsonp41',
                'data': data
            }
            
            # 设置请求头
            headers = {
                'Cookie': cookies_str,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'Referer': 'https://market.m.taobao.com/',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9'
            }
            
            print(f"正在获取客户 {actual_user_nick} 的聊天消息...")
            response = requests.get(self.CHAT_MESSAGE_API, params=params, headers=headers)
            
            if response.status_code == 200:
                # 处理JSONP响应
                response_text = response.text.strip()
                print(f"API响应前200字符: {response_text[:200]}")
                
                # 使用正则表达式匹配JSONP格式
                import re
                match = re.match(r'^(\w+)\((.*)\)$', response_text)
                if match:
                    callback_name = match.group(1)
                    json_str = match.group(2)
                    
                    try:
                        data = json.loads(json_str)
                        print(f"解析后的数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                        
                        # 检查API返回状态
                        if 'ret' in data and data['ret']:
                            if isinstance(data['ret'], list) and len(data['ret']) > 0:
                                ret_msg = data['ret'][0]
                                print(f"API返回状态: {ret_msg}")
                                
                                # 只有在真正的错误时才处理错误
                                if "APPLICATION_ERROR" in ret_msg or "FAIL" in ret_msg:
                                    print("检测到API错误")
                                    
                                    # 如果是APPLICATION_ERROR，尝试使用更早的cursor重试
                                    if "APPLICATION_ERROR" in ret_msg:
                                        print("检测到APPLICATION_ERROR，尝试使用更早的cursor重试...")
                                        
                                        # 重新构建请求数据，使用更早的cursor
                                        retry_data = json.dumps({
                                            "cid": actual_cid,
                                            "userId": actual_user_id,
                                            "cursor": 1757000000000,  # 使用更早的时间戳
                                            "forward": True,
                                            "count": 100,
                                            "needRecalledContent": True
                                        }, separators=(',', ':'))
                                        
                                        # 重新生成签名
                                        retry_timestamp = str(int(time.time() * 1000))
                                        retry_sign = self.generate_sign(token, retry_timestamp, retry_data)
                                        
                                        retry_params = {
                                            'jsv': '2.6.2',
                                            'appKey': self.APP_KEY,
                                            't': retry_timestamp,
                                            'sign': retry_sign,
                                            'api': 'mtop.taobao.wireless.amp2.im.paas.message.list',
                                            'v': '1.0',
                                            'type': 'jsonp',
                                            'dataType': 'jsonp',
                                            'callback': 'mtopjsonp41',
                                            'data': retry_data
                                        }
                                        
                                        print("重试请求中...")
                                        retry_response = requests.get(self.CHAT_MESSAGE_API, params=retry_params, headers=headers)
                                        
                                        if retry_response.status_code == 200:
                                            retry_response_text = retry_response.text.strip()
                                            retry_match = re.match(r'^(\w+)\((.*)\)$', retry_response_text)
                                            if retry_match:
                                                retry_json_str = retry_match.group(2)
                                                try:
                                                    retry_data = json.loads(retry_json_str)
                                                    if 'ret' in retry_data and retry_data['ret']:
                                                        retry_ret_msg = retry_data['ret'][0]
                                                        if "APPLICATION_ERROR" in retry_ret_msg or "FAIL" in retry_ret_msg:
                                                            print(f"重试仍然失败: {retry_data['ret']}")
                                                            return []
                                                        else:
                                                            print("重试成功！")
                                                            data = retry_data  # 使用重试的数据
                                                except json.JSONDecodeError as e:
                                                    print(f"重试响应JSON解析失败: {e}")
                                                    return []
                                    
                                    # 如果仍然是错误，返回空列表
                                    if 'ret' in data and data['ret']:
                                        ret_msg = data['ret'][0]
                                        if "APPLICATION_ERROR" in ret_msg or "FAIL" in ret_msg:
                                            return []
                                elif "SUCCESS" in ret_msg:
                                    print("API调用成功！")
                        
                        # 处理成功的响应
                        if 'data' in data and data['data']:
                            if 'userMessages' in data['data']:
                                messages = data['data']['userMessages']
                                print(f"成功获取到 {len(messages)} 条聊天消息")
                                
                                # 为每条消息添加客户信息
                                for msg in messages:
                                    msg['customer_nick'] = actual_user_nick
                                
                                return messages
                            else:
                                print(f"响应中没有userMessages数据")
                                # 显示可用的字段以便调试
                                if 'data' in data:
                                    print(f"可用字段: {list(data['data'].keys())}")
                                return []
                        else:
                            print("响应中没有data字段或data为空")
                            return []
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON解析失败: {e}")
                        print(f"原始响应: {response_text[:500]}")
                        return []
                else:
                    print("响应格式不是预期的JSONP格式")
                    print(f"原始响应: {response_text[:200]}")
                    return []
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"获取聊天消息失败: {e}")
            return []
    
    def save_to_excel(self, customer_list, all_chat_messages):
        """保存数据到Excel文件 - 按客户汇总聊天记录格式"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"d:/testyd/tm/天猫客服聊天数据_{timestamp}.xlsx"
            
            # 按客户汇总聊天记录
            customer_chat_summary = {}
            
            # 遍历所有聊天消息，按客户分组
            for msg in all_chat_messages:
                customer_nick = msg.get('customer_nick', '未知客户')
                
                # 提取消息内容
                content = ""
                if 'content' in msg:
                    try:
                        # 尝试解析JSON格式的content
                        content_data = json.loads(msg['content'])
                        if isinstance(content_data, dict):
                            # 优先提取text字段，这是实际的消息内容
                            content = content_data.get('text', content_data.get('summary', content_data.get('title', content_data.get('degradeText', str(content_data)))))
                        else:
                            content = str(content_data)
                    except:
                        # 如果不是JSON，直接使用原始内容
                        content = str(msg['content'])
                
                # 添加发送者信息
                if 'ext' in msg:
                    try:
                        ext_data = json.loads(msg['ext'])
                        sender_nick = ext_data.get('senderNickName', ext_data.get('sender_nick', ''))
                        if sender_nick:
                            content = f"[{sender_nick}]: {content}"
                    except:
                        pass
                
                # 汇总到客户记录中
                if customer_nick not in customer_chat_summary:
                    customer_chat_summary[customer_nick] = []
                
                if content.strip():
                    customer_chat_summary[customer_nick].append(content.strip())
            
            # 创建最终的数据格式 [['客户','聊天记录']]
            excel_data = [['客户', '聊天记录']]  # 表头
            
            for customer_nick, messages in customer_chat_summary.items():
                # 将该客户的所有聊天记录合并到一个单元格中，用换行符分隔
                chat_record = '\n'.join(messages) if messages else '暂无聊天记录'
                excel_data.append([customer_nick, chat_record])
            
            # 创建DataFrame并保存到Excel
            df = pd.DataFrame(excel_data[1:], columns=excel_data[0])  # 跳过表头行
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='客户聊天汇总', index=False)
                
                # 调整列宽以便更好地显示聊天记录
                worksheet = writer.sheets['客户聊天汇总']
                worksheet.column_dimensions['A'].width = 20  # 客户列
                worksheet.column_dimensions['B'].width = 80  # 聊天记录列
                
                # 设置聊天记录列的文本换行
                from openpyxl.styles import Alignment
                for row in range(2, len(excel_data) + 1):  # 从第2行开始（跳过表头）
                    cell = worksheet[f'B{row}']
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
            
            print(f"✅ 客户聊天汇总已保存，共 {len(customer_chat_summary)} 个客户")
            print(f"📁 数据已保存到: {filename}")
            
            return filename
            
        except Exception as e:
            print(f"保存Excel文件失败: {e}")
            return None
    
    def run_full_process(self, test_limit=None):
        """运行完整的客服聊天数据获取流程"""
        print("=== 天猫客服聊天数据获取程序启动 ===")
        
        # 1. 从文件加载cookies
        cookie_str = self.load_cookies_from_file()
        if not cookie_str:
            print("获取cookies失败，程序退出")
            return False
        
        # 2. 获取客服列表
        print("\n正在获取客服列表...")
        customer_list_data = self.get_customer_list(cookie_str)
        
        if not customer_list_data:
            print("获取客服列表失败")
            return False
            
        # 解析客户列表数据
        if 'data' in customer_list_data:
            data_section = customer_list_data['data']
            print(f"data字段的内容: {list(data_section.keys()) if isinstance(data_section, dict) else type(data_section)}")
            
            # 检查data是否为空
            if not data_section:
                print("data字段为空，可能当前时间段内没有客户对话数据")
                print("尝试使用更早的日期范围...")
                # 尝试使用更早的日期
                customer_list_data = self.get_customer_list(cookie_str, begin_date="20240901", end_date="20241231")
                if customer_list_data and 'data' in customer_list_data:
                    data_section = customer_list_data['data']
                    print(f"使用更早日期后的data字段内容: {list(data_section.keys()) if isinstance(data_section, dict) else type(data_section)}")
                else:
                    print("使用更早日期仍然没有数据")
                    return False
            
            # 根据实际返回的数据结构，使用result字段
            if 'result' in data_section:
                customer_list = data_section['result']
                print(f"成功获取客服列表，共 {len(customer_list)} 个客户")
            elif 'conversationList' in data_section:
                customer_list = data_section['conversationList']
                print(f"成功获取客服列表，共 {len(customer_list)} 个客户")
            else:
                print(f"data字段中没有result或conversationList")
                print(f"data字段的完整内容: {data_section}")
                return False
        else:
            print(f"返回数据中没有data字段")
            print(f"完整返回数据: {customer_list_data}")
            return False
        
        # 3. 获取所有客户的聊天消息
        all_chat_messages = []
        successful_customers = 0
        failed_customers = 0
        
        # 设置处理客户数量限制
        if test_limit:
            customers_to_process = customer_list[:test_limit]
            print(f"测试模式：只处理前 {len(customers_to_process)} 个客户的聊天记录（共 {len(customer_list)} 个客户）")
        else:
            customers_to_process = customer_list
            print(f"处理所有 {len(customers_to_process)} 个客户的聊天记录")
        
        # 从cookie中解析店铺用户信息
        cookie_user_info = self.extract_user_info_from_cookie(cookie_str)
        user_nick = cookie_user_info.get('nick', 'unknown') if cookie_user_info else 'unknown'
        
        for i, customer in enumerate(customers_to_process, 1):
            conversation_id = customer.get('conversationId', '') or customer.get('cid', {}).get('appCid', '')
            customer_nick = customer.get('displayName', '未知客户')
            print(f"\n正在获取第 {i}/{len(customers_to_process)} 个客户 {customer_nick} 的聊天消息...")
            
            if not conversation_id:
                print(f"客户 {customer_nick} 没有有效的conversation_id，跳过")
                failed_customers += 1
                continue
            
            # 获取聊天消息
            chat_messages_data = self.get_chat_messages_with_user_info(cookie_str, user_nick, customer)
            
            # 处理消息数据
            if chat_messages_data:
                messages = []
                if isinstance(chat_messages_data, list):
                    messages = chat_messages_data
                elif isinstance(chat_messages_data, dict):
                    # 检查各种可能的消息字段
                    if 'userMessages' in chat_messages_data:
                        messages = chat_messages_data['userMessages']
                    elif 'messageList' in chat_messages_data:
                        messages = chat_messages_data['messageList']
                    elif 'data' in chat_messages_data:
                        data_section = chat_messages_data['data']
                        if 'userMessages' in data_section:
                            messages = data_section['userMessages']
                        elif 'messageList' in data_section:
                            messages = data_section['messageList']
                
                if messages:
                    print(f"成功获取聊天消息，共 {len(messages)} 条")
                    # 为每条消息添加客户信息
                    for msg in messages:
                        if isinstance(msg, dict):
                            msg['customer_id'] = conversation_id
                            msg['customer_nick'] = customer_nick
                    all_chat_messages.extend(messages)
                    successful_customers += 1
                else:
                    print(f"获取客户 {customer_nick} 的聊天消息失败：没有找到消息数据")
                    failed_customers += 1
            else:
                print(f"获取客户 {customer_nick} 的聊天消息失败")
                failed_customers += 1
            
            # 添加延迟避免请求过快
            time.sleep(0.5)
        
        print(f"\n=== 数据获取汇总 ===")
        print(f"处理客户数: {len(customers_to_process)}")
        print(f"总客户数: {len(customer_list)}")
        print(f"成功获取: {successful_customers}")
        print(f"获取失败: {failed_customers}")
        print(f"总消息数: {len(all_chat_messages)}")
        
        if all_chat_messages:
            # 4. 保存数据
            self.save_to_excel(customer_list, all_chat_messages)
            print("=== 程序执行完成 ===")
            return True
        else:
            print("没有获取到任何聊天消息")
            return False
    
    def run(self):
        """主运行函数"""
        try:
            return self.run_full_process()
        except Exception as e:
            print(f"❌ 程序执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    manager = TmallChatManager()
    return manager.run_full_process(test_limit=3)  # 测试模式，只处理前3个客户

if __name__ == "__main__":
    main()