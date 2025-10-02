# -*- coding: utf-8 -*-
import logging
import os
import json
import uuid
import time
import requests
import pandas as pd
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Optional, Dict, List, Any
from functools import wraps
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, BrowserContext
import yaml

# 导入自定义模块
try:
    from merge_excel_files import ExcelMerger
    print('成功导入 ExcelMerger 模块')
except ImportError as e:
    print(f'错误：找不到 merge_excel_files 模块，请确保该文件在正确的路径下\n详细错误：{e}')
    sys.exit(1)

# 全局日志对象
logger = logging.getLogger('jd_store')

# 设置默认日志级别
logger.setLevel(logging.INFO)

# 添加控制台输出
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# 配置日志记录器
def setup_logging(log_file: str) -> logging.Logger:
    logger = logging.getLogger('jd_store')
    logger.setLevel(logging.INFO)
    
    # 移除现有的处理器（如果有）
    for handler in logger.handlers[:]: 
        logger.removeHandler(handler)
    
    # 文件处理器
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.INFO)
    
    # 控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # 日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

# 加载配置文件
def load_config() -> dict:
    config_path = Path(__file__).parent / 'config.yml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # 默认配置
        return {
            'paths': {
                'excel': r'D:\yingdao\jd\店铺信息表.xlsx',
                'archive': r'D:/yingdao/jd/库存表',
                'merged': r'D:/yingdao/jd/合并表格'
            },
            'api': {
                'minio_url': 'http://127.0.0.1:8009/api/upload',
                'minio_bucket': 'warehouse',
                'dremio_dataset': 'http://localhost:8003/api'
            },
            'retry': {
                'max_attempts': 60,
                'file_io_max_retry': 5,
                'file_io_retry_sleep': 0.5
            }
        }

# 重试装饰器
def retry_on_exception(retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"重试 {func.__name__} 第{attempt + 1}次失败: {str(e)}")
                    if attempt < retries - 1:
                        time.sleep(delay)
                        continue
                    raise  # 如果最后一次还是失败，则抛出异常
            return True  # 如果执行到这里，说明成功了
        return wrapper
    return decorator

class HTTPClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('http://', HTTPAdapter(max_retries=retry_strategy))
        self.session.mount('https://', HTTPAdapter(max_retries=retry_strategy))
        self.base_url = base_url
        self.timeout = timeout

    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

class FileManager:
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.today_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
    @retry_on_exception(retries=5, delay=0.5)
    def safe_file_operation(self, operation, *args, **kwargs):
        return operation(*args, **kwargs)
    
    def ensure_directories(self):
        """确保所需目录存在"""
        paths = [
            Path(self.config['paths']['archive']),
            Path(self.config['paths']['merged'])
        ]
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
            
    def get_date_directory(self) -> Path:
        """获取日期目录路径"""
        return Path(self.config['paths']['archive']) / self.today_str

