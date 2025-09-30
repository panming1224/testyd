# -*- coding: utf-8 -*-
"""
天猫KPI数据获取工具 - 升级版
功能一：获取自制报表数据
功能二：获取售后解决分析数据
集成任务生成模块和数据库动态读取功能
"""

import requests
import time
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import shutil

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

class TmallKpiCollector:
    def __init__(self):
        # 数据库接口初始化
        self.db_interface = CrawlerDBInterface(
            platform='tm',
            shops_table='tm_shops',
            tasks_table='tm_tasks',
            database='company'
        )
        
        # 基础目录配置
        self.base_report_dir = Path(r"D:\yingdao\tm\天猫客服绩效自制报表")
        self.base_analysis_dir = Path(r"D:\yingdao\tm\天猫客服绩效解决分析报表")
        
        # 合并文件目录
        self.merged_report_dir = Path(r"D:\yingdao\tm\合并文件\天猫客服绩效自制报表")
        self.merged_analysis_dir = Path(r"D:\yingdao\tm\合并文件\天猫客服绩效解决分析报表")
        
        # 创建所有必要目录
        for directory in [self.base_report_dir, self.base_analysis_dir, 
                         self.merged_report_dir, self.merged_analysis_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # 使用T-4日期（4天前）
        self.target_date = (datetime.now() - timedelta(days=4)).strftime('%Y%m%d')
        self.target_date_str = (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')
        
        # MinIO配置
        self.minio_api_url = "http://127.0.0.1:8009/api/upload"
        
        print(f"目标日期: {self.target_date} ({self.target_date_str})")
        
    def generate_daily_tasks(self):
        """生成当日任务"""
        print("\n=== 生成当日任务 ===")
        
        try:
            # 定义任务列
            task_columns = ['kpi_self_status', 'kpi_offical_status']
            
            # 生成任务
            created_count = self.db_interface.generate_tasks(self.target_date_str, task_columns)
            print(f"✓ 成功生成 {created_count} 个任务")
            
            return True
        except Exception as e:
            print(f"✗ 生成任务失败: {e}")
            return False
    
    def get_shops_with_tasks(self, task_type):
        """获取有指定任务类型的店铺信息"""
        try:
            # 获取待处理任务
            pending_tasks = self.db_interface.get_pending_tasks(self.target_date_str, task_type)
            
            if not pending_tasks:
                print(f"没有找到 {task_type} 类型的待处理任务")
                return []
            
            # 获取店铺详细信息
            shops_info = []
            for task in pending_tasks:
                # task是tuple格式，根据JOIN查询的字段顺序：
                # 索引0: time_period, 索引1: shop_name, 索引2-15: 店铺表字段
                # 索引8: sycmcookie, 索引13: reportTemplateId
                shop_name = task[1]  # dt.shop_name
                sycmcookie = task[8] if len(task) > 8 else None  # s.sycmcookie
                report_template_id = task[13] if len(task) > 13 else None  # s.reportTemplateId
                
                if sycmcookie:
                    shops_info.append({
                        'shop_name': shop_name,
                        'sycmcookie': sycmcookie,
                        'reportTemplateId': report_template_id,
                        'task_id': None  # tuple中没有task_id字段
                    })
                    print(f"✓ 店铺 {shop_name}, reportTemplateId: {report_template_id}")
                else:
                    print(f"⚠️ 店铺 {shop_name} 缺少cookie信息，跳过")
            
            print(f"✓ 找到 {len(shops_info)} 个有效店铺")
            return shops_info
            
        except Exception as e:
            print(f"✗ 获取店铺任务信息失败: {e}")
            return []
    
    def get_custom_report_data_for_shop(self, shop_name, cookies, report_template_id=None):
        """为单个店铺获取自制报表数据"""
        print(f"\n--- 获取店铺 {shop_name} 的自制报表数据 ---")
        
        # 使用店铺特定的reportTemplateId，如果没有则使用默认值
        template_id = report_template_id or "7798"
        print(f"使用reportTemplateId: {template_id}")
        
        # 步骤1：发送获取数据请求
        print("步骤1: 发送获取数据请求...")
        
        url = f"https://sycm.taobao.com/csp/api/user/customize/async-excel?startDate={self.target_date}&endDate={self.target_date}&dateType=day&dateRange=cz&reportTemplateId={template_id}&bizCode=selfMadeReport"
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "bx-v": "2.5.31",
            "Cookie": cookies,
            "priority": "u=1, i",
            "referer": "https://sycm.taobao.com/qos/service/self_made_report",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers)
            print(f"请求状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    task_id = data.get('data')
                    print(f"✓ 获取到任务ID: {task_id}")
                    
                    if task_id:
                        # 步骤2：循环检查下载状态
                        return self._check_download_status_for_shop(task_id, cookies, shop_name, 'report')
                    else:
                        print("✗ 未获取到有效的任务ID")
                        return False
                except json.JSONDecodeError as e:
                    print(f"✗ JSON解析失败: {e}")
                    return False
            else:
                print(f"✗ 请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ 发送请求时出错: {e}")
            return False
    
    def get_aftersale_analysis_data_for_shop(self, shop_name, cookies):
        """为单个店铺获取售后解决分析数据"""
        print(f"\n--- 获取店铺 {shop_name} 的售后解决分析数据 ---")
        
        url = f"https://sycm.taobao.com/csp/api/aftsale/cst/list.json?dateRange=cz&endDate={self.target_date}&excludeDates=&orderBy=aftSaleRplyUv&pageSize=10&wwGroup=&accountId=&qnGroupId=&dateType=day&page=1&startDate={self.target_date}&order=desc"
        
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "bx-v": "2.5.31",
            "Cookie": cookies,
            "priority": "u=1, i",
            "referer": "https://sycm.taobao.com/qos/service/frame/customer/performance/new",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sycm-referer": "/qos/service/frame/customer/performance/new",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }
        
        try:
            print("发送售后解决分析数据请求...")
            response = requests.get(url, headers=headers)
            print(f"请求状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ 获取到响应数据")
                
                # 解析数据
                return self._parse_and_save_analysis_data_for_shop(data, shop_name)
            else:
                print(f"✗ 请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ 获取售后解决分析数据时出错: {e}")
            return False
    
    def _check_download_status_for_shop(self, task_id, cookies, shop_name, data_type):
        """检查下载状态并下载文件（针对单个店铺）"""
        print("步骤2: 循环检查下载状态...")
        
        status_url = "https://sycm.taobao.com/csp/api/file/task-list.json?pageNo=1&pageSize=10&bizCode=selfMadeReport"
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "bx-v": "2.5.31",
            "Cookie": cookies,
            "priority": "u=1, i",
            "referer": "https://sycm.taobao.com/qos/service/self_made_report",
            "sec-ch-ua": '"Not=A?Brand";v="24", "Chromium";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }
        
        max_attempts = 60
        attempt = 0
        
        while attempt < max_attempts:
            try:
                print(f"第{attempt + 1}次检查下载状态...")
                
                response = requests.get(status_url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('code') == 200 and data.get('data', {}).get('result'):
                        results = data['data']['result']
                        
                        # 查找对应的任务
                        for result in results:
                            if result.get('id') == task_id:
                                message = result.get('message', '')
                                print(f"任务状态: {message}")
                                
                                if message == "下载完成":
                                    print("✓ 下载完成，获取下载链接...")
                                    return self._download_report_file_for_shop(task_id, cookies, shop_name, data_type)
                                
                        print("任务还在处理中，等待5秒后重试...")
                        time.sleep(5)
                        attempt += 1
                    else:
                        print("未找到任务信息，等待5秒后重试...")
                        time.sleep(5)
                        attempt += 1
                else:
                    print(f"检查状态失败: {response.status_code}")
                    time.sleep(5)
                    attempt += 1
                    
            except Exception as e:
                print(f"检查状态时出错: {e}")
                time.sleep(5)
                attempt += 1
        
        print("✗ 达到最大尝试次数，下载失败")
        return False
    
    def _download_report_file_for_shop(self, task_id, cookies, shop_name, data_type):
        """下载报表文件（针对单个店铺）"""
        print("步骤3: 获取下载链接并下载文件...")
        
        download_url = f"https://sycm.taobao.com/csp/api/file/url?id={task_id}"
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "bx-v": "2.5.31",
            "Cookie": cookies,
            "priority": "u=1, i",
            "referer": "https://sycm.taobao.com/qos/service/self_made_report",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(download_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                file_url = data.get('data')
                
                if file_url:
                    print(f"✓ 获取到下载链接: {file_url}")
                    
                    # 创建日期目录
                    date_dir = self.base_report_dir / self.target_date_str
                    date_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 下载文件，以店铺名称命名
                    filename = f"{shop_name}.xlsx"
                    file_path = date_dir / filename
                    
                    # 如果文件已存在，先删除
                    if file_path.exists():
                        file_path.unlink()
                        print(f"删除已存在的文件: {file_path}")
                    
                    # 下载文件
                    file_response = requests.get(file_url, stream=True)
                    file_response.raise_for_status()
                    
                    with open(file_path, 'wb') as f:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    print(f"✓ 文件下载完成: {file_path}")
                    return str(file_path)
                else:
                    print("✗ 未获取到有效的下载链接")
                    return False
            else:
                print(f"✗ 获取下载链接失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ 下载文件时出错: {e}")
            return False
    
    def _parse_and_save_analysis_data_for_shop(self, data, shop_name):
        """解析并保存售后解决分析数据（针对单个店铺）"""
        print("解析并保存售后解决分析数据...")
        
        try:
            if data.get('code') == 0 and data.get('data'):
                analysis_data = data['data']
                
                # 提取数据
                records = []
                
                # 添加汇总数据
                if 'sumResult' in analysis_data:
                    sum_result = analysis_data['sumResult']
                    records.append({
                        '店铺名称': shop_name,
                        '客服姓名': '汇总',
                        '售后回复UV': sum_result.get('aftSaleRplyUv', {}).get('value', 0),
                        '首次未解决UV': sum_result.get('fstUnsolvUv', {}).get('value', 0),
                        '72小时解决率': '',
                        '统计日期': self.target_date_str
                    })
                
                # 添加平均数据
                if 'avgResult' in analysis_data:
                    avg_result = analysis_data['avgResult']
                    records.append({
                        '店铺名称': shop_name,
                        '客服姓名': '平均值',
                        '售后回复UV': avg_result.get('aftSaleRplyUv', {}).get('value', 0),
                        '首次未解决UV': avg_result.get('fstUnsolvUv', {}).get('value', 0),
                        '72小时解决率': avg_result.get('fcr72Rate', {}).get('value', 0),
                        '统计日期': self.target_date_str
                    })
                
                # 添加详细数据
                if 'data' in analysis_data:
                    for item in analysis_data['data']:
                        records.append({
                            '店铺名称': shop_name,
                            '客服姓名': item.get('psnNickName', {}).get('value', ''),
                            '售后回复UV': item.get('aftSaleRplyUv', {}).get('value', 0),
                            '首次未解决UV': item.get('fstUnsolvUv', {}).get('value', 0),
                            '72小时解决率': item.get('fcr72Rate', {}).get('value', 0),
                            '统计日期': self.target_date_str
                        })
                
                # 创建DataFrame
                df = pd.DataFrame(records)
                
                # 创建日期目录
                date_dir = self.base_analysis_dir / self.target_date_str
                date_dir.mkdir(parents=True, exist_ok=True)
                
                # 保存为Excel文件，以店铺名称命名
                filename = f"{shop_name}.xlsx"
                file_path = date_dir / filename
                
                # 如果文件已存在，先删除
                if file_path.exists():
                    file_path.unlink()
                    print(f"删除已存在的文件: {file_path}")
                
                df.to_excel(file_path, index=False, engine='openpyxl')
                print(f"✓ 售后解决分析数据已保存: {file_path}")
                print(f"✓ 共保存 {len(records)} 条记录")
                
                return str(file_path)
            else:
                print("✗ 响应数据格式异常")
                return False
                
        except Exception as e:
            print(f"✗ 解析和保存数据时出错: {e}")
            return False
    
    def merge_and_upload_files(self, file_type):
        """合并文件并上传到MinIO"""
        print(f"\n=== 合并{file_type}文件并上传 ===")
        
        try:
            # 确定源目录和目标目录
            if file_type == "自制报表":
                source_dir = self.base_report_dir / self.target_date_str
                target_dir = self.merged_report_dir
                minio_path = "warehouse/ods/tm/tm_self_kpi"
                dremio_table = 'minio.warehouse.ods.tm."tm_self_kpi"'
            else:  # 售后解决分析
                source_dir = self.base_analysis_dir / self.target_date_str
                target_dir = self.merged_analysis_dir
                minio_path = "warehouse/ods/tm/tm_offical_kpi"
                dremio_table = 'minio.warehouse.ods.tm."tm_offical_kpi"'
            
            if not source_dir.exists() or not any(source_dir.glob("*.xlsx")):
                print(f"⚠️ 源目录不存在或没有Excel文件: {source_dir}")
                return False
            
            # 使用ExcelMerger合并文件
            print(f"🔄 正在合并{file_type}文件...")
            merger = ExcelMerger(str(source_dir))
            merge_filename = f"{self.target_date_str}.xlsx"
            merge_success = merger.merge_excel_files(merge_filename)
            
            if merge_success:
                # 移动合并后的文件到目标目录
                source_merged_file = source_dir / merge_filename
                target_merged_file = target_dir / merge_filename
                
                if source_merged_file.exists():
                    # 如果目标文件已存在，先删除
                    if target_merged_file.exists():
                        target_merged_file.unlink()
                    
                    shutil.move(str(source_merged_file), str(target_merged_file))
                    print(f"✓ 合并文件已移动到: {target_merged_file}")
                    
                    # 上传到MinIO
                    success = self.upload_to_minio(str(target_merged_file), minio_path)
                    if success:
                        print(f"✓ {file_type}文件上传MinIO成功")
                        
                        # 刷新Dremio
                        self.refresh_dremio_table(dremio_table)
                        return True
                    else:
                        print(f"✗ {file_type}文件上传MinIO失败")
                        return False
                else:
                    print(f"✗ 合并文件不存在: {source_merged_file}")
                    return False
            else:
                print(f"✗ {file_type}文件合并失败")
                return False
                
        except Exception as e:
            print(f"✗ 合并和上传{file_type}文件时出错: {e}")
            return False
    
    def upload_to_minio(self, file_path, minio_path):
        """
        将Excel文件转换为Parquet格式并上传到MinIO
        与jd_store.py的upload_merged_file_to_minio方法保持一致
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
            # 刷新数据集
            print(f'🔄 正在刷新数据集...')
            refresh_dataset_response = requests.post(
                "http://localhost:8003/api/dataset/refresh-metadata",
                headers={"Content-Type": "application/json"},
                json={"dataset_path": table_name}
            )
            if refresh_dataset_response.status_code == 200:
                print(f'✓ 数据集刷新成功: {table_name}')
            else:
                print(f'⚠️ 数据集刷新失败: {refresh_dataset_response.status_code}')
            
            # 刷新反射
            print(f'🔄 正在刷新反射...')
            refresh_reflection_response = requests.post(
                "http://localhost:8003/api/reflection/refresh",
                headers={"Content-Type": "application/json"},
                json={"dataset_path": table_name}
            )
            if refresh_reflection_response.status_code == 200:
                print(f'✓ 反射刷新成功: {table_name}')
            else:
                print(f'⚠️ 反射刷新失败: {refresh_reflection_response.status_code}')
            
            return True
        except Exception as e:
            print(f"✗ 刷新Dremio表失败: {e}")
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
    
    def run(self):
        """运行主程序"""
        print("=== 天猫KPI数据获取工具 - 升级版 ===")
        print(f"目标日期: {self.target_date_str}")
        
        # 1. 生成当日任务
        if not self.generate_daily_tasks():
            print("✗ 任务生成失败，程序退出")
            return False
        
        success_count = 0
        total_tasks = 0
        
        # 2. 处理自制报表任务
        print("\n=== 处理自制报表任务 ===")
        self_report_shops = self.get_shops_with_tasks('kpi_self_status')
        
        if self_report_shops:
            total_tasks += len(self_report_shops)
            downloaded_files = []
            
            for shop_info in self_report_shops:
                shop_name = shop_info['shop_name']
                cookies = shop_info['sycmcookie']
                report_template_id = shop_info.get('reportTemplateId')
                task_id = shop_info.get('task_id')
                
                print(f"\n处理店铺: {shop_name}")
                
                # 获取自制报表数据
                file_path = self.get_custom_report_data_for_shop(shop_name, cookies, report_template_id)
                
                if file_path:
                    downloaded_files.append(file_path)
                    success_count += 1
                    
                    # 更新任务状态
                    self.update_task_status(shop_name, 'kpi_self_status')
                else:
                    print(f"✗ 店铺 {shop_name} 自制报表数据获取失败")
            
            # 合并自制报表文件
            if downloaded_files:
                self.merge_and_upload_files("自制报表")
        
        # 3. 处理售后解决分析任务
        print("\n=== 处理售后解决分析任务 ===")
        analysis_shops = self.get_shops_with_tasks('kpi_offical_status')
        
        if analysis_shops:
            total_tasks += len(analysis_shops)
            downloaded_files = []
            
            for shop_info in analysis_shops:
                shop_name = shop_info['shop_name']
                cookies = shop_info['sycmcookie']
                task_id = shop_info.get('task_id')
                
                print(f"\n处理店铺: {shop_name}")
                
                # 获取售后解决分析数据
                file_path = self.get_aftersale_analysis_data_for_shop(shop_name, cookies)
                
                if file_path:
                    downloaded_files.append(file_path)
                    success_count += 1
                    
                    # 更新任务状态
                    self.update_task_status(shop_name, 'kpi_offical_status')
                else:
                    print(f"✗ 店铺 {shop_name} 售后解决分析数据获取失败")
            
            # 合并售后解决分析文件
            if downloaded_files:
                self.merge_and_upload_files("售后解决分析")
        
        print(f"\n=== 执行完成 ===")
        print(f"成功执行: {success_count}/{total_tasks} 个任务")
        
        return success_count > 0

def main():
    """主函数"""
    collector = TmallKpiCollector()
    success = collector.run()
    
    if success:
        print("\n✓ 程序执行成功！")
    else:
        print("\n✗ 程序执行失败！")

if __name__ == "__main__":
    main()