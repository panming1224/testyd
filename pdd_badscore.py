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
import math

# 设置标准输出编码为UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 添加merge_excel_files模块路径
sys.path.append(r'D:\testyd')
from merge_excel_files import ExcelMerger

# 配置
EXCEL_PATH = r'D:\pdd\拼多多店铺汇总表\拼多多店铺汇总表.xlsx'
BASE_ARCHIVE_DIR = Path('D:/pdd/评价文件存档')  # 基础存档目录
MERGED_FILES_DIR = Path('D:/pdd/合并文件/评价文件存档')  # 合并文件存储目录
SHEET = 0

# MinIO API配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"

# 创建基础存档目录和合并文件目录
os.makedirs(BASE_ARCHIVE_DIR, exist_ok=True)
os.makedirs(MERGED_FILES_DIR, exist_ok=True)

TODAY_STR = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

def update_header_once(df: pd.DataFrame):
    """固定用 N 列（索引 13）作为状态列，每天第一次把表头改成 今天+下载状态"""
    new_status = f'{TODAY_STR}差评下载状态'
    old_header = df.columns[13]         # N 列当前名字

    if old_header == new_status:
        return False                     # 今天已更新过，返回False表示未更新

    # 改名（只改表头，数据不动）
    df.rename(columns={old_header: new_status}, inplace=True)
    # 只在每天第一次运行时清空N列的所有数据（除了表头）
    # 这样避免了每次运行都清空状态的问题
    df.iloc[:, 13] = ''
    # 立即回写 Excel
    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
    return True                          # 返回True表示已更新


def fetch_reviews_data(cookie: str, shop_name: str):
    """
    获取拼多多差评数据
    """
    # 昨天的开始和结束时间戳（秒级）
    start_time = int(datetime.combine(datetime.now().date() - timedelta(days=1), datetime.min.time()).timestamp())
    end_time = int(datetime.combine(datetime.now().date() - timedelta(days=1), datetime.max.time()).timestamp())
    
    # 打印调试信息
    print(f'🔍 查询日期: {TODAY_STR}')
    print(f'🔍 开始时间戳: {start_time} ({datetime.fromtimestamp(start_time)})')
    print(f'🔍 结束时间戳: {end_time} ({datetime.fromtimestamp(end_time)})')
    
    url = 'https://mms.pinduoduo.com/saturn/reviews/list'
    
    headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'anti-content': '',
        'cache-control': 'no-cache',
        'Content-Type': 'application/json',
        'Cookie': cookie,
        'etag': '',
        'origin': 'https://mms.pinduoduo.com',
        'priority': 'u=1, i',
        'referer': 'https://mms.pinduoduo.com/goods/evaluation/index?msfrom=mms_globalsearch',
        'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    }
    
    # 首先获取第一页数据，确定总数据量
    first_page_data = {
        "startTime": start_time,
        "endTime": end_time,
        "pageNo": 1,
        "pageSize": 40,
        "descScore": ["1", "2", "3"],
        "mainReviewContentStatus": "1",
        "orderSn": ""
    }
    
    print(f'🔍 正在获取 {shop_name} 的差评数据...')
    
    try:
        response = requests.post(url, headers=headers, json=first_page_data, timeout=30)
        response.raise_for_status()
        
        # 打印完整的响应内容用于调试
        print(f'🔍 {shop_name} API响应状态码: {response.status_code}')
        print(f'🔍 {shop_name} API响应内容: {response.text[:1000]}...')  # 只打印前1000字符
        
        result = response.json()
        print(f'🔍 {shop_name} 解析后的JSON: {result}')
        
        if not result.get('success'):
            print(f'[错误] API返回失败: {result}')
            raise RuntimeError(f'API返回错误: {result.get("error_msg", "未知错误")}')
        
        total_rows = result.get('result', {}).get('totalRows', 0)
        print(f'📊 {shop_name} 共有 {total_rows} 条差评数据')
        
        if total_rows == 0:
            return []
        
        # 计算需要的页数
        page_size = 40
        total_pages = math.ceil(total_rows / page_size)
        
        all_data = []
        
        # 获取所有页面的数据
        for page_no in range(1, total_pages + 1):
            page_data = {
                "startTime": start_time,
                "endTime": end_time,
                "pageNo": page_no,
                "pageSize": page_size,
                "descScore": ["1", "2", "3"],
                "mainReviewContentStatus": "1",
                "orderSn": ""
            }
            
            print(f'📄 正在获取第 {page_no}/{total_pages} 页数据...')
            
            page_response = requests.post(url, headers=headers, json=page_data, timeout=30)
            page_response.raise_for_status()
            
            print(f'📄 第 {page_no} 页响应状态码: {page_response.status_code}')
            print(f'📄 第 {page_no} 页响应内容: {page_response.text[:500]}...')
            
            page_result = page_response.json()
            print(f'📄 第 {page_no} 页解析后的JSON: {page_result}')
            
            if page_result.get('success'):
                page_items = page_result.get('result', {}).get('data', [])
                print(f'📄 第 {page_no} 页获取到 {len(page_items)} 条数据')
                
                # 添加调试信息，查看数据结构
                if page_items:
                    print(f'📄 第一条数据结构: {page_items[0]}')
                    if 'orderSnapshotInfo' in page_items[0]:
                        print(f'📄 orderSnapshotInfo内容: {page_items[0]["orderSnapshotInfo"]}')
                
                all_data.extend(page_items)
            else:
                print(f'[警告] 第 {page_no} 页获取失败: {page_result.get("error_msg", "未知错误")}')
            
            # 添加延迟避免请求过快
            time.sleep(0.5)
        
        print(f'[成功] {shop_name} 数据获取完成，共 {len(all_data)} 条记录')
        return all_data
    except Exception as e:
        print(f'[错误] {shop_name} 数据获取失败: {str(e)}')
        raise