class JDStoreManager:
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.file_manager = FileManager(config, logger)
        self.minio_client = HTTPClient(config['api']['minio_url'])
        self.dremio_client = HTTPClient(config['api']['dremio_dataset'])
        
    def ensure_column_string_type(self, df: pd.DataFrame) -> None:
        """确保状态列为字符串类型"""
        if not pd.api.types.is_string_dtype(df.iloc[:, 5]):
            df.iloc[:, 5] = df.iloc[:, 5].astype(str).replace('nan', '')
            
    def update_status(self, df: pd.DataFrame, row_idx: int, status: str) -> None:
        """更新状态列的值"""
        try:
            df.iat[row_idx, 5] = str(status) if pd.notna(status) else ''
        except Exception as e:
            self.logger.error(f'状态更新失败: {e}')
        
    def update_header(self, df: pd.DataFrame) -> bool:
        """更新表头，返回是否更新成功"""
        try:
            new_status = f'{self.file_manager.today_str}库存表下载状态'
            old_header = df.columns[5]
            
            if old_header == new_status:
                return False
            
            # 重命名列
            df.rename(columns={old_header: new_status}, inplace=True)
            
            # 确保状态列为字符串类型并重置状态
            self.ensure_column_string_type(df)
            df.iloc[:, 5] = ''
            
            # 保存更改
            self.file_manager.safe_file_operation(
                df.to_excel,
                self.config['paths']['excel'],
                index=False,
                engine='openpyxl'
            )
            return True
            
        except Exception as e:
            self.logger.error(f'表头更新失败: {e}')
            return False
        
    def fetch_download_link_and_download(self, shop_name: str, profile: str) -> bool:
        """获取下载链接并下载文件"""
        USER_DATA_DIR = r"C:\\Users\\1\AppData\\Local\\Chromium\\User Data"
        TARGET_URL = "https://ppzh.jd.com/scbrandweb/brand/view/supplyReport/supplyChainPro.html"
        
        try:
            self.logger.info(f"[{shop_name}] 开始下载处理")
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
                cookies = context.cookies(TARGET_URL)
                cookie_str = '; '.join(f"{c.get('name', '')}={c.get('value', '')}" for c in cookies)
                self.logger.info(f"[{shop_name}] Cookie获取成功")
                
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
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                }
                
                data = {
                    "isRdc": "0",
                    "brandId": "all",
                    "firstCategoryId": "",
                    "secondCategoryId": "",
                    "thirdCategoryId": "all",
                    "date": self.file_manager.today_str,
                    "startDate": self.file_manager.today_str,
                    "endDate": self.file_manager.today_str,
                    "skuId": "",
                    "skuStatusCd": "",
                    "dataType": "realtime",
                    "id": 2,
                    "excludeEmpty": "0"
                }
                
                response = requests.post(url, headers=headers, data=json.dumps(data))
                self.logger.info(f"[{shop_name}] API响应状态: {response.status_code}")
                self.logger.info(f"[{shop_name}] API响应内容: {response.text}")
                
                page.goto('https://ppzh.jd.com/brand/reportCenter/myReport.html', wait_until="domcontentloaded", timeout=30000)
                
                # 监控报表状态
                self.logger.info(f"[{shop_name}] 开始监控报表状态...")
                
                api_uuid = str(uuid.uuid4()).replace('-', '') + '-' + str(int(time.time() * 1000))[-11:]
                api_url = f"https://ppzh.jd.com/brand/reportCenter/myReport/getReportList.ajax?uuid={api_uuid}"
                
                cookie1 = context.cookies('https://ppzh.jd.com/brand/reportCenter/myReport.html')
                cookie_str1 = '; '.join(f"{c.get('name', '')}={c.get('value', '')}" for c in cookie1)
                self.logger.info(f"[{shop_name}] 动态Cookie获取成功")
                
                api_headers = {
                    "accept": "*/*",
                    "accept-language": "zh-CN,zh;q=0.9",
                    "Cookie": cookie_str1,
                    "priority": "u=1, i",
                    "referer": "https://ppzh.jd.com/brand/reportCenter/myReport.html",
                    "sec-ch-ua": "\"Not=A?Brand\";v=\"24\", \"Chromium\";v=\"140\"",
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": "\"Windows\"",
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
                }
                
                max_attempts = self.config['retry']['max_attempts']
                attempt = 0
                download_url = None
                download_success = False
                
                while attempt < max_attempts:
                    try:
                        self.logger.info(f"[{shop_name}] 第{attempt + 1}次检查报表状态...")
                        
                        api_response = requests.get(api_url, headers=api_headers)
                        api_response.raise_for_status()
                        
                        response_data = api_response.json()
                        
                        if response_data.get('message') == 'success' and response_data.get('content', {}).get('data'):
                            reports = response_data['content']['data']
                            
                            if reports:
                                first_report = reports[0]
                                status = first_report.get('status')
                                report_name = first_report.get('reportName', '未知报表')
                                
                                self.logger.info(f"[{shop_name}] 报表: {report_name}, 状态: {status}")
                                
                                if status == "2":  # 状态2表示已完成
                                    download_url = first_report.get('downloadLink', '').strip()
                                    if download_url:
                                        self.logger.info(f"[{shop_name}] 成功 报表已完成！开始下载...")
                                        
                                        # 创建下载目录
                                        date_dir = self.file_manager.get_date_directory()
                                        date_dir.mkdir(parents=True, exist_ok=True)
                                        
                                        # 生成文件名
                                        filename = f"{shop_name}.xlsx"
                                        file_path = date_dir / filename
                                        
                                        # 如果目标文件已存在，先删除
                                        if file_path.exists():
                                            self.logger.info(f'[{shop_name}] 删除 发现同名文件，正在删除: {file_path}')
                                            delete_attempt = 0
                                            while delete_attempt < self.config['retry']['file_io_max_retry']:
                                                try:
                                                    file_path.unlink()
                                                    self.logger.info(f'[{shop_name}] 成功 同名文件已删除')
                                                    break
                                                except PermissionError as del_err:
                                                    delete_attempt += 1
                                                    self.logger.warning(f'[{shop_name}] 警告 删除文件被占用，重试{delete_attempt}/{self.config["retry"]["file_io_max_retry"]}: {del_err}')
                                                    time.sleep(self.config['retry']['file_io_retry_sleep'])
                                            else:
                                                self.logger.error(f'[{shop_name}] 失败 无法删除同名文件，放弃下载: {file_path}')
                                                break
                                        
                                        # 下载文件
                                        download_response = requests.get(download_url, stream=True)
                                        download_response.raise_for_status()
                                        
                                        write_attempt = 0
                                        while write_attempt < self.config['retry']['file_io_max_retry']:
                                            try:
                                                with open(file_path, 'wb') as f:
                                                    for chunk in download_response.iter_content(chunk_size=8192):
                                                        f.write(chunk)
                                                break
                                            except PermissionError as write_err:
                                                write_attempt += 1
                                                self.logger.warning(f'[{shop_name}] 警告 写入文件被占用，重试{write_attempt}/{self.config["retry"]["file_io_max_retry"]}: {write_err}')
                                                time.sleep(self.config['retry']['file_io_retry_sleep'])
                                        else:
                                            self.logger.error(f'[{shop_name}] 失败 文件写入失败，放弃: {file_path}')
                                            break
                                        
                                        self.logger.info(f"[{shop_name}] 成功 文件下载完成: {file_path}")
                                        download_success = True
                                        break
                                    else:
                                        self.logger.error(f"[{shop_name}] 失败 报表已完成但未获取到下载链接")
                                        break
                                else:
                                    self.logger.info(f"[{shop_name}] [等待] 报表状态为 {status}，1秒后重新检查...")
                                    
                                    # 在状态检查后点击页面刷新按钮
                                    try:
                                        page.goto("https://ppzh.jd.com/brand/reportCenter/myReport.html")
                                        page.wait_for_load_state('networkidle')
                                        
                                        refresh_button = page.locator('.content-fresh, span.content-fresh').first
                                        if refresh_button.is_visible():
                                            refresh_button.click()
                                            self.logger.info(f"[{shop_name}] 刷新 已点击页面刷新按钮")
                                            page.wait_for_timeout(1000)
                                        else:
                                            self.logger.warning(f"[{shop_name}] 警告 未找到刷新按钮，尝试页面重新加载")
                                            page.reload()
                                            page.wait_for_load_state('networkidle')
                                    except Exception as refresh_error:
                                        self.logger.warning(f"[{shop_name}] 警告 页面刷新失败: {refresh_error}")
                                    
                                    time.sleep(1)
                                    attempt += 1
                            else:
                                self.logger.warning(f"[{shop_name}] 警告 未找到报表数据")
                                time.sleep(1)
                                attempt += 1
                        else:
                            self.logger.error(f"[{shop_name}] 失败 API响应异常: {response_data}")
                            time.sleep(1)
                            attempt += 1
                            
                    except Exception as e:
                        self.logger.error(f"[{shop_name}] 失败 检查状态时出错: {e}")
                        time.sleep(1)
                        attempt += 1
                
                if attempt >= max_attempts:
                    self.logger.warning(f"[{shop_name}] 警告 达到最大尝试次数，停止监控")
                elif not download_success:
                    self.logger.error(f"[{shop_name}] 失败 未获取到有效的下载链接")

                time.sleep(0.2)
                page.close()
                time.sleep(0.2)
                context.close()
                
                return download_success
                
        except Exception as e:
            self.logger.error(f"[{shop_name}] 异常: {str(e)}")
            return False
        
    @retry_on_exception(retries=3, delay=1)
    def upload_to_minio(self, file_path: str) -> bool:
        """上传文件到MinIO"""
        try:
            df = pd.read_excel(file_path)
            df = self._prepare_dataframe_for_upload(df)
            
            minio_path = f"ods/jd/jd_store/dt={self.file_manager.today_str}/merged_store_data.parquet"
            
            upload_data = {
                "data": df.to_dict('records'),
                "target_path": minio_path,
                "format": "parquet",
                "bucket": self.config['api']['minio_bucket']
            }
            
            # 直接使用根路径，因为基础 URL 已经包含了 /api/upload
            response = self.minio_client.request(
                'POST',
                '',  # 使用空字符串，因为基础 URL 已经包含了完整路径
                json=upload_data,
                headers={'Content-Type': 'application/json'}
            )
            
            return response.json().get('success', False)
            
        except Exception as e:
            self.logger.error(f"上传到MinIO失败: {str(e)}")
            return False
            
    def _prepare_dataframe_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """准备DataFrame用于上传"""
        df = df.fillna('')
        df = df.replace([float('inf'), float('-inf')], '')
        
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32']:
                df[col] = df[col].replace([float('inf'), float('-inf')], '')
            df[col] = df[col].astype(str)
            
        return df
        
    def refresh_dataset_and_reflection(self) -> bool:
        """
        刷新数据集和反射，包含详细的检查和验证
        返回：是否全部刷新成功
        """
        all_success = True
        
        try:
            # 刷新数据集
            self.logger.info('开始刷新数据集...')
            
            dataset_response = self.dremio_client.request(
                'POST',
                '/dataset/metadata/refresh',
                json={
                    "table_path": "minio.warehouse.ods.jd.jd_store",
                    "mode": "full"
                },
                timeout=30  # 设置超时时间
            )
            
            # 检查数据集刷新响应
            if dataset_response.status_code == 200:
                dataset_result = dataset_response.json()
                if dataset_result.get('success', False):
                    self.logger.info('数据集刷新成功')
                else:
                    error_msg = dataset_result.get('message', '未知错误')
                    self.logger.error(f'数据集刷新失败: {error_msg}')
                    all_success = False
            else:
                response_text = dataset_response.text
                self.logger.error(f'数据集刷新请求失败: HTTP {dataset_response.status_code}, Response: {response_text}')
                all_success = False
            
            # 刷新反射
            if all_success:
                self.logger.info('开始刷新反射...')
                
                reflection_response = self.dremio_client.request(
                    'POST',
                    '/reflection/rebuild',
                    json={
                        "dataset_path": "minio.warehouse.ods.jd.jd_store"
                    },
                    timeout=30
                )
                
                # 检查反射刷新响应
                if reflection_response.status_code == 200:
                    reflection_result = reflection_response.json()
                    if reflection_result.get('success', False):
                        self.logger.info('反射刷新成功')
                    else:
                        error_msg = reflection_result.get('message', '未知错误')
                        self.logger.error(f'反射刷新失败: {error_msg}')
                        all_success = False
                else:
                    response_text = reflection_response.text
                    self.logger.error(f'反射刷新请求失败: HTTP {reflection_response.status_code}, Response: {response_text}')
                    all_success = False
            
            return all_success
            
        except Exception as e:
            self.logger.error(f"刷新操作失败: {str(e)}")
            return False

