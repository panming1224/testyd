# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import time
import json
import requests
import uuid
import os
import pandas as pd
import shutil
import re
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 配置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 添加merge_excel_files模块路径
sys.path.append(r'D:\testyd')
from merge_excel_files import ExcelMerger

# 配置
EXCEL_PATH = r'D:\yingdao\erp\店铺信息.xlsx'
BASE_ARCHIVE_DIR_GOODS = Path('D:/yingdao/erp/商品及库存管理')  # 商品及库存管理存档目录
BASE_ARCHIVE_DIR_BOM = Path('D:/yingdao/erp/bom表')  # BOM表存档目录
MERGED_FILES_DIR_GOODS = Path('D:/yingdao/erp/合并表格/商品及库存管理')  # 商品及库存管理合并文件存储目录
MERGED_FILES_DIR_BOM = Path('D:/yingdao/erp/合并表格/bom表')  # BOM表合并文件存储目录
SHEET = 0

# MinIO API配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"

# ERP API配置
ERP_LOGIN_URL = "https://www.erp321.com/epaas"
ERP_API_BASE_URL = "https://api.erp321.com/erp/webapi/ItemApi/Export/ItemSkuAndInventory"

# 创建基础存档目录和合并文件目录
os.makedirs(BASE_ARCHIVE_DIR_GOODS, exist_ok=True)
os.makedirs(BASE_ARCHIVE_DIR_BOM, exist_ok=True)
os.makedirs(MERGED_FILES_DIR_GOODS, exist_ok=True)
os.makedirs(MERGED_FILES_DIR_BOM, exist_ok=True)

# 使用T-1日期（昨天）
TODAY_STR = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

def update_header_once(df: pd.DataFrame):
    """固定用 E、F 列作为状态列，每天第一次把表头改成 今天+下载状态"""
    new_status_goods = f'{TODAY_STR}商品库存下载状态'
    new_status_bom = f'{TODAY_STR}BOM表下载状态'
    
    old_header_e = df.columns[4]  # E列当前名字
    old_header_f = df.columns[5]  # F列当前名字
    
    updated = False
    
    # 更新E列表头（商品及库存管理状态）
    if old_header_e != new_status_goods:
        df.rename(columns={old_header_e: new_status_goods}, inplace=True)
        df.iloc[:, 4] = ''  # 清空E列数据
        updated = True
    
    # 更新F列表头（BOM表状态）
    if old_header_f != new_status_bom:
        df.rename(columns={old_header_f: new_status_bom}, inplace=True)
        df.iloc[:, 5] = ''  # 清空F列数据
        updated = True
    
    if updated:
        # 立即回写 Excel
        df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
        return True
    
    return False

