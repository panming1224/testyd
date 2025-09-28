"""
京东店铺库存数据自动拉取脚本 - 教学版
=================================

这个脚本的主要功能：
1. 自动登录京东商家后台
2. 获取店铺库存报表数据
3. 下载并整理Excel文件
4. 合并多个店铺的数据
5. 上传到MinIO数据仓库

作者：AI助手
日期：2025-09-26
版本：教学版 v1.0

学习重点：
- Python基础语法
- 文件操作
- 网络请求
- 数据处理
- 异常处理
"""

# ========================================
# 第一部分：导入模块（Import Modules）
# ========================================

# 导入模块就像是"借用工具"，每个模块提供不同的功能

# 1. 浏览器自动化工具 - 用来控制浏览器
from playwright.sync_api import sync_playwright

# 2. 时间相关工具
import time           # 用来暂停程序执行
from datetime import datetime, timedelta  # 用来处理日期和时间

# 3. 数据处理工具
import json          # 用来处理JSON格式数据
import pandas as pd  # 用来处理Excel和数据表格

# 4. 网络请求工具
import requests      # 用来发送HTTP请求（下载文件、调用API）

# 5. 文件和系统操作工具
import os            # 用来操作文件夹
import shutil        # 用来移动、复制文件
from pathlib import Path  # 更现代的文件路径处理方式

# 6. 其他工具
import uuid          # 用来生成唯一标识符
import sys           # 用来操作Python系统设置

# 7. 导入自定义模块（ ourselves写的工具）
sys.path.append(r'D:\testyd')  # 告诉Python去哪里找我们的模块
from merge_excel_files import ExcelMerger  # 导入Excel合并工具

# ========================================
# 第二部分：配置参数（Configuration）
# ========================================

# 配置就像是"设置"，告诉程序去哪里找文件、保存到哪里等

# 店铺信息Excel文件的位置
EXCEL_PATH = r'D:\yingdao\jd\店铺信息表.xlsx'

# 存档目录 - 用来保存下载的文件
BASE_ARCHIVE_DIR = Path('D:/yingdao/jd/库存表')

# 合并文件目录 - 用来保存合并后的文件
MERGED_FILES_DIR = Path('D:/yingdao/jd/合并表格')

# Excel表格的工作表编号（0表示第一个工作表）
SHEET = 0

# MinIO数据仓库的配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"  # API地址
MINIO_BUCKET = "warehouse"  # 存储桶名称

# 创建必要的文件夹（如果不存在就创建）
# os.makedirs() 函数用法：
# - 第一个参数：要创建的文件夹路径
# - exist_ok=True：如果文件夹已存在，不报错
os.makedirs(BASE_ARCHIVE_DIR, exist_ok=True)
os.makedirs(MERGED_FILES_DIR, exist_ok=True)

# 计算昨天的日期（T-1日期）
# datetime.now() - 获取当前时间
# timedelta(days=1) - 表示1天的时间差
# strftime('%Y-%m-%d') - 格式化为 "年-月-日" 格式
TODAY_STR = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

print(f"📅 今天处理的日期是：{TODAY_STR}")

# ========================================
# 第三部分：函数定义（Function Definitions）
# ========================================

def update_header_once(df: pd.DataFrame):
    """
    更新Excel表头的函数
    
    函数说明：
    - 这个函数用来更新Excel文件的表头
    - 把F列的标题改成今天的日期+下载状态
    - 如果今天已经更新过了，就不重复更新
    
    参数说明：
    - df: pandas DataFrame对象，代表Excel表格的数据
    
    返回值：
    - True: 表示更新了表头
    - False: 表示今天已经更新过，没有重复更新
    
    使用示例：
    df = pd.read_excel('文件.xlsx')
    result = update_header_once(df)
    if result:
        print("表头已更新")
    else:
        print("今天已经更新过了")
    """
    
    # 生成新的状态列名称
    new_status = f'{TODAY_STR}库存表下载状态'
    
    # 获取F列（索引为5）的当前名称
    # df.columns[5] 表示获取第6列的列名（因为索引从0开始）
    old_header = df.columns[5]
    
    print(f"🔍 检查表头：当前F列名称是 '{old_header}'")
    print(f"🔍 需要的F列名称是 '{new_status}'")
    
    # 检查是否已经是今天的格式
    if old_header == new_status:
        print("✅ 今天已经更新过表头，跳过更新")
        return False  # 返回False表示没有更新
    
    # 更新列名
    # df.rename() 用来重命名列
    # columns={旧名称: 新名称} 是重命名的规则
    # inplace=True 表示直接修改原数据，不创建新的副本
    df.rename(columns={old_header: new_status}, inplace=True)
    
    # 清空F列的所有数据（保留表头）
    # df.iloc[:, 5] 表示选择所有行的第6列
    # '' 表示空字符串
    df.iloc[:, 5] = ''
    
    # 立即保存到Excel文件
    # to_excel() 用来保存DataFrame到Excel文件
    # index=False 表示不保存行索引
    # engine='openpyxl' 指定使用openpyxl引擎处理Excel
    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
    
    print(f"✅ 表头已更新为：{new_status}")
    return True  # 返回True表示已更新


