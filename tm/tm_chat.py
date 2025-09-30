# -*- coding: utf-8 -*-
import os
import json
import time
import hashlib
import requests
import pandas as pd
import urllib.parse
from datetime import datetime
import ast

class TmallChatManager:
    """天猫客服聊天数据管理器"""
    
    def __init__(self):
        # API配置
        self.APP_KEY = "12574478"
        self.CUSTOMER_LIST_API = "https://h5api.m.taobao.com/h5/mtop.taobao.wireless.amp2.paas.conversation.list/1.0/"
        self.CHAT_MESSAGE_API = "https://h5api.m.taobao.com/h5/mtop.taobao.wireless.amp2.im.paas.message.list/1.0/"
        
        # 文件路径
        self.COOKIE_FILE = "d:/testyd/tm/cookies.txt"
    
    def clean_excel_content(self, content):
        """清理Excel不支持的特殊字符"""
        if not content:
            return ""
        
        # 移除或替换Excel不支持的控制字符
        import re
        # 移除控制字符（除了换行符、制表符、回车符）
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        
        # 替换一些特殊的Unicode字符
        content = content.replace('\u0004', '')  # 移除EOT字符
        content = content.replace('\u0001', '')  # 移除SOH字符
        content = content.replace('\u0002', '')  # 移除STX字符
        content = content.replace('\u0003', '')  # 移除ETX字符
        
        return content

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
                    # 清理特殊字符，避免Excel保存错误
                    cleaned_content = self.clean_excel_content(content.strip())
                    customer_chat_summary[customer_nick].append(cleaned_content)
            
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
            print(f"❌ 保存Excel文件失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_cookies_from_file(self):
        """从文件加载cookies"""
        try:
            if os.path.exists(self.COOKIE_FILE):
                with open(self.COOKIE_FILE, 'r', encoding='utf-8') as f:
                    cookie_str = f.read().strip()
                    print(f"[OK] 从文件加载cookies成功，长度: {len(cookie_str)} 字符")
                    return cookie_str
            else:
                print(f"[ERROR] Cookie文件不存在: {self.COOKIE_FILE}")
                return None
        except Exception as e:
            print(f"[ERROR] 加载cookie文件失败: {e}")
            return None

    def get_h5_token(self, cookies_str):
        """从cookie字符串中提取h5 token"""
        try:
            # 查找_m_h5_tk cookie
            for cookie in cookies_str.split(';'):
                cookie = cookie.strip()
                if '_m_h5_tk=' in cookie:
                    token_value = cookie.split('_m_h5_tk=')[1].strip()
                    
                    # token格式为: token_expireTime，我们只需要token部分
                    if '_' in token_value:
                        token_part = token_value.split('_')[0]
                        expire_time = token_value.split('_')[1] if len(token_value.split('_')) > 1 else None
                        
                        # 检查token是否过期
                        if expire_time:
                            try:
                                expire_timestamp = int(expire_time)
                                current_timestamp = int(time.time() * 1000)
                                
                                if current_timestamp > expire_timestamp:
                                    print("[WARNING] Token已过期！")
                                    return None
                                else:
                                    print("[OK] Token仍然有效")
                            except ValueError:
                                print("[WARNING] 无法解析过期时间戳")
                        
                        return token_part
                    else:
                        return token_value
            
            print("[ERROR] 未找到_m_h5_tk cookie")
            return None
        except Exception as e:
            print(f"提取token失败: {e}")
            return None
    
    def generate_sign(self, token, timestamp, data):
        """生成签名 - 按照淘宝mtop API标准算法"""
        try:
            # 签名算法: md5(token + '&' + timestamp + '&' + appKey + '&' + data)
            sign_str = f"{token}&{timestamp}&{self.APP_KEY}&{data}"
            
            # 计算MD5 - 转换为小写
            md5_hash = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
            return md5_hash
        except Exception as e:
            print(f"生成签名失败: {e}")
            return None
    
    def extract_user_info_from_cookie(self, cookies_str):
        """从cookie中提取用户信息"""
        try:
            user_info = {}
            
            for cookie in cookies_str.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    name, value = cookie.split('=', 1)
                    name = name.strip()
                    value = value.strip()
                    
                    # 提取用户ID (unb字段)
                    if name == 'unb':
                        user_info['userId'] = value
                    
                    # 提取用户昵称 (sn字段，需要URL解码)
                    elif name == 'sn':
                        try:
                            decoded_nick = urllib.parse.unquote(value, encoding='utf-8')
                            user_info['nick'] = decoded_nick
                        except Exception as e:
                            print(f"解码用户昵称失败: {e}")
                    
                    # 提取店铺名称 (lid字段，需要URL解码)
                    elif name == 'lid':
                        try:
                            decoded_lid = urllib.parse.unquote(value, encoding='utf-8')
                            user_info['shopName'] = decoded_lid
                        except Exception as e:
                            print(f"解码店铺名称失败: {e}")
            
            # 如果没有找到nick，使用默认值
            if 'nick' not in user_info:
                user_info['nick'] = 'unknown'
            
            return user_info if user_info else None
            
        except Exception as e:
            print(f"从cookie提取用户信息失败: {e}")
            return None
    
    def extract_essential_cookies(self, cookies_str):
        """提取关键认证cookie参数"""
        try:
            # 关键认证参数
            essential_params = [
                't', '_m_h5_tk', '_m_h5_tk_enc', '_tb_token_',
                'cookie2', 'sgcookie', 'unb', 'csg', 'skt', 'tfstk'
            ]
            
            essential_cookies = []
            
            for cookie in cookies_str.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    name = cookie.split('=')[0].strip()
                    if name in essential_params:
                        essential_cookies.append(cookie)
            
            result = '; '.join(essential_cookies)
            return result
            
        except Exception as e:
            print(f"提取关键cookie参数失败: {e}")
            return cookies_str  # 失败时返回原始cookie
    
    def get_customer_list(self, cookies_str, begin_date="20250925", end_date="20250925", page_size=20, page_index=1):
        """获取客户列表"""
        try:
            # 提取token
            token = self.get_h5_token(cookies_str)
            if not token:
                print("无法提取token")
                return None
            
            # 生成时间戳 - 基于begin_date的00:00:00
            from datetime import datetime
            begin_datetime = datetime.strptime(begin_date, "%Y%m%d")
            timestamp = str(int(begin_datetime.timestamp() * 1000))
            
            # 构建请求数据
            request_data = {
                "beginDate": begin_date,
                "endDate": end_date,
                "pageSize": page_size,
                "pageIndex": page_index
            }
            
            # 转换为JSON字符串（用于签名计算）
            data_str = json.dumps(request_data, separators=(',', ':'), ensure_ascii=False)
            
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
                'data': data_str
            }
            
            # 提取关键认证参数
            essential_cookies = self.extract_essential_cookies(cookies_str)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": essential_cookies
            }
            
            # 发送POST请求
            response = requests.post(self.CUSTOMER_LIST_API, data=form_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # 处理JSONP响应
                response_text = response.text.strip()
                
                # 使用正则表达式匹配JSONP格式
                import re
                match = re.match(r'^(\w+)\((.*)\)$', response_text)
                if match:
                    json_str = match.group(2)
                    
                    try:
                        data = json.loads(json_str)
                        print("[OK] 成功获取客服列表数据")
                        return data
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] JSON解析失败: {e}")
                        return None
                else:
                    print("[ERROR] 响应格式不是预期的JSONP格式")
                    return None
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"获取客户列表失败: {e}")
            return None
    
    def get_user_nick_from_cookies(self, cookies_str):
        """从cookies中提取用户昵称"""
        try:
            for cookie in cookies_str.split(';'):
                if 'sn=' in cookie:
                    user_nick = cookie.split('sn=')[1].strip()
                    # URL解码
                    user_nick = urllib.parse.unquote(user_nick)
                    
                    # 确保格式正确：如果不是以cntaobao开头，则添加
                    if not user_nick.startswith('cntaobao'):
                        user_nick = f"cntaobao{user_nick}"
                    
                    print(f"从cookie中获取到userNick: {user_nick}")
                    return user_nick
            
            # 如果没有找到sn，尝试其他可能的字段
            print("警告：无法从cookie中获取userNick，使用默认值")
            return "cntaobao回力棉娅专卖店:可云"
        except Exception as e:
            print(f"从cookie提取userNick失败: {e}")
            return "cntaobao回力棉娅专卖店:可云"
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
            
            # 解析userId，优先提取appUid
            actual_user_id = None
            if 'userID' in customer_data:
                user_id_value = customer_data['userID']
                if isinstance(user_id_value, dict) and 'appUid' in user_id_value:
                    actual_user_id = user_id_value['appUid']
                elif isinstance(user_id_value, str):
                    # 尝试解析字符串格式的字典
                    try:
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
            
            # 确保使用正确的appUid，不使用默认值
            if not actual_user_id:
                print(f"警告：无法提取客户的userId，客户数据: {customer_data}")
                return None
            
            # 使用从cookies中获取的真实用户昵称
            actual_user_nick = self.get_user_nick_from_cookies(cookies_str)
            
            # 提取token
            token = self.get_h5_token(cookies_str)
            if not token:
                print("无法提取token")
                return None
            
            # 生成时间戳
            timestamp = str(int(time.time() * 1000))
            
            # 构建请求数据
            request_data = {
                "userNick": "cntaobao回力棉娅专卖店:可云",  # 固定值
                "cid": actual_cid,
                "userId": actual_user_id,  # 使用实际提取的userId（appUid）
                "cursor": "1758729600000",  # 恢复之前成功的时间戳
                "forward": "true",  # 向前查询
                "count": "20",  # 恢复之前成功的数量
                "needRecalledContent": "true"  # 固定值
            }
            
            print(f"\n=== 聊天消息请求详情 ===")
            print(f"客户: {customer_data.get('displayName', 'Unknown')}")
            print(f"请求URL: {self.CHAT_MESSAGE_API}")
            print(f"请求数据: {request_data}")
            print(f"实际提取的cid: {actual_cid}")
            print(f"实际提取的userId: {actual_user_id}")
            print(f"========================\n")
            
            # 转换为JSON字符串
            data_str = json.dumps(request_data, separators=(',', ':'), ensure_ascii=False)
            
            # 生成签名
            sign = self.generate_sign(token, timestamp, data_str)
            
            # 提取关键认证参数
            essential_cookies = self.extract_essential_cookies(cookies_str)
            
            # 生成动态callback名称
            import random
            callback_num = random.randint(50, 99)
            callback_name = f'mtopjsonp{callback_num}'
            
            # 构建POST表单数据
            form_data = {
                'jsv': '2.6.2',
                'appKey': self.APP_KEY,
                't': timestamp,
                'sign': sign,
                'api': 'mtop.taobao.wireless.amp2.im.paas.message.list',
                'v': '1.0',
                'type': 'jsonp',
                'dataType': 'jsonp',
                'callback': callback_name,
                'data': data_str
            }
            
            # 设置请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": essential_cookies
            }
            
            # 发送请求
            for attempt in range(3):
                response = requests.post(self.CHAT_MESSAGE_API, data=form_data, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    # 处理JSONP响应 - 动态解析callback名称
                    response_text = response.text.strip()
                    
                    # 使用正则表达式动态提取callback名称
                    import re
                    callback_match = re.match(r'^(mtopjsonp\d+)\(', response_text)
                    
                    if callback_match and response_text.endswith(')'):
                        callback_name = callback_match.group(1)
                        # 动态提取JSON部分
                        json_str = response_text[len(callback_name)+1:-1]  # 去掉 'callback_name(' 和 ')'
                        
                        try:
                            data = json.loads(json_str)
                            
                            # 检查返回状态
                            if 'ret' in data and data['ret'] and data['ret'][0].startswith('SUCCESS'):
                                # 获取消息列表
                                if 'data' in data and 'userMessages' in data['data']:
                                    message_list = data['data']['userMessages']
                                    print(f"成功获取到 {len(message_list)} 条消息")
                                    return message_list
                                else:
                                    print("API返回成功但没有消息数据")
                                    print(f"完整响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                                    return []
                            else:
                                # 检查是否直接包含data字段（无ret字段的情况）
                                if 'data' in data and 'userMessages' in data['data']:
                                    message_list = data['data']['userMessages']
                                    print(f"成功获取到 {len(message_list)} 条消息（无ret字段）")
                                    return message_list
                                else:
                                    print(f"API返回错误或无消息数据")
                                    print(f"完整响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                                    return []
                                
                        except json.JSONDecodeError as e:
                            print(f"JSON解析失败: {e}")
                            print(f"响应内容: {response_text[:200]}")
                            return None
                    else:
                        print(f"JSONP格式不匹配: {response_text[:100]}")
                        return None
                else:
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    return None
            
            return None
            
        except Exception as e:
            print(f"获取聊天消息失败: {e}")
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
            
            # 根据实际返回的数据结构，使用result字段
            if 'result' in data_section:
                customer_list = data_section['result']
                print(f"成功获取客服列表，共 {len(customer_list)} 个客户")
            elif 'conversationList' in data_section:
                customer_list = data_section['conversationList']
                print(f"成功获取客服列表，共 {len(customer_list)} 个客户")
            else:
                print(f"data字段中没有result或conversationList")
                return False
        else:
            print(f"返回数据中没有data字段")
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
            time.sleep(1.0)
        
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

def main():
    """主函数"""
    try:
        manager = TmallChatManager()
        success = manager.run_full_process(test_limit=20)  # 测试前20个客户
        
        if success:
            print("\n程序执行完成")
        else:
            print("\n程序测试失败，请检查相关配置。")
            
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()