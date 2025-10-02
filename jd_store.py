# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import time
import json
import requests
import uuid
import os
import pandas as pd
import shutil
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
EXCEL_PATH = r'D:\yingdao\jd\店铺信息表.xlsx'
BASE_ARCHIVE_DIR = Path('D:/yingdao/jd/库存表')  # 基础存档目录
MERGED_FILES_DIR = Path('D:/yingdao/jd/合并表格')  # 合并文件存储目录
SHEET = 0

# MinIO API配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"

# 轮询与文件IO重试配置
MAX_ATTEMPTS = 60
FILE_IO_MAX_RETRY = 5
FILE_IO_RETRY_SLEEP_SEC = 0.5

# 创建基础存档目录和合并文件目录
os.makedirs(BASE_ARCHIVE_DIR, exist_ok=True)
os.makedirs(MERGED_FILES_DIR, exist_ok=True)

# 使用T-1日期（昨天）
TODAY_STR = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

def update_header_once(df: pd.DataFrame):
    """固定用 F 列（索引 5）作为状态列，每天第一次把表头改成 今天+下载状态"""
    new_status = f'{TODAY_STR}库存表下载状态'
    old_header = df.columns[5]          # F 列当前名字

    if old_header == new_status:
        return False                     # 今天已更新过，返回False表示未更新

    # 改名（只改表头，数据不动）
    df.rename(columns={old_header: new_status}, inplace=True)
    # 清空F列的所有数据（除了表头）
    df.iloc[:, 5] = ''
    # 立即回写 Excel
    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
    return True                          # 返回True表示已更新

