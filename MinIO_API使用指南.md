# MinIO API 数据上传服务使用指南

## 服务信息
- **服务名称**: `minio-api`
- **外部访问地址**: `http://127.0.0.1:8009` (推荐)
- **容器内部端口**: `8009`
- **主机映射端口**: `8009`
- **数据格式支持**: JSON、二维列表、Parquet、CSV

### ⚠️ 重要网络连接说明
由于Docker Desktop的网络代理机制，在某些环境下使用 `localhost:8009` 可能会出现404错误。**强烈推荐使用 `127.0.0.1:8009` 进行外部测试**，这样可以避免网络解析问题。

- ✅ **推荐**: `http://127.0.0.1:8009` - 稳定可靠的本地回环地址
- 🔧 **容器内**: `http://minio-api:8009` - 其他容器内服务使用

## 核心API接口

### 1. 健康检查
- **URL**: `/api/health`
- **方法**: GET
- **功能**: 检查服务状态和MinIO连接
- **支持参数**: `bucket` (可选) - 指定要检查的存储桶名称
- **Bash/Curl使用示例**:
```bash
# 检查API服务状态
curl -X GET http://127.0.0.1:8009/api/health

# 检查指定存储桶的连接状态
curl -X GET "http://127.0.0.1:8009/api/health?bucket=my-custom-bucket"

# 在Docker容器内执行
docker exec minio-api curl -X GET http://127.0.0.1:8009/api/health

# 带详细输出的健康检查
curl -v http://127.0.0.1:8009/api/health
```

- **成功响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-20T09:43:37.658875",
  "minio_connection": {
    "success": true,
    "message": "MinIO连接正常",
    "endpoint": "minio:9000",
    "bucket": "warehouse"
  }
}
```

### 2. MinIO连接测试
- **URL**: `/api/test`
- **方法**: GET
- **功能**: 专门测试MinIO连接状态
- **Bash/Curl使用示例**:
```bash
# 测试MinIO连接
curl -X GET http://127.0.0.1:8009/api/test

# 在Docker容器内执行
docker exec minio-api curl -X GET http://127.0.0.1:8009/api/test
```

### 3. 存储桶管理
- **URL**: `/api/buckets`
- **方法**: GET
- **功能**: 列出所有可用的存储桶
- **URL**: `/api/buckets`
- **方法**: POST
- **功能**: 创建新的存储桶
- **请求体**: `{"bucket": "new-bucket-name"}`

**使用示例**:
```bash
# 列出所有存储桶
curl -X GET http://127.0.0.1:8009/api/buckets

# 创建新存储桶
curl -X POST http://127.0.0.1:8009/api/buckets \
  -H "Content-Type: application/json" \
  -d '{"bucket": "my-new-bucket"}'
```

### 4. JSON数据上传转CSV
- **URL**: `/api/upload/json`
- **方法**: POST
- **功能**: 将JSON数据转换为CSV格式并上传到MinIO
- **请求体**:
```json
{
  "data": [
    {"name": "张三", "age": 25, "city": "北京"},
    {"name": "李四", "age": 30, "city": "上海"}
  ],
  "target_path": "uploads/user_data.csv"
}
```

- **Bash/Curl使用示例**:
```bash
# 上传JSON数据转CSV
curl -X POST http://127.0.0.1:8009/api/upload/json \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"name": "张三", "age": 25, "city": "北京"},
      {"name": "李四", "age": 30, "city": "上海"}
    ],
    "target_path": "uploads/user_data.csv"
  }'

# 上传单个JSON对象
curl -X POST http://127.0.0.1:8009/api/upload/json \
  -H "Content-Type: application/json" \
  -d '{
    "data": {"product": "iPhone", "price": 999, "category": "电子产品"},
    "target_path": "products/single_product.csv"
  }'

# 在Docker容器内执行
docker exec minio-api curl -X POST http://127.0.0.1:8009/api/upload/json \
  -H "Content-Type: application/json" \
  -d '{
    "data": [{"test": "data"}],
    "target_path": "test/test_data.csv"
  }'