def parse_reviews_data(data_list):
    """
    解析差评数据，转换为Excel格式
    """
    if not data_list:
        return []
    
    keys = [
        'descScore',           # 用户评价分
        'comment',             # 用户评论
        'orderSn',             # 订单编号
        'name',                # 卖家昵称（在 orderSnapshotInfo 里）
        'goodsId',             # 商品 ID
        'goodsInfoUrl'         # 页返回链接（商品页）
    ]
    
    table = [keys]
    max_pictures = 0  # 用于记录最大图片数量
    
    for item in data_list:
        row = []
        current_pictures = 0  # 当前条目中的图片数量
        
        # 遍历每个字段
        for k in keys:
            if k == 'name':
                # name字段直接在item中，不在orderSnapshotInfo中
                name_value = item.get('name', '')
                # 修复以=开头的name值，在前面加上单引号防止Excel解析为公式
                if isinstance(name_value, str) and name_value.startswith('='):
                    name_value = "'" + name_value
                row.append(name_value)
            else:
                row.append(item.get(k, ''))
        
        # 处理图片链接，每个图片单独一列
        pics = item.get('pictures', []) or []
        current_pictures = len(pics)
        if current_pictures > max_pictures:
            max_pictures = current_pictures
        for pic in pics:
            row.append(pic.get('url', ''))
        
        # 如果当前图片数量少于最大值，填充空字符串以对齐
        if current_pictures < max_pictures:
            row.extend([''] * (max_pictures - current_pictures))
        
        table.append(row)
    
    # 更新表头以包含图片列
    table[0].extend([f'Picture_{i+1}' for i in range(max_pictures)])
    
    return table


def save_to_excel(table_data, shop_name, date_str=None):
    """
    将数据保存到Excel文件
    """
    if date_str is None:
        date_str = TODAY_STR
    
    # 创建日期文件夹路径：D:\pdd\评价文件存档\2025-09-25\
    date_dir = BASE_ARCHIVE_DIR / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件保存路径：D:\pdd\评价文件存档\2025-09-25\店铺名称.xlsx
    file_name = f'{shop_name}.xlsx'
    save_path = date_dir / file_name
    
    # 如果目标文件已存在，先删除
    if save_path.exists():
        print(f'🗑️  发现同名文件，正在删除: {save_path}')
        save_path.unlink()  # 删除文件
        print(f'[成功] 同名文件已删除')
    
    # 转换为DataFrame并保存
    if table_data:
        df = pd.DataFrame(table_data[1:], columns=table_data[0])
        df.to_excel(save_path, index=False, engine='openpyxl')
        print(f'💾 数据已保存到: {save_path}')
        return save_path
    else:
        print(f'[警告] {shop_name} 没有数据需要保存')
        return None


