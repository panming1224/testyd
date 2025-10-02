# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import time
import json
import requests
import uuid
import os
import pandas as pd
import warnings
import shutil
import re
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 过滤openpyxl的无害警告
warnings.filterwarnings("ignore", message="Workbook contains no default style, apply openpyxl's default")

# 配置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 配置 - 写死店铺信息
SHOP_NAME = "义乌市塔智有限公司"
PROFILE = "Default"

# 目录配置
BASE_ARCHIVE_DIR = Path('D:/yingdao/erp/采购单下载')  # 采购单下载存档目录
MERGED_FILES_DIR = Path('D:/yingdao/erp/合并表格/采购单下载')  # 采购单下载合并文件存储目录

# MinIO API配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"

# ERP API配置
ERP_API_BASE_URL = "https://www.erp321.com/app/scm/purchase/purchasemode.aspx?_c=jst-epaas"

# 创建基础存档目录和合并文件目录
os.makedirs(BASE_ARCHIVE_DIR, exist_ok=True)
os.makedirs(MERGED_FILES_DIR, exist_ok=True)

# 使用T-1日期（昨天）
TODAY_STR = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')


def fetch_purchase_order_data(shop_name: str, profile: str):
    """
    获取采购单数据
    直接访问采购单页面，然后点击导入导出按钮
    """
    print(f"[{shop_name}] 开始获取采购单数据...")
    
    USER_DATA_DIR = r"C:\\Users\\1\AppData\\Local\\Chromium\\User Data"
    
    # 设置下载目录
    download_path = BASE_ARCHIVE_DIR / TODAY_STR
    download_path.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=[
                "--start-maximized",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                f"--profile-directory={profile}"
            ],
            no_viewport=True,
            ignore_https_errors=True,
            accept_downloads=True  # 关键：静默下载
        )
        
        page = context.new_page()
        
        try:
            # 直接导航到采购单页面
            purchase_url = ERP_API_BASE_URL 
            print(f"[{shop_name}] 直接访问采购单下载页面: {purchase_url}")
            page.goto(purchase_url, wait_until="domcontentloaded", timeout=30000)
            
            # 等待页面加载
            page.wait_for_load_state('networkidle')
            print(f"[{shop_name}] 采购单页面加载完成")
            
            # 1. 先点父按钮
            print(f"[{shop_name}] 点击采购单导入导出按钮...")
            page.locator('xpath=//*[@id="Tool_Export_Btn"]/span').click()
            
            # 2. 再点「导出/下载」并等待下载完成
            print(f"[{shop_name}] 点击采购单导出选项并等待下载...")
            with page.expect_download() as download_info:
                page.locator('xpath=//*[@id="Tool_Export_Btn"]/div/div[1]').click()
            
            download = download_info.value
            
            # 3. 保存到指定位置
            filename = f"{shop_name}.xlsx"
            final_path = download_path / filename
            download.save_as(final_path)
            
            print(f"[{shop_name}] 采购单下载成功: {final_path}")
            return True
                
        except Exception as e:
            print(f"[{shop_name}] 采购单数据获取失败: {str(e)}")
            return False
        finally:
            context.close()

