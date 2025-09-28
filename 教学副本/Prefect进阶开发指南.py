#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prefect 进阶开发指南
===================

本文件包含了 Prefect 的进阶用法和实际应用场景，
涵盖了复杂的数据处理流程、错误处理、并行执行等高级特性。

作者: AI Assistant
日期: 2024-01-01
版本: 1.0
"""

import asyncio
import json
import logging
import os
import pandas as pd
import requests
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from prefect import flow, task, get_run_logger
from prefect.blocks.system import Secret
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from prefect.task_runners import ConcurrentTaskRunner, SequentialTaskRunner
from prefect.artifacts import create_markdown_artifact
from prefect.results import PersistedResult
from prefect.filesystems import LocalFileSystem

# =============================================================================
# 📊 数据处理任务集合
# =============================================================================

@task(name="数据库连接", description="建立数据库连接", retries=3, retry_delay_seconds=5)
def connect_database(db_path: str = "data/warehouse.db") -> sqlite3.Connection:
    """建立数据库连接"""
    logger = get_run_logger()
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 建立连接
        conn = sqlite3.connect(db_path)
        logger.info(f"✅ 成功连接数据库: {db_path}")
        
        # 创建基础表结构
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                sales_amount REAL NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_sales REAL NOT NULL,
                total_quantity INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        return conn
        
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {str(e)}")
        raise

@task(name="API数据拉取", description="从API获取数据", retries=2, retry_delay_seconds=10)
def fetch_api_data(api_url: str, headers: Optional[Dict] = None) -> List[Dict]:
    """从API获取数据"""
    logger = get_run_logger()
    
    try:
        # 模拟API调用
        if "mock" in api_url:
            # 生成模拟数据
            mock_data = []
            for i in range(100):
                mock_data.append({
                    "id": i + 1,
                    "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                    "product_name": f"产品_{i % 10 + 1}",
                    "category": ["电子产品", "服装", "食品", "家居"][i % 4],
                    "sales_amount": round(100 + (i * 10.5), 2),
                    "quantity": i % 20 + 1
                })
            
            logger.info(f"✅ 成功获取模拟数据: {len(mock_data)} 条记录")
            return mock_data
        
        # 实际API调用
        response = requests.get(api_url, headers=headers or {}, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"✅ 成功获取API数据: {len(data)} 条记录")
        return data
        
    except requests.RequestException as e:
        logger.error(f"❌ API请求失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ 数据获取失败: {str(e)}")
        raise

@task(name="数据清洗", description="清洗和验证数据", retries=1)
def clean_data(raw_data: List[Dict]) -> pd.DataFrame:
    """清洗和验证数据"""
    logger = get_run_logger()
    
    try:
        # 转换为DataFrame
        df = pd.DataFrame(raw_data)
        logger.info(f"📊 原始数据行数: {len(df)}")
        
        # 数据清洗步骤
        initial_count = len(df)
        
        # 1. 删除重复记录
        df = df.drop_duplicates()
        logger.info(f"🧹 删除重复记录: {initial_count - len(df)} 条")
        
        # 2. 处理缺失值
        df = df.dropna(subset=['product_name', 'sales_amount'])
        logger.info(f"🧹 删除缺失值记录: {initial_count - len(df)} 条")
        
        # 3. 数据类型转换
        df['date'] = pd.to_datetime(df['date'])
        df['sales_amount'] = pd.to_numeric(df['sales_amount'], errors='coerce')
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        
        # 4. 数据验证
        df = df[df['sales_amount'] > 0]
        df = df[df['quantity'] > 0]
        
        # 5. 异常值处理
        Q1 = df['sales_amount'].quantile(0.25)
        Q3 = df['sales_amount'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers_count = len(df[(df['sales_amount'] < lower_bound) | (df['sales_amount'] > upper_bound)])
        df = df[(df['sales_amount'] >= lower_bound) & (df['sales_amount'] <= upper_bound)]
        
        logger.info(f"🧹 删除异常值: {outliers_count} 条")
        logger.info(f"✅ 数据清洗完成，最终数据行数: {len(df)}")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ 数据清洗失败: {str(e)}")
        raise

@task(name="数据转换", description="数据转换和聚合", retries=1)
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """数据转换和聚合"""
    logger = get_run_logger()
    
    try:
        # 按日期聚合数据
        daily_summary = df.groupby(df['date'].dt.date).agg({
            'sales_amount': ['sum', 'mean', 'count'],
            'quantity': 'sum'
        }).round(2)
        
        # 重命名列
        daily_summary.columns = ['total_sales', 'avg_sales', 'transaction_count', 'total_quantity']
        daily_summary = daily_summary.reset_index()
        daily_summary['date'] = daily_summary['date'].astype(str)
        
        # 计算平均价格
        daily_summary['avg_price'] = (daily_summary['total_sales'] / daily_summary['total_quantity']).round(2)
        
        logger.info(f"✅ 数据转换完成，聚合后数据行数: {len(daily_summary)}")
        
        return daily_summary
        
    except Exception as e:
        logger.error(f"❌ 数据转换失败: {str(e)}")
        raise

@task(name="数据存储", description="将数据存储到数据库", retries=2)
def store_data(conn: sqlite3.Connection, df: pd.DataFrame, table_name: str = "processed_data") -> int:
    """将数据存储到数据库"""
    logger = get_run_logger()
    
    try:
        # 存储数据
        rows_affected = df.to_sql(table_name, conn, if_exists='append', index=False)
        conn.commit()
        
        logger.info(f"✅ 成功存储 {len(df)} 条记录到表 {table_name}")
        return len(df)
        
    except Exception as e:
        logger.error(f"❌ 数据存储失败: {str(e)}")
        raise
    finally:
        conn.close()

@task(name="生成报告", description="生成数据处理报告")
def generate_report(processed_count: int, start_time: datetime) -> str:
    """生成数据处理报告"""
    logger = get_run_logger()
    
    try:
        end_time = datetime.now()
        duration = end_time - start_time
        
        report = f"""
