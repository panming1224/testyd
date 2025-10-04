# -*- coding: utf-8 -*-
"""
拼多多客服绩效数据采集（日度）
采集T-3日（3天前）的客服绩效数据
"""
import json
import os
import requests
import pandas as pd
import time
from pathlib import Path
from tqdm import tqdm
import shutil
from datetime import datetime, timedelta
import sys

# 设置标准输出编码为UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 添加模块路径
sys.path.append(r'D:\testyd')
sys.path.append(r'D:\testyd\mysql')

from merge_excel_files import ExcelMerger
from crawler_db_interface import CrawlerDBInterface

# 配置
BASE_ARCHIVE_DIR = Path('D:/pdd/客服绩效文件存档')  # 基础存档目录
MERGED_FILES_DIR = Path('D:/pdd/合并文件/客服绩效文件存档')  # 合并文件存储目录

# MinIO API配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"

# Dremio API配置
DREMIO_API_URL = "http://localhost:8003/api"

# 创建基础存档目录和合并文件目录
os.makedirs(BASE_ARCHIVE_DIR, exist_ok=True)
os.makedirs(MERGED_FILES_DIR, exist_ok=True)

# 目标日期：T-3日（3天前）
TODAY_STR = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')


def fetch_download_link(cookie: str):
    """获取客服绩效下载链接"""
    from datetime import time as dt_time
    
    today = datetime.now().date()
    t3_day = today - timedelta(days=3)  # T-3 日期

    # 00:00:00 时间戳（秒）
    ts_start = int(datetime.combine(t3_day, dt_time.min).timestamp())
    # 23:59:59 时间戳（秒）
    ts_end = int(datetime.combine(t3_day, dt_time.max).timestamp())

    url = ('https://mms.pinduoduo.com/chats/csReportDetail/download?'
           f'starttime={ts_start}&endtime={ts_end}&csRemoveRefundSalesAmountGray=true&')

    headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'Cookie': cookie,
        'referer': 'https://mms.pinduoduo.com/mms-chat/overview/merchant',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    
    if data.get('success') and data.get('result'):
        return data['result']
    raise RuntimeError(f'无下载链接：{data.get("error_msg")}')


def silent_download(url: str, shop_name: str, date_str: str = None):
    """
    静默下载Excel文件到指定日期文件夹
    
    Args:
        url: 下载链接
        shop_name: 店铺名称
        date_str: 日期字符串，如 '2025-10-02'，默认使用TODAY_STR
    
    Returns:
        str: 保存的文件路径
    """
    if date_str is None:
        date_str = TODAY_STR
    
    # 创建日期文件夹
    date_folder = BASE_ARCHIVE_DIR / date_str
    date_folder.mkdir(parents=True, exist_ok=True)
    
    # 下载文件
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    
    # 保存文件
    save_path = date_folder / f"{shop_name}.xlsx"
    with open(save_path, 'wb') as f:
        f.write(resp.content)
    
    return str(save_path)


