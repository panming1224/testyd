# -*- coding: utf-8 -*-
"""
爬虫基类
所有爬虫都继承这个基类，提供统一的功能
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import requests

# 设置标准输出编码为UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 添加模块路径
sys.path.append(r'D:\testyd')
sys.path.append(r'D:\testyd\mysql')
sys.path.append(r'D:\testyd\pdd')

from crawler_db_interface import CrawlerDBInterface
from merge_excel_files import ExcelMerger
from crawler_config import DB_CONFIG, STORAGE_CONFIG, MINIO_CONFIG, DREMIO_CONFIG


class BaseCrawler:
    """爬虫基类"""
    
    def __init__(self, task_key, task_config):
        """
        初始化爬虫
        
        Args:
            task_key: 任务键名，如 'badscore'
            task_config: 任务配置字典
        """
        self.task_key = task_key
        self.task_config = task_config
        self.task_name = task_config['name']
        self.status_field = task_config['status_field']
        self.target_date = None  # 由子类设置
        
        # 初始化数据库接口
        self.db_interface = CrawlerDBInterface(**DB_CONFIG)
        
        # 设置存储路径
        self.base_archive_dir = Path(STORAGE_CONFIG['base_archive_dir'])
        self.merged_files_dir = Path(STORAGE_CONFIG['merged_files_dir'])
        
        # MinIO和Dremio配置
        self.minio_api_url = MINIO_CONFIG['api_url']
        self.minio_bucket = MINIO_CONFIG['bucket']
        self.dremio_api_url = DREMIO_CONFIG['api_url']
        
        # 统计信息
        self.success_count = 0
        self.fail_count = 0
        self.downloaded_files = []
    
    def print_header(self):
        """打印程序头部信息"""
        print("=" * 60)
        print(f"{self.task_name} - {self.target_date}")
        print("=" * 60)
    
    def get_pending_tasks(self):
        """
        获取待处理任务
        
        Returns:
            list: 待处理任务列表
        """
        print(f"\n=== 获取待处理任务 ===")
        pending_tasks = self.db_interface.get_pending_tasks(
            self.target_date, 
            self.status_field
        )
        
        if not pending_tasks:
            print("✓ 没有待处理任务，所有任务已完成")
            print(f"\n提示：如需重新执行，请先运行 generate_tasks.py 生成任务")
            return []
        
        print(f"找到 {len(pending_tasks)} 个待处理任务")
        return pending_tasks
    
    def process_shop(self, shop_name, cookie, **kwargs):
        """
        处理单个店铺的数据采集
        子类必须实现此方法
        
        Args:
            shop_name: 店铺名称
            cookie: 店铺Cookie
            **kwargs: 其他参数
        
        Returns:
            str: 保存的文件路径，失败返回None
        """
        raise NotImplementedError("子类必须实现 process_shop 方法")
    
    def run(self):
        """
        执行爬虫任务
        主流程：获取任务 -> 处理数据 -> 合并文件 -> 上传MinIO -> 刷新Dremio
        """
        self.print_header()
        
        # 1. 获取待处理任务
        pending_tasks = self.get_pending_tasks()
        if not pending_tasks:
            sys.exit(0)
        
        # 2. 批量处理所有店铺
        print(f"\n=== 开始数据采集 ===")
        for task in pending_tasks:
            shop_name = task[1] if len(task) > 1 else None
            cookie = task[11] if len(task) > 11 else None
            
            if not cookie:
                print(f'[警告] {shop_name} cookie为空，跳过')
                continue
            
            print(f"\n--- 处理店铺: {shop_name} ---")
            
            try:
                # 调用子类实现的处理方法
                save_path = self.process_shop(shop_name, cookie)
                
                if save_path:
                    print(f'[成功] {shop_name} 数据采集完成: {save_path}')
                    self.downloaded_files.append(save_path)
                    self.success_count += 1
                    
                    # 更新任务状态为已完成
                    self.db_interface.update_task_status(
                        self.target_date, 
                        shop_name, 
                        self.status_field, 
                        '已完成'
                    )
                else:
                    print(f'[失败] {shop_name} 数据采集失败')
                    self.fail_count += 1
            except Exception as e:
                # 失败时不更新状态，保持"待执行"状态便于重试
                print(f'[错误] {shop_name} 失败：{e}，保持待执行状态')
                self.fail_count += 1
        
        # 3. 打印统计信息
        print(f"\n=== 数据采集完成 ===")
        print(f"成功: {self.success_count}/{len(pending_tasks)} 个店铺")
        print(f"失败: {self.fail_count}/{len(pending_tasks)} 个店铺")
        
        # 4. 合并文件
        if self.downloaded_files:
            self.merge_files()
        else:
            print('\n[警告] 没有新下载的文件，跳过合并和上传步骤')
            return
        
        # 5. 上传到MinIO
        self.upload_to_minio()
        
        # 6. 刷新Dremio
        self.refresh_dremio()
        
        print('\n🎉 所有任务完成！')
    
    def merge_files(self):
        """合并Excel文件"""
        print(f'\n=== 合并文件 ===')
        print(f'共 {len(self.downloaded_files)} 个文件需要合并')
        
        # 获取日期文件夹
        date_dir = self.base_archive_dir / self.get_date_folder_name() / self.target_date
        
        # 创建合并文件目录
        task_merged_dir = self.merged_files_dir / self.get_date_folder_name()
        task_merged_dir.mkdir(parents=True, exist_ok=True)
        
        # 合并文件
        merger = ExcelMerger(str(date_dir), output_dir=str(task_merged_dir))
        merge_success = merger.merge_excel_files(f"{self.task_key}_{self.target_date}.xlsx")
        
        if merge_success:
            self.merged_file_path = task_merged_dir / f"{self.task_key}_{self.target_date}.xlsx"
            print(f'[成功] 文件合并完成: {self.merged_file_path}')
        else:
            print('[错误] 文件合并失败')
            self.merged_file_path = None
    
    def upload_to_minio(self):
        """上传合并文件到MinIO"""
        if not hasattr(self, 'merged_file_path') or not self.merged_file_path:
            print('\n[跳过] 没有合并文件，跳过MinIO上传')
            return
        
        print(f'\n=== 上传到MinIO ===')
        
        try:
            # 读取Excel文件
            df = pd.read_excel(self.merged_file_path)
            
            # 处理NaN值
            df = df.fillna('')
            df = df.replace([float('inf'), float('-inf')], '')
            
            # 确保所有数据都能正常序列化
            for col in df.columns:
                if df[col].dtype in ['float64', 'float32']:
                    df[col] = df[col].replace([float('inf'), float('-inf')], '')
                df[col] = df[col].astype(str)
            
            # 构建MinIO路径
            minio_path = f"{self.task_config['minio_path']}/dt={self.target_date}/merged_data.parquet"
            
            # 准备上传数据
            upload_data = {
                "data": df.to_dict('records'),
                "target_path": minio_path,
                "format": "parquet",
                "bucket": self.minio_bucket
            }
            
            # 发送POST请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.minio_api_url, json=upload_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"[成功] MinIO上传成功: {minio_path}")
                else:
                    print(f"[失败] MinIO上传失败: {result.get('message', '未知错误')}")
            else:
                print(f"[失败] MinIO API请求失败: {response.status_code}")
        except Exception as e:
            print(f"[错误] MinIO上传异常: {e}")
    
    def refresh_dremio(self):
        """刷新Dremio数据集和反射"""
        print('\n=== 刷新Dremio ===')
        
        dataset_path = self.task_config['dremio_table']
        
        # 刷新数据集
        try:
            response = requests.post(
                f"{self.dremio_api_url}/dataset/refresh-metadata",
                headers={"Content-Type": "application/json"},
                json={"dataset_path": dataset_path}
            )
            if response.status_code == 200:
                print('[成功] 数据集刷新成功')
            else:
                print(f'[警告] 数据集刷新失败: {response.status_code}')
        except Exception as e:
            print(f'[错误] 数据集刷新异常: {e}')
        
        # 刷新反射
        try:
            response = requests.post(
                f"{self.dremio_api_url}/reflection/refresh",
                headers={"Content-Type": "application/json"},
                json={"dataset_path": dataset_path}
            )
            if response.status_code == 200:
                print('[成功] 反射刷新成功')
            else:
                print(f'[警告] 反射刷新失败: {response.status_code}')
        except Exception as e:
            print(f'[错误] 反射刷新异常: {e}')
    
    def get_date_folder_name(self):
        """
        获取日期文件夹名称
        子类可以重写此方法以自定义文件夹名称
        
        Returns:
            str: 文件夹名称
        """
        return self.task_key