```

### 5. 列表数据上传转CSV
- **URL**: `/api/upload/list`
- **方法**: POST
- **功能**: 将二维列表数据转换为CSV格式并上传到MinIO
- **请求体**:
```json
{
  "data": [
    ["姓名", "年龄", "城市"],
    ["张三", 25, "北京"],
    ["李四", 30, "上海"]
  ],
  "target_path": "uploads/list_data.csv"
}
```

- **Bash/Curl使用示例**:
```bash
# 上传列表数据转CSV
curl -X POST http://127.0.0.1:8009/api/upload/list \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      ["产品名称", "价格", "类别"],
      ["iPhone", 999, "电子产品"],
      ["MacBook", 1999, "电子产品"]
    ],
    "target_path": "products/product_list.csv"
  }'

# PowerShell使用示例
$body = @{
  data = @(
    @("姓名", "年龄", "城市"),
    @("张三", 25, "北京"),
    @("李四", 30, "上海")
  )
  target_path = "uploads/powershell_data.csv"
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri 'http://127.0.0.1:8009/api/upload/list' -Method POST -Body $body -ContentType 'application/json'
```

### 5. Parquet格式数据上传
- **URL**: `/api/upload/parquet`
- **方法**: POST
- **功能**: 将数据转换为Parquet格式并上传到MinIO
- **请求体**:
```json
{
  "data": [
    {"id": 1, "name": "产品A", "price": 100.5},
    {"id": 2, "name": "产品B", "price": 200.0}
  ],
  "target_path": "warehouse/products.parquet",
  "columns": ["id", "name", "price"]
}
```

- **Bash/Curl使用示例**:
```bash
# 上传Parquet格式数据
curl -X POST http://127.0.0.1:8009/api/upload/parquet \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"id": 1, "name": "产品A", "price": 100.5},
      {"id": 2, "name": "产品B", "price": 200.0}
    ],
    "target_path": "warehouse/products.parquet"
  }'

# 指定列顺序的Parquet上传
curl -X POST http://127.0.0.1:8009/api/upload/parquet \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"price": 100.5, "name": "产品A", "id": 1},
      {"price": 200.0, "name": "产品B", "id": 2}
    ],
    "target_path": "warehouse/ordered_products.parquet",
    "columns": ["id", "name", "price"]
  }'
```

### 6. 通用数据上传接口
- **URL**: `/api/upload`
- **方法**: POST
- **功能**: 支持指定格式的通用上传接口
- **请求体**:
### 5. 通用数据上传接口 ⭐ (推荐)
- **URL**: `/api/upload`
- **方法**: POST
- **功能**: 统一的数据上传接口，支持多种数据格式和输出格式
- **支持的数据类型**:
  - 字典列表 (推荐): `[{"name": "张三", "age": 25}, {"name": "李四", "age": 30}]`
  - 二维列表: `[["name", "age"], ["张三", 25], ["李四", 30]]` (第一行自动作为列名)
  - 一维列表: `["value1", "value2", "value3"]`
  - JSON对象: `{"key": "value"}`
- **支持的输出格式**: `parquet` (推荐), `json`
- **支持自定义存储桶**: 通过 `bucket` 参数指定

#### 请求体参数
- `data` (必需): 要上传的数据
- `target_path` (必需): 目标文件路径
- `format` (必需): 输出格式 ("parquet" 或 "json")
- `columns` (可选): 自定义列名数组
- `bucket` (可选): 自定义存储桶名称，不指定则使用默认桶

#### ⚠️ 重要注意事项

##### 1. 二维列表列名处理
- **自动列名**: 二维列表的第一行会自动作为列名
- **中文列名支持**: 完全支持中文列名，自动处理编码问题
- **列名清理**: 自动移除特殊字符（如BOM、换行符、制表符）
- **唯一性保证**: 重复列名会自动添加后缀 `_1`, `_2` 等

```json
// 示例：二维列表自动使用第一行作为列名
{
  "data": [
    ["姓名", "年龄", "城市"],
    ["张三", 25, "北京"],
    ["李四", 30, "上海"]
  ],
  "target_path": "test/chinese_header.parquet",
  "format": "parquet"
}
```

##### 2. columns参数使用建议
- **字典列表**: ❌ 不建议指定 `columns`，会导致重复列名错误
- **二维列表**: ✅ 可以指定 `columns` 替换第一行作为列名
- **一维列表**: ✅ 可以指定 `columns` 替换默认的 "value" 列名

```json
// ❌ 错误用法：字典列表不要指定columns
{
  "data": [{"name": "张三"}, {"name": "李四"}],
  "columns": ["姓名"],  // 会导致重复列名错误
  "format": "parquet"
}

