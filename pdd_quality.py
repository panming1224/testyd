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

# 配置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 添加merge_excel_files模块路径
sys.path.append(r'D:\testyd')
from merge_excel_files import ExcelMerger

# 配置
EXCEL_PATH = r'D:\pdd\拼多多店铺汇总表\拼多多店铺汇总表.xlsx'
EXCEL_BACKUP_PATH = r'D:\pdd\拼多多店铺汇总表\拼多多店铺汇总表.xlsx'
BASE_ARCHIVE_DIR = Path('D:/pdd/产品质量体验存档')  # 基础存档目录
MERGED_FILES_DIR = Path('D:/pdd/合并文件/产品质量体验存档')  # 合并文件存储目录
SHEET = 0

# MinIO API配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"

# 创建基础存档目录和合并文件目录
os.makedirs(BASE_ARCHIVE_DIR, exist_ok=True)
os.makedirs(MERGED_FILES_DIR, exist_ok=True)

TODAY_STR = datetime.now().strftime('%Y-%m-%d')

# 产品质量数据表头和对应字段
QUALITY_HEADERS = ['商品id', '商品名称', '商品主图链接', '商品质量体验排名', '近30天异常订单数', 
                   '异常订单占比', '权益状态', '商品质量等级', '近30天品质求助平台率', 
                   '近30天商品评价分排名', '老客订单占比']

QUALITY_FIELDS = ['goods_id', 'goods_name', 'img_url', 'rank_percent', 'abnormal_order_num', 
                  'abnormal_order_ratio', 'right_status', 'quality_level', 'quality_help_rate_last30_days', 
                  'goods_rating_rank', 'repeat_purchase_ratio']

def update_header_once(df: pd.DataFrame):
    """固定用 K 列（索引 10）作为状态列，每天第一次把表头改成 今天+产品质量下载状态"""
    new_status = f'{TODAY_STR}产品质量下载状态'
    old_header = df.columns[10]          # K 列当前名字

    if old_header == new_status:
        return False                     # 今天已更新过，返回False表示未更新

    # 改名（只改表头，数据不动）
    df.rename(columns={old_header: new_status}, inplace=True)
    # 只在每天第一次运行时清空K列的所有数据（除了表头）
    # 这样避免了每次运行都清空状态的问题
    df.iloc[:, 10] = ''
    
    # 立即回写 Excel
    try:
        df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
        print(f"已更新表头为: {new_status} 并清空所有状态")
        return True                      # 返回True表示已更新
    except PermissionError:
        print(f"无法写入Excel文件，可能被其他程序占用。继续使用内存中的数据...")
        return False


