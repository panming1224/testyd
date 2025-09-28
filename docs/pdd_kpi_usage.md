# 拼多多KPI数据拉取脚本使用文档

## 📋 概述

`pdd_kpi_copy.py` 是专门用于自动拉取拼多多KPI数据的脚本。该脚本使用Playwright自动化框架，模拟用户操作登录拼多多商家后台，自动下载KPI报表数据。

## 🎯 功能特性

- **自动登录**: 使用保存的用户数据自动登录拼多多商家后台
- **智能导航**: 自动导航到KPI数据页面
- **数据下载**: 自动触发数据导出和下载
- **文件管理**: 自动重命名下载文件，避免重复
- **错误处理**: 完善的异常处理和日志记录
- **调度集成**: 与调度器完美集成，支持定时执行

## 🏗️ 技术架构

### 核心依赖
- **Playwright**: 浏览器自动化框架
- **asyncio**: 异步编程支持
- **pathlib**: 文件路径处理
- **datetime**: 时间处理
- **logging**: 日志记录

### 工作流程
```
启动脚本 → 初始化浏览器 → 加载用户数据 → 访问拼多多后台 → 
导航到KPI页面 → 等待数据加载 → 触发导出 → 下载报表 → 
文件重命名 → 清理资源 → 记录日志
```

## 🚀 使用方法

### 独立运行
```bash
# 进入脚本目录
cd D:\testyd

# 直接运行脚本
python pdd_kpi_copy.py
```

### 通过调度器运行（推荐）
脚本已集成到调度器中，每天12:00自动执行：
```bash
# 启动调度器
scheduler_control.bat start

# 查看执行日志
scheduler_control.bat log
```

## ⚙️ 配置说明

### 关键配置参数

#### 1. 用户数据目录
```python
user_data_dir = r"D:\testyd\chrome_user_data"
```
- **用途**: 存储浏览器用户数据，包括登录状态
- **重要性**: 确保自动登录功能正常工作

#### 2. 下载目录
```python
download_path = r"D:\testyd\pdd_downloads"
```
- **用途**: 存储下载的报表文件
- **注意**: 确保目录存在且有写入权限

#### 3. 目标URL
```python
url = "https://mms.pinduoduo.com/data/kpi"
```
- **用途**: 拼多多商家后台KPI数据页面
- **说明**: 如页面地址变更需要更新此配置

#### 4. 等待时间配置
```python
await page.wait_for_timeout(20000)  # 等待20秒
```
- **用途**: 等待页面加载和数据生成
- **调整**: 根据网络情况可适当调整等待时间

## 📊 输出文件

### 文件命名规则
```
pdd_kpi_data_YYYYMMDD_HHMMSS.xlsx
```

### 示例文件名
```
pdd_kpi_data_20250926_120345.xlsx
```

### 文件内容
- 店铺KPI数据
- 销售业绩指标
- 流量数据统计
- 转化率相关数据

## 🔧 自定义配置

### 修改下载等待时间
如果网络较慢或数据量大，可以增加等待时间：
```python
# 在脚本中找到这行并修改数值（毫秒）
await page.wait_for_timeout(30000)  # 改为30秒
```

### 修改文件保存位置
```python
# 修改下载目录
download_path = r"D:\your_custom_path\pdd_downloads"

# 确保目录存在
os.makedirs(download_path, exist_ok=True)
```

### 添加数据筛选条件
```python
# 在导出前设置日期范围
await page.click('input[placeholder="开始日期"]')
await page.fill('input[placeholder="开始日期"]', '2025-09-01')

await page.click('input[placeholder="结束日期"]')
await page.fill('input[placeholder="结束日期"]', '2025-09-26')
```

## 🛡️ 错误处理

### 常见问题及解决方案

#### 1. 登录失败
**症状**: 脚本运行后无法自动登录
**原因**: 用户数据过期或损坏
**解决方案**:
```bash
# 删除用户数据目录重新登录
rmdir /s D:\testyd\chrome_user_data
# 手动运行脚本进行首次登录
python pdd_kpi_copy.py
```