# 📊 数据处理报告

## 处理概要
- **开始时间**: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **结束时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
- **处理时长**: {duration.total_seconds():.2f} 秒
- **处理记录数**: {processed_count} 条

## 处理状态
✅ **成功完成**

## 下一步操作
- 数据已存储到数据库
- 可以进行进一步的分析和可视化
- 建议设置定期数据质量检查
        """
        
        # 创建 Prefect 报告工件
        create_markdown_artifact(
            key="data-processing-report",
            markdown=report,
            description="数据处理完成报告"
        )
        
        logger.info("✅ 报告生成完成")
        return report
        
    except Exception as e:
        logger.error(f"❌ 报告生成失败: {str(e)}")
        raise

# =============================================================================
# 🔄 并行处理任务
# =============================================================================

@task(name="并行数据处理", description="并行处理多个数据源")
async def parallel_data_processing(data_sources: List[str]) -> List[Dict]:
    """并行处理多个数据源"""
    logger = get_run_logger()
    
    async def process_single_source(source: str) -> Dict:
        """处理单个数据源"""
        await asyncio.sleep(2)  # 模拟处理时间
        
        return {
            "source": source,
            "status": "completed",
            "records": len(source) * 10,  # 模拟记录数
            "processed_at": datetime.now().isoformat()
        }
    
    try:
        # 并行处理所有数据源
        tasks = [process_single_source(source) for source in data_sources]
        results = await asyncio.gather(*tasks)
        
        logger.info(f"✅ 并行处理完成，处理了 {len(results)} 个数据源")
        return results
        
    except Exception as e:
        logger.error(f"❌ 并行处理失败: {str(e)}")
        raise

@task(name="批量文件处理", description="批量处理文件")
def batch_file_processing(file_patterns: List[str], output_dir: str = "output") -> List[str]:
    """批量处理文件"""
    logger = get_run_logger()
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        processed_files = []
        
        for pattern in file_patterns:
            # 模拟文件处理
            output_file = os.path.join(output_dir, f"processed_{pattern}.json")
            
            # 生成模拟处理结果
            result = {
                "input_pattern": pattern,
                "processed_at": datetime.now().isoformat(),
                "status": "success",
                "output_records": len(pattern) * 5
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            processed_files.append(output_file)
            logger.info(f"✅ 处理完成: {pattern} -> {output_file}")
        
        logger.info(f"✅ 批量处理完成，共处理 {len(processed_files)} 个文件")
        return processed_files
        
    except Exception as e:
        logger.error(f"❌ 批量处理失败: {str(e)}")
        raise

# =============================================================================
# 🌊 复杂数据流程
# =============================================================================

@flow(name="完整数据处理流程", description="端到端的数据处理流程", 
      task_runner=ConcurrentTaskRunner())
def complete_data_pipeline(
    api_url: str = "https://api.mock.com/data",
    db_path: str = "data/warehouse.db"
) -> str:
    """完整的数据处理流程"""
    logger = get_run_logger()
    start_time = datetime.now()
    
    logger.info("🚀 开始完整数据处理流程")
    
    try:
        # 1. 建立数据库连接
        conn = connect_database(db_path)
        
        # 2. 获取数据
        raw_data = fetch_api_data(api_url)
        
        # 3. 数据清洗
        clean_df = clean_data(raw_data)
        
        # 4. 数据转换
        transformed_df = transform_data(clean_df)
        
        # 5. 数据存储
        processed_count = store_data(conn, transformed_df)
        
        # 6. 生成报告
        report = generate_report(processed_count, start_time)
        
        logger.info("✅ 完整数据处理流程执行成功")
        return report
        
    except Exception as e:
        logger.error(f"❌ 数据处理流程失败: {str(e)}")
        raise

@flow(name="并行数据处理流程", description="并行处理多个数据源的流程",
      task_runner=ConcurrentTaskRunner())
async def parallel_processing_pipeline(
    data_sources: List[str] = None,
    file_patterns: List[str] = None
) -> Dict[str, Any]:
    """并行数据处理流程"""
    logger = get_run_logger()
    
    if data_sources is None:
        data_sources = ["source_1", "source_2", "source_3", "source_4"]
    
    if file_patterns is None:
        file_patterns = ["pattern_a", "pattern_b", "pattern_c"]
    
    logger.info("🚀 开始并行数据处理流程")
    
    try:
        # 并行执行多个任务
        data_results = await parallel_data_processing(data_sources)
        file_results = batch_file_processing(file_patterns)
        
        # 汇总结果
        summary = {
            "data_processing": {
                "sources_processed": len(data_results),
                "total_records": sum(result["records"] for result in data_results),
                "results": data_results
            },
            "file_processing": {
                "files_processed": len(file_results),
                "output_files": file_results
            },
            "completed_at": datetime.now().isoformat()
        }
        
        logger.info("✅ 并行数据处理流程执行成功")
        return summary
        
    except Exception as e:
        logger.error(f"❌ 并行处理流程失败: {str(e)}")
        raise

# =============================================================================
# 🔧 错误处理和重试机制
# =============================================================================

@task(name="容错任务", description="具有完善错误处理的任务", 
      retries=3, retry_delay_seconds=5)
def fault_tolerant_task(data: Any, fail_probability: float = 0.3) -> Dict[str, Any]:
    """具有容错机制的任务"""
    logger = get_run_logger()
    
    import random
    
    try:
        # 模拟随机失败
        if random.random() < fail_probability:
            raise Exception("模拟任务失败")
        
        # 处理数据
        result = {
            "input_data": str(data)[:100],  # 限制长度
            "processed_at": datetime.now().isoformat(),
            "status": "success",
            "processing_time": random.uniform(1, 5)
        }
        
        logger.info("✅ 容错任务执行成功")
        return result
        
    except Exception as e:
        logger.warning(f"⚠️ 任务执行失败，将重试: {str(e)}")
        raise

@flow(name="容错数据流程", description="具有完善错误处理的数据流程")
def fault_tolerant_pipeline(input_data: List[Any]) -> List[Dict[str, Any]]:
    """容错数据处理流程"""
    logger = get_run_logger()
    
    logger.info("🚀 开始容错数据处理流程")
    
    results = []
    failed_items = []
    
    for i, data in enumerate(input_data):
        try:
            result = fault_tolerant_task(data, fail_probability=0.2)
            results.append(result)
            logger.info(f"✅ 项目 {i+1} 处理成功")
            
        except Exception as e:
            logger.error(f"❌ 项目 {i+1} 处理失败: {str(e)}")
            failed_items.append({"index": i, "data": data, "error": str(e)})
    
    # 生成处理摘要
    summary = {
        "total_items": len(input_data),
        "successful_items": len(results),
        "failed_items": len(failed_items),
        "success_rate": len(results) / len(input_data) * 100,
        "results": results,
        "failures": failed_items
    }
    
    logger.info(f"✅ 容错流程完成，成功率: {summary['success_rate']:.1f}%")
    
    return summary

# =============================================================================
# 📈 监控和指标收集
# =============================================================================

@task(name="性能监控", description="收集性能指标")
def collect_performance_metrics() -> Dict[str, Any]:
    """收集性能指标"""
    logger = get_run_logger()
    
    try:
        import psutil
        
        # 系统指标
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            },
            "process": {
                "pid": os.getpid(),
                "memory_mb": psutil.Process().memory_info().rss / (1024**2)
            }
        }
        
        logger.info(f"📊 性能指标收集完成: CPU {cpu_percent}%, 内存 {memory.percent}%")
        return metrics
        
    except ImportError:
        logger.warning("⚠️ psutil 未安装，使用基础指标")
        return {
            "timestamp": datetime.now().isoformat(),
            "basic_metrics": {
                "pid": os.getpid(),
                "working_directory": os.getcwd()
            }
        }
    except Exception as e:
        logger.error(f"❌ 指标收集失败: {str(e)}")
        raise

@flow(name="监控数据流程", description="带监控的数据处理流程")
def monitored_data_pipeline(data_size: int = 1000) -> Dict[str, Any]:
    """带监控的数据处理流程"""
    logger = get_run_logger()
    
    logger.info("🚀 开始监控数据处理流程")
    
    # 收集开始时的性能指标
    start_metrics = collect_performance_metrics()
    start_time = time.time()
    
    try:
        # 模拟数据处理
        processed_data = []
        for i in range(data_size):
            processed_data.append({
                "id": i,
                "value": i * 2,
                "processed_at": datetime.now().isoformat()
            })
            
            # 每处理100条记录收集一次指标
            if (i + 1) % 100 == 0:
                current_metrics = collect_performance_metrics()
                logger.info(f"📊 已处理 {i+1}/{data_size} 条记录")
        
        # 收集结束时的性能指标
        end_metrics = collect_performance_metrics()
        end_time = time.time()
        
        # 计算处理统计
        processing_time = end_time - start_time
        throughput = data_size / processing_time
        
        result = {
            "processing_summary": {
                "total_records": data_size,
                "processing_time_seconds": processing_time,
                "throughput_records_per_second": throughput,
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.fromtimestamp(end_time).isoformat()
            },
            "performance_metrics": {
                "start": start_metrics,
                "end": end_metrics
            },
            "data_sample": processed_data[:5]  # 只返回前5条作为样本
        }
        
        logger.info(f"✅ 监控流程完成，处理速度: {throughput:.2f} 记录/秒")
        return result
        
    except Exception as e:
        logger.error(f"❌ 监控流程失败: {str(e)}")
        raise

# =============================================================================
# 🚀 部署配置
# =============================================================================

def create_advanced_deployments():
    """创建进阶部署配置"""
    
    # 1. 完整数据处理流程部署
    complete_pipeline_deployment = Deployment.build_from_flow(
        flow=complete_data_pipeline,
        name="完整数据处理-定时执行",
        schedule=CronSchedule(cron="0 2 * * *", timezone="Asia/Shanghai"),  # 每天凌晨2点
        tags=["数据处理", "ETL", "定时任务"],
        description="完整的端到端数据处理流程，包含数据获取、清洗、转换和存储",
        parameters={
            "api_url": "https://api.mock.com/data",
            "db_path": "data/warehouse.db"
        }
    )
    
    # 2. 并行处理流程部署
    parallel_pipeline_deployment = Deployment.build_from_flow(
        flow=parallel_processing_pipeline,
        name="并行数据处理-手动执行",
        tags=["并行处理", "高性能", "手动执行"],
        description="并行处理多个数据源和文件的高性能流程",
        parameters={
            "data_sources": ["source_1", "source_2", "source_3", "source_4", "source_5"],
            "file_patterns": ["pattern_a", "pattern_b", "pattern_c", "pattern_d"]
        }
    )
    
    # 3. 容错流程部署
    fault_tolerant_deployment = Deployment.build_from_flow(
        flow=fault_tolerant_pipeline,
        name="容错数据处理-定时执行",
        schedule=CronSchedule(cron="0 */4 * * *", timezone="Asia/Shanghai"),  # 每4小时
        tags=["容错处理", "可靠性", "定时任务"],
        description="具有完善错误处理和重试机制的数据处理流程",
        parameters={
            "input_data": [f"data_item_{i}" for i in range(20)]
        }
    )
    
    # 4. 监控流程部署
    monitored_pipeline_deployment = Deployment.build_from_flow(
        flow=monitored_data_pipeline,
        name="监控数据处理-手动执行",
        tags=["性能监控", "指标收集", "手动执行"],
        description="带有性能监控和指标收集的数据处理流程",
        parameters={
            "data_size": 5000
        }
    )
    
    # 应用所有部署
    deployments = [
        complete_pipeline_deployment,
        parallel_pipeline_deployment,
        fault_tolerant_deployment,
        monitored_pipeline_deployment
    ]
    
    for deployment in deployments:
        deployment.apply()
        print(f"✅ 部署已创建: {deployment.name}")
    
    print(f"\n🎉 成功创建 {len(deployments)} 个进阶部署配置！")

# =============================================================================
# 🧪 测试和示例
# =============================================================================

def test_advanced_flows():
    """测试进阶流程"""
    print("🧪 开始测试进阶流程...")
    
    # 测试完整数据处理流程
    print("\n1. 测试完整数据处理流程")
    try:
        result = complete_data_pipeline(api_url="https://api.mock.com/data")
        print("✅ 完整数据处理流程测试成功")
        print(f"📊 处理结果预览: {result[:200]}...")
    except Exception as e:
        print(f"❌ 完整数据处理流程测试失败: {e}")
    
    # 测试容错流程
    print("\n2. 测试容错流程")
    try:
        test_data = [f"test_item_{i}" for i in range(10)]
        result = fault_tolerant_pipeline(test_data)
        print("✅ 容错流程测试成功")
        print(f"📊 成功率: {result['success_rate']:.1f}%")
    except Exception as e:
        print(f"❌ 容错流程测试失败: {e}")
    
    # 测试监控流程
    print("\n3. 测试监控流程")
    try:
        result = monitored_data_pipeline(data_size=100)
        print("✅ 监控流程测试成功")
        print(f"📊 处理速度: {result['processing_summary']['throughput_records_per_second']:.2f} 记录/秒")
    except Exception as e:
        print(f"❌ 监控流程测试失败: {e}")
    
    print("\n🎉 进阶流程测试完成！")

if __name__ == "__main__":
    print("🚀 Prefect 进阶开发指南")
    print("=" * 50)
    
    # 选择操作
    print("\n请选择操作:")
    print("1. 创建进阶部署配置")
    print("2. 测试进阶流程")
    print("3. 查看帮助信息")
    
    choice = input("\n请输入选择 (1-3): ").strip()
    
    if choice == "1":
        create_advanced_deployments()
    elif choice == "2":
        test_advanced_flows()
    elif choice == "3":
        print("""
🔧 Prefect 进阶开发指南使用说明

本文件包含了以下进阶功能:

📊 数据处理任务:
- connect_database: 数据库连接管理
- fetch_api_data: API数据获取
- clean_data: 数据清洗和验证
- transform_data: 数据转换和聚合
- store_data: 数据存储
- generate_report: 报告生成

🔄 并行处理:
- parallel_data_processing: 异步并行处理
- batch_file_processing: 批量文件处理

🌊 复杂流程:
- complete_data_pipeline: 完整ETL流程
- parallel_processing_pipeline: 并行处理流程

🔧 错误处理:
- fault_tolerant_task: 容错任务
- fault_tolerant_pipeline: 容错流程

📈 监控指标:
- collect_performance_metrics: 性能监控
- monitored_data_pipeline: 监控流程

🚀 使用方法:
1. 运行脚本创建部署配置
2. 在 Prefect UI 中查看和执行流程
3. 监控执行状态和性能指标

💡 最佳实践:
- 使用适当的重试策略
- 实施完善的错误处理
- 收集性能指标和监控
- 使用并行处理提高效率
- 创建详细的执行报告
        """)
    else:
        print("❌ 无效选择，请重新运行脚本")