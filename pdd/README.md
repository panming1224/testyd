# 拼多多爬虫任务集合

## 项目概述

本目录包含拼多多平台的各类爬虫任务，所有任务已统一使用数据库接口进行任务管理和状态跟踪。

## 文件列表

### 1. pdd_badscore.py - 差评数据采集
**功能**：采集拼多多店铺的差评数据

**数据源**：`https://mms.pinduoduo.com/saturn/reviews/list`

**任务类型**：`badscore_status`

**输出目录**：
- 原始文件：`D:/pdd/评价文件存档/{日期}/`
- 合并文件：`D:/pdd/合并文件/评价文件存档/`

**MinIO路径**：`ods/pdd/pdd_badscore/dt={日期}/`

**Dremio表**：`minio.warehouse.ods.pdd.pdd_badscore`

**运行方式**：
```bash
python D:\testyd\pdd\pdd_badscore.py
```

**数据字段**：
- descScore: 用户评价分
- comment: 用户评论
- orderSn: 订单编号
- name: 卖家昵称
- goodsId: 商品ID
- goodsInfoUrl: 商品页链接
- Picture_1, Picture_2, ...: 评价图片

---

### 2. pdd_quality.py - 产品质量体验数据采集
**功能**：采集拼多多店铺的产品质量体验数据

**数据源**：`https://mms.pinduoduo.com/api/price/mariana/quality_experience/goods_list`

**任务类型**：`quality_status`

**输出目录**：
- 原始文件：`D:/pdd/产品质量体验存档/{日期}/`
- 合并文件：`D:/pdd/合并文件/产品质量体验存档/`

**MinIO路径**：`ods/pdd/pdd_quality/dt={日期}/`

**Dremio表**：`minio.warehouse.ods.pdd.pdd_quality`

**运行方式**：
```bash
python D:\testyd\pdd\pdd_quality.py
```

**数据字段**：
- 商品id
- 商品名称
- 商品主图链接
- 商品质量体验排名
- 近30天异常订单数
- 异常订单占比
- 权益状态
- 商品质量等级
- 近30天品质求助平台率
- 近30天商品评价分排名
- 老客订单占比

---

### 3. pdd_kpi.py - 客服绩效数据采集（日度）
**功能**：采集拼多多店铺的客服绩效数据（T-3日）

**数据源**：`https://mms.pinduoduo.com/chats/csReportDetail/download`

**任务类型**：`kpi_status`

**输出目录**：
- 原始文件：`D:/pdd/客服绩效文件存档/{日期}/`
- 合并文件：`D:/pdd/合并文件/客服绩效文件存档/`

**MinIO路径**：`ods/pdd/pdd_kpi/dt={日期}/`

**Dremio表**：`minio.warehouse.ods.pdd.pdd_kpi`

**运行方式**：
```bash
python D:\testyd\pdd\pdd_kpi.py
```

**说明**：采集T-3日的数据（3天前的数据）

---

### 4. pdd_kpi_weekly.py - 客服绩效数据采集（周度）
**功能**：采集拼多多店铺的客服绩效数据（周度汇总）

**数据源**：`https://mms.pinduoduo.com/chats/csReportDetail/download`

**任务类型**：`kpi_weekly_status`

**输出目录**：
- 原始文件：`D:/pdd/客服绩效文件存档周度/{日期范围}/`
- 合并文件：`D:/pdd/合并文件/客服绩效文件存档周度/`

**MinIO路径**：`ods/pdd/pdd_kpi_weekly/dt={日期范围}/`

**Dremio表**：`minio.warehouse.ods.pdd.pdd_kpi_weekly`

**运行方式**：
```bash
python D:\testyd\pdd\pdd_kpi_weekly.py
```

**说明**：采集T-9至T-3的7天数据

---

### 5. pdd_kpi_monthly.py - 客服绩效数据采集（月度）
**功能**：采集拼多多店铺的客服绩效数据（月度汇总）

**数据源**：`https://mms.pinduoduo.com/chats/csReportDetail/download`

**任务类型**：`kpi_monthly_status`

**输出目录**：
- 原始文件：`D:/pdd/客服绩效文件存档月度/{日期范围}/`
- 合并文件：`D:/pdd/合并文件/客服绩效文件存档月度/`