def fetch_download_link_and_download(shop_name: str, profile: str):
    """
    获取下载链接并下载文件
    shop_name: 店铺名称
    profile: 浏览器配置文件
    """
    # 使用独立的用户数据目录避免冲突
    USER_DATA_DIR = r"C:\\Users\\1\AppData\\Local\\Chromium\\User Data"
    TARGET_URL = "https://ppzh.jd.com/scbrandweb/brand/view/supplyReport/supplyChainPro.html"
    
    #最大化登录，使用用户目录
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
        page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
        cookies=context.cookies(TARGET_URL)
        cookie_str='; '.join(f"{c['name']}={c['value']}" for c in cookies)
        print(f"[{shop_name}] Cookie获取成功")
        
        # 添加UUID参数到URL
        request_uuid = str(uuid.uuid4())
        url = f"https://zhgateway.jd.com/inventoryajax/reportCenter/recommendReport/downloadERPSupplyChainProData.ajax?uuid={request_uuid}"
        headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "zh-CN,zh;q=0.9",
                "content-type": "application/json;charset=UTF-8",
                "origin": "https://ppzh.jd.com",
                "priority": "u=1, i",
                "referer": "https://ppzh.jd.com/scbrandweb/brand/view/supplyReport/supplyChainPro.html",
                "cookie": cookie_str,
                "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "user-mnp": "",
                "user-mup": "1",
                "x-requested-with": "XMLHttpRequest"
            }
        data = {
                "isRdc": "0",
                "brandId": "all",
                "firstCategoryId": "",
                "secondCategoryId": "",
                "thirdCategoryId": "all",
                "date": TODAY_STR,
                "startDate": TODAY_STR,
                "endDate": TODAY_STR,
                "skuId": "",
                "skuStatusCd": "",
                "dataType": "realtime",
                "id": 2,
                "excludeEmpty": "0"
            }   
        # 修复代码错误：将data转换为JSON字符串
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"[{shop_name}] API响应状态:", response.status_code)
        print(f"[{shop_name}] API响应内容:", response.text)
        page.goto('https://ppzh.jd.com/brand/reportCenter/myReport.html', wait_until="domcontentloaded", timeout=30000)
        
        # ===== 使用API监控报表状态并下载 =====
        print(f"[{shop_name}] 开始通过API监控报表状态...")
        
        # 生成新的UUID
        api_uuid = str(uuid.uuid4()).replace('-', '') + '-' + str(int(time.time() * 1000))[-11:]
        api_url = f"https://ppzh.jd.com/brand/reportCenter/myReport/getReportList.ajax?uuid={api_uuid}"

        # 获取当前页面的Cookie
        cookie1=context.cookies('https://ppzh.jd.com/brand/reportCenter/myReport.html')
        cookie_str1='; '.join(f"{c['name']}={c['value']}" for c in cookie1)
        print(f"[{shop_name}] 动态Cookie获取成功")
        
        api_headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "Cookie": cookie_str1,
            "p-pin": "",
            "priority": "u=1, i",
            "referer": "https://ppzh.jd.com/brand/reportCenter/myReport.html",
            "sec-ch-ua": "\"Not=A?Brand\";v=\"24\", \"Chromium\";v=\"140\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "user-mnp": "dfe8c70a03ddb7554dbb93a150a40a25",
            "user-mup": "1758866860479",
            "x-requested-with": "XMLHttpRequest"
        }
        
        max_attempts = MAX_ATTEMPTS  # 最大尝试次数，避免无限循环
        attempt = 0
        download_url = None
        download_success = False
        
        while attempt < max_attempts:
            try:
                print(f"[{shop_name}] 第{attempt + 1}次检查报表状态...")
                
                # 发送API请求获取报表列表
                api_response = requests.get(api_url, headers=api_headers)
                api_response.raise_for_status()
                
                response_data = api_response.json()
                
                if response_data.get('message') == 'success' and response_data.get('content', {}).get('data'):
                    reports = response_data['content']['data']
                    
                    if reports:
                        first_report = reports[0]
                        status = first_report.get('status')
                        report_name = first_report.get('reportName', '未知报表')
                        
                        print(f"[{shop_name}] 报表: {report_name}, 状态: {status}")
                        
                        if status == "2":  # 状态2表示已完成
                            download_url = first_report.get('downloadLink', '').strip()
                            if download_url:
                                print(f"[{shop_name}] 成功 报表已完成！开始下载...")
                                
                                # 创建下载目录
                                date_dir = BASE_ARCHIVE_DIR / TODAY_STR
                                date_dir.mkdir(parents=True, exist_ok=True)
                                
                                # 生成文件名
                                filename = f"{shop_name}.xlsx"
                                file_path = date_dir / filename
                                
                                # 如果目标文件已存在，先删除（带重试，避免占用）
                                if file_path.exists():
                                    print(f'[{shop_name}] 删除 发现同名文件，正在删除: {file_path}')
                                    delete_attempt = 0
                                    while delete_attempt < FILE_IO_MAX_RETRY:
                                        try:
                                            file_path.unlink()
                                            print(f'[{shop_name}] 成功 同名文件已删除')
                                            break
                                        except PermissionError as del_err:
                                            delete_attempt += 1
                                            print(f'[{shop_name}] 警告 删除文件被占用，重试{delete_attempt}/{FILE_IO_MAX_RETRY}: {del_err}')
                                            time.sleep(FILE_IO_RETRY_SLEEP_SEC)
                                    else:
                                        print(f'[{shop_name}] 失败 无法删除同名文件，放弃下载: {file_path}')
                                        break
                                
                                # 下载文件
                                download_response = requests.get(download_url, stream=True)
                                download_response.raise_for_status()
                                
                                write_attempt = 0
                                while write_attempt < FILE_IO_MAX_RETRY:
                                    try:
                                        with open(file_path, 'wb') as f:
                                            for chunk in download_response.iter_content(chunk_size=8192):
                                                f.write(chunk)
                                        break
                                    except PermissionError as write_err:
                                        write_attempt += 1
                                        print(f'[{shop_name}] 警告 写入文件被占用，重试{write_attempt}/{FILE_IO_MAX_RETRY}: {write_err}')
                                        time.sleep(FILE_IO_RETRY_SLEEP_SEC)
                                else:
                                    print(f'[{shop_name}] 失败 文件写入失败，放弃: {file_path}')
                                    break
                                
                                print(f"[{shop_name}] 成功 文件下载完成: {file_path}")
                                download_success = True
                                break
                            else:
                                print(f"[{shop_name}] 失败 报表已完成但未获取到下载链接")
                                break
                        else:
                            print(f"[{shop_name}] [等待] 报表状态为 {status}，1秒后重新检查...")
                            
                            # 在状态检查后点击页面刷新按钮
                            try:
                                # 导航到报表页面并点击刷新
                                page.goto("https://ppzh.jd.com/brand/reportCenter/myReport.html")
                                page.wait_for_load_state('networkidle')
                                
                                # 查找并点击刷新按钮 - 使用正确的选择器
                                refresh_button = page.locator('.content-fresh, span.content-fresh').first
                                if refresh_button.is_visible():
                                    refresh_button.click()
                                    print(f"[{shop_name}] 刷新 已点击页面刷新按钮")
                                    page.wait_for_timeout(1000)  # 等待2秒让页面刷新
                                else:
                                    print(f"[{shop_name}] 警告 未找到刷新按钮，尝试页面重新加载")
                                    page.reload()
                                    page.wait_for_load_state('networkidle')
                            except Exception as refresh_error:
                                print(f"[{shop_name}] 警告 页面刷新失败: {refresh_error}")
                            
                            time.sleep(1)
                            attempt += 1
                    else:
                        print(f"[{shop_name}] 警告 未找到报表数据")
                        time.sleep(1)
                        attempt += 1
                else:
                    print(f"[{shop_name}] 失败 API响应异常: {response_data}")
                    time.sleep(1)
                    attempt += 1
                    
            except Exception as e:
                print(f"[{shop_name}] 失败 检查状态时出错: {e}")
                time.sleep(1)
                attempt += 1
        
        if attempt >= max_attempts:
            print(f"[{shop_name}] 警告 达到最大尝试次数，停止监控")
        elif not download_success:
            print(f"[{shop_name}] 失败 未获取到有效的下载链接")

        time.sleep(0.2)
        page.close()
        time.sleep(0.2)
        context.close()
        
        return download_success

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
        
        # 构建MinIO路径：ods/jd/jd_store/dt=日期/merged_store_data.parquet
        minio_path = f"ods/jd/jd_store/dt={date_str}/merged_store_data.parquet"
        
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
            "bucket": MINIO_BUCKET
        }
        
        # 发送POST请求到MinIO API
        headers = {'Content-Type': 'application/json'}
        response = requests.post(MINIO_API_URL, json=upload_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"成功 成功上传合并文件到MinIO: {minio_path}")
                return True
            else:
                print(f"失败 MinIO上传失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"失败 MinIO API请求失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"失败 上传合并文件到MinIO时出错: {str(e)}")
        return False