// ✅ 正确用法：二维列表可以指定columns
{
  "data": [["张三", 25], ["李四", 30]],
  "columns": ["姓名", "年龄"],
  "format": "parquet"
}
```

##### 3. 自定义存储桶
- 支持动态指定存储桶名称
- 存储桶不存在时会自动创建
- 存储桶名称必须符合MinIO命名规范（小写字母、数字、连字符）

```json
{
  "data": [["name", "age"], ["Alice", 25]],
  "target_path": "test/data.parquet",
  "format": "parquet",
  "bucket": "my-custom-bucket"
}
```

#### 使用示例

**PowerShell示例**:
```powershell
# 字典列表上传（推荐方式）
$data = @{
  data = @(
    @{name="张三"; age=25; city="北京"},
    @{name="李四"; age=30; city="上海"}
  )
  target_path = "users/data.parquet"
  format = "parquet"
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://127.0.0.1:8009/api/upload" -Method POST -Body $data -ContentType "application/json"

# 二维列表上传（第一行作为列名）
$data = @{
  data = @(
    @("姓名", "年龄", "城市"),
    @("张三", 25, "北京"),
    @("李四", 30, "上海")
  )
  target_path = "users/chinese_data.parquet"
  format = "parquet"
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://127.0.0.1:8009/api/upload" -Method POST -Body $data -ContentType "application/json"

# 自定义存储桶上传
$data = @{
  data = @(@("name", "score"), @("Alice", 95), @("Bob", 87))
  target_path = "test/scores.parquet"
  format = "parquet"
  bucket = "exam-results"
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://127.0.0.1:8009/api/upload" -Method POST -Body $data -ContentType "application/json"
```

**Curl示例**:
```bash
# 字典列表上传
curl -X POST http://127.0.0.1:8009/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"name": "张三", "age": 25, "city": "北京"},
      {"name": "李四", "age": 30, "city": "上海"}
    ],
    "target_path": "users/data.parquet",
    "format": "parquet"
  }'

# 二维列表上传（中文列名）
curl -X POST http://127.0.0.1:8009/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      ["姓名", "年龄", "城市"],
      ["张三", 25, "北京"],
      ["李四", 30, "上海"]
    ],
    "target_path": "users/chinese_data.parquet",
    "format": "parquet"
  }'

# JSON格式上传
curl -X POST http://127.0.0.1:8009/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"name": "张三", "score": 95},
      {"name": "李四", "score": 87}
    ],
    "target_path": "students/scores.json",
    "format": "json"
  }'
```

#### 成功响应示例
```json
{
  "success": true,
  "message": "Parquet文件上传成功: users/data.parquet",
  "target_path": "users/data.parquet",
  "data_format": "parquet",
  "file_size": 2269,
  "rows_count": 2,
  "columns_count": 3
}
```

## 环境配置

### 环境变量
服务支持以下环境变量配置：

```bash
# MinIO连接配置
MINIO_ENDPOINT=minio:9000          # MinIO服务地址
MINIO_ACCESS_KEY=admin             # 访问密钥
MINIO_SECRET_KEY=admin123          # 秘密密钥
MINIO_BUCKET=warehouse        # 存储桶名称

# 服务配置
FLASK_PORT=8009                    # 服务端口
HOST=0.0.0.0                       # 监听地址
```

### Docker Compose配置示例
```yaml
services:
  minio-api:
    build: ./上传minioapi
    container_name: minio-api
    ports:
      - "8009:8009"
    environment:
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=admin
      - MINIO_SECRET_KEY=admin123
      - MINIO_BUCKET=warehouse
      - FLASK_PORT=8009
    volumes:
      - ./上传minioapi/logs:/app/logs
    networks:
      - trae_data_network
    depends_on:
      - minio
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8009/api/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