def fetch_quality_data(cookie: str):
    """
    获取产品质量体验数据
    """
    url = 'https://mms.pinduoduo.com/api/price/mariana/quality_experience/goods_list'
    
    headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'anti-content': '',
        'cache-control': '',
        'Content-Type': 'application/json',
        'Cookie': cookie,
        'etag': '',
        'origin': 'https://mms.pinduoduo.com',
        'priority': '',
        'referer': 'https://mms.pinduoduo.com/mms-marketing-mixin/quality-experience?msfrom=mms_globalsearch',
        'sec-ch-ua': '',
        'sec-ch-ua-mobile': '',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': '',
        'sec-fetch-mode': '',
        'sec-fetch-site': '',
        'user-agent': ''
    }

    # 先获取第一页数据，确定总数量
    body = {"sort_field": 1, "sort_type": "ASC", "page_size": 40, "page_no": 1}
    
    resp = requests.post(url, headers=headers, json=body, timeout=15)
    print(f'【响应】{resp.text}')
    resp.raise_for_status()
    
    first_page_data = resp.json()
    if not first_page_data.get('success'):
        raise RuntimeError(f'API请求失败：{first_page_data.get("error_msg")}')
    
    result = first_page_data.get('result', {})
    total = result.get('total', 0)
    
    print(f'总共有 {total} 条产品质量数据')
    
    # 计算需要多少页
    page_size = 40
    total_pages = (total + page_size - 1) // page_size
    
    all_goods_list = []
    
    # 获取所有页面的数据
    for page_no in range(1, total_pages + 1):
        print(f'正在获取第 {page_no}/{total_pages} 页数据...')
        
        body = {"sort_field": 1, "sort_type": "ASC", "page_size": page_size, "page_no": page_no}
        
        resp = requests.post(url, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        
        page_data = resp.json()
        if page_data.get('success'):
            page_result = page_data.get('result', {})
            goods_list = page_result.get('goods_list', [])
            all_goods_list.extend(goods_list)
            print(f'第 {page_no} 页获取到 {len(goods_list)} 条数据')
        else:
            print(f'第 {page_no} 页获取失败：{page_data.get("error_msg")}')
        
        # 添加延迟避免请求过快
        time.sleep(0.15)
    
    return total, all_goods_list


def to_list(total, goods_list, cols):
    """
    解析响应数据，转换为矩阵格式
    """
    matrix = [[row.get(c, '') for c in cols] for row in goods_list]
    return [total, matrix]


def save_quality_data_to_excel(shop_name: str, total: int, goods_list: list, date_str: str = None):
    """
    将产品质量数据保存到Excel文件
    """
    if date_str is None:
        date_str = TODAY_STR
    
    # 创建日期文件夹路径
    date_dir = BASE_ARCHIVE_DIR / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件保存路径
    file_name = f'{shop_name}产品质量数据.xlsx'
    save_path = date_dir / file_name

    # 如果目标文件已存在，先删除
    if save_path.exists():
        print(f'发现同名文件，正在删除: {save_path}')
        save_path.unlink()
        print(f'同名文件已删除')

    # 转换数据为DataFrame格式
    total_data, matrix = to_list(total, goods_list, QUALITY_FIELDS)
    
    # 创建DataFrame
    df = pd.DataFrame(matrix, columns=QUALITY_HEADERS)
    
    # 保存到Excel文件
    df.to_excel(save_path, index=False, engine='openpyxl')
    
    print(f'产品质量数据已保存: {save_path} (共 {len(matrix)} 条数据)')
    
    return save_path


def upload_merged_file_to_minio(merged_file_path: str, date_str: str = None) -> bool:
    """
    将合并后的Excel文件转换为Parquet格式并上传到MinIO
    """
    if date_str is None:
        date_str = TODAY_STR
    
    try:
        # 读取合并后的Excel文件
        df = pd.read_excel(merged_file_path)
        
        # 处理NaN值，替换为None
        df = df.replace({pd.NA: None})
        df = df.where(pd.notnull(df), None)
        
        # 转换为字典列表
        data_dict = df.to_dict(orient='records')
        
        # 进一步清理NaN值
        cleaned_data = []
        for record in data_dict:
            cleaned_record = {}
            for key, value in record.items():
                if pd.isna(value) or value is pd.NA:
                    cleaned_record[key] = ""  # 使用空字符串替代NaN
                elif isinstance(value, float) and (value != value):  # 检查NaN
                    cleaned_record[key] = ""
                else:
                    cleaned_record[key] = value
            cleaned_data.append(cleaned_record)
        
        # 构建MinIO路径：ods/pdd/pdd_quality/dt=日期/merged_quality_data.parquet
        minio_path = f"ods/pdd/pdd_quality/dt={date_str}/merged_quality_data.parquet"
        
        # 准备上传数据
        upload_data = {
            "data": cleaned_data,
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
                print(f"成功上传合并文件到MinIO: {minio_path}")
                return True
            else:
                print(f"MinIO上传失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"MinIO API请求失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"上传合并文件到MinIO时出错: {str(e)}")
        return False


def safe_read_excel():
    """安全读取Excel文件，如果主文件损坏则使用备份文件"""
    try:
        print(f"尝试读取主Excel文件: {EXCEL_PATH}")
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)
        print("✅ 主Excel文件读取成功")
        return df, EXCEL_PATH
    except Exception as e:
        print(f"❌ 主Excel文件读取失败: {e}")
        print(f"尝试读取备份Excel文件: {EXCEL_BACKUP_PATH}")
        try:
            df = pd.read_excel(EXCEL_BACKUP_PATH, sheet_name=SHEET)
            print("✅ 备份Excel文件读取成功")
            # 将备份文件复制为主文件
            import shutil
            shutil.copy2(EXCEL_BACKUP_PATH, EXCEL_PATH)
            print("✅ 已将备份文件复制为主文件")
            return df, EXCEL_PATH
        except Exception as backup_e:
            print(f"❌ 备份Excel文件也读取失败: {backup_e}")
            raise Exception(f"主文件和备份文件都无法读取: 主文件错误={e}, 备份文件错误={backup_e}")


if __name__ == '__main__':
    # 1. 安全读表 & 更新表头
    df, used_file = safe_read_excel()
    header_updated = update_header_once(df)

    # 2. 定位关键列
    cookie_idx = 9    # J列 (cookie)
    status_idx = 10   # K列 (状态列)
    shop_idx   = 1    # B列 (店铺名称)

    print(f"DataFrame形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    print(f"状态列名: {df.columns[status_idx]}")

    # 3. 收集所有需要拉取数据的店铺信息
    download_tasks = []
    for row_idx in range(len(df)):
        shop   = df.iloc[row_idx, shop_idx]
        cookie = df.iloc[row_idx, cookie_idx]
        status = df.iloc[row_idx, status_idx]

        # 转换为字符串处理
        status_str = str(status) if pd.notna(status) else ''
        
        print(f"检查第{row_idx+2}行: {shop}, 状态: '{status_str}'")

        # 空值/已完成的跳过 - 由于我们已经清空了状态，所以不会有"已完成"
        if status_str.strip() == '已完成':
            print(f'[跳过] {shop}  状态已完成，跳过')
            continue
        if pd.isna(cookie) or str(cookie).strip() == '' or str(cookie).strip() == 'nan':
            print(f'[警告] {shop}  cookie 为空，跳过')
            continue
            
        download_tasks.append({
            'row_idx': row_idx,
            'shop': shop,
            'cookie': str(cookie)
        })
    
    print(f"共找到 {len(download_tasks)} 个需要拉取产品质量数据的店铺")
    
    # 4. 批量拉取所有店铺的产品质量数据
    saved_files = []
    for task in download_tasks:
        row_idx = task['row_idx']
        shop = task['shop']
        cookie = task['cookie']
        
        try:
            total, goods_list = fetch_quality_data(cookie)
            save_path = save_quality_data_to_excel(shop, total, goods_list)
            print(f'[成功] {shop}  产品质量数据拉取完成: {save_path}')
            
            saved_files.append(save_path)
            
            # 更新状态为已完成
            df.iloc[row_idx, status_idx] = '已完成'
        except Exception as e:
            # 失败时置空状态，便于重试
            df.iloc[row_idx, status_idx] = ''
            print(f'{shop} 失败：{e}，已置空待重试')

    # 5. 保存Excel状态更新
    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
    print('Excel状态已更新！')
    
    # 6. 如果有保存的文件，进行合并和上传
    if saved_files:
        print(f'开始合并 {len(saved_files)} 个Excel文件...')
        
        # 创建日期文件夹路径
        date_dir = BASE_ARCHIVE_DIR / TODAY_STR
        
        # 使用修复后的ExcelMerger合并文件，指定独立的输出目录
        merger = ExcelMerger(str(date_dir), output_dir=str(MERGED_FILES_DIR))
        merge_success = merger.merge_excel_files(f"{TODAY_STR}.xlsx")
        
        if merge_success:
            # 合并后的文件直接在最终目录中
            final_merged_file_path = MERGED_FILES_DIR / f"{TODAY_STR}.xlsx"
            
            # 读取合并后的文件进行验证
            merged_df = pd.read_excel(final_merged_file_path)
            
            print(f'文件合并完成，保存至: {final_merged_file_path}')
            print(f'📊 合并文件统计: {len(merged_df)} 行, {len(merged_df.columns)} 列')
            
            # 检查是否有日期格式的shop
            if 'shop' in merged_df.columns:
                date_shops = merged_df[merged_df['shop'].str.match(r'^\d{4}-\d{2}-\d{2}$', na=False)]
                if len(date_shops) > 0:
                    print(f'[警告] 警告: 发现 {len(date_shops)} 行日期格式的shop数据')
                else:
                    print(f'验证通过: 无日期格式的shop数据，共 {merged_df["shop"].nunique()} 个有效店铺')
            
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
    print('[警告] 没有新保存的文件，跳过合并和上传步骤')

# 7. 所有文件上传完成后，刷新数据集和反射
print('正在刷新数据集...')
try:
    refresh_dataset_response = requests.post(
        "http://localhost:8003/api/dataset/refresh-metadata",
        headers={"Content-Type": "application/json"},
        json={"dataset_path": "minio.warehouse.ods.pdd.pdd_quality"}
    )
    if refresh_dataset_response.status_code == 200:
        print('数据集刷新成功')
    else:
        print(f'数据集刷新失败: {refresh_dataset_response.status_code}')
except Exception as e:
    print(f'数据集刷新异常: {e}')

print('正在刷新反射...')
try:
    refresh_reflection_response = requests.post(
        "http://localhost:8003/api/reflection/refresh",
        headers={"Content-Type": "application/json"},
        json={"dataset_path": "minio.warehouse.ods.pdd.pdd_quality"}
    )
    if refresh_reflection_response.status_code == 200:
        print('反射刷新成功')
    else:
        print(f'反射刷新失败: {refresh_reflection_response.status_code}')
except Exception as e:
    print(f'反射刷新异常: {e}')

print('🎉 所有任务完成！')