if __name__ == '__main__':
    # 1. 读表 & 更新表头
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)  
    header_updated = update_header_once(df)
    
    # 如果表头更新了，需要重新读取DataFrame
    if header_updated:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)

    # 2. 定位关键列
    shop_idx   = 1    # B列 (店铺名称)
    profile_idx = 4   # E列 (浏览器)
    status_idx = 5    # F列 (状态列)

    print(f"DataFrame形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    print(f"状态列名: {df.columns[status_idx]}")

    # 3. 收集所有需要下载的店铺信息
    download_tasks = []
    for row_idx in range(len(df)):
        shop   = df.iloc[row_idx, shop_idx]
        profile = df.iloc[row_idx, profile_idx]
        status = df.iloc[row_idx, status_idx]

        # 转换为字符串处理
        status_str = str(status) if pd.notna(status) else ''
        
        print(f"检查第{row_idx+2}行: {shop}, 状态: '{status_str}'")

        # 空值/已完成的跳过
        if status_str.strip() == '已完成':
            print(f'跳过 {shop} - 状态已完成')
            continue
        if pd.isna(profile) or str(profile).strip() == '' or str(profile).strip() == 'nan':
            print(f'跳过 {shop} - 浏览器配置为空')
            continue
            
        download_tasks.append({
            'row_idx': row_idx,
            'shop': shop,
            'profile': str(profile)
        })
    
    print(f"共找到 {len(download_tasks)} 个需要下载的店铺")
    
    # 4. 批量下载所有文件
    downloaded_files = []
    for task in download_tasks:
        row_idx = task['row_idx']
        shop = task['shop']
        profile = task['profile']
        
        try:
            success = fetch_download_link_and_download(shop, profile)
            if success:
                print(f'成功 {shop} - 下载完成')
                
                # 记录下载的文件路径
                date_dir = BASE_ARCHIVE_DIR / TODAY_STR
                file_path = date_dir / f"{shop}.xlsx"
                downloaded_files.append(file_path)
                
                # 更新状态为已完成
                df.iloc[row_idx, status_idx] = '已完成'
            else:
                # 失败时置空状态，便于重试
                df.iloc[row_idx, status_idx] = ''
                print(f'失败 {shop} - 下载失败，已置空待重试')
        except Exception as e:
            # 失败时置空状态，便于重试
            df.iloc[row_idx, status_idx] = ''
            print(f'失败 {shop} - 异常：{e}，已置空待重试')

    # 5. 保存Excel状态更新（带重试机制）
    save_attempt = 0
    save_success = False
    while save_attempt < FILE_IO_MAX_RETRY and not save_success:
        try:
            time.sleep(FILE_IO_RETRY_SLEEP_SEC)
            df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
            print('Excel状态已更新！')
            save_success = True
        except PermissionError as e:
            save_attempt += 1
            print(f'警告 Excel文件被占用，重试{save_attempt}/{FILE_IO_MAX_RETRY}: {e}')
            time.sleep(FILE_IO_RETRY_SLEEP_SEC)
        except Exception as e:
            save_attempt += 1
            print(f'警告 Excel写回异常，重试{save_attempt}/{FILE_IO_MAX_RETRY}: {e}')
            time.sleep(FILE_IO_RETRY_SLEEP_SEC)
    if not save_success:
        print('失败 多次重试后仍无法写回Excel，请关闭Excel后重试')
    
    # 6. 如果有下载的文件，进行合并和上传
    if downloaded_files:
        print(f'开始合并 {len(downloaded_files)} 个Excel文件...')
        
        # 创建日期文件夹路径
        date_dir = BASE_ARCHIVE_DIR / TODAY_STR
        
        # 使用ExcelMerger合并文件
        merger = ExcelMerger(str(date_dir))
        merge_success = merger.merge_excel_files(f"{TODAY_STR}.xlsx")
        
        if merge_success:
            # 读取合并后的文件
            merged_file_path = date_dir / f"{TODAY_STR}.xlsx"
            
            # 移动到最终目录
            final_merged_file_path = MERGED_FILES_DIR / f"{TODAY_STR}.xlsx"
            shutil.move(str(merged_file_path), str(final_merged_file_path))
            
            print(f'成功 文件合并完成，保存至: {final_merged_file_path}')
            
            # 上传合并后的文件到MinIO
            print(f'处理 正在上传合并文件到MinIO...')
            upload_success = upload_merged_file_to_minio(str(final_merged_file_path), TODAY_STR)
            
            if upload_success:
                print(f'成功 合并文件MinIO上传成功')
            else:
                print(f'警告 合并文件MinIO上传失败，但本地文件已保存')
        else:
            print('失败 文件合并失败，无法生成合并文件')
    else:
        print('警告 没有新下载的文件，跳过合并和上传步骤')
    
    # 7. 所有文件上传完成后，刷新数据集和反射
    print('处理 正在刷新数据集...')
    try:
        refresh_dataset_response = requests.post(
            "http://localhost:8003/api/dataset/refresh-metadata",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.jd.jd_store"}
        )
        if refresh_dataset_response.status_code == 200:
            print('成功 数据集刷新成功')
        else:
            print(f'警告 数据集刷新失败: {refresh_dataset_response.status_code}')
    except Exception as e:
        print(f'失败 数据集刷新异常: {e}')
    
    print('处理 正在刷新反射...')
    try:
        refresh_reflection_response = requests.post(
            "http://localhost:8003/api/reflection/refresh",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.jd.jd_store"}
        )
        if refresh_reflection_response.status_code == 200:
            print('成功 反射刷新成功')
        else:
            print(f'警告 反射刷新失败: {refresh_reflection_response.status_code}')
    except Exception as e:
        print(f'失败 反射刷新异常: {e}')
    
    print('成功 所有任务完成！')
