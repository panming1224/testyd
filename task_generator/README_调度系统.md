# 任务调度系统 - 快速开始

## 🎯 系统概述

**新的统一调度系统** - 管理所有数据拉取任务的定时执行

### 核心特性

✅ **统一管理** - 所有任务集中配置和管理  
✅ **后台运行** - 不占用终端，关闭窗口不影响服务  
✅ **可视化监控** - Web界面实时查看任务状态  
✅ **自动重试** - 失败任务自动重试  
✅ **易于扩展** - 新增任务只需3步  

---

## 🚀 快速开始

### 1. 启动服务

```bash
cd D:\testyd
python scheduler_manager.py start
```

### 2. 查看状态

```bash
python scheduler_manager.py status
```

### 3. 访问Web界面

浏览器打开: http://127.0.0.1:4200

### 4. 停止服务

```bash
python scheduler_manager.py stop
```

---

## 📋 当前调度任务

### 已启用的任务（6个）

| 序号 | 任务名称 | 执行时间 | 说明 |
|------|---------|---------|------|
| 1 | PDD任务生成 | 每天00:05 | 生成PDD待执行任务 |
| 2 | ERP门店数据 | 每天07:00 | 拉取ERP门店数据 |
| 3 | 京东门店数据 | 每天07:30 | 拉取京东门店数据 |
| 4 | PDD质量数据 | 每天08:00 | 拉取PDD质量数据 |
| 5 | PDD差评数据 | 每天08:30 | 拉取PDD差评数据 |
| 6 | PDDKPI数据 | 每天11:00 | 拉取PDDKPI数据 |

### 待实现的任务（3个）

| 任务名称 | 执行时间 | 状态 |
|---------|---------|------|
| PDD聊天数据 | 每天09:00 | ⏸️ 待实现 |
| PDDKPI周报 | 每周六12:00 | ⏸️ 待实现 |
| PDDKPI月报 | 每月3号12:30 | ⏸️ 待实现 |

---

## 📁 核心文件

| 文件 | 说明 |
|------|------|
| `scheduler_manager.py` | 服务管理器 - 启动/停止/状态检查 |
| `scheduler_config.py` | 调度配置 - 定义所有定时任务 |
| `scheduler_flows.py` | 工作流定义 - 封装任务执行逻辑 |
| `scheduler.log` | 日志文件 - 记录执行历史 |

---

## ➕ 新增任务（3步）

### 步骤1：在 `scheduler_flows.py` 添加工作流

```python
@flow(name="新任务数据流")
def new_task_flow():
    """新任务数据拉取流程"""
    logger = get_run_logger()
    logger.info("开始执行新任务")
    
    result = execute_script(
        "path/to/script.py",
        "新任务",
        timeout=3600
    )
    
    return result
```

### 步骤2：在 `scheduler_config.py` 添加配置

```python
TASK_CONFIGS = [
    # ... 现有配置 ...
    {
        'flow': new_task_flow,
        'name': '新任务-定时执行',
        'cron': '0 10 * * *',  # 每天10:00
        'description': '每天10:00执行新任务',
        'tags': ['新任务', '定时'],
        'enabled': True
    }
]
```

### 步骤3：重启服务

```bash
python scheduler_manager.py restart
```

**完成！** 新任务已添加！

---

## 🔍 监控和日志

### Web界面

访问 http://127.0.0.1:4200 查看：
- ✅ 任务执行历史
- ✅ 任务执行状态
- ✅ 任务执行日志
- ✅ 任务调度计划

### 日志文件

```bash
# 查看日志
type D:\testyd\scheduler.log

# 查看最后100行
powershell -command "Get-Content D:\testyd\scheduler.log -Tail 100"
```

---

## 🛠️ 常用命令

```bash
# 启动服务
python scheduler_manager.py start

# 停止服务
python scheduler_manager.py stop

# 查看状态
python scheduler_manager.py status

# 重启服务
python scheduler_manager.py restart

# 测试配置
python test_scheduler.py
```

---

## 📚 详细文档

- **调度系统文档**: `调度系统文档.md` - 完整的系统文档
- **PDD架构文档**: `pdd/架构文档.md` - PDD爬虫系统架构

---

## ⚠️ 重要说明

1. **后台运行** - 服务在后台运行，关闭终端不影响
2. **自动启动** - 需要开机自动启动请配置Windows任务计划程序
3. **日志清理** - 定期清理日志文件避免占用过多空间
4. **端口占用** - 确保4200端口未被占用

---

## 🔧 故障排查

### 服务启动失败

```bash
# 检查端口占用
netstat -ano | findstr :4200

# 检查Python环境
python --version
pip list | findstr prefect
```

### 任务未执行

```bash
# 检查服务状态
python scheduler_manager.py status

# 查看日志
type D:\testyd\scheduler.log

# 手动测试脚本
python pdd/pdd_quality.py
```

---

## 📞 技术支持

遇到问题请查看：
1. 日志文件: `D:\testyd\scheduler.log`
2. Prefect UI: http://127.0.0.1:4200
3. 详细文档: `调度系统文档.md`

---

**维护者：** AI Assistant  
**最后更新：** 2025-10-03  
**版本：** 1.0.0

