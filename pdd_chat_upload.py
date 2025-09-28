#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path
import re
from merge_excel_files import ExcelMerger

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdd_quality_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PDDChatUploader:
    def __init__(self, api_url="http://127.0.0.1:8009/api/upload", bucket="warehouse"):
        self.api_url = api_url
        self.bucket = bucket
        self.base_path = Path("D:/pdd/产品质量体验存档")
        
    def extract_date_from_folder(self, folder_name):
        """从文件夹名提取日期"""
        # 直接返回文件夹名作为日期标识，支持格式如：2025-08-01_2025-08-31
        return folder_name
    
    def extract_shop_name_from_file(self, file_name):
        """从文件名提取店铺名"""
        # 移除.xlsx扩展名
        shop_name = file_name.replace('.xlsx', '')
        return shop_name
    
    def delete_minio_data(self, date):
        """删除MinIO中指定日期的数据"""
        try:
            # 构建删除路径 - 删除整个日期分区
            delete_path = f"ods/pdd/pdd_quality/dt={date}/"
            
            payload = {
                "bucket_name": self.bucket,
                "object_path": delete_path
            }
            
            logger.info(f"准备删除MinIO数据: {delete_path}")
            
            response = requests.delete(
                "http://127.0.0.1:8009/api/delete/folder",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info(f"成功删除MinIO数据: {delete_path}")
                return True
            else:
                logger.warning(f"删除MinIO数据失败或数据不存在: {response.status_code} - {response.text}")
                return True  # 即使删除失败也继续，可能是数据不存在
                
        except Exception as e:
            logger.error(f"删除MinIO数据时发生错误: {str(e)}")
            return False
    
    def read_excel_file(self, file_path):
        """读取Excel文件并转换为二维数组格式（包含列名）"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            logger.info(f"成功读取Excel文件: {file_path}, 行数: {len(df)}, 列数: {len(df.columns)}")
            logger.info(f"列名: {list(df.columns)}")
            
            # 构建二维数组：第一行是列名，后续行是数据
            data_array = []
            
            # 添加列名作为第一行
            column_names = list(df.columns)
            data_array.append(column_names)
            
            # 处理NaN值，将其替换为空字符串
            df = df.fillna('')
            
            # 处理所有数据类型，确保能够序列化
            for col in df.columns:
                # 处理时间类型
                if df[col].dtype == 'datetime64[ns]':
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                elif 'time' in str(df[col].dtype).lower():
                    df[col] = df[col].astype(str)
                # 处理数值类型，确保没有无穷大或NaN
                elif df[col].dtype in ['float64', 'float32']:
                    df[col] = df[col].replace([float('inf'), float('-inf')], '')
                # 确保所有数据都转换为字符串，避免类型问题
                df[col] = df[col].astype(str)
            
            # 将DataFrame转换为二维数组
            for _, row in df.iterrows():
                data_array.append(row.tolist())
            
            if len(df) > 0:
                logger.info(f"文件包含数据，总共 {len(df)} 行数据")
            else:
                logger.info(f"Excel文件为空，只包含列名结构: {file_path}")
            
            logger.info(f"成功读取文件 {file_path}，构建二维数组，总共 {len(data_array)} 行（包含列名）")
            return data_array
            
        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {str(e)}")
            return None
    
    def merge_excel_files_by_date(self, folder_path, date):
        """合并指定文件夹中的所有Excel文件，添加shop列 - 使用ExcelMerger"""
        try:
            folder_path = Path(folder_path)
            
            if not folder_path.exists():
                logger.error(f"文件夹不存在: {folder_path}")
                return None
            
            # 使用ExcelMerger进行合并
            logger.info(f"使用ExcelMerger合并文件夹: {folder_path}")
            merger = ExcelMerger(str(folder_path))
            
            # 获取所有Excel文件
            excel_files = merger.find_excel_files()
            if not excel_files:
                logger.warning(f"文件夹 {folder_path} 中没有找到Excel文件")
                return None
            
            logger.info(f"找到 {len(excel_files)} 个Excel文件需要合并")
            
            # 读取并合并所有文件
            all_dataframes = []
            
            for file_path in excel_files:
                df = merger.read_excel_file(file_path)
                if df is not None:
                    # 处理数据类型以确保能够序列化
                    df = df.fillna('')
                    for col in df.columns:
                        if df[col].dtype == 'datetime64[ns]':
                            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                        elif 'time' in str(df[col].dtype).lower():
                            df[col] = df[col].astype(str)
                        elif df[col].dtype in ['float64', 'float32']:
                            df[col] = df[col].replace([float('inf'), float('-inf')], '')
                        df[col] = df[col].astype(str)
                    
                    all_dataframes.append(df)
            
            if not all_dataframes:
                logger.error("没有成功读取任何Excel文件")
                return None
            
            # 合并所有数据框
            merged_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
            
            # 将shop列移到第一列
            cols = merged_df.columns.tolist()
            if 'shop' in cols:
                cols.remove('shop')
                cols.insert(0, 'shop')
                merged_df = merged_df[cols]
            
            logger.info(f"合并完成，总行数: {len(merged_df)}, 总列数: {len(merged_df.columns)}")
            logger.info(f"包含的店铺: {merged_df['shop'].unique().tolist()}")
            
            # 转换为二维数组格式
            data_array = []
            # 添加列名作为第一行
            data_array.append(merged_df.columns.tolist())
            # 添加数据行
            for _, row in merged_df.iterrows():
                data_array.append(row.tolist())
            
            return data_array
            
        except Exception as e:
            logger.error(f"合并Excel文件时发生错误: {str(e)}")
            return None
    
    def upload_to_minio(self, data, file_path_in_minio):
        """上传数据到MinIO"""
        try:
            payload = {
                "data": data,
                "target_path": file_path_in_minio,
                "bucket_name": self.bucket
            }
            
            logger.info(f"准备上传到MinIO: {file_path_in_minio}")
            logger.info(f"数据行数: {len(data)}")
            
            response = requests.post(
                "http://127.0.0.1:8009/api/upload/parquet",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=300  # 5分钟超时
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"上传成功: {result}")
                return True
            else:
                logger.error(f"上传失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"上传过程中发生错误: {str(e)}")
            return False
    
    def process_date_folder(self, date_folder_path, date=None):
        """处理单个日期文件夹，合并所有Excel文件并上传"""
        try:
            date_folder_path = Path(date_folder_path)
            
            # 如果没有提供日期，尝试从文件夹名提取
            if date is None:
                date = self.extract_date_from_folder(date_folder_path.name)
            
            if not date:
                logger.error(f"无法确定日期: {date_folder_path}")
                return False
            
            logger.info(f"开始处理日期文件夹: {date_folder_path} (日期: {date})")
            
            # 1. 删除MinIO中的现有数据
            logger.info(f"步骤1: 删除MinIO中日期 {date} 的现有数据")
            self.delete_minio_data(date)
            
            # 2. 合并Excel文件
            logger.info(f"步骤2: 合并日期 {date} 的所有Excel文件")
            merged_data = self.merge_excel_files_by_date(date_folder_path, date)
            
            if merged_data is None:
                logger.error(f"合并文件失败: {date_folder_path}")
                return False
            
            # 3. 构建MinIO存储路径（只按日期分区）
            minio_path = f"ods/pdd/pdd_quality/dt={date}/pdd_quality_{date}.parquet"
            
            # 4. 上传到MinIO
            logger.info(f"步骤3: 上传合并后的数据到MinIO")
            success = self.upload_to_minio(merged_data, minio_path)
            
            if success:
                logger.info(f"日期文件夹处理完成: {date_folder_path} -> {minio_path}")
                logger.info(f"数据行数: {len(merged_data)-1} (不含列名)")  # 减1是因为第一行是列名
            else:
                logger.error(f"日期文件夹处理失败: {date_folder_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"处理日期文件夹时发生错误: {str(e)}")
            return False

    def process_all_files(self):
        """处理所有评价文件 - 按日期分区合并"""
        if not self.base_path.exists():
            logger.error(f"基础路径不存在: {self.base_path}")
            return
        
        total_folders = 0
        success_folders = 0
        failed_folders = 0
        
        # 遍历所有日期文件夹
        for date_folder in self.base_path.iterdir():
            if not date_folder.is_dir():
                continue
            
            total_folders += 1
            logger.info(f"处理日期文件夹 {total_folders}: {date_folder.name}")
            
            if self.process_date_folder(date_folder):
                success_folders += 1
            else:
                failed_folders += 1
        
        # 输出统计信息
        logger.info("=" * 50)
        logger.info("处理完成统计:")
        logger.info(f"总文件夹数: {total_folders}")
        logger.info(f"成功处理: {success_folders}")
        logger.info(f"失败文件夹: {failed_folders}")
        logger.info("=" * 50)
    
    def process_date_range(self, start_date=None, end_date=None):
        """处理指定日期范围的文件 - 按日期分区合并"""
        if not self.base_path.exists():
            logger.error(f"基础路径不存在: {self.base_path}")
            return
        
        total_folders = 0
        success_folders = 0
        failed_folders = 0
        
        # 遍历所有日期文件夹
        for date_folder in self.base_path.iterdir():
            if not date_folder.is_dir():
                continue
            
            # 提取日期并检查是否在指定范围内
            date = self.extract_date_from_folder(date_folder.name)
            if not date:
                continue
            
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
            
            total_folders += 1
            logger.info(f"处理日期文件夹 {total_folders}: {date_folder.name}")
            
            if self.process_date_folder(date_folder, date):
                success_folders += 1
            else:
                failed_folders += 1
        
        # 输出统计信息
        logger.info("=" * 50)
        logger.info("处理完成统计:")
        logger.info(f"总文件夹数: {total_folders}")
        logger.info(f"成功处理: {success_folders}")
        logger.info(f"失败文件夹: {failed_folders}")
        logger.info("=" * 50)

def merge_and_upload_folder(folder_path, output_date=None):
    """
    外部调用接口：合并指定文件夹中的Excel文件并上传到MinIO
    
    Args:
        folder_path (str): 包含Excel文件的文件夹路径
        output_date (str): 输出日期，格式为YYYY-MM-DD，如果不提供则尝试从文件夹名提取
        
    Returns:
        bool: 处理是否成功
    """
    uploader = PDDChatUploader()
    return uploader.process_date_folder(folder_path, output_date)

def main():
    """主函数"""
    uploader = PDDChatUploader()
    
    # 可以选择处理所有文件或指定日期范围
    print("PDD评价文件上传工具 (按日期分区合并版本)")
    print("1. 处理所有文件")
    print("2. 处理指定日期范围")
    print("3. 处理单个文件夹")
    
    choice = input("请选择操作 (1/2/3): ").strip()
    
    if choice == "1":
        uploader.process_all_files()
    elif choice == "2":
        start_date = input("请输入开始日期 (格式: 2025-09-15, 留空表示不限制): ").strip()
        end_date = input("请输入结束日期 (格式: 2025-09-23, 留空表示不限制): ").strip()
        
        start_date = start_date if start_date else None
        end_date = end_date if end_date else None
        
        uploader.process_date_range(start_date, end_date)
    elif choice == "3":
        folder_path = input("请输入文件夹路径: ").strip()
        output_date = input("请输入输出日期 (格式: 2025-09-15, 留空则从文件夹名提取): ").strip()
        
        output_date = output_date if output_date else None
        
        if os.path.exists(folder_path):
            success = uploader.process_date_folder(folder_path, output_date)
            if success:
                print("文件夹处理成功！")
            else:
                print("文件夹处理失败！")
        else:
            print(f"文件夹不存在: {folder_path}")
    else:
        print("无效选择")

if __name__ == "__main__":
    main()