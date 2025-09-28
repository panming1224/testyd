# 数据拉取自动化系统

## 📋 项目概述

本项目是一个完整的电商数据自动化拉取系统，支持京东和拼多多平台的数据采集、处理和存储。系统采用调度器模式，可以自动定时执行数据拉取任务，并将数据上传到MinIO对象存储。

## 🏗️ 系统架构

```
数据拉取自动化系统
├── 调度器模块 (scheduler.py)
├── 京东数据拉取 (jd_store.py)
├── 拼多多数据拉取 (pdd_kpi.py, pdd_chat.py)
├── Excel文件合并 (merge_excel_files.py)
└── 后台服务管理 (start_scheduler_service.py)
```

## 📁 核心文件说明

### 🔧 调度器相关
- **`scheduler.py`** - 主调度器，负责定时执行数据拉取任务
- **`start_scheduler_service.py`** - 后台服务管理器，用于启动/停止/监控调度器
- **`scheduler_control.bat`** - 便捷的批处理管理工具

### 📊 数据拉取脚本
- **`jd_store.py`** - 京东店铺库存数据拉取脚本
- **`pdd_kpi.py`** - 拼多多KPI数据拉取脚本（主版本）
- **`pdd_kpi_copy.py`** - 拼多多KPI数据拉取脚本（备份版本）
- **`pdd_chat.py`** - 拼多多客服聊天数据拉取脚本

### 🛠️ 工具脚本
- **`merge_excel_files.py`** - Excel文件合并工具
- **`pdd_chat_upload.py`** - 拼多多聊天数据上传工具

## ⏰ 调度时间表

| 任务 | 执行时间 | 脚本文件 | 说明 |
|------|----------|----------|------|
| 京东店铺库存数据 | 每天 08:30 | `jd_store.py` | 自动拉取京东店铺库存报表 |
| 拼多多KPI数据 | 每天 12:00 | `pdd_kpi_copy.py` | 自动拉取拼多多KPI数据 |

## 🚀 快速开始

### 1. 启动调度器
```bash
# 方法1: 使用Python脚本
python start_scheduler_service.py start

# 方法2: 使用批处理文件
scheduler_control.bat start
```

### 2. 检查运行状态
```bash
# 检查调度器状态
python start_scheduler_service.py status

# 或使用批处理
scheduler_control.bat status
```

### 3. 查看日志
```bash
# 查看后台日志
scheduler_control.bat log

# 或直接查看文件
type scheduler_background.log
```

### 4. 停止调度器
```bash
# 停止调度器
python start_scheduler_service.py stop

# 或使用批处理
scheduler_control.bat stop
```

## 📝 日志文件

- **`scheduler_background.log`** - 后台调度器运行日志
- **`scheduler.log`** - 调度器详细日志
- **`merge_excel.log`** - Excel合并操作日志
- **`pdd_chat_upload.log`** - 拼多多聊天数据上传日志
- **`pdd_kpi_days_upload.log`** - 拼多多日度KPI上传日志
- **`pdd_kpi_monthly_upload.log`** - 拼多多月度KPI上传日志

## 🔧 管理命令

### 调度器管理
```bash
# 启动调度器
scheduler_control.bat start

# 停止调度器
scheduler_control.bat stop

# 重启调度器
scheduler_control.bat restart

# 检查状态
scheduler_control.bat status

# 查看日志
scheduler_control.bat log
```

## 📊 数据流程

### 京东数据流程
1. 自动登录京东商家后台
2. 生成库存报表
3. 监控报表生成状态
4. 下载完成的报表
5. 合并多个Excel文件
6. 上传到MinIO存储
7. 刷新Dremio数据集

### 拼多多数据流程
1. 自动登录拼多多商家后台
2. 下载各类数据报表
3. 按日期和类型分类存储
4. 合并同类型文件
5. 上传到MinIO存储

## 🛡️ 错误处理

系统具备完善的错误处理机制：
- 自动重试机制
- 详细的错误日志记录
- 异常情况下的数据恢复
- 网络中断后的自动恢复

## 📋 系统要求

- Python 3.8+
- Chrome浏览器
- 网络连接
- MinIO存储服务
- Dremio数据服务（可选）

## 🔗 相关文档

- [调度器使用文档](./docs/scheduler_usage.md)
- [京东数据拉取文档](./docs/jd_store_usage.md)
- [拼多多数据拉取文档](./docs/pdd_kpi_usage.md)

## 📞 技术支持

如遇问题，请查看相应的日志文件或联系技术支持。

---

**最后更新**: 2025-09-26
**版本**: v1.0.0