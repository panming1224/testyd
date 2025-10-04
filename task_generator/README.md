# 统一任务管理系统

## 📋 概述

**统一任务管理系统** - 所有平台（拼多多、天猫等）的任务生成和调度集中管理。

### 核心特性

✅ **统一任务生成** - 所有平台任务配置集中管理
✅ **统一任务调度** - 所有平台任务统一调度执行
✅ **自动化运行** - 后台运行，不占用终端
✅ **易于扩展** - 新增平台或任务只需添加配置
✅ **灵活调度** - 支持日度、周度、月度任务
✅ **可视化监控** - Web界面实时查看任务状态

---

## 📁 文件结构

```
task_generator/
├── README.md                      # 本文档
├── platform_config.py             # 平台任务配置（核心配置文件）
├── generate_all_tasks.py          # 统一任务生成器
├── scheduler_manager.py           # 调度服务管理器
├── scheduler_config.py            # 调度配置
├── scheduler_flows.py             # 工作流定义
├── 调度系统文档.md                 # 调度系统详细文档
├── README_调度系统.md              # 调度系统快速开始
└── scheduler.log                  # 调度日志文件
```

---

## 🚀 快速使用

### 一、调度服务管理

#### 1. 启动调度服务

```bash
cd D:\testyd\task_generator
python scheduler_manager.py start
```

服务启动后会：
- ✅ 自动启动Prefect服务器
- ✅ 自动启动任务调度器
- ✅ 后台运行，不占用终端
- ✅ 按配置的时间自动执行所有任务

#### 2. 查看服务状态

```bash
python scheduler_manager.py status
```

#### 3. 停止服务

```bash
python scheduler_manager.py stop
```

#### 4. 重启服务

```bash
python scheduler_manager.py restart
```

#### 5. 访问Web监控界面

浏览器打开: http://127.0.0.1:4200

---

### 二、手动生成任务（测试用）

#### 1. 生成每日任务（所有平台）

```bash
cd D:\testyd\task_generator
python generate_all_tasks.py --schedule daily
```

#### 2. 生成周度任务（所有平台）

```bash
python generate_all_tasks.py --schedule weekly
```

#### 3. 生成月度任务（所有平台）

```bash
python generate_all_tasks.py --schedule monthly
```

#### 4. 生成所有类型任务

```bash
python generate_all_tasks.py --schedule all
```

#### 5. 只为指定平台生成任务

```bash
# 只为拼多多生成任务
python generate_all_tasks.py --schedule daily --platforms pdd

# 只为天猫生成任务
python generate_all_tasks.py --schedule daily --platforms tm

# 为拼多多和天猫生成任务
python generate_all_tasks.py --schedule daily --platforms pdd tm
```

#### 6. 测试模式（指定日期）

```bash
python generate_all_tasks.py --schedule daily --date 2025-10-02
```

---

## 📊 自动调度时间表

### 任务生成

| 任务类型 | 执行时间 | Cron表达式 | 说明 |
|---------|---------|-----------|------|
| 每日任务生成 | 每天00:05 | `5 0 * * *` | 为所有平台生成每日任务 |
| 每周任务生成 | 每周六00:10 | `10 0 * * 6` | 为所有平台生成周度任务 |
| 每月任务生成 | 每月1号00:15 | `15 0 1 * *` | 为所有平台生成月度任务 |

### 任务执行

| 任务 | 执行时间 | 说明 |
|------|---------|------|
| ERP门店数据 | 每天07:00 | 拉取ERP门店数据 |
| 京东门店数据 | 每天07:30 | 拉取京东门店数据 |
| PDD质量数据 | 每天08:00 | 拉取PDD质量数据 |
| PDD差评数据 | 每天08:30 | 拉取PDD差评数据 |
| PDDKPI数据 | 每天11:00 | 拉取PDDKPI数据 |
| PDDKPI周报 | 每周六12:00 | 拉取PDDKPI周报 |
| PDDKPI月报 | 每月3号12:30 | 拉取PDDKPI月报 |

---

## 📊 当前支持的平台

| 平台 | 平台代码 | 店铺表 | 任务表 |
|------|---------|--------|--------|
| 拼多多 | pdd | pdd_shops | pdd_tasks |
| 天猫 | tm | tm_shops | tm_tasks |

---

## 📋 任务配置说明

### 拼多多任务

| 任务类型 | 调度类型 | 日期偏移 | 状态字段 | 说明 |
|---------|---------|---------|---------|------|
| badscore | daily | T-1 | badsscore_status | 差评数据 |
| quality | daily | T | quality_status | 产品质量 |
| kpi_days | daily | T-3 | kpi_days_status | 客服绩效（日度） |
| chat | daily | T-1 | chat_status | 聊天记录 |
| kpi_weekly | weekly | T-9~T-3 | kpi_weekly_status | 客服绩效（周度） |
| kpi_monthly | monthly | 上月 | kpi_monthly_status | 客服绩效（月度） |

### 天猫任务

| 任务类型 | 调度类型 | 日期偏移 | 状态字段 | 说明 |
|---------|---------|---------|---------|------|
| badscore | daily | T-1 | badscore_status | 差评数据 |
| chat | daily | T-1 | chat_status | 聊天记录 |
| kpi_self | daily | T-4 | kpi_self_status | 客服绩效自制报表 |
| kpi_official | daily | T-4 | kpi_official_status | 客服绩效官方报表 |
| kpi_weekly | weekly | T-9~T-3 | kpi_weekly_status | 客服绩效（周度） |
| kpi_monthly | monthly | 上月 | kpi_monthly_status | 客服绩效（月度） |

---

## ➕ 新增平台指南

### 步骤1：在 `platform_config.py` 添加平台配置

