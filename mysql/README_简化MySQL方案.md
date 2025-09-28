# 拼多多爬虫通用数据库接口 - 优化版本

## 📋 项目概述

这是一个专为拼多多爬虫项目设计的通用数据库接口，提供了完整的任务管理、状态跟踪和数据存储解决方案。经过优化后，支持动态任务类型、店铺名称管理、文件夹路径等高级功能。

## 核心特性

- ✅ **单例模式**: 全局唯一的数据库接口实例
- ✅ **连接池管理**: 高效的数据库连接复用
- ✅ **简化表结构**: 只有店铺表和任务表两个核心表
- ✅ **通用接口**: 支持所有爬虫类型的统一调用
- ✅ **自动任务生成**: 根据日期和店铺自动创建任务记录
- ✅ **Cookie集中管理**: 在店铺表中统一存储和更新Cookie

## 文件结构

```
mysql/
├── crawler_db_interface.py    # 唯一的通用数据库接口文件
└── README_简化MySQL方案.md    # 本文档
```

## 数据库设计

### 1. 店铺表 (shops)
```sql
CREATE TABLE shops (
    shop_id INT PRIMARY KEY AUTO_INCREMENT,
    shop_name VARCHAR(255) NOT NULL UNIQUE,
    cookie TEXT,                              -- Cookie存储在这里
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 2. 任务表 (daily_tasks)
```sql
CREATE TABLE daily_tasks (
    task_date DATE NOT NULL,                  -- 任务日期
    shop_id INT NOT NULL,                     -- 店铺ID
    chat_status ENUM('待处理', '处理中', '已完成', '失败', '跳过') DEFAULT '待处理',
    quality_status ENUM('待处理', '处理中', '已完成', '失败', '跳过') DEFAULT '待处理',
    badreview_status ENUM('待处理', '处理中', '已完成', '失败', '跳过') DEFAULT '待处理',
    kpi_status ENUM('待处理', '处理中', '已完成', '失败', '跳过') DEFAULT '待处理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (task_date, shop_id)          -- 复合主键
);
```

## 快速开始

### 1. 导入和初始化

```python
from mysql.crawler_db_interface import db_interface, TaskType, TaskStatus

# 接口会自动初始化，无需手动创建实例
```

### 2. 导入店铺信息（仅需一次）

```python
# 从Excel导入店铺基础信息
count = db_interface.import_shops_from_excel("店铺信息.xlsx")
print(f"导入了 {count} 个店铺")
```

### 3. 生成每日任务

```python
# 每个爬虫脚本开始前调用，根据日期生成任务
task_date = "2024-01-15"  # 你的抓取日期
created_count = db_interface.generate_daily_tasks(task_date)
print(f"为 {task_date} 创建了 {created_count} 个新任务")
```

### 4. 获取待处理任务

```python
# 获取指定类型的待处理任务
pending_tasks = db_interface.get_pending_tasks(
    task_date="2024-01-15",
    task_type=TaskType.BAD_REVIEW,  # 差评任务
    limit=10  # 限制数量
)

for task in pending_tasks:
    print(f"店铺: {task['shop_name']}, Cookie: {task['cookie']}")
```

### 5. 更新任务状态

```python
# 开始处理
db_interface.update_task_status(
    task_date="2024-01-15",
    shop_id=1,
    task_type=TaskType.BAD_REVIEW,
    status=TaskStatus.PROCESSING
)

# 完成任务
db_interface.update_task_status(
    task_date="2024-01-15",
    shop_id=1,
    task_type=TaskType.BAD_REVIEW,
    status=TaskStatus.COMPLETED
)
```

### 6. Cookie管理

```python
# 获取店铺Cookie
cookie = db_interface.get_shop_cookie(shop_id=1)

# 更新店铺Cookie
db_interface.update_shop_cookie(shop_id=1, cookie="新的cookie值")
```

## 任务状态管理 - 简化版本

系统采用简化的任务状态管理，只有两种状态：

- **null（待处理）**：任务尚未开始处理，数据库中对应字段为null或空字符串
- **已完成**：任务已完成处理，数据库中对应字段值为"已完成"

```python
class TaskStatus:
    """任务状态常量 - 简化版本"""
    COMPLETED = "已完成"
    # null值表示待处理状态