def upload_file_to_minio(file_path: str, minio_path: str, date_str: str = None) -> bool:
    """
    将文件转换为Parquet格式并上传到MinIO
    
    Args:
        file_path: 本地文件路径
        minio_path: MinIO存储路径
        date_str: 日期字符串，默认使用今天
    
    Returns:
        bool: 上传是否成功
    """
    if date_str is None:
        date_str = TODAY_STR
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 添加唯一值列：日期_序号格式
        date_prefix = date_str.replace('-', '')  # 将2025-10-01转换为20251001
        df['unique_id'] = [f"{date_prefix}_{i+1:06d}" for i in range(len(df))]
        
        # 将unique_id列移到第一列
        cols = ['unique_id'] + [col for col in df.columns if col != 'unique_id']
        df = df[cols]
        
        # 构建完整的MinIO路径
        full_minio_path = f"{minio_path}/dt={date_str}/data.parquet"
        
        # 处理NaN值和无穷大值
        df = df.fillna('')
        df = df.replace([float('inf'), float('-inf')], '')
        
        # 确保所有数据都能正常序列化
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32']:
                df[col] = df[col].replace([float('inf'), float('-inf')], '')
            # 转换为字符串以避免序列化问题（除了unique_id列保持原样）
            if col != 'unique_id':
                df[col] = df[col].astype(str)
        
        # 准备上传数据
        upload_data = {
            "data": df.to_dict('records'),
            "target_path": full_minio_path,
            "format": "parquet",
            "bucket": MINIO_BUCKET
        }
        
        # 发送POST请求到MinIO API
        headers = {'Content-Type': 'application/json'}
        response = requests.post(MINIO_API_URL, json=upload_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"成功上传文件到MinIO: {full_minio_path}")
                return True
            else:
                print(f"MinIO上传失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"MinIO API请求失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"上传文件到MinIO时出错: {str(e)}")
        return False

def refresh_dremio_dataset(dataset_path: str) -> bool:
    """
    刷新Dremio数据集
    """
    try:
        refresh_response = requests.post(
            "http://localhost:8003/api/dataset/refresh-metadata",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": dataset_path}
        )
        if refresh_response.status_code == 200:
            print(f'数据集刷新成功: {dataset_path}')
            return True
        else:
            print(f'数据集刷新失败: {dataset_path} - {refresh_response.status_code}')
            return False
    except Exception as e:
        print(f'数据集刷新异常: {dataset_path} - {e}')
        return False

def refresh_dremio_reflection(dataset_path: str) -> bool:
    """
    刷新Dremio反射
    """
    try:
        refresh_response = requests.post(
            "http://localhost:8003/api/reflection/refresh",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": dataset_path}
        )
        if refresh_response.status_code == 200:
            print(f'反射刷新成功: {dataset_path}')
            return True
        else:
            print(f'反射刷新失败: {dataset_path} - {refresh_response.status_code}')
            return False
    except Exception as e:
        print(f'反射刷新异常: {dataset_path} - {e}')
        return False

if __name__ == '__main__':
    print("ERP采购单数据抓取程序启动...")
    print(f"店铺名称: {SHOP_NAME}")
    print(f"浏览器配置文件: {PROFILE}")
    print(f"处理日期: {TODAY_STR}")
    
    # 下载采购单数据
    try:
        purchase_success = fetch_purchase_order_data(SHOP_NAME, PROFILE)
        if purchase_success:
            print(f'[{SHOP_NAME}] 采购单数据下载成功')
            
            # 上传文件到MinIO
            date_dir = BASE_ARCHIVE_DIR / TODAY_STR
            file_path = date_dir / f"{SHOP_NAME}.xlsx"
            if file_path.exists():
                if upload_file_to_minio(str(file_path), "ods/erp/purchase_orders", TODAY_STR):
                    print(f'[{SHOP_NAME}] 采购单文件上传MinIO成功')
                else:
                    print(f'[{SHOP_NAME}] 采购单文件上传MinIO失败')
            else:
                print(f'[{SHOP_NAME}] 采购单文件不存在: {file_path}')
        else:
            print(f'[{SHOP_NAME}] 采购单数据下载失败')
    except Exception as e:
        print(f'[{SHOP_NAME}] 采购单数据处理异常: {e}')

    # 刷新Dremio数据集和反射
    print("\n刷新Dremio数据集...")
    refresh_dremio_dataset("minio.warehouse.ods.erp.purchase_orders")
    
    print("\n刷新Dremio反射...")
    refresh_dremio_reflection("minio.warehouse.ods.erp.purchase_orders")
    
    print("\n所有任务完成！")