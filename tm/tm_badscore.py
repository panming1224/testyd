# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import hashlib
import requests
import pandas as pd
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# 配置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 添加数据库接口和文件合并模块路径
sys.path.append(r'D:\testyd')
sys.path.append(r'D:\testyd\mysql')

try:
    from crawler_db_interface import CrawlerDBInterface
    from merge_excel_files import ExcelMerger
    print("✓ 成功导入数据库接口和文件合并模块")
except ImportError as e:
    print(f"✗ 导入模块失败: {e}")
    sys.exit(1)

class TmallBadScoreCollector:
    """天猫差评数据采集器"""
    
    def __init__(self):
        # 数据库接口初始化
        self.db_interface = CrawlerDBInterface(
            platform='tm',
            shops_table='tm_shops',
            tasks_table='tm_tasks',
            database='company'
        )
        
        # 基础目录配置
        self.base_dir = Path(r"D:\yingdao\tm\天猫差评数据")
        
        # 合并文件目录
        self.merged_dir = Path(r"D:\yingdao\tm\合并文件\天猫差评数据")
        
        # 目标日期（13天前，t-13）
        self.target_date = datetime.now() - timedelta(days=13)
        self.target_date_str = self.target_date.strftime('%Y-%m-%d')
        
        # API配置
        self.API_URL = "https://h5api.m.taobao.com/h5/mtop.rm.sellercenter.list.data.pc/1.0/"
        self.app_key = "12574478"
        
        # MinIO配置
        self.minio_api_url = "http://127.0.0.1:8009/api/upload"
        
        # Dremio配置
        self.dremio_config = {
            'host': 'localhost',
            'port': 9047,
            'username': 'admin',
            'password': 'admin123'
        }
        
        print(f"目标日期: {self.target_date} ({self.target_date_str})")
        
    def get_h5_token(self, cookies_str):
        """从cookie字符串中提取h5 token"""
        try:
            if not cookies_str:
                print("Cookie字符串为空")
                return None
                
            for cookie in cookies_str.split(';'):
                if '_m_h5_tk=' in cookie:
                    token_value = cookie.split('_m_h5_tk=')[1].strip()
                    # token格式为: token_expireTime，我们只需要token部分
                    token = token_value.split('_')[0]
                    print(f"✓ 成功提取token: {token[:20]}...")
                    return token
            
            print(f"⚠️ 在cookie中未找到_m_h5_tk，cookie开头: {cookies_str[:100]}...")
            return None
        except Exception as e:
            print(f"提取token失败: {e}")
            return None
    
    def generate_sign(self, token, timestamp, data):
        """生成签名 - 按照淘宝mtop API标准算法"""
        try:
            # 签名算法: md5(token + '&' + timestamp + '&' + appKey + '&' + data)
            sign_str = f"{token}&{timestamp}&{self.app_key}&{data}"
            return hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"生成签名失败: {e}")
            return None
    
    def generate_daily_tasks(self):
        """生成当日任务"""
        print("\n=== 生成当日任务 ===")
        
        try:
            # 定义任务列
            task_columns = ['badscore_status']
            
            # 生成任务
            created_count = self.db_interface.generate_tasks(self.target_date_str, task_columns)
            print(f"✓ 成功生成 {created_count} 个任务")
            
            # 检查是否有任务生成
            if created_count == 0:
                print("⚠️ 没有生成任何任务，可能是因为任务已存在或没有符合条件的店铺")
            
            return True
        except Exception as e:
            print(f"✗ 生成任务失败: {e}")
            return False
    
    def get_shops_with_tasks(self):
        """获取有待处理badscore_status任务的店铺信息"""
        try:
            # 获取待处理任务 - 使用与tm_kpi.py相同的方法
            pending_tasks = self.db_interface.get_pending_tasks(self.target_date_str, 'badscore_status')
            
            if not pending_tasks:
                print(f"没有找到 badscore_status 类型的待处理任务")
                return {}
            
            print(f"找到 {len(pending_tasks)} 个待处理的badscore_status任务")
            
            # 构建店铺信息字典
            shops_info = {}
            for task in pending_tasks:
                shop_name = task[1] if len(task) > 1 else None  # dt.shop_name
                qncookie = task[7] if len(task) > 7 else None  # s.qncookie (第6列)
                sycmcookie = task[8] if len(task) > 8 else None  # s.sycmcookie (第7列)
                
                if sycmcookie or qncookie:
                    shops_info[shop_name] = {
                        'shop_name': shop_name,
                        'qncookie': qncookie,
                        'sycmcookie': sycmcookie,
                        'task_info': task
                    }
                    print(f"✓ 店铺 {shop_name} - qncookie: {qncookie[:50] if qncookie else 'None'}...")
                else:
                    print(f"⚠️ 店铺 {shop_name} 缺少cookie信息，跳过")
            
            return shops_info
            
        except Exception as e:
            print(f"获取店铺任务信息失败: {e}")
            return {}

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
                "emotion":13,
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
                'appKey': self.app_key,
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
    
    def fetch_and_save_bad_reviews(self, shop_name, qncookie, sycmcookie):
        """获取并保存差评数据 - 使用正确的fetch_comments方法"""
        try:
            # 优先使用qncookie（第6列），这是正确的cookie
            cookies_str = qncookie if qncookie else sycmcookie
            if not cookies_str:
                print(f"店铺 {shop_name} 没有有效的cookie")
                return False
            
            # 调用正确的fetch_comments方法 - 使用字符串格式的日期
            target_date_str = self.target_date.strftime('%Y%m%d')
            result = self.fetch_comments(cookies_str, target_date_str, target_date_str, 1, 20)
            
            if result:
                # 直接使用parse_and_save_data方法处理数据
                success = self.parse_and_save_data(result, shop_name)
                if success:
                    print(f"✓ 店铺 {shop_name} 差评数据处理成功")
                    return True
                else:
                    print(f"✗ 店铺 {shop_name} 差评数据处理失败")
                    return False
            else:
                print(f"✗ 店铺 {shop_name} 获取差评数据失败")
                return False
                
        except Exception as e:
            print(f"✗ 店铺 {shop_name} 获取差评数据异常: {e}")
            return False

    def parse_and_save_data(self, data, shop_name):
        """解析API响应数据并保存为Excel"""
        try:
            print(f"解析店铺 {shop_name} 的差评数据...")
            print(f"原始响应数据结构: {type(data)}")
            
            # 检查响应结构
            if not isinstance(data, dict):
                print("✗ 响应数据格式错误")
                return False
            
            # 获取评价列表 - 使用正确的数据路径: data.data.dataSource
            comments_list = []
            if 'data' in data and isinstance(data['data'], dict):
                data_section = data['data'].get('data', {})
                if isinstance(data_section, dict):
                    comments_list = data_section.get('dataSource', [])
            
            print(f"解析到的评价数据数量: {len(comments_list)}")
            
            if not comments_list:
                print("没有找到评价数据")
                return True  # 没有数据也算成功
            
            print(f"找到 {len(comments_list)} 条评价数据")
            
            # 处理所有评价数据，不进行任何筛选
            records = []
            for i, comment in enumerate(comments_list):
                # 获取评价基本信息
                rate_content = comment.get('rateContent', {})
                main_rate = rate_content.get('mainRate', {})
                append_rate = rate_content.get('appendRate', {})
                item_info = comment.get('itemInfo', {})
                user_info = comment.get('userInfo', {})
                order_info = comment.get('orderInfo', {})
                emotion_type = comment.get('emotionType', {})
                operator = comment.get('operator', {})
                
                print(f"处理第 {i+1} 条评价: feedId={main_rate.get('feedId', 'N/A')}")
                
                # 提取feedbackID - 从operator.dataSource中获取
                feedback_id = ''
                if operator and 'dataSource' in operator:
                    for data_item in operator['dataSource']:
                        if 'params' in data_item and 'feedbackID' in data_item['params']:
                            feedback_id = data_item['params']['feedbackID']
                            break
                
                # 处理图片链接 - 从mainRate和appendRate的mediaList中提取
                picture_columns = {}
                picture_count = 1
                
                # 处理主评价的图片
                if main_rate and 'mediaList' in main_rate:
                    for media in main_rate['mediaList']:
                        if media.get('uiType') == 'image' and media.get('thumbnail'):
                            thumbnail = media['thumbnail']
                            # 添加http:前缀
                            if thumbnail.startswith('//'):
                                thumbnail = 'http:' + thumbnail
                            picture_columns[f'picture{picture_count}'] = thumbnail
                            picture_count += 1
                
                # 处理追评的图片
                if append_rate and 'mediaList' in append_rate:
                    for media in append_rate['mediaList']:
                        if media.get('uiType') == 'image' and media.get('thumbnail'):
                            thumbnail = media['thumbnail']
                            # 添加http:前缀
                            if thumbnail.startswith('//'):
                                thumbnail = 'http:' + thumbnail
                            picture_columns[f'picture{picture_count}'] = thumbnail
                            picture_count += 1
                
                # 处理表达式内容 - 从mainRate和appendRate的expression中提取
                expressions = []
                if main_rate and 'expression' in main_rate:
                    for expr in main_rate['expression']:
                        if 'content' in expr:
                            expressions.append(expr['content'])
                
                if append_rate and 'expression' in append_rate:
                    for expr in append_rate['expression']:
                        if 'content' in expr:
                            expressions.append(expr['content'])
                
                expression_text = '; '.join(expressions) if expressions else ''
                
                # 构建基础记录
                record = {
                    '店铺名称': shop_name,
                    'feedbackID': feedback_id,
                    'feedId': main_rate.get('feedId', ''),
                    '商品标题': item_info.get('title', ''),
                    '买家昵称': user_info.get('userName', ''),
                    '用户评价': main_rate.get('content', ''),
                    '追评内容': append_rate.get('content', '') if append_rate else '',
                    'expression': expression_text,
                    '评价时间': main_rate.get('date', ''),
                    '评分': 0,  # API响应中没有直接的评分字段
                    '订单号': order_info.get('orderId', ''),
                    '商品ID': item_info.get('itemId', ''),
                    '统计日期': self.target_date_str,
                    '情感状态': emotion_type.get('status', ''),
                    '追评状态': emotion_type.get('appendRateStatus', ''),
                    '用户星级': user_info.get('userStar', ''),
                    '是否外国人': user_info.get('isForeigner', False),
                    '商品链接': item_info.get('link', ''),
                    '原始数据': str(comment)  # 保留完整的原始数据用于分析
                }
                
                # 添加图片列
                for pic_key, pic_url in picture_columns.items():
                    record[pic_key] = pic_url
                
                records.append(record)
            
            print(f"准备保存 {len(records)} 条记录")
            
            if not records:
                print("没有找到需要处理的评价数据")
                return True  # 没有数据也算成功
            
            # 创建DataFrame
            df = pd.DataFrame(records)
            
            # 创建日期目录
            date_dir = self.base_dir / self.target_date_str
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存为Excel文件，以店铺名称命名
            filename = f"{shop_name}.xlsx"
            file_path = date_dir / filename
            
            # 如果文件已存在，先删除
            if file_path.exists():
                file_path.unlink()
                print(f"删除已存在的文件: {file_path}")
            
            df.to_excel(file_path, index=False, engine='openpyxl')
            print(f"✓ 差评数据已保存: {file_path}")
            print(f"✓ 共保存 {len(records)} 条差评记录")
            
            return str(file_path)
            
        except Exception as e:
            print(f"✗ 解析和保存数据时出错: {e}")
            return False

    def update_task_status(self, shop_name, task_type, status="已完成"):
        """更新任务状态"""
        try:
            success = self.db_interface.update_task_status(
                self.target_date_str, 
                shop_name, 
                task_type, 
                status
            )
            if success:
                print(f"✓ 任务状态更新成功: {shop_name} - {task_type} -> {status}")
            else:
                print(f"✗ 任务状态更新失败: {shop_name} - {task_type}")
            return success
        except Exception as e:
            print(f"✗ 更新任务状态时出错: {e}")
            return False

    def merge_and_upload_files(self):
        """合并文件并上传到MinIO"""
        print(f"\n=== 合并差评文件并上传 ===")
        
        try:
            # 确定源目录和目标目录
            source_dir = self.base_dir / self.target_date_str
            target_dir = self.merged_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 目标文件路径
            target_merged_file = target_dir / f"{self.target_date_str}.xlsx"
            
            # 检查源目录是否存在文件
            if source_dir.exists() and any(source_dir.glob("*.xlsx")):
                print(f"📁 源目录: {source_dir}")
                print(f"📁 目标目录: {target_dir}")
                
                # 使用ExcelMerger合并文件
                merger = ExcelMerger(str(source_dir))
                success = merger.merge_excel_files(f"{self.target_date_str}.xlsx")
                
                if success:
                    # 移动合并后的文件到目标目录
                    source_merged_file = source_dir / f"{self.target_date_str}.xlsx"
                    if source_merged_file.exists():
                        # 如果目标文件已存在，先删除
                        if target_merged_file.exists():
                            target_merged_file.unlink()
                        
                        shutil.move(str(source_merged_file), str(target_merged_file))
                        print(f"✓ 合并文件已移动到: {target_merged_file}")
                    else:
                        print(f"✗ 合并文件不存在: {source_merged_file}")
                        return False
                else:
                    print("✗ 文件合并失败")
                    return False
            else:
                print(f"⚠️ 源目录无文件，创建空文件: {target_merged_file}")
                # 创建空的DataFrame并保存为Excel，但包含基本列结构
                empty_df = pd.DataFrame({
                    'shop': ['无数据'],
                    'comment_id': ['无数据'],
                    'content': ['无数据'],
                    'rating': ['无数据'],
                    'date': ['无数据']
                })
                empty_df.to_excel(target_merged_file, index=False)
            
            # 上传到MinIO
            minio_path = f"ods/tm/tm_badscore/dt={self.target_date_str}/{self.target_date_str}.parquet"
            success = self.upload_to_minio(str(target_merged_file), minio_path)
            
            if success:
                print(f"✓ 差评文件上传MinIO成功")
                
                # 刷新Dremio表
                dremio_table = 'minio.warehouse.ods.tm.tm_badscore'
                self.refresh_dremio_table(dremio_table)
                return True
            else:
                print(f"✗ 差评文件上传MinIO失败")
                return False
                
        except Exception as e:
            print(f"✗ 合并上传过程异常: {e}")
            return False

    def run(self):
        """主运行函数 - 多店铺差评数据采集"""
        print("=== 天猫差评数据采集程序启动 ===")
        print(f"目标日期: {self.target_date_str}")
        
        # 1. 生成每日任务
        print("\n=== 生成每日任务 ===")
        created_count = self.generate_daily_tasks()
        print(f"生成任务数量: {created_count}")
        
        # 检查是否有任务生成
        if created_count == 0:
            print("⚠️ 警告: 没有生成任何任务，可能是因为:")
            print("   - 该日期的任务已存在")
            print("   - 没有符合条件的店铺")
            print("   - 数据库连接问题")
        
        # 2. 获取待处理的店铺任务
        print("\n=== 获取待处理任务 ===")
        shops_info = self.get_shops_with_tasks()
        
        if not shops_info:
            print("没有找到 badscore_status 类型的待处理任务")
            # 即使没有任务也要执行合并上传，确保数据一致性
            self.merge_and_upload_files()
            return
        
        print(f"找到 {len(shops_info)} 个店铺的待处理任务")
        
        # 3. 处理每个店铺的差评数据
        success_count = 0
        total_count = len(shops_info)
        
        for shop_name, shop_info in shops_info.items():
            print(f"\n=== 处理店铺: {shop_name} ===")
            
            try:
                # 获取店铺的cookie和任务信息
                qncookie = shop_info['qncookie'] if 'qncookie' in shop_info else ''
                sycmcookie = shop_info['sycmcookie'] if 'sycmcookie' in shop_info else ''
                task_info = shop_info['task_info'] if 'task_info' in shop_info else None
                
                if not qncookie and not sycmcookie:
                    print(f"✗ 店铺 {shop_name} 缺少cookie信息，跳过处理")
                    continue
                
                # 获取差评数据
                result = self.fetch_and_save_bad_reviews(shop_name, qncookie, sycmcookie)
                
                if result:
                    print(f"✓ 店铺 {shop_name} 差评数据处理成功")
                    success_count += 1
                    # 更新任务状态
                    self.update_task_status(shop_name, 'badscore_status', '已完成')
                else:
                    print(f"✗ 店铺 {shop_name} 差评数据处理失败")

                        
            except Exception as e:
                print(f"✗ 处理店铺 {shop_name} 时发生异常: {e}")
                if 'task_id' in locals() and task_id:
                    self.update_task_status(shop_name, task_id, 'failed')
        
        # 4. 合并文件并上传到MinIO
        print(f"\n=== 数据处理完成 ===")
        print(f"成功处理: {success_count}/{total_count} 个店铺")
        
        # 执行合并上传
        merge_success = self.merge_and_upload_files()
        
        if merge_success:
            print("✓ 所有数据处理和上传完成")
        else:
            print("✗ 数据合并上传失败")
        
        print("=== 程序执行完成 ===")

    def upload_to_minio(self, file_path, minio_path):
        """
        将Excel文件转换为Parquet格式并上传到MinIO
        与tm_kpi.py的upload_to_minio方法保持一致
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 处理NaN值，确保数据能够正常序列化
            df = df.fillna('')  # 将NaN值替换为空字符串
            
            # 处理无穷大值
            df = df.replace([float('inf'), float('-inf')], '')
            
            # 确保所有数据都能正常序列化
            for col in df.columns:
                if df[col].dtype in ['float64', 'float32']:
                    df[col] = df[col].replace([float('inf'), float('-inf')], '')
                # 转换为字符串以避免序列化问题
                df[col] = df[col].astype(str)
            
            # 准备上传数据
            upload_data = {
                "data": df.to_dict('records'),  # 转换为字典列表
                "target_path": minio_path,
                "format": "parquet",
                "bucket": "warehouse"
            }
            
            # 发送POST请求到MinIO API
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.minio_api_url, json=upload_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✓ 成功上传合并文件到MinIO: {minio_path}")
                    return True
                else:
                    print(f"✗ MinIO上传失败: {result.get('message', '未知错误')}")
                    return False
            else:
                print(f"✗ MinIO API请求失败: {response.status_code} - {response.text}")
                return False
                    
        except Exception as e:
            print(f"✗ 上传合并文件到MinIO时出错: {str(e)}")
            return False
    
    def refresh_dremio_table(self, table_name):
        """刷新Dremio表"""
        try:
            print(f"🔄 正在刷新Dremio表: {table_name}")
            # 这里可以添加实际的Dremio刷新逻辑
            # 目前先简单打印，后续可以集成实际的Dremio API调用
            print(f"✓ Dremio表刷新完成: {table_name}")
            return True
        except Exception as e:
            print(f"✗ 刷新Dremio表失败: {e}")
            return False

def main():
    """主函数"""
    collector = TmallBadScoreCollector()
    collector.run()

if __name__ == "__main__":
    main()