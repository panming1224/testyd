# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import time
import json
import requests
import os
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
import sys
import math

# 配置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 添加merge_excel_files模块路径
sys.path.append(r'D:\testyd')
from merge_excel_files import ExcelMerger

# 配置
BASE_ARCHIVE_DIR = Path('D:/yingdao/erp/erp店铺信息')  # 店铺信息存档目录
MERGED_FILES_DIR = Path('D:/yingdao/erp/合并表格/erp店铺信息')  # 合并文件存储目录

# MinIO API配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"

# ERP配置
ERP_WEB_URL = "https://src.erp321.com/ka-web-group/brand-management-partner/shops?_c=jst-epaas"
ERP_API_URL = "https://api.erp321.com/ka/webapi/brandmanagement/v3/refactorings/partner/cooperationShop/list"

# 创建基础存档目录和合并文件目录
os.makedirs(BASE_ARCHIVE_DIR, exist_ok=True)
os.makedirs(MERGED_FILES_DIR, exist_ok=True)

# 使用今天日期
TODAY_STR = datetime.now().strftime('%Y-%m-%d')

class ERPShopInfoCollector:
    """ERP店铺信息数据采集器"""
    
    def __init__(self, profile: str = "Default"):
        self.profile = profile
        self.USER_DATA_DIR = r"C:\\Users\\1\AppData\\Local\\Chromium\\User Data"
        self.cookie_str = None
        self.gwfp = None
        
    def get_dynamic_params(self):
        """
        获取动态参数：Cookie、gwfp
        """
        print("开始获取动态参数...")
        
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.USER_DATA_DIR,
                headless=False,
                args=[
                    "--start-maximized",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    f"--profile-directory={self.profile}"
                ],
                no_viewport=True,
                ignore_https_errors=True
            )
            
            page = context.new_page()
            
            try:
                # 导航到店铺信息页面
                print(f"导航到店铺信息页面: {ERP_WEB_URL}")
                page.goto(ERP_WEB_URL, wait_until="domcontentloaded", timeout=60000)
                
                # 等待页面完全加载
                time.sleep(3)
                
                # 获取Cookie
                cookies = context.cookies()
                self.cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
                print(f"✓ 获取Cookie成功: {self.cookie_str[:100]}...")
                
                # 尝试从localStorage获取gwfp
                try:
                    gwfp = page.evaluate("() => localStorage.getItem('gwfp')")
                    if gwfp:
                        self.gwfp = gwfp
                        print(f"✓ 获取gwfp成功: {self.gwfp}")
                    else:
                        # 如果localStorage中没有，尝试从页面请求中获取
                        print("⚠️ localStorage中未找到gwfp，使用默认值")
                        self.gwfp = "e9d9166eb907a8ff2427e2114f39e16b"
                except Exception as e:
                    print(f"⚠️ 获取gwfp失败: {e}，使用默认值")
                    self.gwfp = "e9d9166eb907a8ff2427e2114f39e16b"
                
                return True
                
            except Exception as e:
                print(f"获取动态参数失败: {e}")
                return False
            finally:
                context.close()
    
    def fetch_shop_info_data(self, page_index: int = 1, page_size: int = 200):
        """
        获取店铺信息数据
        """
        if not self.cookie_str:
            print("Cookie不完整，无法发送请求")
            return None

        # 构建请求头
        headers = {
            'accept': 'application/json',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/json',
            'gwfp': self.gwfp,
            'origin': 'https://src.erp321.com',
            'priority': 'u=1, i',
            'referer': 'https://src.erp321.com/',
            'sec-ch-ua': '"Not=A?Brand";v="24", "Chromium";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Cookie': self.cookie_str
        }
        
        # 构建请求体
        skip_count = (page_index - 1) * page_size
        request_data = {
            "data": {
                "pageIndex": page_index,
                "pageSize": page_size,
                "skipCount": skip_count,
                "maxResultCount": page_size
            },
            "ip": "",
            "coid": "12910783",
            "uid": "21599824"
        }
        
        try:
            print(f"发送店铺信息数据请求 (页码: {page_index}, 每页: {page_size})...")
            response = requests.post(ERP_API_URL, headers=headers, json=request_data)

            if response.status_code == 200:
                print(f"✓ 请求成功，状态码: {response.status_code}")
                return response.text
            else:
                print(f"✗ 请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text[:500]}")
                return None

        except Exception as e:
            print(f"发送请求时出错: {e}")
            return None
    
    def parse_response(self, response_text):
        """
        解析响应数据
        """
        try:
            # 直接解析JSON
            data = json.loads(response_text)
            
            if data.get('data'):
                result_data = data['data']
                total_count = result_data.get('totalCount', 0)
                items = result_data.get('items', [])
                
                print(f"解析结果: 总数 {total_count}, 当前页数据条数: {len(items)}")
                
                return {
                    'total_count': total_count,
                    'items': items
                }
            else:
                print(f"API返回失败: {data}")
                return None
                
        except Exception as e:
            print(f"解析响应数据时出错: {e}")
            print(f"响应内容: {response_text[:500]}")
            return None
    
    def collect_all_data(self, page_size: int = 200):
        """
        收集所有店铺信息数据
        """
        all_data = []
        
        # 先获取第一页，确定总数
        response_text = self.fetch_shop_info_data(page_index=1, page_size=page_size)
        if not response_text:
            print("获取第1页数据失败")
            return all_data
        
        # 解析第一页数据
        parsed_data = self.parse_response(response_text)
        if not parsed_data:
            print("解析第1页数据失败")
            return all_data
        
        # 添加第一页数据
        all_data.extend(parsed_data['items'])
        print(f"已收集第1页数据，共{len(parsed_data['items'])}条记录")
        
        # 计算总页数
        total_count = parsed_data['total_count']
        total_pages = math.ceil(total_count / page_size)
        print(f"总共 {total_count} 条数据，分 {total_pages} 页")
        
        # 获取剩余页面
        for page_index in range(2, total_pages + 1):
            response_text = self.fetch_shop_info_data(page_index=page_index, page_size=page_size)
            if not response_text:
                print(f"获取第{page_index}页数据失败")
                continue
            
            parsed_data = self.parse_response(response_text)
            if not parsed_data:
                print(f"解析第{page_index}页数据失败")
                continue
            
            all_data.extend(parsed_data['items'])
            print(f"已收集第{page_index}页数据，共{len(parsed_data['items'])}条记录")
            
            time.sleep(0.5)  # 避免请求过快
        
        print(f"总共收集到 {len(all_data)} 条店铺信息数据")
        return all_data

    def save_to_excel(self, data, filename="义务塔智有限公司.xlsx"):
        """
        保存数据到Excel文件
        """
        if not data:
            print("没有数据需要保存")
            return None

        try:
            # 创建日期目录
            date_dir = BASE_ARCHIVE_DIR / TODAY_STR
            date_dir.mkdir(parents=True, exist_ok=True)

            # 转换为DataFrame
            df = pd.DataFrame(data)

            # 保存文件
            file_path = date_dir / filename
            df.to_excel(file_path, index=False, engine='openpyxl')

            print(f"✓ 数据已保存到: {file_path}")
            return file_path

        except Exception as e:
            print(f"保存Excel文件时出错: {e}")
            return None

    def merge_files(self):
        """
        合并文件
        """
        try:
            # 源目录
            source_dir = BASE_ARCHIVE_DIR / TODAY_STR

            # 目标文件
            merged_dir = MERGED_FILES_DIR
            merged_dir.mkdir(parents=True, exist_ok=True)
            merged_file = merged_dir / f"{TODAY_STR}.xlsx"

            if not source_dir.exists():
                print(f"源目录不存在: {source_dir}")
                return None

            # 使用ExcelMerger合并文件
            merger = ExcelMerger(str(source_dir), str(merged_dir))
            success = merger.merge_excel_files(f"{TODAY_STR}.xlsx")

            if success:
                print(f"✓ 文件合并成功: {merged_file}")
                return merged_file
            else:
                print("文件合并失败")
                return None

        except Exception as e:
            print(f"合并文件时出错: {e}")
            return None

    def upload_to_minio(self, file_path):
        """
        上传文件到MinIO
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)

            # 构建MinIO路径
            minio_path = f"ods/erp/shop_info/dt={TODAY_STR}/{TODAY_STR}.parquet"

            # 处理数据
            df = df.fillna('')
            df = df.replace([float('inf'), float('-inf')], '')

            # 确保所有数据都能正常序列化
            for col in df.columns:
                if df[col].dtype in ['float64', 'float32']:
                    df[col] = df[col].replace([float('inf'), float('-inf')], '')
                df[col] = df[col].astype(str)

            # 准备上传数据
            upload_data = {
                "data": df.to_dict('records'),
                "target_path": minio_path,
                "format": "parquet",
                "bucket": MINIO_BUCKET
            }

            # 发送请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(MINIO_API_URL, json=upload_data, headers=headers)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✓ 成功上传文件到MinIO: {minio_path}")
                    return True
                else:
                    print(f"MinIO上传失败: {result.get('message', '未知错误')}")
                    return False
            else:
                print(f"MinIO API请求失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"上传文件到MinIO时出错: {e}")
            return False

    def refresh_dremio_dataset(self):
        """
        刷新Dremio数据集和反射
        """
        dataset_path = "minio.warehouse.ods.erp.shop_info"

        try:
            # 刷新数据集
            refresh_response = requests.post(
                "http://localhost:8003/api/dataset/refresh-metadata",
                headers={"Content-Type": "application/json"},
                json={"dataset_path": dataset_path}
            )

            if refresh_response.status_code == 200:
                print(f'✓ 数据集刷新成功: {dataset_path}')
            else:
                print(f'数据集刷新失败: {dataset_path} - {refresh_response.status_code}')

            # 刷新反射
            reflection_response = requests.post(
                "http://localhost:8003/api/reflection/refresh",
                headers={"Content-Type": "application/json"},
                json={"dataset_path": dataset_path}
            )

            if reflection_response.status_code == 200:
                print(f'✓ 反射刷新成功: {dataset_path}')
                return True
            else:
                print(f'反射刷新失败: {dataset_path} - {reflection_response.status_code}')
                return False

        except Exception as e:
            print(f'刷新Dremio时出错: {e}')
            return False

def main():
    """
    主函数
    """
    print("ERP店铺信息数据采集程序启动...")
    print(f"目标日期: {TODAY_STR}")

    # 创建采集器
    collector = ERPShopInfoCollector(profile="Default")

    # 1. 获取动态参数
    if not collector.get_dynamic_params():
        print("获取动态参数失败，程序退出")
        return

    # 2. 收集所有数据
    all_data = collector.collect_all_data(page_size=200)
    if not all_data:
        print("没有收集到数据，程序退出")
        return

    # 3. 保存到Excel
    excel_file = collector.save_to_excel(all_data)
    if not excel_file:
        print("保存Excel文件失败，程序退出")
        return

    # 4. 合并文件
    merged_file = collector.merge_files()
    if not merged_file:
        print("合并文件失败，使用原始文件")
        merged_file = excel_file

    # 5. 上传到MinIO
    if not collector.upload_to_minio(merged_file):
        print("上传MinIO失败")
        return

    # 6. 刷新Dremio
    if not collector.refresh_dremio_dataset():
        print("刷新Dremio失败")
        return

    print("✓ ERP店铺信息数据采集完成！")

if __name__ == '__main__':
    main()