def get_cookie_from_erp(profile: str = "Default"):
    """
    获取ERP系统的Cookie
    profile: 浏览器配置文件
    """
    USER_DATA_DIR = r"C:\\Users\\1\AppData\\Local\\Chromium\\User Data"
    
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
            ignore_https_errors=True
        )
        
        page = context.new_page()
        page.goto(ERP_LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        
        # 等待页面加载完成
        page.wait_for_load_state('networkidle')
        
        # 获取Cookie
        cookies = context.cookies(ERP_LOGIN_URL)
        cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
        
        page.close()
        context.close()
        
        return cookie_str

def data(text):
    """解析响应数据"""
    raw = json.loads(text)
    data = raw.get("data", "")
    return data

def download(result):
    """解析下载进度和URL"""
    try:
        raw = json.loads(result)
        print(f"原始响应数据: {raw}")
        
        # 检查响应格式
        if raw.get("code") == 0:
            data = raw.get("data", "")
            
            # 如果data是数字，可能是任务ID，需要用另一个API查询进度
            if isinstance(data, int):
                print(f"获得任务ID: {data}")
                # 这里应该返回任务ID，用于后续查询
                return [0, ""]  # 进度0，URL为空，表示任务刚开始
            
            # 如果data是对象，尝试获取progress和url
            elif isinstance(data, dict):
                progress = data.get("progress", 0)
                url = data.get("url", "")
                return [progress, url]
            
            # 如果data是字符串，可能是URL
            elif isinstance(data, str) and data.startswith("http"):
                return [100, data]  # 直接返回URL，进度100
                
        return [0, ""]  # 默认返回
        
    except Exception as e:
        print(f"解析响应时出错: {e}")
        return [0, ""]

def fetch_goods_inventory_data(shop_name: str, owner_co_id: str, authorize_co_id: str, profile: str):
    """
    获取商品及库存管理数据
    第一步：发送POST请求生成导出任务，获取任务ID
    第二步：轮询查询任务状态，直到进度100且获得下载URL
    """
    # 获取cookies
    cookie_str = get_cookie_from_erp(profile)
    if not cookie_str:
        print(f'获取 {shop_name} 的cookies失败')
        return False
    print(f"[{shop_name}] 开始获取商品及库存管理数据...")
    
    # 第一步：发送导出请求，生成任务
    export_url = f"https://api.erp321.com/erp/webapi/ItemApi/Export/ItemSkuAndInventory?owner_co_id={owner_co_id}&authorize_co_id={authorize_co_id}"
    
    # 构建请求头
    headers = {
        "accept": "application/json",
        "accept-language": "zh-CN,zh;q=0.9",
        "Content-Type": "application/json; charset=utf-8",
        "Cookie": cookie_str,
        "gwfp": "",
        "origin": "https://src.erp321.com",
        "priority": "u=1, i",
        "sec-ch-ua": "",
        "sec-ch-ua-mobile": "",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    
    # 构建请求体
    export_body = {
        "ip": "",
        "uid": "21599824",
        "coid": owner_co_id,
        "data": {
            "type": 3,
            "searchCondition": {
                "enabled": "1",
                "queryFlds": [
                    "pic", "i_id", "sku_id", "name", "properties_value", "order_lock", "qty", "orderable",
                    "purchase_qty", "virtual_qty", "sales_qty_3", "short_name", "sale_price", "cost_price",
                    "purchase_price", "market_price", "brand", "category", "vc_name", "labels", "sku_code",
                    "_sku_codes", "supplier_name", "purchaseFeature", "purchaseQty", "weight", "l", "w", "h",
                    "volume", "unit", "enabled", "stock_opensync", "remark", "sku_tag", "bin_min_qty",
                    "bin_max_qty", "overflow_qty", "pack_qty", "pack_volume", "bin", "other_price_1",
                    "other_price_2", "other_price_3", "other_1", "other_2", "other_3", "modified", "created",
                    "creator_name", "is_cpfr", "cpfr_qty", "pic_big"
                ],
                "sku_type": 1,
                "orderBy": ""
            },
            "filterType": 2
        },
        "isOtherStore": False
    }
    
    try:
        # 第一步：发送导出请求
        print(f"[{shop_name}] 发送导出任务请求...")
        export_response = requests.post(export_url, headers=headers, data=json.dumps(export_body))
        print(f"[{shop_name}] 导出任务响应状态: {export_response.status_code}")
        print(f"[{shop_name}] 导出任务响应内容: {export_response.text}")
        
        if export_response.status_code != 200:
            print(f"[{shop_name}] 导出任务请求失败: {export_response.status_code}")
            return False
            
        # 解析任务ID
        try:
            export_result = json.loads(export_response.text)
            if export_result.get("code") != 0:
                print(f"[{shop_name}] 导出任务失败: {export_result}")
                return False
                
            task_data = export_result.get("data")
            if isinstance(task_data, int):
                task_id = task_data
                print(f"[{shop_name}] 获得导出任务ID: {task_id}")
            else:
                print(f"[{shop_name}] 无法获取任务ID: {task_data}")
                return False
                
        except Exception as parse_error:
            print(f"[{shop_name}] 解析导出任务响应失败: {parse_error}")
            return False
        
        # 第二步：轮询查询任务状态
        query_url = f"https://api.erp321.com/erp/webapi/ItemApi/Export/GetExportData?owner_co_id={owner_co_id}&authorize_co_id={authorize_co_id}"
        
        query_body = {
            "ip": "",
            "uid": "",
            "coid": owner_co_id,
            "data": task_id  # 使用任务ID
        }
        
        max_attempts = 60  # 最大尝试次数
        attempt = 0
        
        while attempt < max_attempts:
            try:
                print(f"[{shop_name}] 第{attempt + 1}次查询任务状态...")
                
                # 查询任务状态
                query_response = requests.post(query_url, headers=headers, data=json.dumps(query_body))
                print(f"[{shop_name}] 状态查询响应状态: {query_response.status_code}")
                print(f"[{shop_name}] 状态查询响应内容: {query_response.text}")
                
                if query_response.status_code == 200:
                    try:
                        progress_data = download(query_response.text)
                        progress = progress_data[0]
                        download_url = progress_data[1]
                        
                        print(f"[{shop_name}] 解析结果 - 进度: {progress}, URL: {download_url}")
                        
                        if progress == 100 and download_url and download_url != "":
                            print(f"[{shop_name}] 任务完成，开始下载文件...")
                            
                            # 下载文件
                            download_response = requests.get(download_url, stream=True)
                            if download_response.status_code == 200:
                                # 创建下载目录
                                date_dir = BASE_ARCHIVE_DIR_GOODS / TODAY_STR
                                date_dir.mkdir(parents=True, exist_ok=True)
                                
                                # 生成文件名
                                filename = f"{shop_name}.xlsx"
                                file_path = date_dir / filename
                                
                                # 如果目标文件已存在，先删除
                                if file_path.exists():
                                    print(f'[{shop_name}] 删除同名文件: {file_path}')
                                    file_path.unlink()
                                
                                # 保存文件
                                with open(file_path, 'wb') as f:
                                    for chunk in download_response.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                
                                print(f"[{shop_name}] 商品库存数据下载完成: {file_path}")
                                return True
                            else:
                                print(f"[{shop_name}] 文件下载失败: {download_response.status_code}")
                                return False
                        else:
                            print(f"[{shop_name}] 任务进行中，进度: {progress}%, URL: {download_url}")
                            time.sleep(3)  # 等待3秒后重试
                            attempt += 1
                    except Exception as parse_error:
                        print(f"[{shop_name}] 解析状态查询响应时出错: {parse_error}")
                        time.sleep(3)
                        attempt += 1
                else:
                    print(f"[{shop_name}] 状态查询失败: {query_response.status_code}")
                    time.sleep(3)
                    attempt += 1
                    
            except Exception as e:
                print(f"[{shop_name}] 查询任务状态时出错: {e}")
                time.sleep(3)
                attempt += 1
        
        print(f"[{shop_name}] 达到最大尝试次数，任务可能超时")
        return False
        
    except Exception as e:
        print(f"[{shop_name}] 获取商品库存数据时出错: {e}")
        return False

def fetch_bom_data(shop_name: str, owner_co_id: str, authorize_co_id: str, profile: str):
    """
    获取BOM表数据
    直接访问BOM页面，然后点击导入导出按钮
    """
    print(f"[{shop_name}] 开始获取BOM表数据...")
    
    USER_DATA_DIR = r"C:\\Users\\1\AppData\\Local\\Chromium\\User Data"
    
    # 设置下载目录
    download_path = BASE_ARCHIVE_DIR_BOM / TODAY_STR
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
            # 直接导航到BOM页面
            bom_url = "https://www.erp321.com/app/item/item_sku/bom/item_sku.aspx?_c=jst-epaas"
            print(f"[{shop_name}] 直接访问BOM页面: {bom_url}")
            page.goto(bom_url, wait_until="domcontentloaded", timeout=30000)
            
            # 等待页面加载
            page.wait_for_load_state('networkidle')
            print(f"[{shop_name}] BOM页面加载完成")
            
            # 1. 先点父按钮
            print(f"[{shop_name}] 点击BOM导入导出按钮...")
            page.locator('xpath=//*[@id="BomOpration_Btn"]/span[2]').click()
            
            # 2. 再点「导出/下载」并等待下载完成
            print(f"[{shop_name}] 点击BOM导出选项并等待下载...")
            with page.expect_download() as download_info:
                page.locator('xpath=//*[@id="BomOpration_Btn"]/div/div[2]').click()
            
            download = download_info.value
            
            # 3. 保存到指定位置
            filename = f"{shop_name}.xlsx"
            final_path = download_path / filename
            download.save_as(final_path)
            
            print(f"[{shop_name}] BOM表下载成功: {final_path}")
            return True
                
        except Exception as e:
            print(f"[{shop_name}] BOM表数据获取失败: {str(e)}")
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
        
        # 构建完整的MinIO路径
        full_minio_path = f"{minio_path}/dt={date_str}/data.parquet"
        
        # 处理NaN值和无穷大值
        df = df.fillna('')
        df = df.replace([float('inf'), float('-inf')], '')
        
        # 确保所有数据都能正常序列化
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32']:
                df[col] = df[col].replace([float('inf'), float('-inf')], '')
            # 转换为字符串以避免序列化问题
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
    print("ERP数据抓取程序启动...")
    print(f"目标日期: {TODAY_STR}")
    
    # 1. 读表 & 更新表头
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)  
    header_updated = update_header_once(df)
    
    # 如果表头更新了，需要重新读取DataFrame
    if header_updated:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)
        print("表头已更新")

    # 2. 定位关键列
    shop_idx = 0        # A列 (店铺名称)
    profile_idx = 1     # B列 (浏览器配置文件)
    owner_co_id_idx = 2 # C列 (owner_co_id)
    authorize_co_id_idx = 3  # D列 (authorize_co_id)
    goods_status_idx = 4     # E列 (商品库存状态)
    bom_status_idx = 5       # F列 (BOM表状态)

    print(f"DataFrame形状: {df.shape}")
    print(f"列名: {list(df.columns)}")

    # 3. 收集所有需要处理的店铺信息
    download_tasks = []
    for row_idx in range(len(df)):
        shop = df.iloc[row_idx, shop_idx]
        profile = df.iloc[row_idx, profile_idx]
        owner_co_id = df.iloc[row_idx, owner_co_id_idx]
        authorize_co_id = df.iloc[row_idx, authorize_co_id_idx]
        goods_status = df.iloc[row_idx, goods_status_idx]
        bom_status = df.iloc[row_idx, bom_status_idx]

        # 转换为字符串处理
        goods_status_str = str(goods_status) if pd.notna(goods_status) else ''
        bom_status_str = str(bom_status) if pd.notna(bom_status) else ''
        
        print(f"检查第{row_idx+2}行: {shop}, 商品库存状态: '{goods_status_str}', BOM状态: '{bom_status_str}'")

        # 检查是否需要下载商品库存数据
        need_goods = goods_status_str.strip() != '已完成'
        # 检查是否需要下载BOM数据
        need_bom = bom_status_str.strip() != '已完成'
        
        if need_goods or need_bom:
            # 验证必要参数
            if pd.isna(profile) or pd.isna(owner_co_id) or pd.isna(authorize_co_id):
                print(f'跳过 {shop} - 缺少必要的参数')
                continue
                
            download_tasks.append({
                'row_idx': row_idx,
                'shop': shop,
                'profile': str(profile),
                'owner_co_id': str(owner_co_id),
                'authorize_co_id': str(authorize_co_id),
                'need_goods': need_goods,
                'need_bom': need_bom
            })
    
    print(f"共找到 {len(download_tasks)} 个需要处理的店铺")
    
    # 4. 批量处理所有店铺
    for task in download_tasks:
        row_idx = task['row_idx']
        shop = task['shop']
        profile = task['profile']
        owner_co_id = task['owner_co_id']
        authorize_co_id = task['authorize_co_id']
        need_goods = task['need_goods']
        need_bom = task['need_bom']
        
        print(f"\n处理店铺: {shop}")
        
        # 下载商品库存数据
        if need_goods:
            try:
                goods_success = fetch_goods_inventory_data(shop, owner_co_id, authorize_co_id, profile)
                if goods_success:
                    print(f'[{shop}] 商品库存数据下载成功')
                    df.iloc[row_idx, goods_status_idx] = '已完成'
                    
                    # 上传到MinIO
                    date_dir = BASE_ARCHIVE_DIR_GOODS / TODAY_STR
                    file_path = date_dir / f"{shop}.xlsx"
                    if file_path.exists():
                        upload_file_to_minio(str(file_path), "ods/erp/goodscount", TODAY_STR)
                else:
                    print(f'[{shop}] 商品库存数据下载失败')
                    df.iloc[row_idx, goods_status_idx] = ''
            except Exception as e:
                print(f'[{shop}] 商品库存数据处理异常: {e}')
                df.iloc[row_idx, goods_status_idx] = ''
        
        # 下载BOM表数据
        if need_bom:
            try:
                bom_success = fetch_bom_data(shop, owner_co_id, authorize_co_id, profile)
                if bom_success:
                    print(f'[{shop}] BOM表数据下载成功')
                    df.iloc[row_idx, bom_status_idx] = '已完成'
                    
                    
                    date_dir = BASE_ARCHIVE_DIR_BOM / TODAY_STR
                    file_path = date_dir / f"{shop}.xlsx"
                    if file_path.exists():
                        upload_file_to_minio(str(file_path), "ods/erp/goodsbom", TODAY_STR)
                else:
                    print(f'[{shop}] BOM表数据下载失败')
                    df.iloc[row_idx, bom_status_idx] = ''
            except Exception as e:
                print(f'[{shop}] BOM表数据处理异常: {e}')
                df.iloc[row_idx, bom_status_idx] = ''

    # 5. 保存Excel状态更新
    try:
        time.sleep(1)  # 等待1秒确保文件释放
        df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
        print('Excel状态已更新！')
    except PermissionError as e:
        print(f'警告: Excel文件被占用，无法更新状态: {e}')
        print('请关闭Excel文件后重新运行脚本')
    
    # 6. 合并文件
    print("\n开始合并文件...")
    
    # 合并商品库存文件
    goods_date_dir = BASE_ARCHIVE_DIR_GOODS / TODAY_STR
    if goods_date_dir.exists() and any(goods_date_dir.iterdir()):
        print("合并商品库存文件...")
        merger = ExcelMerger(str(goods_date_dir))
        merge_success = merger.merge_excel_files(f"{TODAY_STR}.xlsx")
        
        if merge_success:
            merged_file_path = goods_date_dir / f"{TODAY_STR}.xlsx"
            final_merged_file_path = MERGED_FILES_DIR_GOODS / f"{TODAY_STR}.xlsx"
            shutil.move(str(merged_file_path), str(final_merged_file_path))
            print(f'商品库存文件合并完成: {final_merged_file_path}')
            
            # 上传合并后的商品库存文件到MinIO
            if upload_file_to_minio(str(final_merged_file_path), "ods/erp/goodscount", TODAY_STR):
                print(f'商品库存文件上传MinIO成功: {final_merged_file_path}')
            else:
                print(f'商品库存文件上传MinIO失败: {final_merged_file_path}')
    
    # 合并BOM表文件
    bom_date_dir = BASE_ARCHIVE_DIR_BOM / TODAY_STR
    if bom_date_dir.exists() and any(bom_date_dir.iterdir()):
        print("合并BOM表文件...")
        merger = ExcelMerger(str(bom_date_dir))
        merge_success = merger.merge_excel_files(f"{TODAY_STR}.xlsx")
        
        if merge_success:
            merged_file_path = bom_date_dir / f"{TODAY_STR}.xlsx"
            final_merged_file_path = MERGED_FILES_DIR_BOM / f"{TODAY_STR}.xlsx"
            shutil.move(str(merged_file_path), str(final_merged_file_path))
            print(f'BOM表文件合并完成: {final_merged_file_path}')
            
            # 上传合并后的BOM表文件到MinIO
            if upload_file_to_minio(str(final_merged_file_path), "ods/erp/goodsbom", TODAY_STR):
                print(f'BOM表文件上传MinIO成功: {final_merged_file_path}')
            else:
                print(f'BOM表文件上传MinIO失败: {final_merged_file_path}')

    # 7. 刷新Dremio数据集和反射
    print("\n刷新Dremio数据集...")
    refresh_dremio_dataset("minio.warehouse.ods.erp.goodscount")
    refresh_dremio_dataset("minio.warehouse.ods.erp.goodsbom")
    
    # 8. 刷新反射
    print("\n刷新Dremio反射...")
    refresh_dremio_reflection("minio.warehouse.ods.erp.goodscount")
    refresh_dremio_reflection("minio.warehouse.ods.erp.goodsbom")
    
    print("\n所有任务完成！")