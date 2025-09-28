# -*- coding: utf-8 -*-
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

# 设置输出编码为UTF-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# 添加merge_excel_files模块路径
sys.path.append(r'D:\testyd')
from merge_excel_files import ExcelMerger

# 配置
EXCEL_PATH = r'D:\pdd\拼多多店铺汇总表\拼多多店铺汇总表.xlsx'
BASE_ARCHIVE_DIR = Path('D:/pdd/客服绩效文件存档周度')  # 基础存档目录
MERGED_FILES_DIR = Path('D:/pdd/合并文件/客服绩效文件存档周度')  # 合并文件存储目录
SHEET = 0

# MinIO API配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"

# 创建基础存档目录和合并文件目录
os.makedirs(BASE_ARCHIVE_DIR, exist_ok=True)
os.makedirs(MERGED_FILES_DIR, exist_ok=True)

TODAY_STR = (datetime.now()-timedelta(days=9)).strftime('%Y-%m-%d')+'_'+(datetime.now()-timedelta(days=3)).strftime('%Y-%m-%d')

def update_header_once(df: pd.DataFrame):
    """固定用 O 列（索引 15）作为状态列，每周第一天把表头改成 本周日期+下载状态"""
    new_status = f'{TODAY_STR}客服绩效下载状态'
    old_header = df.columns[15]          # O 列当前名字

    if old_header == new_status:
        return False                     # 今天已更新过，返回False表示未更新

    # 改名（只改表头，数据不动）
    df.rename(columns={old_header: new_status}, inplace=True)
    # 清空O列的所有数据（除了表头）
    df.iloc[:, 15] = ''
    # 立即回写 Excel
    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
    return True                          # 返回True表示已更新


def fetch_download_link(cookie: str):
    today = datetime.now().date()          # 今天日期
    t3_day = today - timedelta(days=3)     # T-3 日期
    t6_day = today - timedelta(days=9)     # T-6 日期

    # 00:00:00 时间戳（秒）
    ts_start = int(datetime.combine(t6_day, datetime.min.time()).timestamp())

    # 23:59:59 时间戳（秒）
    ts_end = int(datetime.combine(t3_day, datetime.max.time()).timestamp())

    url = ('https://mms.pinduoduo.com/chats/csReportDetail/download?'
           f'starttime={ts_start}&endtime={ts_end}&csRemoveRefundSalesAmountGray=true&')

    headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'anti-content': '',
        'cache-control': '',
        'Cookie': cookie,
        'priority': '',
        'referer': 'https://mms.pinduoduo.com/mms-chat/overview/merchant',
        'sec-ch-ua': '',
        'sec-ch-ua-mobile': '',
        'sec-ch-ua-platform': '',
        'sec-fetch-dest': '',
        'sec-fetch-mode': '',
        'sec-fetch-site': '',
        'user-agent': ''
    }

    resp = requests.get(url, headers=headers, timeout=15)
    print(f'【响应】{resp.text}')      # 先打印
    resp.raise_for_status()
    data = resp.json()
    if data.get('success') and data.get('result'):
        return data['result']
    raise RuntimeError(f'无下载链接：{data.get("error_msg")}')


def silent_download(url: str, shop_name: str, date_str: str = None):
    """
    下载文件到指定的日期文件夹中
    url: 下载链接
    shop_name: 店铺名称
    date_str: 日期字符串
    """
    if date_str is None:
        date_str = TODAY_STR
    
    # 创建日期文件夹路径：D:\pdd\客服绩效文件存档周度\2025-09-25\
    date_dir = BASE_ARCHIVE_DIR / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件保存路径：D:\pdd\客服绩效文件存档周度\2025-09-25\店铺名称.xlsx
    file_name = f'{shop_name}.xlsx'
    save_path = date_dir / file_name

    # 如果目标文件已存在，先删除
    if save_path.exists():
        print(f'发现同名文件，正在删除: {save_path}')
        save_path.unlink()  # 删除文件
        print(f'[成功] 同名文件已删除')

    # 直接使用requests下载文件，避免Playwright的事件循环问题
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return save_path


def upload_merged_file_to_minio(merged_file_path: str, date_str: str = None) -> bool:
    """
    将合并后的Excel文件转换为Parquet格式并上传到MinIO
    
    Args:
        merged_file_path: 合并后的Excel文件路径
        date_str: 日期字符串，默认使用今天
    
    Returns:
        bool: 上传是否成功
    """
    if date_str is None:
        date_str = TODAY_STR
    
    try:
        # 读取合并后的Excel文件
        df = pd.read_excel(merged_file_path)
        
        # 处理NaN值，避免JSON序列化错误
        df = df.fillna('')
        
        # 构建MinIO路径：ods/pdd/pdd_kpi_weekly/dt=日期/merged_kpi_data.parquet
        minio_path = f"ods/pdd/pdd_kpi_weekly/dt={date_str}/merged_kpi_data.parquet"
        
        # 准备上传数据
        upload_data = {
            "data": df.to_dict('records'),  # 转换为字典列表
            "target_path": minio_path,
            "format": "parquet",
            "bucket": MINIO_BUCKET
        }
        
        # 发送POST请求到MinIO API
        headers = {'Content-Type': 'application/json'}
        response = requests.post(MINIO_API_URL, json=upload_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"[成功] 成功上传合并文件到MinIO周度: {minio_path}")
                return True
            else:
                print(f"[错误] MinIO上传失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"[错误] MinIO API请求失败周度: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"[错误] 上传合并文件到MinIO周度时出错: {str(e)}")
        return False