def upload_merged_file_to_minio(file_path, date_str):
    """
    上传合并后的Excel文件到MinIO（转换为Parquet格式）
    
    Args:
        file_path: 本地Excel文件路径
        date_str: 日期字符串，用于分区
    
    Returns:
        bool: 上传是否成功
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 处理NaN值和无穷大值
        df = df.fillna('')
        df = df.replace([float('inf'), float('-inf')], '')
        
        # 确保所有数据都能正常序列化
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32']:
                df[col] = df[col].replace([float('inf'), float('-inf')], '')
            df[col] = df[col].astype(str)
        
        # 构建MinIO路径
        minio_path = f"ods/pdd/pdd_kpi_days/dt={date_str}/merged_data.parquet"
        
        # 准备上传数据
        upload_data = {
            "data": df.to_dict('records'),
            "target_path": minio_path,
            "format": "parquet",
            "bucket": MINIO_BUCKET
        }
        
        # 发送POST请求
        headers = {'Content-Type': 'application/json'}
        response = requests.post(MINIO_API_URL, json=upload_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✓ MinIO上传成功: {minio_path}")
                return True
            else:
                print(f"✗ MinIO上传失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"✗ MinIO API请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ MinIO上传异常: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print(f"拼多多客服绩效数据采集（日度）- {TODAY_STR}")
    print("=" * 60)
    
    # 初始化数据库接口
    db_interface = CrawlerDBInterface(
        platform='pdd',
        shops_table='pdd_shops',
        tasks_table='pdd_tasks',
        database='company'
    )
    
    # 获取待处理任务（不生成任务，由 generate_daily_tasks.py 统一生成）
    print(f"\n=== 获取待处理任务 ===")
    pending_tasks = db_interface.get_pending_tasks(TODAY_STR, 'kpi_days_status')
    
    if not pending_tasks:
        print("✓ 没有待处理任务，所有任务已完成")
        print("\n提示：如需重新执行，请先运行 generate_daily_tasks.py 生成任务")
        sys.exit(0)
    
    print(f"找到 {len(pending_tasks)} 个待处理任务")
    
    # 批量下载所有文件
    downloaded_files = []
    success_count = 0
    
    for task in pending_tasks:
        shop_name = task[1] if len(task) > 1 else None  # dt.shop_name
        cookie = task[11] if len(task) > 11 else None  # s.cookie (索引11)
        
        if not cookie:
            print(f'[警告] {shop_name} cookie为空，跳过')
            continue
        
        print(f"\n=== 处理店铺: {shop_name} ===")
        
        try:
            down_url = fetch_download_link(cookie)
            save_path = silent_download(down_url, shop_name)
            print(f'[成功] {shop_name}  下载完成: {save_path}')
            
            downloaded_files.append(save_path)
            success_count += 1
            
            # 更新任务状态为已完成
            db_interface.update_task_status(TODAY_STR, shop_name, 'kpi_days_status', '已完成')
        except Exception as e:
            # 失败时不更新状态，保持待执行状态便于重试
            print(f'[错误] {shop_name}  失败：{e}，保持待执行状态')
    
    print(f"\n=== 数据处理完成 ===")
    print(f"成功处理: {success_count}/{len(pending_tasks)} 个店铺")
    
    # 合并文件
    if downloaded_files:
        print(f'\n🔄 开始合并 {len(downloaded_files)} 个Excel文件...')
        date_dir = BASE_ARCHIVE_DIR / TODAY_STR
        merger = ExcelMerger(str(date_dir), output_dir=str(MERGED_FILES_DIR))
        merge_success = merger.merge_excel_files(f"客服绩效合并_{TODAY_STR}.xlsx")
        
        if merge_success:
            final_merged_file_path = MERGED_FILES_DIR / f"客服绩效合并_{TODAY_STR}.xlsx"
            print(f'[成功] 文件合并完成: {final_merged_file_path}')
            
            # 上传到MinIO
            print(f'🔄 正在上传合并文件到MinIO...')
            upload_success = upload_merged_file_to_minio(str(final_merged_file_path), TODAY_STR)
            
            if upload_success:
                print(f'[成功] 合并文件MinIO上传成功')
            else:
                print(f'[警告] 合并文件MinIO上传失败，但本地文件已保存')
        else:
            print('[错误] 文件合并失败，无法生成合并文件')
    else:
        print('[警告] 没有新下载的文件，跳过合并和上传步骤')
    
    # 刷新Dremio
    print('\n🔄 正在刷新Dremio数据集和反射...')
    try:
        refresh_dataset_response = requests.post(
            f"{DREMIO_API_URL}/dataset/refresh-metadata",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.pdd.pdd_kpi_days"}
        )
        if refresh_dataset_response.status_code == 200:
            print('[成功] 数据集刷新成功')
        else:
            print(f'[警告] 数据集刷新失败: {refresh_dataset_response.status_code}')
    except Exception as e:
        print(f'[错误] 数据集刷新异常: {e}')
    
    try:
        refresh_reflection_response = requests.post(
            f"{DREMIO_API_URL}/reflection/refresh",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.pdd.pdd_kpi_days"}
        )
        if refresh_reflection_response.status_code == 200:
            print('[成功] 反射刷新成功')
        else:
            print(f'[警告] 反射刷新失败: {refresh_reflection_response.status_code}')
    except Exception as e:
        print(f'[错误] 反射刷新异常: {e}')
    
    print('\n🎉 所有任务完成！')