def main():
    print('开始执行程序...')
    print('正在初始化日志和配置...')
    # 加载配置
    try:
        config = load_config()
        print('配置加载成功')
    except Exception as e:
        print(f'配置加载失败: {e}')
        return
    
    # 设置日志
    log_file = Path('jd_store.log')
    logger = setup_logging(str(log_file))
    
    # 创建管理器实例
    manager = JDStoreManager(config, logger)
    
    try:
        # 确保目录存在
        manager.file_manager.ensure_directories()
        
        # 读取Excel
        df = pd.read_excel(config['paths']['excel'], sheet_name=0)
        if manager.update_header(df):
            df = pd.read_excel(config['paths']['excel'], sheet_name=0)
            
        # 确保状态列为字符串类型
        manager.ensure_column_string_type(df)
        
        # 收集下载任务
        download_tasks = []
        for row_idx in range(len(df)):
            shop = df.iat[row_idx, 1]  # 使用iat进行更高效的访问
            profile = df.iat[row_idx, 4]
            status = df.iat[row_idx, 5]
            
            # 跳过已完成或无效的任务
            if (pd.notna(status) and str(status).strip() == '已完成') or \
               pd.isna(profile) or str(profile).strip() in ('', 'nan'):
                continue
                
            download_tasks.append({
                'row_idx': row_idx,
                'shop': shop,
                'profile': str(profile)
            })
            
        logger.info(f'找到 {len(download_tasks)} 个需要下载的店铺')
            
        # 执行下载任务
        downloaded_files = []
        for task in download_tasks:
            try:
                success = manager.fetch_download_link_and_download(task['shop'], task['profile'])
                if success:
                    downloaded_files.append(manager.file_manager.get_date_directory() / f"{task['shop']}.xlsx")
                    manager.update_status(df, task['row_idx'], '已完成')
                else:
                    manager.update_status(df, task['row_idx'], '')
                    logger.warning(f'下载失败: {task["shop"]}')
            except Exception as e:
                logger.error(f'下载异常 {task["shop"]}: {str(e)}')
                manager.update_status(df, task['row_idx'], '')
                
        # 保存Excel更新
        manager.file_manager.safe_file_operation(
            df.to_excel,
            config['paths']['excel'],
            index=False,
            engine='openpyxl'
        )
        
        # 无论是否有新下载的文件，都执行合并和上传操作
        logger.info('开始执行文件合并操作...')
        merger = ExcelMerger(str(manager.file_manager.get_date_directory()))
        
        # 检查日期目录是否存在
        date_dir = manager.file_manager.get_date_directory()
        if not date_dir.exists():
            logger.info(f'创建日期目录: {date_dir}')
            date_dir.mkdir(parents=True, exist_ok=True)
            
        # 检查目录中是否有Excel文件
        excel_files = list(date_dir.glob('*.xlsx'))
        if not excel_files:
            logger.warning(f'目录 {date_dir} 中没有找到Excel文件')
        else:
            logger.info(f'找到 {len(excel_files)} 个Excel文件')
            
        # 执行合并操作
        if merger.merge_excel_files(f"{manager.file_manager.today_str}.xlsx"):
            logger.info('文件合并成功')
            
            # 移动合并后的文件
            source = manager.file_manager.get_date_directory() / f"{manager.file_manager.today_str}.xlsx"
            target = Path(config['paths']['merged']) / f"{manager.file_manager.today_str}.xlsx"
            
            # 确保目标目录存在
            target.parent.mkdir(parents=True, exist_ok=True)
            
            if source.exists():
                # 如果目标文件已存在，先删除
                if target.exists():
                    try:
                        target.unlink()
                        logger.info(f'删除已存在的目标文件: {target}')
                    except Exception as e:
                        logger.error(f'删除目标文件失败: {e}')
                        raise
                
                # 移动文件
                try:
                    shutil.move(str(source), str(target))
                    logger.info(f'合并文件已移动到: {target}')
                except Exception as e:
                    logger.error(f'移动文件失败: {e}')
                    raise
                
                # 上传到MinIO并刷新数据集
                if manager.upload_to_minio(str(target)):
                    logger.info('MinIO上传成功')
                    # 刷新数据集和反射
                    refresh_success = manager.refresh_dataset_and_reflection()
                    if refresh_success:
                        logger.info('数据集和反射刷新完成')
                    else:
                        logger.error('数据集或反射刷新失败，请检查日志获取详细信息')
                else:
                    logger.error('MinIO上传失败')
            else:
                logger.error(f'合并后的文件不存在: {source}')
        else:
            logger.error('文件合并失败')
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        raise
        
if __name__ == '__main__':
    main()