#### 2. 页面元素找不到
**症状**: 脚本报错找不到页面元素
**原因**: 拼多多后台页面结构变化
**解决方案**:
- 检查页面元素选择器是否正确
- 使用浏览器开发者工具重新定位元素
- 更新脚本中的选择器

#### 3. 下载失败
**症状**: 脚本执行完成但没有下载文件
**原因**: 导出按钮未正确触发或网络问题
**解决方案**:
- 增加等待时间
- 检查导出按钮的选择器
- 确认拼多多后台是否正常

#### 4. 文件权限错误
**症状**: 无法创建或写入文件
**解决方案**:
```bash
# 检查目录权限
icacls D:\testyd\pdd_downloads

# 创建目录（如果不存在）
mkdir D:\testyd\pdd_downloads
```

## 📋 维护指南

### 日常维护
1. **检查用户数据**: 定期检查登录状态是否有效
2. **清理下载文件**: 定期清理过期的下载文件
3. **监控日志**: 查看执行日志确保正常运行

### 定期更新
1. **更新依赖**: 定期更新Playwright版本
2. **检查页面变化**: 拼多多后台页面更新时需要调整脚本
3. **备份配置**: 备份重要的配置和用户数据

### 性能优化
1. **减少等待时间**: 根据实际情况优化等待时间
2. **并发处理**: 如有多个任务可考虑并发执行
3. **资源清理**: 确保浏览器资源正确释放

## 🔍 调试模式

### 启用调试模式
```python
# 在脚本开头添加
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用浏览器可视化模式
browser = await playwright.chromium.launch(
    headless=False,  # 显示浏览器窗口
    slow_mo=1000     # 减慢操作速度
)
```

### 查看详细日志
```bash
# 查看脚本执行日志
type D:\testyd\scheduler.log | findstr "pdd_kpi"
```

## 📈 扩展功能

### 添加数据验证
```python
def validate_downloaded_file(file_path):
    """验证下载的文件是否有效"""
    if not file_path.exists():
        return False
    
    # 检查文件大小
    if file_path.stat().st_size < 1024:  # 小于1KB可能是错误文件
        return False
    
    return True
```

### 添加多时间段数据拉取
```python
async def download_multiple_periods():
    """下载多个时间段的数据"""
    periods = [
        ('2025-09-01', '2025-09-07'),  # 第一周
        ('2025-09-08', '2025-09-14'),  # 第二周
        ('2025-09-15', '2025-09-21'),  # 第三周
    ]
    
    for start_date, end_date in periods:
        await set_date_range(start_date, end_date)
        await download_data()
```

### 添加数据格式转换
```python
import pandas as pd

def convert_to_csv(excel_file):
    """将Excel文件转换为CSV格式"""
    df = pd.read_excel(excel_file)
    csv_file = excel_file.with_suffix('.csv')
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    return csv_file
```

## 🔧 高级配置

### 自定义浏览器设置
```python
browser = await playwright.chromium.launch(
    headless=True,
    args=[
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1920,1080'
    ]
)
```

### 设置代理
```python
context = await browser.new_context(
    proxy={
        "server": "http://proxy-server:port",
        "username": "username",
        "password": "password"
    }
)
```

### 添加请求拦截
```python
async def handle_request(request):
    """拦截和处理请求"""
    if 'analytics' in request.url:
        await request.abort()  # 阻止分析请求
    else:
        await request.continue_()

await page.route('**/*', handle_request)
```

## 🔗 相关文档

- [主文档](../README.md)
- [调度器使用文档](./scheduler_usage.md)
- [京东数据拉取文档](./jd_store_usage.md)

## 📞 技术支持

如遇到问题，请：
1. 查看日志文件定位问题
2. 检查网络连接和权限设置
3. 确认拼多多后台页面是否有变化
4. 参考错误处理章节的解决方案

## 🚨 注意事项

1. **合规使用**: 请确保数据拉取符合拼多多的使用条款
2. **频率控制**: 避免过于频繁的请求，以免被系统限制
3. **数据安全**: 妥善保管下载的数据文件
4. **版本兼容**: 定期检查脚本与拼多多后台的兼容性

---

**最后更新**: 2025-09-26
**版本**: v1.0.0
**兼容性**: Python 3.7+, Playwright 1.40+