# Excel文件合并工具使用说明

## 功能介绍
这个工具可以将指定文件夹中的所有Excel文件合并成一个大文件，并将原文件名作为新的"shop"列添加到数据中。

## 安装依赖
```bash
pip install -r requirements_merge.txt
```

## 使用方法

### 1. 交互式模式（推荐新手使用）
直接运行脚本，按提示输入参数：
```bash
python merge_excel_files.py
```

### 2. 命令行模式
```bash
# 基本用法
python merge_excel_files.py "文件夹路径"

# 指定输出文件名
python merge_excel_files.py "文件夹路径" -o "自定义文件名.xlsx"

# 显示文件摘要信息
python merge_excel_files.py "文件夹路径" -s

# 完整示例
python merge_excel_files.py "d:/pdd/文件存档/2025-09-12" -o "合并数据_20250912.xlsx" -s
```

## 参数说明
- `folder_path`: 包含Excel文件的文件夹路径（必需）
- `-o, --output`: 输出文件名（可选，默认：merged_data.xlsx）
- `-s, --summary`: 显示文件摘要信息（可选）

## 支持的文件格式
- .xlsx (Excel 2007+)
- .xls (Excel 97-2003)
- .xlsm (Excel宏文件)

## 输出结果
- 合并后的Excel文件将保存在指定的文件夹中
- 新增"shop"列，包含原文件名（不含扩展名）
- "shop"列会自动移到第一列
- 生成日志文件 `merge_excel.log` 记录处理过程

## 使用示例

### 示例1：合并PDD文件存档
```bash
python merge_excel_files.py "d:/pdd/文件存档/2025-09-12" -o "pdd_data_20250912.xlsx"
```

### 示例2：合并客服绩效文件
```bash
python merge_excel_files.py "d:/pdd/客服绩效文件存档/2025-09-14" -o "客服绩效_20250914.xlsx" -s
```

## 注意事项
1. 确保文件夹路径正确且存在
2. 确保有足够的磁盘空间存储合并后的文件
3. 如果Excel文件很大，合并过程可能需要一些时间
4. 程序会自动处理不同Excel文件的列结构差异
5. 如果某个文件读取失败，程序会跳过该文件并继续处理其他文件

## 错误处理
- 文件读取失败：跳过该文件，记录错误日志
- 文件夹不存在：程序退出并提示错误
- 内存不足：建议分批处理大文件

## 日志文件
程序运行时会生成 `merge_excel.log` 日志文件，包含：
- 处理进度信息
- 成功读取的文件数量和行数
- 错误信息和警告
- 最终合并结果统计

## 输出文件结构
合并后的Excel文件结构：
```
shop | 原列1 | 原列2 | ... | 原列N
-----|-------|-------|-----|-------
文件名1 | 数据 | 数据 | ... | 数据
文件名2 | 数据 | 数据 | ... | 数据
...
```