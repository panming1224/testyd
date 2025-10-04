# 拼多多爬虫系统 - 新架构使用指南

## 📋 架构概述

新架构采用**配置驱动**的设计，具有以下特点：

1. **集中配置管理** - 所有爬虫配置集中在 `crawler_config.py`
2. **统一任务生成** - 使用 `generate_tasks.py` 统一生成所有任务
3. **爬虫基类** - 所有爬虫继承 `BaseCrawler`，复用通用功能
4. **易于扩展** - 新增爬虫只需添加配置和实现数据采集逻辑

## 🗂️ 文件结构

```
testyd/pdd/
├── crawler_config.py          # 爬虫配置文件（核心）
├── generate_tasks.py          # 统一任务生成器
├── base_crawler.py            # 爬虫基类
├── pdd_badscore.py           # 差评数据爬虫
├── pdd_quality.py            # 产品质量爬虫
├── pdd_kpi.py                # 客服绩效爬虫（日度）
├── pdd_kpi_weekly.py         # 客服绩效爬虫（周度）
└── pdd_kpi_monthly.py        # 客服绩效爬虫（月度）
```

## 🚀 使用流程

### 1. 生成任务（每天最先执行）

```bash
# 生成每日任务（差评、产品质量、客服绩效日度）
python testyd/pdd/generate_tasks.py --schedule daily

# 生成每周任务（客服绩效周度）
python testyd/pdd/generate_tasks.py --schedule weekly

# 生成每月任务（客服绩效月度）
python testyd/pdd/generate_tasks.py --schedule monthly

# 生成所有类型的任务
python testyd/pdd/generate_tasks.py --schedule all

# 指定日期生成任务（用于测试）
python testyd/pdd/generate_tasks.py --schedule daily --date 2025-10-02
```

### 2. 执行爬虫程序

```bash
# 执行差评数据采集
python testyd/pdd/pdd_badscore.py

# 执行产品质量数据采集
python testyd/pdd/pdd_quality.py

# 执行客服绩效数据采集（日度）
python testyd/pdd/pdd_kpi.py
```

### 3. 任务状态说明

- **NULL（空值）** - 暂时没有任务（这个店铺这一天不需要执行这个任务类型）
- **"待执行"** - 有任务需要执行（由 generate_tasks.py 生成）
- **"已完成"** - 任务已完成

## ➕ 如何新增爬虫

### 步骤1：在 `crawler_config.py` 中添加配置

```python
CRAWLER_TASKS = {
    # ... 现有配置 ...
    
    'new_task': {  # 任务键名
        'name': '新任务名称',
        'script': 'pdd_new_task.py',  # 脚本文件名
        'status_field': 'new_task_status',  # 数据库状态字段名
        'schedule': 'daily',  # daily/weekly/monthly
        'date_offset': -1,  # T-1（昨天）
        'minio_path': 'ods/pdd/pdd_new_task',  # MinIO路径
        'dremio_table': 'minio.warehouse.ods.pdd.pdd_new_task',  # Dremio表名
        'enabled': True  # 是否启用
    }
}
```

### 步骤2：在数据库中添加状态字段

```sql
ALTER TABLE pdd_tasks ADD COLUMN new_task_status VARCHAR(20) DEFAULT NULL;
```

### 步骤3：创建爬虫脚本

```python
# -*- coding: utf-8 -*-
"""新任务数据采集"""
import sys
sys.path.append(r'D:\testyd\pdd')

from base_crawler import BaseCrawler
from crawler_config import CRAWLER_TASKS
from datetime import datetime, timedelta

class NewTaskCrawler(BaseCrawler):
    """新任务爬虫"""
    
    def __init__(self):
        task_config = CRAWLER_TASKS['new_task']
        super().__init__('new_task', task_config)
        
        # 设置目标日期
        offset = task_config.get('date_offset', -1)
        self.target_date = (datetime.now() + timedelta(days=offset)).strftime('%Y-%m-%d')
    
    def process_shop(self, shop_name, cookie, **kwargs):
        """
        处理单个店铺的数据采集
        
        Args:
            shop_name: 店铺名称
            cookie: 店铺Cookie
        
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            # 1. 调用API获取数据
            data = self.fetch_data(cookie)
            
            # 2. 保存到Excel
            save_path = self.save_to_excel(data, shop_name)
            
            return save_path
        except Exception as e:
            print(f'[错误] {shop_name} 数据采集失败: {e}')
            return None
    
    def fetch_data(self, cookie):
        """获取数据（实现具体的API调用逻辑）"""
        # TODO: 实现数据获取逻辑
        pass
    
    def save_to_excel(self, data, shop_name):
        """保存数据到Excel"""
        # TODO: 实现数据保存逻辑
        pass

if __name__ == '__main__':
    crawler = NewTaskCrawler()
    crawler.run()
```