def upload_merged_file_to_minio(merged_file_path: str, date_str: str = None) -> bool:
    """
    将合并后的Excel文件转换为Parquet格式并上传到MinIO
    
    Args:
        merged_file_path: 合并后的Excel文件路径
        date_str: 日期字符串，默认使用昨天
    
    Returns:
        bool: 上传是否成功
    """
    if date_str is None:
        date_str = TODAY_STR
    
    try:
        # 读取合并后的Excel文件
        df = pd.read_excel(merged_file_path)
        
        # 清理NaN值，将NaN替换为空字符串或None
        df = df.fillna('')  # 将所有NaN值替换为空字符串
        
        # 构建MinIO路径：ods/pdd/pdd_badscore/dt=日期/merged_badscore_data.parquet
        minio_path = f"ods/pdd/pdd_badscore/dt={date_str}/merged_badscore_data.parquet"
        
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
                print(f"[成功] 成功上传合并文件到MinIO: {minio_path}")
                return True
            else:
                print(f"[错误] MinIO上传失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"[错误] MinIO API请求失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[错误] 上传合并文件到MinIO时出错: {str(e)}")
        return False


if __name__ == '__main__':
    # 1. 读表 & 更新表头
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)  
    header_updated = update_header_once(df)
    
    # 如果表头更新了，需要重新读取DataFrame
    if header_updated:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)

    # 2. 定位关键列
    cookie_idx = 9    # J列 (cookie)
    status_idx = 13   # N列 (状态列)
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
        
        print(f"检查第{row_idx+2}行: {shop}, 状态: '{status_str}', cookie: '{str(cookie)[:50]}...'")

        # 检查cookie是否有效
        if pd.isna(cookie) or str(cookie).strip() == '' or str(cookie).strip() == 'nan':
            print(f'[警告] {shop}  cookie 为空，跳过')
            continue
            
        # 检查状态：只有空状态或非"已完成"状态才需要下载
        if status_str.strip() == '已完成':
            print(f'[跳过] {shop}  状态已完成，跳过')
            continue
        else:
            # 空状态或其他状态都需要下载
            download_tasks.append({
                'row_idx': row_idx,
                'shop': shop,
                'cookie': str(cookie)
            })
    
    print(f"共找到 {len(download_tasks)} 个需要下载的店铺")
    
    # 4. 批量获取所有店铺的差评数据
    downloaded_files = []
    for task in download_tasks:
        row_idx = task['row_idx']
        shop = task['shop']
        cookie = task['cookie']
        
        try:
            # 获取差评数据
            reviews_data = fetch_reviews_data(cookie, shop)
            
            if reviews_data:
                # 解析数据
                table_data = parse_reviews_data(reviews_data)
                
                # 保存到Excel
                save_path = save_to_excel(table_data, shop)
                if save_path:
                    downloaded_files.append(save_path)
                    print(f'[成功] {shop}  差评数据处理完成: {save_path}')
                else:
                    print(f'[警告] {shop}  没有数据保存')
            else:
                print(f'ℹ️  {shop}  没有差评数据')
            
            # 更新状态为已完成
            df.iloc[row_idx, status_idx] = '已完成'
            
        except Exception as e:
            # 失败时置空状态，便于重试
            df.iloc[row_idx, status_idx] = ''
            print(f'[错误] {shop}  失败：{e}，已置空待重试')

    # 5. 保存Excel状态更新
    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
    print('Excel状态已更新！')
    
    # 6. 如果有下载的文件，进行合并和上传
    if downloaded_files:
        print(f'🔄 开始合并 {len(downloaded_files)} 个Excel文件...')
        
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
    
    # 7. 所有文件上传完成后，刷新数据集和反射
    print('🔄 正在刷新数据集...')
    try:
        refresh_dataset_response = requests.post(
            "http://localhost:8003/api/dataset/refresh-metadata",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.pdd.pdd_badscore"}
        )
        if refresh_dataset_response.status_code == 200:
            print('[成功] 数据集刷新成功')
        else:
            print(f'[警告] 数据集刷新失败: {refresh_dataset_response.status_code}')
    except Exception as e:
        print(f'[错误] 数据集刷新异常: {e}')
    
    print('🔄 正在刷新反射...')
    try:
        refresh_reflection_response = requests.post(
            "http://localhost:8003/api/reflection/refresh",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.pdd.pdd_badscore"}
        )
        if refresh_reflection_response.status_code == 200:
            print('[成功] 反射刷新成功')
        else:
            print(f'[警告] 反射刷新失败: {refresh_reflection_response.status_code}')
    except Exception as e:
        print(f'[错误] 反射刷新异常: {e}')
    
    print('🎉 所有任务完成！')