```python
# 新平台任务配置
NEW_PLATFORM_TASKS = {
    'task1': {
        'name': '任务1名称',
        'script': 'new_platform/task1.py',
        'status_field': 'task1_status',
        'schedule': 'daily',
        'date_offset': -1,
        'minio_path': 'ods/new_platform/task1',
        'dremio_table': 'minio.warehouse.ods.new_platform.task1',
        'enabled': True
    }
}

# 添加到平台数据库配置
PLATFORM_DB_CONFIG['new_platform'] = {
    'platform': 'new_platform',
    'shops_table': 'new_platform_shops',
    'tasks_table': 'new_platform_tasks',
    'database': 'company'
}

# 添加到所有平台配置
ALL_PLATFORMS['new_platform'] = {
    'name': '新平台',
    'tasks': NEW_PLATFORM_TASKS,
    'db_config': PLATFORM_DB_CONFIG['new_platform']
}
```

### 步骤2：测试

```bash
python generate_all_tasks.py --schedule daily --platforms new_platform
```

### 步骤3：完成！

新平台已添加到统一任务生成系统中！

---

## ➕ 新增任务指南

### 为现有平台添加新任务

在 `platform_config.py` 中找到对应平台的任务配置，添加新任务：

```python
PDD_TASKS['new_task'] = {
    'name': '新任务名称',
    'script': 'pdd/pdd_new_task.py',
    'status_field': 'new_task_status',
    'schedule': 'daily',
    'date_offset': -1,
    'minio_path': 'ods/pdd/pdd_new_task',
    'dremio_table': 'minio.warehouse.ods.pdd.pdd_new_task',
    'enabled': True
}
```

**注意事项：**
1. `status_field` 必须在数据库任务表中存在
2. `date_offset` 为负数表示过去的日期（T-1表示昨天）
3. `schedule` 支持 'daily'、'weekly'、'monthly'
4. 周度任务使用 `date_range` 而不是 `date_offset`
5. 月度任务使用 `date_range: 'last_month'`

---

## 🔧 配置文件详解

### platform_config.py

**核心配置文件**，包含：

1. **任务配置** - 每个平台的所有任务配置
2. **数据库配置** - 每个平台的数据库连接配置
3. **辅助函数** - 获取配置、计算日期等工具函数

**任务配置字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | str | ✅ | 任务显示名称 |
| script | str | ✅ | 脚本路径（相对于testyd目录） |
| status_field | str | ✅ | 数据库状态字段名 |
| schedule | str | ✅ | 调度类型：daily/weekly/monthly |
| date_offset | int | ⚠️ | 日期偏移（daily任务必填） |
| date_range | tuple/str | ⚠️ | 日期范围（weekly/monthly任务必填） |
| minio_path | str | ❌ | MinIO存储路径 |
| dremio_table | str | ❌ | Dremio表名 |
| enabled | bool | ❌ | 是否启用（默认True） |

---

## 📊 执行流程

```
1. 读取平台配置
   ↓
2. 筛选指定调度类型的任务
   ↓
3. 遍历每个平台
   ↓
4. 为每个平台的每个任务：
   - 计算目标日期
   - 连接数据库
   - 生成任务记录
   - 更新状态为"待执行"
   ↓
5. 打印执行摘要
```

---

## 🔍 日期计算规则

### 日度任务（daily）

使用 `date_offset` 字段：
- `date_offset: 0` → 今天（T）
- `date_offset: -1` → 昨天（T-1）
- `date_offset: -3` → 3天前（T-3）

### 周度任务（weekly）

使用 `date_range` 字段：
- `date_range: (-9, -3)` → T-9 到 T-3（7天）
- 返回格式：`2025-09-24_2025-09-30`

### 月度任务（monthly）

使用 `date_range: 'last_month'`：
- 自动计算上个月
- 返回格式：`2025-09`

---

## 📝 使用示例

### 示例1：每天凌晨自动生成所有平台的日度任务

```bash
# 在调度系统中配置
python generate_all_tasks.py --schedule daily
```

### 示例2：每周六生成所有平台的周度任务

```bash
python generate_all_tasks.py --schedule weekly
```

### 示例3：每月3号生成所有平台的月度任务

```bash
python generate_all_tasks.py --schedule monthly
```

### 示例4：测试某个日期的任务生成

```bash
python generate_all_tasks.py --schedule daily --date 2025-10-02
```

---

## 🔗 与调度系统集成

在 `scheduler_config.py` 中配置：

```python
{
    'flow': unified_task_generation_flow,
    'name': '统一任务生成-定时执行',
    'cron': '5 0 * * *',  # 每天00:05
    'description': '每天00:05为所有平台生成待执行任务',
    'tags': ['任务生成', '定时'],
    'enabled': True
}
```

---

## ⚠️ 重要说明

1. **任务生成不会重复** - 使用 `INSERT IGNORE` 机制，相同日期的任务不会重复生成
2. **状态字段必须存在** - 确保数据库任务表中有对应的状态字段
3. **日期计算自动** - 根据配置自动计算目标日期，无需手动指定
4. **平台独立** - 每个平台使用独立的数据库表，互不影响

---

## 📞 技术支持

**相关文档：**
- 调度系统文档: `testyd/调度系统文档.md`
- PDD架构文档: `testyd/pdd/架构文档.md`
- TM架构文档: `testyd/tm/架构文档.md`

**常见问题：**

Q: 如何查看生成了哪些任务？  
A: 查看数据库对应平台的任务表，状态为"待执行"的即为新生成的任务。

Q: 任务生成失败怎么办？  
A: 检查数据库连接、状态字段是否存在、配置是否正确。

Q: 如何禁用某个任务？  
A: 在配置中设置 `'enabled': False`。

---

**维护者：** AI Assistant  
**最后更新：** 2025-10-04  
**版本：** 1.0.0