### 步骤4：测试新爬虫

```bash
# 1. 生成任务
python testyd/pdd/generate_tasks.py --schedule daily --date 2025-10-02

# 2. 执行爬虫
python testyd/pdd/pdd_new_task.py

# 3. 检查状态
python testyd/check_task_status.py
```

## 🔧 配置说明

### 调度类型（schedule）

- **daily** - 每日执行
- **weekly** - 每周执行
- **monthly** - 每月执行

### 日期偏移（date_offset）

- `-1` - T-1（昨天）
- `-3` - T-3（3天前）
- 其他负数 - 相应天数前

### 日期范围（date_range）

用于周度和月度任务：
- 周度：`(-9, -3)` 表示 T-9 到 T-3（7天）
- 月度：`'last_month'` 表示上个月

## 📊 数据库设计

### pdd_shops 表

存储店铺信息，包括：
- `shop_name` - 店铺名称（主键）
- `cookie` - 店铺Cookie（索引11）
- 其他店铺信息...

### pdd_tasks 表

存储任务记录，包括：
- `time_period` - 时间周期（主键之一）
- `shop_name` - 店铺名称（主键之一）
- `badsscore_status` - 差评数据状态
- `quality_status` - 产品质量状态
- `kpi_days_status` - 客服绩效（日度）状态
- `kpi_weekly_status` - 客服绩效（周度）状态
- `kpi_monthly_status` - 客服绩效（月度）状态

**联合主键：** `(time_period, shop_name)`

## 🎯 核心优势

### 1. 配置驱动

所有爬虫配置集中管理，修改配置无需改动代码。

### 2. 任务独立

不同任务类型可以独立执行，互不影响：
- 日度任务每天执行
- 周度任务每周执行
- 月度任务每月执行

### 3. 状态管理

- **空值（NULL）** - 没有任务
- **"待执行"** - 需要执行
- **"已完成"** - 已完成

失败的任务保持"待执行"状态，方便重试。

### 4. 易于扩展

新增爬虫只需3步：
1. 添加配置
2. 添加数据库字段
3. 创建爬虫脚本（继承BaseCrawler）

### 5. 代码复用

BaseCrawler提供通用功能：
- 任务获取
- 状态更新
- 文件合并
- MinIO上传
- Dremio刷新

## 🔍 故障排查

### 问题1：任务生成失败

检查：
1. 数据库连接是否正常
2. 状态字段是否存在于 pdd_tasks 表中
3. 配置文件中的 status_field 是否正确

### 问题2：爬虫执行失败

检查：
1. 任务是否已生成（状态为"待执行"）
2. Cookie是否有效
3. API是否正常响应

### 问题3：文件合并失败

检查：
1. 文件路径是否正确
2. Excel文件是否损坏
3. 磁盘空间是否充足

## 📝 最佳实践

1. **每天最先执行任务生成器**
   ```bash
   python testyd/pdd/generate_tasks.py --schedule daily
   ```

2. **按顺序执行爬虫程序**
   ```bash
   python testyd/pdd/pdd_badscore.py
   python testyd/pdd/pdd_quality.py
   python testyd/pdd/pdd_kpi.py
   ```

3. **定期检查任务状态**
   ```bash
   python testyd/check_task_status.py
   ```

4. **失败任务重新执行**
   - 不需要重新生成任务
   - 直接重新执行对应的爬虫程序即可

## 🎉 总结

新架构通过配置驱动和基类复用，大大简化了爬虫开发流程。新增爬虫只需：

1. 在配置文件中添加几行配置
2. 在数据库中添加一个字段
3. 创建一个继承BaseCrawler的脚本

无需修改任务生成器、数据库接口等核心代码，实现了真正的"即插即用"！

