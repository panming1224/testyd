# 调度器使用文档

## 📋 概述

调度器是整个数据拉取系统的核心组件，负责按照预设的时间表自动执行各种数据拉取任务。系统采用后台服务模式运行，不占用用户终端。

## 🏗️ 系统架构

```
调度器系统
├── scheduler.py                    # 主调度器程序
├── start_scheduler_service.py      # 集成管理工具（启动、停止、状态、日志）
├── scheduler.pid                   # 进程ID文件
├── scheduler_background.log        # 后台运行日志
└── scheduler.log                   # 详细执行日志
```

## ⏰ 调度配置

### 当前调度任务

| 任务名称 | 执行时间 | 脚本文件 | 功能描述 |
|----------|----------|----------|----------|
| 京东店铺库存数据 | 每天 08:30 | `jd_store.py` | 自动拉取京东店铺库存报表数据 |
| 拼多多KPI数据 | 每天 12:00 | `pdd_kpi_copy.py` | 自动拉取拼多多KPI数据报表 |

### 时间设置说明
- 使用24小时制格式
- 精确到分钟
- 系统会在指定时间自动触发任务执行

## 🚀 启动和管理

### 使用集成管理工具

#### 启动调度器
```bash
python start_scheduler_service.py start
```

#### 检查状态
```bash
python start_scheduler_service.py status
```

#### 停止调度器
```bash
python start_scheduler_service.py stop
```

#### 重启调度器
```bash
python start_scheduler_service.py restart
```

#### 查看日志
```bash
python start_scheduler_service.py log
# 或者
python start_scheduler_service.py logs
```

## 📊 监控和日志

### 日志文件说明

#### 1. scheduler_background.log
- **用途**: 后台服务运行日志
- **内容**: 调度器启动、停止、任务执行状态
- **查看**: `python start_scheduler_service.py log`

#### 2. scheduler.log
- **用途**: 详细执行日志
- **内容**: 任务执行详情、错误信息、输出结果
- **查看**: `python start_scheduler_service.py log`

### 日志示例

```
2025-09-26 08:30:00,123 - INFO - 开始执行京东店铺库存数据拉取任务...
2025-09-26 08:35:42,456 - INFO - 京东店铺库存数据拉取任务执行成功
2025-09-26 12:00:00,789 - INFO - 开始执行拼多多KPI数据拉取任务...
2025-09-26 12:15:33,012 - INFO - 拼多多KPI数据拉取任务执行成功
```

## 🔧 配置修改

### 修改调度时间

编辑 `scheduler.py` 文件中的时间设置：

```python
# 设置每天上午8:30执行京东店铺库存任务
schedule.every().day.at("08:30").do(run_jd_store_task)

# 设置每天中午12点执行拼多多KPI任务
schedule.every().day.at("12:00").do(run_pdd_kpi_task)
```

### 添加新任务

1. 在 `scheduler.py` 中添加新的任务函数：
```python
def run_new_task():
    """执行新任务"""
    try:
        logger.info("开始执行新任务...")
        # 任务执行逻辑
        script_path = r"d:\testyd\new_script.py"
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, encoding='utf-8', cwd=r"d:\testyd")
        
        if result.returncode == 0:
            logger.info("新任务执行成功")
        else:
            logger.error("新任务执行失败")
            
    except Exception as e:
        logger.error(f"执行新任务时发生异常: {str(e)}")
```

2. 在 `main()` 函数中添加调度：
```python
# 设置新任务的执行时间
schedule.every().day.at("14:00").do(run_new_task)
```

## 🛡️ 错误处理

### 常见问题及解决方案

#### 1. 调度器无法启动
**症状**: 执行启动命令后没有反应
**解决方案**:
- 检查Python环境是否正确
- 确认所有依赖包已安装
- 查看错误日志: `type scheduler_background.log`

#### 2. 任务执行失败
**症状**: 日志显示任务执行失败
**解决方案**:
- 检查对应脚本文件是否存在
- 确认脚本文件路径正确
- 查看详细错误信息: `type scheduler.log`

#### 3. 进程意外停止
**症状**: 调度器自动停止运行
**解决方案**:
- 检查系统资源是否充足
- 查看错误日志定位问题
- 重启调度器: `python start_scheduler_service.py restart`

### 调试模式

如需调试，可以直接运行调度器查看实时输出：
```bash
python scheduler.py
```

## 📋 维护建议

### 日常维护
1. **定期检查状态**: 每周检查一次调度器运行状态
2. **清理日志文件**: 定期清理过大的日志文件
3. **监控磁盘空间**: 确保有足够空间存储日志和数据

### 备份建议
1. 备份配置文件: `scheduler.py`
2. 备份重要日志: `scheduler.log`
3. 备份进程管理脚本: `start_scheduler_service.py`

## 🔗 相关文档

- [主文档](../README.md)
- [京东数据拉取文档](./jd_store_usage.md)
- [拼多多数据拉取文档](./pdd_kpi_usage.md)

---

**最后更新**: 2025-09-26
**版本**: v1.0.0