def fetch_download_link_and_download(shop_name: str, profile: str):
    """
    获取下载链接并下载文件的主要函数
    
    函数说明：
    - 这是整个脚本的核心函数
    - 负责打开浏览器、登录京东、获取数据、下载文件
    
    参数说明：
    - shop_name: 店铺名称（字符串类型）
    - profile: 浏览器配置文件名称（字符串类型）
    
    返回值：
    - True: 下载成功
    - False: 下载失败
    
    使用示例：
    success = fetch_download_link_and_download("测试店铺", "Profile 1")
    if success:
        print("下载成功")
    else:
        print("下载失败")
    """
    
    print(f"\n🚀 开始处理店铺：{shop_name}")
    print(f"📁 使用浏览器配置：{profile}")
    
    # 浏览器用户数据目录（存储登录信息、Cookie等）
    USER_DATA_DIR = r"C:\\Users\\1\AppData\\Local\\Chromium\\User Data"
    
    # 目标网页地址
    TARGET_URL = "https://ppzh.jd.com/scbrandweb/brand/view/supplyReport/supplyChainPro.html"
    
    # 使用 try-except 来处理可能出现的错误
    try:
        # ========================================
        # 步骤1：启动浏览器并登录
        # ========================================
        
        print(f"🌐 正在启动浏览器...")
        
        # sync_playwright() 是Playwright的入口
        # 使用 with 语句确保资源正确释放
        with sync_playwright() as p:
            
            # 启动浏览器上下文
            # launch_persistent_context() 用来启动带用户数据的浏览器
            context = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,  # 用户数据目录
                headless=False,               # False表示显示浏览器窗口
                args=[                        # 浏览器启动参数
                    "--start-maximized",      # 最大化窗口
                    "--no-sandbox",           # 禁用沙盒模式
                    "--disable-dev-shm-usage",  # 禁用/dev/shm使用
                    "--disable-blink-features=AutomationControlled",  # 隐藏自动化特征
                    f"--profile-directory={profile}"  # 指定配置文件
                ],
                no_viewport=True,             # 不限制视口大小
                ignore_https_errors=True      # 忽略HTTPS错误
            )
            
            # 创建新页面
            page = context.new_page()
            
            print(f"🔗 正在访问京东页面...")
            
            # 访问目标网页
            # goto() 用来导航到指定URL
            # wait_until="domcontentloaded" 等待页面DOM加载完成
            # timeout=30000 设置30秒超时
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            
            # ========================================
            # 步骤2：获取Cookie（用于API请求）
            # ========================================
            
            print(f"🍪 正在获取Cookie...")
            
            # 获取当前页面的Cookie
            # cookies() 方法返回指定URL的所有Cookie
            cookies = context.cookies(TARGET_URL)
            
            # 将Cookie转换为字符串格式
            # 使用列表推导式和join()方法
            # f"{c['name']}={c['value']}" 格式化每个Cookie
            # '; '.join() 用分号连接所有Cookie
            cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
            
            print(f"✅ Cookie获取成功，长度：{len(cookie_str)}")
            
            # ========================================
            # 步骤3：发送API请求生成报表
            # ========================================
            
            print(f"📊 正在请求生成报表...")
            
            # 生成唯一的请求ID
            # uuid.uuid4() 生成随机UUID
            # str() 转换为字符串
            request_uuid = str(uuid.uuid4())
            
            # 构建API请求URL
            url = f"https://zhgateway.jd.com/inventoryajax/reportCenter/recommendReport/downloadERPSupplyChainProData.ajax?uuid={request_uuid}"
            
            # 设置HTTP请求头
            # 请求头告诉服务器我们的浏览器信息、接受的数据类型等
            headers = {
                "accept": "application/json, text/plain, */*",  # 接受的数据类型
                "accept-language": "zh-CN,zh;q=0.9",           # 语言偏好
                "content-type": "application/json;charset=UTF-8",  # 发送的数据类型
                "origin": "https://ppzh.jd.com",               # 请求来源
                "priority": "u=1, i",                          # 请求优先级
                "referer": "https://ppzh.jd.com/scbrandweb/brand/view/supplyReport/supplyChainPro.html",  # 引用页面
                "cookie": cookie_str,                          # Cookie信息
                "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",  # 浏览器信息
                "sec-ch-ua-mobile": "?0",                      # 是否移动设备
                "sec-ch-ua-platform": "\"Windows\"",          # 操作系统
                "sec-fetch-dest": "empty",                     # 请求目标
                "sec-fetch-mode": "cors",                      # 请求模式
                "sec-fetch-site": "same-site",                 # 请求站点
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",  # 用户代理
                "user-mnp": "",                                # 用户标识
                "user-mup": "1",                               # 用户标识
                "x-requested-with": "XMLHttpRequest"           # AJAX请求标识
            }
            
            # 设置请求数据
            # 这些参数告诉京东我们要什么样的报表
            data = {
                "isRdc": "0",                    # 是否RDC
                "brandId": "all",                # 品牌ID（all表示所有）
                "firstCategoryId": "",           # 一级分类ID
                "secondCategoryId": "",          # 二级分类ID
                "thirdCategoryId": "all",        # 三级分类ID
                "date": TODAY_STR,               # 日期
                "startDate": TODAY_STR,          # 开始日期
                "endDate": TODAY_STR,            # 结束日期
                "skuId": "",                     # 商品ID
                "skuStatusCd": "",               # 商品状态
                "dataType": "realtime",          # 数据类型（实时）
                "id": 2,                         # 报表ID
                "excludeEmpty": "0"              # 是否排除空数据
            }
            
            # 发送POST请求
            # requests.post() 发送POST请求
            # json.dumps(data) 将字典转换为JSON字符串
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            print(f"📡 API响应状态码：{response.status_code}")
            print(f"📡 API响应内容：{response.text[:200]}...")  # 只显示前200个字符
            
            # ========================================
            # 步骤4：导航到报表页面
            # ========================================
            
            print(f"📄 正在导航到报表页面...")
            
            # 访问报表列表页面
            page.goto('https://ppzh.jd.com/brand/reportCenter/myReport.html', 
                     wait_until="domcontentloaded", timeout=30000)
            
            # ========================================
            # 步骤5：监控报表状态并下载
            # ========================================
            
            print(f"👀 开始监控报表生成状态...")
            
            # 生成新的API请求UUID
            api_uuid = str(uuid.uuid4()).replace('-', '') + '-' + str(int(time.time() * 1000))[-11:]
            
            # 构建状态查询API URL
            api_url = f"https://ppzh.jd.com/brand/reportCenter/myReport/getReportList.ajax?uuid={api_uuid}"
            
            # 获取报表页面的Cookie
            cookie1 = context.cookies('https://ppzh.jd.com/brand/reportCenter/myReport.html')
            cookie_str1 = '; '.join(f"{c['name']}={c['value']}" for c in cookie1)
            
            print(f"🍪 报表页面Cookie获取成功")
            
            # 设置API请求头
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
            
            # 设置循环参数
            max_attempts = 60  # 最大尝试次数（避免无限循环）
            attempt = 0        # 当前尝试次数
            download_url = None      # 下载链接
            download_success = False # 下载是否成功
            
            # 开始循环检查报表状态
            # while 循环：当条件为True时继续执行
            while attempt < max_attempts:
                try:
                    print(f"🔍 第{attempt + 1}次检查报表状态...")
                    
                    # 发送GET请求获取报表列表
                    # requests.get() 发送GET请求
                    api_response = requests.get(api_url, headers=api_headers)
                    
                    # 检查响应是否成功
                    # raise_for_status() 如果状态码不是200会抛出异常
                    api_response.raise_for_status()
                    
                    # 解析JSON响应
                    # .json() 方法将响应内容解析为Python字典
                    response_data = api_response.json()
                    
                    # 检查响应是否包含数据
                    # .get() 方法安全地获取字典中的值，如果不存在返回默认值
                    if response_data.get('message') == 'success' and response_data.get('content', {}).get('data'):
                        reports = response_data['content']['data']
                        
                        # 检查是否有报表数据
                        if reports:
                            # 获取第一个报表的信息
                            first_report = reports[0]
                            status = first_report.get('status')
                            report_name = first_report.get('reportName', '未知报表')
                            
                            print(f"📊 报表名称：{report_name}")
                            print(f"📊 报表状态：{status}")
                            
                            # 检查报表是否完成
                            if status == "2":  # 状态2表示已完成
                                # 获取下载链接
                                download_url = first_report.get('downloadLink', '').strip()
                                
                                if download_url:
                                    print(f"✅ 报表生成完成！开始下载...")
                                    
                                    # ========================================
                                    # 步骤6：下载文件
                                    # ========================================
                                    
                                    # 创建日期目录
                                    # Path() 创建路径对象
                                    # mkdir() 创建目录
                                    # parents=True 创建父目录
                                    # exist_ok=True 如果已存在不报错
                                    date_dir = BASE_ARCHIVE_DIR / TODAY_STR
                                    date_dir.mkdir(parents=True, exist_ok=True)
                                    # 📚 知识点：Path对象的方法
                                    # .mkdir(): 创建目录
                                    # .exists(): 检查是否存在
                                    # .unlink(): 删除文件
                                    # .glob(): 模式匹配查找文件
                                    # .parent: 获取父目录
                                    # .name: 获取文件名
                                    # .suffix: 获取文件扩展名
                                    
                                    # 生成文件名
                                    filename = f"{shop_name}.xlsx"
                                    file_path = date_dir / filename
                                    
                                    print(f"💾 保存路径：{file_path}")
                                    
                                    # 如果文件已存在，先删除
                                    if file_path.exists():
                                        print(f"🗑️ 发现同名文件，正在删除...")
                                        file_path.unlink()  # unlink() 删除文件
                                        print(f"✅ 同名文件已删除")
                                    
                                    # 下载文件
                                    print(f"⬇️ 正在下载文件...")
                                    
                                    # stream=True 表示流式下载（适合大文件）
                                    download_response = requests.get(download_url, stream=True)
                                    download_response.raise_for_status()
                                    # 📚 知识点：文件下载的最佳实践
                                    # stream=True: 流式下载，不会一次性加载到内存
                                    # 适合大文件下载
                                    # 可以显示下载进度
                                    
                                    # 写入文件
                                    # 'wb' 表示以二进制写入模式打开文件
                                    with open(file_path, 'wb') as f:
                                        # iter_content() 分块读取内容
                                        # chunk_size=8192 每次读取8KB
                                        for chunk in download_response.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                    # 📚 知识点：文件操作模式
                                    # 'r': 读取文本文件
                                    # 'w': 写入文本文件
                                    # 'rb': 读取二进制文件
                                    # 'wb': 写入二进制文件
                                    # 'a': 追加模式
                                    
                                    print(f"✅ 文件下载完成：{file_path}")
                                    download_success = True
                                    break  # 跳出while循环
                                else:
                                    print(f"❌ 报表已完成但未获取到下载链接")
                                    break
                            else:
                                print(f"⏳ 报表状态为 {status}，继续等待...")
                        else:
                            print(f"⏳ 暂无报表数据，继续等待...")
                    else:
                        print(f"⏳ API响应异常，继续等待...")
                
                except requests.exceptions.RequestException as e:
                    print(f"❌ 网络请求异常：{e}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析异常：{e}")
                except Exception as e:
                    print(f"❌ 其他异常：{e}")
                # 📚 知识点：异常处理的层次结构
                # Exception (基类)
                # ├── requests.exceptions.RequestException (网络异常)
                # │   ├── ConnectionError (连接错误)
                # │   ├── Timeout (超时)
                # │   └── HTTPError (HTTP错误)
                # ├── json.JSONDecodeError (JSON解析错误)
                # └── 其他异常
                
                # 增加尝试次数
                attempt += 1
                
                # 如果还没有成功，等待一段时间再试
                if attempt < max_attempts and not download_success:
                    print(f"⏰ 等待10秒后进行第{attempt + 1}次尝试...")
                    time.sleep(10)  # 等待10秒
                    # 📚 知识点：轮询间隔的选择
                    # 太短：浪费资源，可能被服务器限制
                    # 太长：用户体验差
                    # 一般选择5-30秒之间
            
            # 检查最终结果
            if download_success:
                print(f"🎉 店铺 {shop_name} 数据下载成功！")
                return True
            else:
                print(f"❌ 店铺 {shop_name} 数据下载失败，已达到最大尝试次数")
                return False
    
    except Exception as e:
        print(f"❌ 处理店铺 {shop_name} 时发生异常：{e}")
        return False