if __name__ == '__main__':
    # 1. 读表 & 更新表头
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)  
    header_updated = update_header_once(df)
    
    # 如果表头更新了，需要重新读取DataFrame
    if header_updated:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)

    # 2. 定位关键列
    cookie_idx = 9    # J列 (2025-09-24cookie)
    status_idx = 15   # P列 (状态列)
    shop_idx   = 1    # B列 (店铺名称)

    print(f"DataFrame形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    print(f"状态列名: {df.columns[status_idx]}")

    # 3. 收集所有需要下载的店铺信息
    download_tasks = []
    for row_idx in range(len(df)):
        shop   = df.iloc[row_idx, shop_idx]
        cookie = df.iloc[row_idx, cookie_idx]
        status = df.iloc[row_idx, status_idx]

        # 转换为字符串处理
        status_str = str(status) if pd.notna(status) else ''
        
        print(f"检查第{row_idx+2}行: {shop}, 状态: '{status_str}'")

        # 空值/已完成的跳过
        if status_str.strip() == '已完成':
            print(f'[跳过] {shop}  状态已完成，跳过')
            continue
        if pd.isna(cookie) or str(cookie).strip() == '' or str(cookie).strip() == 'nan':
            print(f'[警告]  {shop}  cookie 为空，跳过')
            continue
            
        download_tasks.append({
            'row_idx': row_idx,
            'shop': shop,
            'cookie': str(cookie)
        })
    
    print(f"共找到 {len(download_tasks)} 个需要下载的店铺")
    
    # 4. 批量下载所有文件
    downloaded_files = []
    for task in download_tasks:
        row_idx = task['row_idx']
        shop = task['shop']
        cookie = task['cookie']
        
        try:
            down_url = fetch_download_link(cookie)
            save_path = silent_download(down_url, shop)  # 传入店铺名称，函数内部会自动创建日期文件夹
            print(f'[成功] {shop}  下载完成: {save_path}')
            
            downloaded_files.append(save_path)
            
            # 更新状态为已完成
            df.iloc[row_idx, status_idx] = '已完成'
        except Exception as e:
            # 失败时置空状态，便于重试
            df.iloc[row_idx, status_idx] = ''
            print(f'[错误] {shop}  失败：{e}，已置空待重试')

    # 5. 保存Excel状态更新
    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
    print('Excel状态已更新！')
    
    # 6. 不管有没有下载文件，都进行合并和上传
    if downloaded_files:
        print(f'开始合并 {len(downloaded_files)} 个新下载的Excel文件...')
    else:
        print('[提示] 没有新下载的文件，但仍执行合并操作（合并现有文件）')
    
    # 创建日期文件夹路径
    date_dir = BASE_ARCHIVE_DIR / TODAY_STR
    
    # 使用ExcelMerger合并文件
    merger = ExcelMerger(str(date_dir))
    merge_success = merger.merge_excel_files(f"{TODAY_STR}.xlsx")
    
    if merge_success:
        # 读取合并后的文件
        merged_file_path = date_dir / f"{TODAY_STR}.xlsx"
        merged_df = pd.read_excel(merged_file_path)
        
        # 移动到最终目录
        final_merged_file_path = MERGED_FILES_DIR / f"{TODAY_STR}.xlsx"
        shutil.move(str(merged_file_path), str(final_merged_file_path))
        
        print(f'[成功] 文件合并完成，保存至: {final_merged_file_path}')
        
        # 上传合并后的文件到MinIO
        print(f'正在上传合并文件到MinIO...')
        upload_success = upload_merged_file_to_minio(str(final_merged_file_path), TODAY_STR)
        
        if upload_success:
            print(f'[成功] 合并文件MinIO上传成功')
        else:
            print(f'[警告]  合并文件MinIO上传失败，但本地文件已保存')
    else:
        print('[错误] 文件合并失败，无法生成合并文件')
    
    # 7. 所有文件上传完成后，刷新数据集和反射
    print('正在刷新数据集...')
    try:
        refresh_dataset_response = requests.post(
            "http://localhost:8003/api/dataset/refresh-metadata",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.pdd.pdd_kpi_weekly"}
        )
        if refresh_dataset_response.status_code == 200:
            print('[成功] 数据集刷新成功')
        else:
            print(f'[警告]  数据集刷新失败: {refresh_dataset_response.status_code}')
    except Exception as e:
        print(f'[错误] 数据集刷新异常: {e}')
    
    print('正在刷新反射...')
    try:
        refresh_reflection_response = requests.post(
            "http://localhost:8003/api/reflection/refresh",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.pdd.pdd_kpi_weekly"}
        )
        if refresh_reflection_response.status_code == 200:
            print('[成功] 反射刷新成功')
        else:
            print(f'[警告]  反射刷新失败: {refresh_reflection_response.status_code}')
    except Exception as e:
        print(f'[错误] 反射刷新异常: {e}')
    
    print('所有任务完成！')