```

## 动态任务类型

系统不再使用固定的TaskType枚举，而是支持动态传入列名，更加灵活：

```python
# 定义自定义任务类型（动态列名）
custom_tasks = [
    'chat_status',          # 客服聊天记录
    'quality_status',       # 产品质量下载
    'badreview_status',     # 差评下载
    'kpi_status',          # 客服绩效下载
    'promotion_status',     # 推广数据下载（新增）
    'inventory_status'      # 库存数据下载（新增）
]

# 生成任务时传入自定义任务列表
db_interface.generate_daily_tasks(today, custom_tasks)

# 获取待处理任务时传入具体列名
pending_tasks = db_interface.get_pending_tasks(today, 'badreview_status')

# 更新任务状态时传入具体列名
db_interface.update_task_status(today, shop_name, 'badreview_status', TaskStatus.COMPLETED)
```

## 使用示例

### 简化版差评爬虫使用示例

```python
from mysql.crawler_db_interface import CrawlerDBInterface, TaskStatus
from datetime import datetime

def main():
    # 1. 初始化数据库接口
    db = CrawlerDBInterface()
    
    # 2. 生成今日任务（支持自定义任务列）
    today = datetime.now().strftime('%Y-%m-%d')
    custom_tasks = ['chat_status', 'quality_status', 'badreview_status', 'kpi_status']
    db.generate_daily_tasks(today, custom_tasks)
    
    # 3. 获取待处理的差评任务（null状态）
    pending_tasks = db.get_pending_tasks(today, 'badreview_status')
    
    for task in pending_tasks:
        shop_name = task['shop_name']
        cookie = task['cookie']
        folder_path = task['folder_path']
        
        try:
            print(f"开始处理店铺: {shop_name}")
            # ... 你的爬虫代码 ...
            
            # 4. 标记为完成
            db.update_task_status(today, shop_name, 'badreview_status', TaskStatus.COMPLETED)
            print(f"店铺 {shop_name} 处理完成")
            
        except Exception as e:
            print(f"店铺 {shop_name} 处理失败: {e}")
            # 注意：简化版本中失败的任务保持null状态，可手动重新处理

if __name__ == "__main__":
    main()
```

## 核心优势

### 1. 极简设计
- 只有一个文件：`crawler_db_interface.py`
- 只有两个表：`shops` 和 `daily_tasks`
- 只有两种状态：null（待处理）和已完成

### 2. 灵活性强
- 支持动态任务类型，无需修改代码即可新增任务
- 任务列名完全自定义，适应各种业务场景
- 简化的状态管理，减少复杂度

### 3. 自动化程度高
- 自动创建数据库和表结构
- 自动管理连接池
- 自动生成任务记录

### 4. 性能优化
- 连接池复用连接
- 索引优化查询
- 单例模式避免重复初始化

## 配置说明

数据库配置在 `CrawlerDBInterface.__init__()` 中：

```python
self.db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin123',
    'database': 'company',
    'charset': 'utf8mb4',
    'port': 3306
}
```

## 监控和统计

```python
# 获取任务统计
stats = db_interface.get_task_statistics("2024-01-15")
print(f"总店铺数: {stats['total_shops']}")
print(f"差评完成数: {stats['badreview_completed']}")
print(f"差评待处理: {stats['badreview_pending']}")
```

## 故障排除

### 1. 数据库连接失败
- 检查MySQL服务是否启动
- 确认数据库配置信息正确
- 检查网络连接

### 2. 表不存在
- 接口会自动创建表，如果失败请检查数据库权限

### 3. 任务重复创建
- `generate_daily_tasks()` 会自动检查重复，不会创建重复任务

## 总结

这个简化版本的MySQL方案完全满足你的需求：

1. ✅ **只保留通用接口**: 只有 `crawler_db_interface.py` 一个文件
2. ✅ **简单的任务生成**: 传入日期就能自动生成任务
3. ✅ **Cookie集中管理**: 存储在店铺表中，所有任务共享
4. ✅ **状态独立管理**: 每个任务类型有独立的状态字段
5. ✅ **变量传入即用**: 所有功能都通过参数传入，无需复杂配置

现在你可以在任何爬虫脚本中简单地导入和使用这个接口，实现统一的任务管理！