def upload_merged_file_to_minio(merged_file_path: str, date_str: str = None) -> bool:
    """
    将合并后的Excel文件上传到MinIO数据仓库
    
    函数说明：
    - 读取合并后的Excel文件
    - 转换数据格式
    - 上传到MinIO数据仓库
    
    参数说明：
    - merged_file_path: 合并后的Excel文件路径（字符串）
    - date_str: 日期字符串，默认使用今天（可选参数）
    
    返回值：
    - True: 上传成功
    - False: 上传失败
    
    使用示例：
    success = upload_merged_file_to_minio("合并文件.xlsx", "2025-09-26")
    if success:
        print("上传成功")
    """
    
    # 如果没有提供日期，使用默认日期
    if date_str is None:
        date_str = TODAY_STR
    
    print(f"☁️ 开始上传文件到MinIO：{merged_file_path}")
    
    try:
        # ========================================
        # 步骤1：读取Excel文件
        # ========================================
        
        print(f"📖 正在读取Excel文件...")
        
        # pd.read_excel() 读取Excel文件为DataFrame
        df = pd.read_excel(merged_file_path)
        
        print(f"📊 文件包含 {len(df)} 行数据，{len(df.columns)} 列")
        
        # ========================================
        # 步骤2：构建MinIO路径
        # ========================================
        
        # 构建MinIO中的存储路径
        # 路径格式：ods/jd/jd_store/dt=日期/文件名.parquet
        minio_path = f"ods/jd/jd_store/dt={date_str}/merged_store_data.parquet"
        
        print(f"🗂️ MinIO存储路径：{minio_path}")
        
        # ========================================
        # 步骤3：数据清理
        # ========================================
        
        print(f"🧹 正在清理数据...")
        
        # 处理NaN值（空值）
        # fillna('') 将所有NaN值替换为空字符串
        df = df.fillna('')
        
        # 处理无穷大值
        # replace() 替换指定值
        # float('inf') 正无穷大
        # float('-inf') 负无穷大
        df = df.replace([float('inf'), float('-inf')], '')
        
        # 确保所有数据都能正常序列化
        for col in df.columns:
            # 检查列的数据类型
            if df[col].dtype in ['float64', 'float32']:
                # 处理浮点数列的无穷大值
                df[col] = df[col].replace([float('inf'), float('-inf')], '')
            
            # 转换为字符串类型（避免序列化问题）
            # astype(str) 转换数据类型
            df[col] = df[col].astype(str)
        
        print(f"✅ 数据清理完成")
        
        # ========================================
        # 步骤4：准备上传数据
        # ========================================
        
        print(f"📦 正在准备上传数据...")
        
        # 准备上传的数据结构
        upload_data = {
            "data": df.to_dict('records'),  # 转换为字典列表格式
            "target_path": minio_path,      # 目标路径
            "format": "parquet",            # 文件格式
            "bucket": MINIO_BUCKET          # 存储桶
        }
        
        print(f"📊 数据记录数：{len(upload_data['data'])}")
        
        # ========================================
        # 步骤5：发送上传请求
        # ========================================
        
        print(f"🚀 正在发送上传请求...")
        
        # 设置请求头
        headers = {'Content-Type': 'application/json'}
        
        # 发送POST请求
        # json=upload_data 自动将字典转换为JSON并设置正确的Content-Type
        response = requests.post(MINIO_API_URL, json=upload_data, headers=headers)
        
        print(f"📡 上传响应状态码：{response.status_code}")
        
        # ========================================
        # 步骤6：检查上传结果
        # ========================================
        
        if response.status_code == 200:
            # 解析响应结果
            result = response.json()
            
            if result.get('success'):
                print(f"✅ 文件上传成功到MinIO：{minio_path}")
                return True
            else:
                error_msg = result.get('message', '未知错误')
                print(f"❌ MinIO上传失败：{error_msg}")
                return False
        else:
            print(f"❌ MinIO API请求失败：{response.status_code}")
            print(f"❌ 错误详情：{response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 上传文件到MinIO时发生错误：{str(e)}")
        return False


