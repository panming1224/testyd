# 京东店铺库存数据拉取脚本使用文档

## 📋 概述

`jd_store.py` 是专门用于自动拉取京东店铺库存数据的脚本。该脚本使用Playwright自动化框架，模拟用户操作登录京东商家后台，自动下载库存报表数据。

## 🎯 功能特性

- **自动登录**: 使用保存的用户数据自动登录京东商家后台
- **智能等待**: 自动等待页面加载和数据生成
- **文件管理**: 自动下载并重命名文件，避免重复
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
启动脚本 → 初始化浏览器 → 加载用户数据 → 访问京东后台 → 
导航到库存页面 → 等待数据加载 → 下载报表 → 文件重命名 → 
清理资源 → 记录日志
```

## 🚀 使用方法

### 独立运行
```bash
# 进入脚本目录
cd D:\testyd

# 直接运行脚本
python jd_store.py
```

### 通过调度器运行（推荐）
脚本已集成到调度器中，每天08:30自动执行：
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
download_path = r"D:\testyd\jd_downloads"
```
- **用途**: 存储下载的报表文件
- **注意**: 确保目录存在且有写入权限

#### 3. 目标URL
```python
url = "https://mp.jd.com/report/inventory"
```
- **用途**: 京东商家后台库存报表页面
- **说明**: 如页面地址变更需要更新此配置

#### 4. 等待时间配置
```python
await page.wait_for_timeout(30000)  # 等待30秒
```
- **用途**: 等待页面加载和数据生成
- **调整**: 根据网络情况可适当调整等待时间

## 📊 输出文件

### 文件命名规则
```
jd_store_inventory_YYYYMMDD_HHMMSS.xlsx
```

### 示例文件名
```
jd_store_inventory_20250926_083045.xlsx
```

### 文件内容
- 店铺商品库存数据
- 商品基本信息
- 库存数量统计
- 销售相关数据

## 🔧 自定义配置

### 修改下载等待时间
如果网络较慢或数据量大，可以增加等待时间：
```python
# 在脚本中找到这行并修改数值（毫秒）
await page.wait_for_timeout(45000)  # 改为45秒
```

### 修改文件保存位置
```python
# 修改下载目录
download_path = r"D:\your_custom_path\downloads"

# 确保目录存在
os.makedirs(download_path, exist_ok=True)
```

### 添加额外的页面操作
```python
# 在下载前添加额外操作
await page.click('button[data-action="refresh"]')  # 刷新数据
await page.wait_for_timeout(5000)  # 等待5秒
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
python jd_store.py
```

#### 2. 下载失败
**症状**: 脚本执行完成但没有下载文件
**原因**: 页面加载时间不足或网络问题
**解决方案**:
- 增加等待时间
- 检查网络连接
- 确认京东后台页面是否正常

#### 3. 文件权限错误
**症状**: 无法创建或写入文件
**解决方案**:
```bash
# 检查目录权限
icacls D:\testyd\jd_downloads

# 创建目录（如果不存在）
mkdir D:\testyd\jd_downloads
```

#### 4. 浏览器启动失败
**症状**: Playwright无法启动浏览器
**解决方案**:
```bash
# 重新安装浏览器
playwright install chromium
```

## 📋 维护指南

### 日常维护
1. **检查用户数据**: 定期检查登录状态是否有效
2. **清理下载文件**: 定期清理过期的下载文件
3. **监控日志**: 查看执行日志确保正常运行

### 定期更新
1. **更新依赖**: 定期更新Playwright版本
2. **检查页面变化**: 京东后台页面更新时需要调整脚本
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
type D:\testyd\scheduler.log | findstr "jd_store"
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

### 添加邮件通知
```python
import smtplib
from email.mime.text import MIMEText

def send_notification(status, file_path=None):
    """发送执行结果通知"""
    # 邮件发送逻辑
    pass
```

## 🔗 相关文档

- [主文档](../README.md)
- [调度器使用文档](./scheduler_usage.md)
- [拼多多数据拉取文档](./pdd_kpi_usage.md)

## 📞 技术支持

如遇到问题，请：
1. 查看日志文件定位问题
2. 检查网络连接和权限设置
3. 确认京东后台页面是否有变化
4. 参考错误处理章节的解决方案

---

**最后更新**: 2025-09-26
**版本**: v1.0.0
**兼容性**: Python 3.7+, Playwright 1.40+