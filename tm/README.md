# 天猫KPI数据获取工具

## 功能说明

本工具实现了两个主要功能：

1. **功能一：获取自制报表数据**
   - 自动发送获取数据请求
   - 循环检查下载状态直到完成
   - 获取下载链接并静默下载文件
   - 保存到指定日期文件夹

2. **功能二：获取售后解决分析数据**
   - 发送API请求获取售后数据
   - 解析响应数据
   - 保存为Excel格式

## 文件说明

- `get_sycm_cookies.py` - Cookie获取脚本
- `tm_kpi.py` - 主程序
- `test_tm_kpi.py` - 测试脚本
- `sycm_cookie.txt` - Cookie存储文件（需要先获取）

## 使用步骤

### 1. 获取Cookie

首先运行Cookie获取脚本：

```bash
python get_sycm_cookies.py
```

- 脚本会自动打开浏览器访问天猫生意参谋
- 如果需要登录，请在浏览器中完成登录
- 确认页面正确加载后按回车键
- Cookie会自动保存到 `sycm_cookie.txt` 文件

### 2. 运行测试

运行测试脚本检查配置：

```bash
python test_tm_kpi.py
```

测试内容包括：
- 目录创建测试
- Cookie文件测试
- 日期计算测试

### 3. 运行主程序

如果测试通过，运行主程序：

```bash
python tm_kpi.py
```

## 数据保存位置

- **自制报表数据**: `D:\yingdao\tm\天猫客服绩效自制报表\{日期}\`
- **售后解决分析数据**: `D:\yingdao\tm\天猫客服绩效解决分析报表\{日期}\`

## 日期说明

- 程序默认获取T-4日期（4天前）的数据
- 日期格式：YYYY-MM-DD（如：2025-09-26）

## 注意事项

1. 确保网络连接正常
2. Cookie有时效性，如果请求失败可能需要重新获取Cookie
3. 程序会自动创建所需的目录结构
4. 如果目标文件已存在，会先删除再重新下载

## 错误处理

- 如果Cookie过期，重新运行 `get_sycm_cookies.py`
- 如果网络请求失败，检查网络连接和Cookie有效性
- 如果文件保存失败，检查目录权限

## 依赖库

```
requests
pandas
openpyxl
playwright
pathlib
```

安装依赖：

```bash
pip install requests pandas openpyxl playwright
```