## 数据格式支持

### 1. JSON格式
支持以下JSON数据结构：
- **对象数组**: `[{"key": "value"}, {"key": "value"}]`
- **单个对象**: `{"key": "value"}`
- **JSON字符串**: 自动解析JSON字符串

### 2. 列表格式
支持二维列表数据：
- **带表头**: `[["列1", "列2"], ["值1", "值2"]]`
- **纯数据**: `[["值1", "值2"], ["值3", "值4"]]`

### 3. 输出格式
- **CSV**: 逗号分隔值，UTF-8编码
- **Parquet**: 高效的列式存储格式
- **JSON**: 原始JSON格式保存

## 使用场景

### 1. 数据ETL流程
```bash
# 1. 从外部系统获取JSON数据
# 2. 转换并上传到MinIO
curl -X POST http://127.0.0.1:8009/api/upload/json \
  -H "Content-Type: application/json" \
  -d '{
    "data": '$(cat external_data.json)',
    "target_path": "etl/processed_data.csv"
  }'
```

### 2. 批量数据处理
```bash
# 处理Excel导出的CSV数据
curl -X POST http://127.0.0.1:8009/api/upload/list \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      ["订单号", "客户", "金额"],
      ["001", "客户A", 1000],
      ["002", "客户B", 2000]
    ],
    "target_path": "orders/daily_orders.csv"
  }'
```

### 3. 数据仓库集成
```bash
# 上传到数据仓库分区
curl -X POST http://127.0.0.1:8009/api/upload/parquet \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"date": "2025-09-20", "sales": 10000, "region": "华北"},
      {"date": "2025-09-20", "sales": 15000, "region": "华东"}
    ],
    "target_path": "warehouse/sales/year=2025/month=09/day=20/sales.parquet"
  }'
```

## 响应格式

### 成功响应
```json
{
  "success": true,
  "message": "数据上传成功",
  "bucket": "warehouse",
  "object_path": "uploads/data.csv",
  "file_size": 1258,
  "upload_time": "2025-09-20T09:44:03.123456",
  "data_format": "csv"
}
```

### 错误响应
```json
{
  "success": false,
  "error": "数据字段不能为空"
}
```

## 性能优化

### 1. 数据大小建议
- **小数据集** (<1MB): 直接上传
- **中等数据集** (1-10MB): 使用Parquet格式
- **大数据集** (>10MB): 分批上传

### 2. 格式选择建议
- **分析查询**: 使用Parquet格式
- **数据交换**: 使用CSV格式
- **原始存储**: 使用JSON格式

### 3. 路径规划
```
warehouse/
├── raw/           # 原始数据
├── processed/     # 处理后数据
├── analytics/     # 分析数据
└── exports/       # 导出数据
```

## 监控与调试

### 1. 健康检查
```bash
# 定期检查服务状态
curl -s http://127.0.0.1:8009/api/health | jq .status
```

### 2. 日志查看
```bash
# 查看服务日志
docker logs --tail 50 -f minio-api

# 查看应用日志
docker exec minio-api tail -f /app/logs/minio_api.log
```

### 3. 性能监控
```bash
# 检查容器资源使用
docker stats minio-api

# 测试上传性能
time curl -X POST http://127.0.0.1:8009/api/upload/json \
  -H "Content-Type: application/json" \
  -d '{"data": [{"test": "data"}], "target_path": "test/perf_test.csv"}'
```

## 错误处理

### 常见错误及解决方案

**1. 连接错误**
```json
{
  "success": false,
  "error": "MinIO连接失败: Connection refused"
}
```
解决方案：检查MinIO服务状态和网络连接

**2. 数据格式错误**
```json
{
  "success": false,
  "error": "无效的JSON字符串"
}
```
解决方案：验证JSON数据格式正确性