# ========================================
# 第四部分：主程序（Main Program）
# ========================================

if __name__ == '__main__':
    """
    主程序入口
    
    这里是程序的主要执行逻辑：
    1. 读取Excel配置文件
    2. 更新表头
    3. 收集需要下载的店铺信息
    4. 批量下载文件
    5. 合并文件
    6. 上传到数据仓库
    7. 刷新数据集
    
    if __name__ == '__main__': 的作用：
    - 只有直接运行这个脚本时才会执行下面的代码
    - 如果这个文件被其他脚本导入，下面的代码不会执行
    """
    
    print("=" * 60)
    print("🚀 京东店铺库存数据自动拉取程序启动")
    print("=" * 60)
    
    # ========================================
    # 步骤1：读取和更新Excel配置文件
    # ========================================
    
    print(f"\n📋 步骤1：读取Excel配置文件")
    print(f"📁 文件路径：{EXCEL_PATH}")
    
    try:
        # 读取Excel文件
        # pd.read_excel() 参数说明：
        # - 第一个参数：文件路径
        # - sheet_name：工作表名称或索引
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)
        
        print(f"✅ Excel文件读取成功")
        print(f"📊 数据形状：{df.shape[0]}行 x {df.shape[1]}列")
        
    except Exception as e:
        print(f"❌ 读取Excel文件失败：{e}")
        print("🛑 程序终止")
        exit(1)  # 退出程序，返回错误代码1
    
    # 更新表头
    print(f"\n🔄 正在检查和更新表头...")
    header_updated = update_header_once(df)
    
    # 如果表头更新了，需要重新读取DataFrame
    if header_updated:
        print(f"🔄 重新读取更新后的Excel文件...")
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET)
    
    # ========================================
    # 步骤2：分析Excel数据结构
    # ========================================
    
    print(f"\n📋 步骤2：分析数据结构")
    
    # 定义重要列的索引（从0开始计数）
    shop_idx = 1      # B列：店铺名称
    profile_idx = 4   # E列：浏览器配置
    status_idx = 5    # F列：下载状态
    
    print(f"📊 数据结构分析：")
    print(f"   - 总行数：{len(df)}")
    print(f"   - 总列数：{len(df.columns)}")
    print(f"   - 列名：{list(df.columns)}")
    print(f"   - 店铺名称列（B列）：{df.columns[shop_idx]}")
    print(f"   - 浏览器配置列（E列）：{df.columns[profile_idx]}")
    print(f"   - 状态列（F列）：{df.columns[status_idx]}")
    
    # ========================================
    # 步骤3：收集需要下载的店铺信息
    # ========================================
    
    print(f"\n📋 步骤3：收集需要下载的店铺")
    
    # 创建下载任务列表
    download_tasks = []
    
    # 遍历每一行数据
    # range(len(df)) 生成从0到数据行数-1的序列
    for row_idx in range(len(df)):
        
        # 获取当前行的数据
        # df.iloc[行索引, 列索引] 获取指定位置的数据
        shop = df.iloc[row_idx, shop_idx]        # 店铺名称
        profile = df.iloc[row_idx, profile_idx]  # 浏览器配置
        status = df.iloc[row_idx, status_idx]    # 下载状态
        
        # 处理状态值
        # pd.notna() 检查值是否不为空
        # str() 转换为字符串
        status_str = str(status) if pd.notna(status) else ''
        
        print(f"🔍 检查第{row_idx + 2}行：店铺={shop}, 配置={profile}, 状态='{status_str}'")
        
        # 检查是否需要跳过
        
        # 1. 检查状态是否已完成
        if status_str.strip() == '已完成':
            print(f"   ⏩ 状态已完成，跳过")
            continue
        
        # 2. 检查浏览器配置是否为空
        # pd.isna() 检查是否为空值
        if pd.isna(profile) or str(profile).strip() == '' or str(profile).strip() == 'nan':
            print(f"   ⚠️ 浏览器配置为空，跳过")
            continue
        
        # 3. 检查店铺名称是否为空
        if pd.isna(shop) or str(shop).strip() == '':
            print(f"   ⚠️ 店铺名称为空，跳过")
            continue
        
        # 添加到下载任务列表
        download_tasks.append({
            'row_idx': row_idx,           # 行索引（用于后续更新状态）
            'shop': str(shop).strip(),    # 店铺名称
            'profile': str(profile).strip()  # 浏览器配置
        })
        
        print(f"   ✅ 已添加到下载队列")
    
    print(f"\n📊 任务统计：")
    print(f"   - 总店铺数：{len(df)}")
    print(f"   - 需要下载：{len(download_tasks)}")
    print(f"   - 跳过数量：{len(df) - len(download_tasks)}")
    
    # 如果没有需要下载的任务，提前结束
    if len(download_tasks) == 0:
        print(f"\n✅ 没有需要下载的店铺，程序结束")
        exit(0)
    
    # ========================================
    # 步骤4：批量下载文件
    # ========================================
    
    print(f"\n📋 步骤4：开始批量下载")
    
    # 记录下载成功的文件
    downloaded_files = []
    
    # 遍历所有下载任务
    # enumerate() 函数返回索引和值的元组
    for task_idx, task in enumerate(download_tasks):
        
        print(f"\n🎯 处理任务 {task_idx + 1}/{len(download_tasks)}")
        
        row_idx = task['row_idx']
        shop = task['shop']
        profile = task['profile']
        
        print(f"📍 店铺：{shop}")
        print(f"📍 配置：{profile}")
        
        try:
            # 调用下载函数
            success = fetch_download_link_and_download(shop, profile)
            
            if success:
                print(f"✅ {shop} 下载成功")
                
                # 记录下载的文件路径
                date_dir = BASE_ARCHIVE_DIR / TODAY_STR
                file_path = date_dir / f"{shop}.xlsx"
                downloaded_files.append(file_path)
                
                # 更新Excel中的状态为"已完成"
                df.iloc[row_idx, status_idx] = '已完成'
                
            else:
                print(f"❌ {shop} 下载失败")
                
                # 失败时清空状态，便于重试
                df.iloc[row_idx, status_idx] = ''
                
        except Exception as e:
            print(f"❌ {shop} 处理异常：{str(e)}")
            
            # 异常时也清空状态
            df.iloc[row_idx, status_idx] = ''
    
    # ========================================
    # 步骤5：保存Excel状态更新
    # ========================================
    
    print(f"\n📋 步骤5：保存状态更新")
    
    try:
        # 等待一下确保文件没有被占用
        time.sleep(1)
        
        # 保存更新后的DataFrame到Excel
        df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
        
        print(f"✅ Excel状态已更新并保存")
        
    except PermissionError as e:
        print(f"⚠️ Excel文件被占用，无法保存状态：{e}")
        print(f"💡 请关闭Excel文件后重新运行脚本")
    except Exception as e:
        print(f"❌ 保存Excel时发生错误：{e}")
    
    # ========================================
    # 步骤6：合并下载的文件
    # ========================================
    
    print(f"\n📋 步骤6：合并Excel文件")
    
    if downloaded_files:
        print(f"📊 准备合并 {len(downloaded_files)} 个文件")
        
        # 显示要合并的文件列表
        for i, file_path in enumerate(downloaded_files, 1):
            print(f"   {i}. {file_path.name}")
        
        try:
            # 创建日期目录路径
            date_dir = BASE_ARCHIVE_DIR / TODAY_STR
            
            # 使用ExcelMerger合并文件
            print(f"🔄 正在合并文件...")
            
            merger = ExcelMerger(str(date_dir))
            merge_filename = f"京东库存合并_{TODAY_STR}.xlsx"
            merge_success = merger.merge_excel_files(merge_filename)
            
            if merge_success:
                # 合并成功，移动文件到最终目录
                merged_file_path = date_dir / merge_filename
                final_merged_file_path = MERGED_FILES_DIR / merge_filename
                
                # 使用shutil.move()移动文件
                shutil.move(str(merged_file_path), str(final_merged_file_path))
                
                print(f"✅ 文件合并完成：{final_merged_file_path}")
                
                # ========================================
                # 步骤7：上传到MinIO数据仓库
                # ========================================
                
                print(f"\n📋 步骤7：上传到数据仓库")
                
                print(f"☁️ 正在上传合并文件到MinIO...")
                upload_success = upload_merged_file_to_minio(str(final_merged_file_path), TODAY_STR)
                
                if upload_success:
                    print(f"✅ MinIO上传成功")
                else:
                    print(f"⚠️ MinIO上传失败，但本地文件已保存")
                    
            else:
                print(f"❌ 文件合并失败")
                
        except Exception as e:
            print(f"❌ 合并文件时发生错误：{str(e)}")
    else:
        print(f"⚠️ 没有新下载的文件，跳过合并步骤")
    
    # ========================================
    # 步骤8：刷新数据集和反射
    # ========================================
    
    print(f"\n📋 步骤8：刷新数据仓库")
    
    # 刷新数据集元数据
    print(f"🔄 正在刷新数据集元数据...")
    
    try:
        refresh_dataset_response = requests.post(
            "http://localhost:8003/api/dataset/refresh-metadata",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.jd.jd_store"}
        )
        
        if refresh_dataset_response.status_code == 200:
            print(f"✅ 数据集元数据刷新成功")
        else:
            print(f"⚠️ 数据集元数据刷新失败：{refresh_dataset_response.status_code}")
            
    except Exception as e:
        print(f"❌ 数据集元数据刷新异常：{e}")
    
    # 刷新反射
    print(f"🔄 正在刷新数据反射...")
    
    try:
        refresh_reflection_response = requests.post(
            "http://localhost:8003/api/reflection/refresh",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.jd.jd_store"}
        )
        
        if refresh_reflection_response.status_code == 200:
            print(f"✅ 数据反射刷新成功")
        else:
            print(f"⚠️ 数据反射刷新失败：{refresh_reflection_response.status_code}")
            
    except Exception as e:
        print(f"❌ 数据反射刷新异常：{e}")
    
    # ========================================
    # 程序结束
    # ========================================
    
    print(f"\n" + "=" * 60)
    print(f"🎉 程序执行完成！")
    print(f"📊 执行统计：")
    print(f"   - 处理日期：{TODAY_STR}")
    print(f"   - 总任务数：{len(download_tasks)}")
    print(f"   - 成功下载：{len(downloaded_files)}")
    print(f"   - 失败数量：{len(download_tasks) - len(downloaded_files)}")
    print(f"=" * 60)

