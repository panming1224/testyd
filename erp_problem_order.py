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
from urllib.parse import urlencode

# 配置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 添加merge_excel_files模块路径
sys.path.append(r'D:\testyd')
from merge_excel_files import ExcelMerger

# 配置
BASE_ARCHIVE_DIR = Path('D:/yingdao/erp/异常订单')  # 异常订单存档目录
MERGED_FILES_DIR = Path('D:/yingdao/erp/合并表格/异常订单')  # 合并文件存储目录

# MinIO API配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"

# ERP配置
ERP_LOGIN_URL = "https://www.erp321.com/epaas"
ERP_ORDER_LIST_URL = "https://www.erp321.com/app/order/order/list.aspx"

# 创建基础存档目录和合并文件目录
os.makedirs(BASE_ARCHIVE_DIR, exist_ok=True)
os.makedirs(MERGED_FILES_DIR, exist_ok=True)

# 使用今天日期
TODAY_STR = datetime.now().strftime('%Y-%m-%d')

class ERPProblemOrderCollector:
    """ERP异常订单数据采集器"""

    def __init__(self, profile: str = "Default"):
        self.profile = profile
        self.USER_DATA_DIR = r"C:\\Users\\1\AppData\\Local\\Chromium\\User Data"
        self.cookie_str = None
        self.viewstate = None
        self.viewstate_generator = None
        self.ts = None

    def get_dynamic_params(self):
        """
        获取动态参数：Cookie、__VIEWSTATE、__VIEWSTATEGENERATOR、ts
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
                # 直接导航到订单列表页面
                order_list_url = f"{ERP_ORDER_LIST_URL}?_c=jst-epaas"
                print(f"导航到订单列表页面: {order_list_url}")
                page.goto(order_list_url, wait_until="domcontentloaded", timeout=60000)

                # 等待页面完全加载
                time.sleep(1)

                # 获取Cookie
                cookies = context.cookies(ERP_ORDER_LIST_URL)
                self.cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
                print(f"✓ 获取Cookie成功: {self.cookie_str[:100]}...")

                # 获取页面内容用于解析动态参数
                content = page.content()

                # 解析__VIEWSTATE和__VIEWSTATEGENERATOR
                viewstate_match = re.search(r'name="__VIEWSTATE"[^>]*value="([^"]*)"', content)
                viewstate_gen_match = re.search(r'name="__VIEWSTATEGENERATOR"[^>]*value="([^"]*)"', content)

                if viewstate_match:
                    self.viewstate = viewstate_match.group(1)
                    print(f"✓ 获取__VIEWSTATE成功: {self.viewstate[:50]}...")
                else:
                    print("⚠️ 未找到__VIEWSTATE")

                if viewstate_gen_match:
                    self.viewstate_generator = viewstate_gen_match.group(1)
                    print(f"✓ 获取__VIEWSTATEGENERATOR成功: {self.viewstate_generator}")
                else:
                    print("⚠️ 未找到__VIEWSTATEGENERATOR")

                # 生成时间戳
                self.ts = str(int(time.time() * 1000))
                print(f"✓ 生成时间戳: {self.ts}")

                return True

            except Exception as e:
                print(f"获取动态参数失败: {e}")
                return False
            finally:
                context.close()

    def fetch_problem_orders(self, page_index: int = 1):
        """
        获取异常订单数据
        """
        if not all([self.cookie_str, self.viewstate, self.viewstate_generator, self.ts]):
            print("动态参数不完整，无法发送请求")
            return None

        # 构建URL
        url_params = {
            '_c': 'jst-epaas',
            'ts___': self.ts,
            'am___': 'LoadDataToJSON'
        }
        url = f"{ERP_ORDER_LIST_URL}?{urlencode(url_params)}"

        # 构建请求头
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': self.cookie_str,
            'origin': 'https://www.erp321.com',
            'priority': 'u=1, i',
            'referer': 'https://www.erp321.com/app/order/order/list.aspx?_c=jst-epaas',
            'sec-ch-ua': '"Not=A?Brand";v="24", "Chromium";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }

        # 构建请求体
        callback_param = {
            "Method": "LoadDataToJSON",
            "Args": [
                str(page_index),
                '[{"k":"status","v":"question","c":"@="},{"k":"question_type","v":"亏钱订单,商品编码缺失,没有任何可发货商品","c":"@="},{"k":"order_date","v":"今天","c":">=","t":"date"},{"k":"order_date","v":"今天 23:59:59.998","c":"<=","t":"date"}]',
                "{}"
            ]
        }

        form_data = {
            '__VIEWSTATE': self.viewstate,
            '__VIEWSTATEGENERATOR': self.viewstate_generator,
            'insurePrice': '',
            '_jt_page_count_enabled': 'true',
            '_jt_page_increament_enabled': 'true',
            '_jt_page_increament_page_mode': '',
            '_jt_page_increament_key_value': '',
            '_jt_page_increament_business_values': '',
            '_jt_page_increament_key_name': 'o_id',
            '_jt_page_size': '2000',
            '_jt_page_action': '2',
            'fe_node_desc': '',
            'receiver_state': '',
            'receiver_city': '',
            'receiver_district': '',
            'receiver_address': '',
            'receiver_name': '',
            'receiver_phone': '',
            'receiver_mobile': '',
            'check_name': '',
            'check_address': '',
            'fe_remark_type': 'single',
            'node_type': '',
            'fe_flag': '',
            'fe_is_append_remark': '',
            'feedback': '',
            '__CALLBACKID': 'JTable1',
            '__CALLBACKPARAM': json.dumps(callback_param)
        }

        try:
            print(f"发送异常订单数据请求 (页码: {page_index})...")
            response = requests.post(url, headers=headers, data=form_data)

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
            # 响应格式: "0|{json_data}"
            if response_text.startswith('0|'):
                json_str = response_text[2:]  # 去掉前缀 "0|"
                data = json.loads(json_str)

                if data.get('IsSuccess'):
                    return_value = json.loads(data.get('ReturnValue', '{}'))

                    # 获取分页信息
                    dp = return_value.get('dp', {})
                    page_count = dp.get('PageCount', 0)
                    page_index = dp.get('PageIndex', 1)

                    # 获取数据
                    datas = return_value.get('datas', [])

                    print(f"解析结果: 页码 {page_index}/{page_count}, 数据条数: {len(datas)}")

                    return {
                        'page_count': page_count,
                        'page_index': page_index,
                        'data': datas
                    }
                else:
                    print(f"API返回失败: {data.get('ExceptionMessage', '未知错误')}")
                    return None
            else:
                print(f"响应格式不正确: {response_text[:100]}...")
                return None

        except Exception as e:
            print(f"解析响应数据时出错: {e}")
            return None

    def collect_all_data(self):
        """
        收集所有异常订单数据
        """
        all_data = []
        page_index = 1

        while True:
            # 获取当前页数据
            response_text = self.fetch_problem_orders(page_index)
            if not response_text:
                print(f"获取第{page_index}页数据失败")
                break

            # 解析数据
            parsed_data = self.parse_response(response_text)
            if not parsed_data:
                print(f"解析第{page_index}页数据失败")
                break

            # 添加数据
            page_data = parsed_data['data']
            all_data.extend(page_data)

            # 检查是否还有更多页
            page_count = parsed_data['page_count']
            current_page = parsed_data['page_index']

            print(f"已收集第{current_page}页数据，共{len(page_data)}条记录")

            if current_page >= page_count or page_count == 0:
                print("所有数据收集完成")
                break

            page_index += 1
            time.sleep(1)  # 避免请求过快

        print(f"总共收集到 {len(all_data)} 条异常订单数据")
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
            minio_path = f"ods/erp/problem_order/dt={TODAY_STR}/{TODAY_STR}.parquet"

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
        dataset_path = "minio.warehouse.ods.erp.problem_order"

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
    print("ERP异常订单数据采集程序启动...")
    print(f"目标日期: {TODAY_STR}")

    # 创建采集器
    collector = ERPProblemOrderCollector(profile="Default")

    # 1. 获取动态参数
    if not collector.get_dynamic_params():
        print("获取动态参数失败，程序退出")
        return

    # 2. 收集所有数据
    all_data = collector.collect_all_data()
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

    print("✓ ERP异常订单数据采集完成！")

if __name__ == '__main__':
    main()