**3. 存储桶错误**
```json
{
  "success": false,
  "error": "存储桶操作失败"
}
```
解决方案：检查MinIO权限和存储桶配置

## 最佳实践

### 1. 数据验证
- 上传前验证数据格式
- 检查必要字段完整性
- 处理特殊字符和编码

### 2. 路径管理
- 使用有意义的路径结构
- 包含时间戳避免冲突
- 遵循数据分区规范

### 3. 错误处理
- 实现重试机制
- 记录详细错误日志
- 提供用户友好的错误信息

### 4. 安全考虑
- 验证上传数据大小
- 限制文件路径访问
- 使用安全的连接配置

## 集成示例

### Python客户端示例
```python
import requests
import json

def upload_json_data(data, target_path):
    """上传JSON数据到MinIO"""
    url = "http://127.0.0.1:8009/api/upload/json"
    payload = {
        "data": data,
        "target_path": target_path
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# 使用示例
data = [
    {"name": "张三", "age": 25},
    {"name": "李四", "age": 30}
]
result = upload_json_data(data, "users/user_data.csv")
print(result)
```

### JavaScript客户端示例
```javascript
async function uploadJsonData(data, targetPath) {
    const response = await fetch('http://127.0.0.1:8009/api/upload/json', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            data: data,
            target_path: targetPath
        })
    });
    
    return await response.json();
}

// 使用示例
const data = [
    {name: "张三", age: 25},
    {name: "李四", age: 30}
];

uploadJsonData(data, "users/user_data.csv")
    .then(result => console.log(result));
```

## 注意事项

### 1. 二维列表数据处理
- **列名处理**: 当使用二维列表时，第一行会自动作为列名
- **中文列名**: 支持中文列名，系统会自动处理编码问题
- **重复列名**: 如果存在重复列名，系统会自动添加数字后缀（如：列名_1, 列名_2）
- **特殊字符**: 列名中的特殊字符会被清理，确保兼容性

### 2. 自定义存储桶支持
- **默认存储桶**: 如不指定，使用环境变量配置的默认存储桶
- **自定义存储桶**: 在请求中添加 `bucket` 参数可指定目标存储桶
- **存储桶创建**: 如果指定的存储桶不存在，系统会自动创建
- **权限检查**: 确保MinIO用户有相应存储桶的读写权限

### 3. 数据格式注意点

#### JSON格式
- **编码要求**: 所有文本数据使用UTF-8编码
- **数据类型**: 支持字符串、数字、布尔值、null值
- **嵌套对象**: 复杂嵌套对象会被展平处理
- **数组字段**: 数组类型字段会转换为字符串表示

#### 列表格式
- **数据一致性**: 每行数据长度应保持一致
- **类型混合**: 支持同一列中的不同数据类型
- **空值处理**: 空值会保留为空字符串或NaN
- **第一行作为列名**: 强烈建议第一行包含有意义的列名

#### Parquet格式
- **性能优势**: 适合大数据量和分析查询
- **类型推断**: 自动推断数据类型，提高存储效率
- **压缩支持**: 内置压缩，减少存储空间
- **列名限制**: 列名必须符合Parquet规范

### 4. 通用上传接口使用建议
- **columns参数**: 当数据不包含列名时，建议使用columns参数指定
- **format参数**: 根据使用场景选择合适的输出格式
- **target_path**: 使用有意义的路径结构，便于数据管理
- **bucket**: 根据数据类型和用途选择合适的存储桶

### 5. 其他重要注意事项
- **文件覆盖**: 同名文件会被自动覆盖
- **路径创建**: 不存在的路径会自动创建
- **数据大小**: 建议单次上传不超过100MB
- **并发限制**: 避免同时大量并发上传请求
- **网络超时**: 大文件上传可能需要调整超时设置

## 版本信息

- **当前版本**: 1.0.0
- **Python版本**: 3.11+
- **Flask版本**: 3.1.2
- **MinIO客户端**: 7.2.0
- **Pandas版本**: 2.1.1

---

*本文档基于MinIO API服务 v1.0.0 编写，如有问题请查看服务日志或联系技术支持。*