**MinIO路径**：`ods/pdd/pdd_kpi_monthly/dt={日期范围}/`

**Dremio表**：`minio.warehouse.ods.pdd.pdd_kpi_monthly`

**运行方式**：
```bash
python D:\testyd\pdd\pdd_kpi_monthly.py
```

**说明**：采集上个月的完整数据

---

## 数据库表结构

### pdd_shops 表
存储拼多多店铺信息

**主要字段**：
- `shop_name`: 店铺名称（主键）
- `cookie`: 店铺Cookie
- `create_time`: 创建时间
- `update_time`: 更新时间

### pdd_tasks 表
存储拼多多任务状态

**主要字段**：
- `time_period`: 时间周期（主键之一）
- `shop_name`: 店铺名称（主键之一）
- `badscore_status`: 差评任务状态
- `quality_status`: 产品质量任务状态
- `kpi_status`: 客服绩效任务状态（日度）
- `kpi_weekly_status`: 客服绩效任务状态（周度）
- `kpi_monthly_status`: 客服绩效任务状态（月度）
- `create_time`: 创建时间
- `update_time`: 更新时间

**任务状态说明**：
- `NULL` 或空：待执行
- `已完成`：执行成功

---

## 工作流程

### 1. 任务生成
```python
# 为所有店铺生成当日任务
db_interface.generate_tasks(time_period, task_columns)
```

### 2. 获取待处理任务
```python
# 获取待处理的任务列表
pending_tasks = db_interface.get_pending_tasks(time_period, task_column)
```

### 3. 执行任务
```python
for task in pending_tasks:
    shop_name = task[1]
    cookie = task[3]
    
    try:
        # 获取数据
        data = fetch_data(cookie, shop_name)
        
        # 保存数据
        save_to_excel(data, shop_name)
        
        # 更新状态为已完成
        db_interface.update_task_status(time_period, shop_name, task_column, '已完成')
    except Exception as e:
        # 失败时不更新状态，保持待执行
        print(f'失败：{e}')
```

### 4. 合并文件
```python
# 合并所有店铺的Excel文件
merger = ExcelMerger(source_dir, output_dir=target_dir)
merger.merge_excel_files(output_filename)
```

### 5. 上传MinIO
```python
# 上传合并后的文件到MinIO（转换为Parquet格式）
upload_to_minio(file_path, minio_path, date_str)
```

### 6. 刷新Dremio
```python
# 刷新Dremio数据集和反射
refresh_dremio(dataset_path)
```

---

## 依赖模块

### 核心依赖
- `crawler_db_interface.py`: 数据库接口
- `merge_excel_files.py`: Excel文件合并工具

### Python包
- pandas
- requests
- openpyxl
- pymysql
- dbutils

---

## 配置说明

### 数据库配置
```python
db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'admin123',
    'database': 'company',
    'charset': 'utf8mb4'
}
```

### MinIO配置
```python
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"
```

### Dremio配置
```python
DREMIO_API_URL = "http://localhost:8003/api"
```

---

## 注意事项

1. **Cookie管理**
   - Cookie需要定期更新
   - Cookie失效会导致数据获取失败

2. **任务状态**
   - 创建任务时状态为 `待执行`（NULL）
   - 成功后更新为 `已完成`
   - 失败时不更新状态，保持 `待执行`，便于重试

3. **数据时效性**
   - 差评数据：T-1日（昨天）
   - 产品质量：当天
   - 客服绩效（日度）：T-3日（3天前）
   - 客服绩效（周度）：T-9至T-3（7天）
   - 客服绩效（月度）：上个月

4. **错误处理**
   - 单个店铺失败不影响其他店铺
   - 失败的任务保持待执行状态，可重新运行

---

## 相关文档

- [爬虫通用模板使用指南](../爬虫通用模板使用指南.md)
- [数据库接口文档](../mysql/README_简化MySQL方案.md)

---

## 维护记录

- 2025-10-03: 统一使用数据库接口，移除Excel状态管理
- 2025-10-03: 添加任务状态管理规则
- 2025-10-03: 完善文档说明