"""
========================================
学习总结和扩展建议
========================================

通过这个脚本，你可以学到：

1. Python基础语法：
   - 变量定义和使用
   - 函数定义和调用
   - 条件判断（if/else）
   - 循环（for/while）
   - 异常处理（try/except）

2. 数据处理：
   - pandas库的使用
   - Excel文件读写
   - 数据清理和转换

3. 网络编程：
   - HTTP请求（GET/POST）
   - Cookie处理
   - 文件下载

4. 文件操作：
   - 文件路径处理
   - 文件创建、删除、移动
   - 目录操作

5. 浏览器自动化：
   - Playwright的使用
   - 页面导航和操作
   - 元素定位和交互

扩展练习建议：

1. 初级练习：
   - 修改文件保存路径
   - 调整等待时间
   - 添加更多的日志输出

2. 中级练习：
   - 添加邮件通知功能
   - 实现多线程下载
   - 添加配置文件支持

3. 高级练习：
   - 实现GUI界面
   - 添加数据库支持
   - 实现分布式处理

学习资源推荐：
- Python官方文档：https://docs.python.org/
- pandas文档：https://pandas.pydata.org/docs/
- requests文档：https://docs.python-requests.org/
- Playwright文档：https://playwright.dev/python/

记住：编程是一个实践的过程，多写多练才能掌握！
"""