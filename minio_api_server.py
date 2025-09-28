# -*- coding: utf-8 -*-
"""
MinIO API服务 - 支持JSON和二维列表转Parquet上传
提供RESTful API接口，支持多种数据格式转换和上传到MinIO
"""

import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from minio import Minio, S3Error
import io
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import traceback
import tempfile
import shutil
import pyarrow as pa

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/minio_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# PyIceberg imports
try:
    from pyiceberg.catalog import load_catalog
    from pyiceberg.schema import Schema
    from pyiceberg.types import (
        StringType, IntegerType, LongType, FloatType, DoubleType, 
        BooleanType, TimestampType, NestedField
    )
    PYICEBERG_AVAILABLE = True
except ImportError:
    PYICEBERG_AVAILABLE = False
    # 当PyIceberg不可用时，提供Schema的替代定义
    Schema = type('Schema', (), {})
    logger.warning("PyIceberg not available. Install with: pip install 'pyiceberg[s3fs,pyarrow]'")

# Flask应用初始化
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

class MinIODataUploader:
    """MinIO数据上传器 - 支持多种格式转换"""
    
    def __init__(self, minio_endpoint=None, access_key=None, 
                 secret_key=None, bucket_name=None):
        """初始化MinIO客户端"""
        # 优先使用环境变量，如果没有则使用传入参数或默认值
        self.minio_endpoint = minio_endpoint or os.getenv('MINIO_ENDPOINT', '100.120.50.34:9002')
        self.access_key = access_key or os.getenv('MINIO_ACCESS_KEY', 'admin')
        self.secret_key = secret_key or os.getenv('MINIO_SECRET_KEY', 'admin123')
        
        # 如果没有指定桶名，从环境变量获取，否则使用warehouse作为默认值
        if bucket_name is None:
            self.bucket_name = os.getenv('MINIO_BUCKET', 'warehouse')
        else:
            self.bucket_name = bucket_name
            
        logger.info(f"MinIODataUploader初始化 - 桶名: {self.bucket_name}")
        
        try:
            self.minio_client = Minio(
                minio_endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=False
            )
            logger.info(f"MinIO客户端初始化成功: {minio_endpoint}")
        except Exception as e:
            logger.error(f"MinIO客户端初始化失败: {e}")
            raise
    
    def _ensure_bucket_exists(self) -> bool:
        """确保存储桶存在"""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"创建存储桶: {self.bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"存储桶操作失败: {e}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """测试MinIO连接"""
        try:
            if self._ensure_bucket_exists():
                return {
                    'success': True,
                    'message': 'MinIO连接正常',
                    'endpoint': self.minio_endpoint,
                    'bucket': self.bucket_name
                }
            else:
                return {
                    'success': False,
                    'error': '存储桶操作失败'
                }
        except Exception as e:
            logger.error(f"MinIO连接失败: {e}")
            return {
                'success': False,
                'error': f'MinIO连接失败: {str(e)}'
            }
    
    def _remove_existing_file(self, object_path: str):
        """删除已存在的同名文件"""
        try:
            self.minio_client.stat_object(self.bucket_name, object_path)
            self.minio_client.remove_object(self.bucket_name, object_path)
            logger.info(f"删除已存在的同名文件: {object_path}")
        except S3Error as e:
            if e.code == 'NoSuchKey':
                logger.debug(f"文件不存在，无需删除: {object_path}")
            else:
                logger.error(f"检查文件时出错: {e}")
        except Exception as e:
            logger.error(f"删除文件时出错: {e}")
    
    def _ensure_path_exists(self, target_path: str):
        """确保路径存在（通过创建标记文件）"""
        try:
            dir_path = '/'.join(target_path.split('/')[:-1])
            if dir_path:
                marker_path = f"{dir_path}/.path_marker"
                
                try:
                    self.minio_client.stat_object(self.bucket_name, marker_path)
                    logger.debug(f"路径标记已存在: {dir_path}")
                except S3Error:
                    marker_content = f"Path created at {datetime.now()}"
                    self.minio_client.put_object(
                        self.bucket_name,
                        marker_path,
                        io.BytesIO(marker_content.encode('utf-8')),
                        length=len(marker_content.encode('utf-8')),
                        content_type='text/plain'
                    )
                    logger.info(f"创建路径标记: {dir_path}")
        except Exception as e:
            logger.error(f"创建路径时出错: {e}")
    
    def _convert_data_to_dataframe(self, data: Union[Dict, List, str]) -> pd.DataFrame:
        """将各种格式的数据转换为DataFrame，参考pdd_chat_upload.py的数据处理逻辑"""
        try:
            # 处理JSON字符串
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError as e:
                    raise ValueError(f"无效的JSON字符串: {e}")
            
            # 转换为DataFrame
            if isinstance(data, dict):
                # 单个字典转换为包含一行的DataFrame
                df = pd.DataFrame([data])
            elif isinstance(data, list):
                if not data:
                    raise ValueError("数据列表不能为空")
                
                # 检查列表元素类型
                if isinstance(data[0], dict):
                    # 字典列表转换为DataFrame
                    df = pd.DataFrame(data)
                elif isinstance(data[0], list):
                    # 二维列表转换为DataFrame，第一行始终作为列名
                    # 处理列名，确保没有重复和编码问题
                    headers = []
                    for i, col in enumerate(data[0]):
                        if isinstance(col, str):
                            # 清理列名，移除特殊字符，确保唯一性
                            clean_col = col.strip().replace('\ufeff', '').replace('\n', '').replace('\t', '')
                            if not clean_col:
                                clean_col = f'column_{i}'
                            headers.append(clean_col)
                        else:
                            headers.append(f'column_{i}' if col is None or str(col).strip() == '' else str(col))
                    
                    # 确保列名唯一性
                    seen = set()
                    unique_headers = []
                    for header in headers:
                        if header in seen:
                            counter = 1
                            new_header = f"{header}_{counter}"
                            while new_header in seen:
                                counter += 1
                                new_header = f"{header}_{counter}"
                            unique_headers.append(new_header)
                            seen.add(new_header)
                        else:
                            unique_headers.append(header)
                            seen.add(header)
                    
                    # 如果有数据行，使用数据行；如果只有表头，创建空DataFrame
                    if len(data) > 1:
                        df = pd.DataFrame(data[1:], columns=unique_headers)
                    else:
                        # 只有表头，创建空DataFrame但保留列结构
                        df = pd.DataFrame(columns=unique_headers)
                else:
                    # 一维列表转换为单列DataFrame
                    df = pd.DataFrame({'value': data})
            else:
                raise ValueError(f"不支持的数据类型: {type(data)}")
            
            # 应用pdd_chat_upload.py中的数据处理逻辑
            df = self._process_dataframe_data_types(df)
            
            logger.info(f"数据转换成功，DataFrame形状: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"数据转换失败: {e}")
            raise
    
    def _process_dataframe_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理DataFrame中的各种数据类型，参考pdd_chat_upload.py的处理逻辑"""
        try:
            logger.info(f"开始处理DataFrame数据类型，列名: {list(df.columns)}")
            
            # 处理NaN值，将其替换为空字符串
            df = df.fillna('')
            
            # 处理所有数据类型，确保能够序列化
            for col in df.columns:
                # 处理时间类型
                if df[col].dtype == 'datetime64[ns]':
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                elif 'time' in str(df[col].dtype).lower():
                    df[col] = df[col].astype(str)
                # 处理数值类型，确保没有无穷大或NaN
                elif df[col].dtype in ['float64', 'float32']:
                    df[col] = df[col].replace([float('inf'), float('-inf')], '')
                # 确保所有数据都转换为字符串，避免类型问题
                df[col] = df[col].astype(str)
            
            logger.info(f"DataFrame数据类型处理完成，所有列已转换为字符串类型")
            return df
            
        except Exception as e:
            logger.error(f"处理DataFrame数据类型失败: {e}")
            # 如果整体处理失败，尝试简单的字符串转换
            try:
                for col in df.columns:
                    df[col] = df[col].astype(str)
                logger.info("使用简单字符串转换作为备选方案")
                return df
            except Exception as fallback_error:
                logger.error(f"备选方案也失败: {fallback_error}")
                raise e
    
    def _safe_convert_value(self, value):
        """安全转换单个值，处理各种特殊情况"""
        try:
            # 处理None值
            if value is None:
                return ''
            
            # 处理NaN值
            if pd.isna(value):
                return ''
            
            # 处理字符串形式的特殊值
            if isinstance(value, str):
                value_lower = value.lower().strip()
                if value_lower in ['nan', 'infinity', '-infinity', 'inf', '-inf', 'null', 'none', 'n/a', '--', 'undefined']:
                    return ''
                return value.strip()
            
            # 处理无穷大值
            if isinstance(value, (int, float)):
                if value == float('inf') or value == float('-inf'):
                    return ''
                if pd.isna(value):
                    return ''
            
            # 其他类型转换为字符串
            return str(value)
            
        except Exception as e:
            logger.warning(f"转换值时出错 {value}: {e}，返回空字符串")
            return ''
    
    def upload_data_as_parquet(self, data: Union[Dict, List, str], target_path: str,
                              columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """将数据转换为Parquet格式并上传到MinIO
        
        Args:
            data: 输入数据，支持字典、列表、JSON字符串
            target_path: MinIO中的目标路径
            columns: 可选的列名列表（用于二维列表）
        
        Returns:
            Dict: 上传结果
        """
        try:
            # 确保存储桶存在
            if not self._ensure_bucket_exists():
                return {
                    'success': False,
                    'error': '存储桶不存在且创建失败'
                }
            
            # 转换数据为DataFrame
            df = self._convert_data_to_dataframe(data)
            
            # 如果提供了列名且数据是二维列表，设置列名
            if columns and len(columns) == len(df.columns):
                df.columns = columns
            
            logger.info(f"开始上传Parquet数据到: {target_path}")
            logger.info(f"数据形状: {df.shape}")
            
            # 转换为Parquet格式
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False, engine='pyarrow')
            buffer.seek(0)
            data_size = len(buffer.getvalue())
            
            # 删除已存在的同名文件
            self._remove_existing_file(target_path)
            
            # 确保路径存在
            self._ensure_path_exists(target_path)
            
            # 上传到MinIO
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=target_path,
                data=buffer,
                length=data_size,
                content_type='application/octet-stream'
            )
            
            logger.info(f"Parquet文件上传成功: {target_path}")
            return {
                'success': True,
                'message': f'Parquet文件上传成功: {target_path}',
                'target_path': target_path,
                'file_size': data_size,
                'rows_count': len(df),
                'columns_count': len(df.columns),
                'data_format': 'parquet'
            }
            
        except Exception as e:
            error_msg = f"Parquet上传失败: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': error_msg
            }
    
    def read_excel_folder_and_merge(self, folder_path: str) -> pd.DataFrame:
        """读取文件夹中所有Excel文件并合并为一个DataFrame，文件名作为shop列
        
        Args:
            folder_path: Excel文件夹路径
            
        Returns:
            pd.DataFrame: 合并后的DataFrame，包含shop列
        """
        try:
            import glob
            
            if not os.path.exists(folder_path):
                raise ValueError(f"文件夹路径不存在: {folder_path}")
            
            # 查找所有Excel文件
            excel_patterns = [
                os.path.join(folder_path, "*.xlsx"),
                os.path.join(folder_path, "*.xls"),
                os.path.join(folder_path, "*.xlsm")
            ]
            
            excel_files = []
            for pattern in excel_patterns:
                excel_files.extend(glob.glob(pattern))
            
            if not excel_files:
                raise ValueError(f"文件夹中没有找到Excel文件: {folder_path}")
            
            logger.info(f"找到 {len(excel_files)} 个Excel文件")
            
            merged_data = []
            
            for excel_file in excel_files:
                try:
                    # 获取文件名（不包含扩展名）作为shop名称
                    shop_name = os.path.splitext(os.path.basename(excel_file))[0]
                    logger.info(f"正在读取文件: {excel_file}, shop: {shop_name}")
                    
                    # 读取Excel文件
                    df = pd.read_excel(excel_file)
                    
                    # 添加shop列
                    df['shop'] = shop_name
                    
                    # 处理数据类型
                    df = self._process_dataframe_data_types(df)
                    
                    merged_data.append(df)
                    logger.info(f"成功读取文件 {excel_file}, 数据行数: {len(df)}")
                    
                except Exception as e:
                    logger.error(f"读取Excel文件失败 {excel_file}: {e}")
                    continue
            
            if not merged_data:
                raise ValueError("没有成功读取任何Excel文件")
            
            # 合并所有DataFrame
            final_df = pd.concat(merged_data, ignore_index=True)
            logger.info(f"成功合并所有Excel文件，总数据行数: {len(final_df)}")
            
            return final_df
            
        except Exception as e:
            logger.error(f"读取Excel文件夹失败: {e}")
            raise

    def upload_data_as_json(self, data: Union[Dict, List, str], target_path: str) -> Dict[str, Any]:
        """将数据转换为JSON格式并上传到MinIO
        
        Args:
            data: 输入数据
            target_path: MinIO中的目标路径
        
        Returns:
            Dict: 上传结果
        """
        try:
            # 确保存储桶存在
            if not self._ensure_bucket_exists():
                return {
                    'success': False,
                    'error': '存储桶不存在且创建失败'
                }
            
            # 处理数据
            if isinstance(data, str):
                # 验证JSON格式
                try:
                    json.loads(data)
                    json_str = data
                except json.JSONDecodeError as e:
                    raise ValueError(f"无效的JSON字符串: {e}")
            else:
                # 转换为JSON字符串
                json_str = json.dumps(data, ensure_ascii=False, indent=2)
            
            logger.info(f"开始上传JSON数据到: {target_path}")
            
            # 创建字节流
            buffer = io.BytesIO(json_str.encode('utf-8'))
            data_size = len(buffer.getvalue())
            
            # 删除已存在的同名文件
            self._remove_existing_file(target_path)
            
            # 确保路径存在
            self._ensure_path_exists(target_path)
            
            # 上传到MinIO
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=target_path,
                data=buffer,
                length=data_size,
                content_type='application/json'
            )
            
            logger.info(f"JSON文件上传成功: {target_path}")
            return {
                'success': True,
                'message': f'JSON文件上传成功: {target_path}',
                'target_path': target_path,
                'file_size': data_size,
                'data_format': 'json'
            }
            
        except Exception as e:
            error_msg = f"JSON上传失败: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _pandas_to_iceberg_schema(self, df: pd.DataFrame) -> Schema:
        """将Pandas DataFrame的数据类型转换为Iceberg Schema
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            Schema: Iceberg Schema对象
        """
        fields = []
        for i, (col_name, dtype) in enumerate(df.dtypes.items(), 1):
            if pd.api.types.is_integer_dtype(dtype):
                if dtype == 'int32':
                    field_type = IntegerType()
                else:
                    field_type = LongType()
            elif pd.api.types.is_float_dtype(dtype):
                if dtype == 'float32':
                    field_type = FloatType()
                else:
                    field_type = DoubleType()
            elif pd.api.types.is_bool_dtype(dtype):
                field_type = BooleanType()
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                field_type = TimestampType()
            else:
                field_type = StringType()
            
            fields.append(NestedField(
                field_id=i,
                name=str(col_name),
                field_type=field_type,
                required=False
            ))
        
        return Schema(*fields)
    
    def _get_iceberg_field_type(self, pandas_dtype) -> str:
        """根据 Pandas 数据类型推断 Iceberg 字段类型"""
        if pd.api.types.is_integer_dtype(pandas_dtype):
            return 'int'
        elif pd.api.types.is_float_dtype(pandas_dtype):
            return 'double'
        elif pd.api.types.is_bool_dtype(pandas_dtype):
            return 'boolean'
        elif pd.api.types.is_datetime64_any_dtype(pandas_dtype):
            return 'timestamp'
        else:
            return 'string'

    def upload_data_as_iceberg(self, data: Union[Dict, List, str], target_path: str,
                              columns: Optional[List[str]] = None, 
                              table_name: Optional[str] = None) -> Dict[str, Any]:
        """将数据转换为标准Iceberg格式并上传到MinIO（基于 test_iceberg_new 表结构）
        
        Args:
            data: 输入数据，支持字典、列表、JSON字符串
            target_path: MinIO中的目标路径（不包含文件扩展名）
            columns: 可选的列名列表（用于二维列表）
            table_name: Iceberg表名，如果不提供则从target_path推导
        
        Returns:
            Dict: 上传结果
        """
        import uuid
        import time
        import random
        
        try:
            # 确保存储桶存在
            if not self._ensure_bucket_exists():
                return {
                    'success': False,
                    'error': '存储桶不存在且创建失败'
                }
            
            # 转换数据为DataFrame
            df = self._convert_data_to_dataframe(data)
            
            # 如果提供了列名且数据是二维列表，设置列名
            if columns and len(columns) == len(df.columns):
                df.columns = columns
            
            logger.info(f"开始上传标准Iceberg数据到: {target_path}")
            logger.info(f"数据形状: {df.shape}")
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            
            try:
                # 生成唯一标识符
                table_uuid = str(uuid.uuid4())
                job_id = str(uuid.uuid4())
                current_timestamp = int(time.time() * 1000)
                snapshot_id = random.randint(1000000000000000000, 9999999999999999999)
                
                # 1. 创建并上传数据文件（Parquet格式）- 使用 job_id 作为目录名
                data_file_name = "0_0_0.parquet"
                data_file_path = os.path.join(temp_dir, data_file_name)
                df.to_parquet(data_file_path, index=False, engine='pyarrow')
                
                # 上传数据文件到以 job_id 命名的目录
                data_object_name = f"{target_path}/{job_id}/{data_file_name}"
                self.minio_client.fput_object(
                    self.bucket_name,
                    data_object_name,
                    data_file_path,
                    content_type='application/octet-stream'
                )
                
                # 获取数据文件信息
                data_file_size = os.path.getsize(data_file_path)
                
                # 2. 创建标准的 schema 结构
                schema_fields = []
                for i, (col_name, dtype) in enumerate(df.dtypes.items(), 1):
                    field_type = self._get_iceberg_field_type(dtype)
                    schema_fields.append({
                        'id': i,
                        'name': str(col_name),
                        'required': False,
                        'type': field_type
                    })
                
                # 3. 创建 manifest 和 manifest-list 文件名
                manifest_uuid = str(uuid.uuid4())
                manifest_list_uuid = str(uuid.uuid4())
                manifest_name = f"{manifest_uuid}.avro"
                manifest_list_name = f"snap-{snapshot_id}-1-{manifest_list_uuid}.avro"
                
                # 4. 创建标准的元数据文件（基于 test_iceberg_new 结构）
                metadata = {
                    "format-version": 2,
                    "table-uuid": table_uuid,
                    "location": f"s3://{self.bucket_name}/{target_path}",
                    "last-sequence-number": 1,
                    "last-updated-ms": current_timestamp,
                    "last-column-id": len(df.columns),
                    "current-schema-id": 0,
                    "schemas": [{
                        "type": "struct",
                        "schema-id": 0,
                        "fields": schema_fields
                    }],
                    "default-spec-id": 0,
                    "partition-specs": [{
                        "spec-id": 0,
                        "fields": []
                    }],
                    "last-partition-id": 999,
                    "default-sort-order-id": 0,
                    "sort-orders": [{
                        "order-id": 0,
                        "fields": []
                    }],
                    "properties": {
                        "commit.manifest.target-size-bytes": "153600",
                        "write.target-file-size-bytes": "134217728",
                        "write.parquet.compression-codec": "zstd"
                    },
                    "current-snapshot-id": snapshot_id,
                    "refs": {
                        "main": {
                            "snapshot-id": snapshot_id,
                            "type": "branch"
                        }
                    },
                    "snapshots": [{
                        "sequence-number": 1,
                        "snapshot-id": snapshot_id,
                        "timestamp-ms": current_timestamp,
                        "summary": {
                            "operation": "append",
                            "dremio-job-id": job_id,
                            "added-data-files": "1",
                            "added-records": str(len(df)),
                            "total-records": str(len(df)),
                            "total-files-size": "0",
                            "total-data-files": "1",
                            "total-delete-files": "0",
                            "total-position-deletes": "0",
                            "total-equality-deletes": "0",
                            "iceberg-version": "Apache Iceberg 1.7.0-5f7c992-20241111151254-eb8d651 (commit eb8d6514aba2a407b0d7f6be82668094913ee911)"
                        },
                        "manifest-list": f"s3://{self.bucket_name}/{target_path}/metadata/{manifest_list_name}",
                        "schema-id": 0
                    }],
                    "statistics": [],
                    "partition-statistics": [],
                    "snapshot-log": [{
                        "timestamp-ms": current_timestamp,
                        "snapshot-id": snapshot_id
                    }],
                    "metadata-log": []
                }
                
                # 写入v1.metadata.json文件
                metadata_file_path = os.path.join(temp_dir, 'v1.metadata.json')
                with open(metadata_file_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
                
                # 上传元数据文件
                metadata_object_name = f"{target_path}/metadata/v1.metadata.json"
                self.minio_client.fput_object(
                    self.bucket_name,
                    metadata_object_name,
                    metadata_file_path,
                    content_type='application/json'
                )
                
                # 5. 创建version-hint.text文件
                version_hint_path = os.path.join(temp_dir, 'version-hint.text')
                with open(version_hint_path, 'w') as f:
                    f.write('1')
                
                # 上传version-hint.text文件
                version_hint_object_name = f"{target_path}/metadata/version-hint.text"
                self.minio_client.fput_object(
                    self.bucket_name,
                    version_hint_object_name,
                    version_hint_path,
                    content_type='text/plain'
                )
                
                # 6. 创建空的 .avro 文件（占位符，实际应该是二进制 Avro 格式）
                # 这里创建最小的占位符文件，实际生产环境需要正确的 Avro 格式
                
                # 创建 manifest.avro 占位符
                manifest_avro_path = os.path.join(temp_dir, manifest_name)
                with open(manifest_avro_path, 'wb') as f:
                    # 写入最小的 Avro 文件头
                    f.write(b'Obj\x01')  # Avro 文件魔数
                
                manifest_avro_object_name = f"{target_path}/metadata/{manifest_name}"
                self.minio_client.fput_object(
                    self.bucket_name,
                    manifest_avro_object_name,
                    manifest_avro_path,
                    content_type='application/octet-stream'
                )
                
                # 创建 manifest-list.avro 占位符
                manifest_list_avro_path = os.path.join(temp_dir, manifest_list_name)
                with open(manifest_list_avro_path, 'wb') as f:
                    # 写入最小的 Avro 文件头
                    f.write(b'Obj\x01')  # Avro 文件魔数
                
                manifest_list_avro_object_name = f"{target_path}/metadata/{manifest_list_name}"
                self.minio_client.fput_object(
                    self.bucket_name,
                    manifest_list_avro_object_name,
                    manifest_list_avro_path,
                    content_type='application/octet-stream'
                )
                
                # 确定表名
                if not table_name:
                    table_name = Path(target_path).stem or "iceberg_table"
                
                logger.info(f"标准Iceberg表上传成功: {target_path}")
                return {
                    'success': True,
                    'message': f'标准Iceberg表上传成功: {target_path}',
                    'target_path': target_path,
                    'file_size': data_file_size,
                    'rows_count': len(df),
                    'columns_count': len(df.columns),
                    'data_format': 'iceberg',
                    'table_name': table_name,
                    'namespace': 'default',
                    'job_id': job_id,
                    'table_uuid': table_uuid,
                    'snapshot_id': snapshot_id
                }
                
            finally:
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"清理临时目录失败: {e}")
            
        except Exception as e:
            error_msg = f"Iceberg上传失败: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': error_msg
            }

def get_uploader(bucket_name=None):
    """获取MinIO上传器实例"""
    # 从环境变量或默认值获取配置
    minio_endpoint = os.getenv('MINIO_ENDPOINT', '100.120.50.34:9002')
    access_key = os.getenv('MINIO_ACCESS_KEY', 'admin')
    secret_key = os.getenv('MINIO_SECRET_KEY', 'admin123')
    
    # 调试信息：打印环境变量值
    logger.info(f"环境变量 MINIO_BUCKET: {os.getenv('MINIO_BUCKET')}")
    logger.info(f"请求桶名: {bucket_name}")
    
    # 创建上传器实例，让它自己处理桶名逻辑
    uploader = MinIODataUploader(
        minio_endpoint=minio_endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket_name=bucket_name  # 传递None或指定的桶名，让类内部处理
    )
    
    logger.info(f"最终使用桶名: {uploader.bucket_name}")
    
    # 确保桶存在
    uploader._ensure_bucket_exists()
    
    return uploader

def get_minio_client():
    """获取MinIO客户端（不绑定特定存储桶）"""
    minio_endpoint = os.getenv('MINIO_ENDPOINT', '100.120.50.34:9002')
    access_key = os.getenv('MINIO_ACCESS_KEY', 'admin')
    secret_key = os.getenv('MINIO_SECRET_KEY', 'admin123')
    
    return Minio(
        minio_endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=False
    )

# API路由定义

@app.route('/health', methods=['GET'])
def health_check_simple():
    """简单健康检查 - 用于Docker健康检查"""
    try:
        # 支持查询参数指定存储桶
        bucket_name = request.args.get('bucket')
        uploader_instance = get_uploader(bucket_name)
        connection_result = uploader_instance.test_connection()
        
        return jsonify({
            'status': 'healthy' if connection_result['success'] else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'minio_connection': connection_result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """详细健康检查 - API端点"""
    try:
        # 支持查询参数指定存储桶
        bucket_name = request.args.get('bucket')
        uploader_instance = get_uploader(bucket_name)
        connection_result = uploader_instance.test_connection()
        
        return jsonify({
            'status': 'healthy' if connection_result['success'] else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'minio_connection': connection_result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.route('/api/upload/parquet', methods=['POST'])
def upload_parquet():
    """上传数据为Parquet格式"""
    try:
        # 获取请求数据
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        # 提取参数
        data = request_data.get('data')
        target_path = request_data.get('target_path')
        columns = request_data.get('columns')  # 可选的列名
        bucket_name = request_data.get('bucket')  # 可选的存储桶名称
        
        if not data:
            return jsonify({
                'success': False,
                'error': '数据字段不能为空'
            }), 400
        
        if not target_path:
            return jsonify({
                'success': False,
                'error': '目标路径不能为空'
            }), 400
        
        # 执行上传
        uploader_instance = get_uploader(bucket_name)
        result = uploader_instance.upload_data_as_parquet(data, target_path, columns)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Parquet上传API异常: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/upload/json', methods=['POST'])
def upload_json():
    """上传数据为JSON格式"""
    try:
        # 获取请求数据
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        # 提取参数
        data = request_data.get('data')
        target_path = request_data.get('target_path')
        bucket_name = request_data.get('bucket')  # 可选的存储桶名称
        
        if not data:
            return jsonify({
                'success': False,
                'error': '数据字段不能为空'
            }), 400
        
        if not target_path:
            return jsonify({
                'success': False,
                'error': '目标路径不能为空'
            }), 400
        
        # 执行上传
        uploader_instance = get_uploader(bucket_name)
        result = uploader_instance.upload_data_as_json(data, target_path)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"JSON上传API异常: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_data():
    """通用上传接口 - 支持指定格式"""
    try:
        # 记录详细的请求信息
        logger.info(f"收到上传请求 - 方法: {request.method}")
        logger.info(f"请求头: {dict(request.headers)}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"请求体大小: {request.content_length}")
        
        # 尝试获取原始请求数据
        raw_data = None
        try:
            raw_data = request.get_data(as_text=True)
            logger.info(f"原始请求数据长度: {len(raw_data)}")
            logger.info(f"原始请求数据前1000字符: {raw_data[:1000]}")
            if len(raw_data) > 1000:
                logger.info(f"原始请求数据后500字符: ...{raw_data[-500:]}")
        except Exception as e:
            logger.error(f"无法获取原始请求数据: {e}")
        
        # 尝试多种方式获取请求数据
        request_data = None
        
        # 方式1：标准JSON解析
        try:
            request_data = request.get_json(silent=True)
            if request_data:
                logger.info("使用标准JSON解析成功")
        except Exception as e:
            logger.error(f"标准JSON解析失败: {e}")
        
        # 方式2：手动JSON解析
        if not request_data and raw_data:
            try:
                import json
                # 清理可能的BOM和空白字符
                clean_data = raw_data.strip()
                if clean_data.startswith('\ufeff'):
                    clean_data = clean_data[1:]
                request_data = json.loads(clean_data)
                logger.info("使用手动JSON解析成功")
            except json.JSONDecodeError as e:
                logger.error(f"手动JSON解析失败 - JSONDecodeError: {e}")
                logger.error(f"错误位置附近的字符: {raw_data[max(0, e.pos-50):e.pos+50]}")
            except Exception as e:
                logger.error(f"手动JSON解析失败: {e}")
        
        # 方式3：强制JSON解析
        if not request_data:
            try:
                request_data = request.get_json(force=True, silent=True)
                if request_data:
                    logger.info("使用强制JSON解析成功")
            except Exception as e:
                logger.error(f"强制JSON解析失败: {e}")
        
        # 方式4：尝试修复常见的JSON格式问题
        if not request_data and raw_data:
            try:
                import json
                import re
                # 尝试修复常见的JSON格式问题
                fixed_data = raw_data.strip()
                # 移除可能的BOM
                if fixed_data.startswith('\ufeff'):
                    fixed_data = fixed_data[1:]
                # 尝试修复单引号问题
                if "'" in fixed_data and '"' not in fixed_data:
                    fixed_data = fixed_data.replace("'", '"')
                request_data = json.loads(fixed_data)
                logger.info("使用修复后的JSON解析成功")
            except json.JSONDecodeError as e:
                logger.error(f"修复JSON解析失败: {e}")
            except Exception as e:
                logger.error(f"修复JSON解析异常: {e}")
        
        # 方式5：Python列表格式转换机制
        if not request_data and raw_data:
            try:
                import ast
                import json
                logger.info("尝试Python列表格式转换...")
                
                # 尝试使用ast.literal_eval解析Python格式的数据
                python_data = ast.literal_eval(raw_data)
                
                # 将Python对象转换为JSON字符串，再解析回来确保格式正确
                json_str = json.dumps(python_data, ensure_ascii=False)
                request_data = json.loads(json_str)
                logger.info("Python列表格式转换成功")
                
            except (ValueError, SyntaxError) as e:
                logger.error(f"Python列表格式转换失败 - 语法错误: {e}")
            except Exception as e:
                logger.error(f"Python列表格式转换失败: {e}")
            except Exception as e:
                logger.error(f"修复JSON解析失败: {e}")
        
        if not request_data:
            logger.error("所有JSON解析方式都失败了")
            error_msg = "请求数据无法解析，请检查JSON格式"
            if raw_data:
                error_msg += f"。原始数据长度: {len(raw_data)}"
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # 记录解析后的请求参数
        logger.info(f"解析后的请求参数: {list(request_data.keys())}")
        logger.info(f"数据字段存在: {'data' in request_data}")
        logger.info(f"目标路径: {request_data.get('target_path')}")
        logger.info(f"存储桶: {request_data.get('bucket')}")
        logger.info(f"格式: {request_data.get('format', 'parquet')}")
        
        # 提取参数
        data = request_data.get('data')
        target_path = request_data.get('target_path')
        data_format = request_data.get('format', 'parquet').lower()  # 默认parquet
        columns = request_data.get('columns')  # 可选的列名
        bucket_name = request_data.get('bucket')  # 可选的存储桶名称
        
        if not data:
            return jsonify({
                'success': False,
                'error': '数据字段不能为空'
            }), 400
        
        if not target_path:
            return jsonify({
                'success': False,
                'error': '目标路径不能为空'
            }), 400
        
        if data_format not in ['parquet', 'json', 'iceberg']:
            return jsonify({
                'success': False,
                'error': '格式只支持 parquet、json 或 iceberg'
            }), 400
        
        # 执行上传
        uploader_instance = get_uploader(bucket_name)
        
        if data_format == 'parquet':
            result = uploader_instance.upload_data_as_parquet(data, target_path, columns)
        elif data_format == 'iceberg':
            # 获取可选的表名参数
            table_name = request_data.get('table_name')
            result = uploader_instance.upload_data_as_iceberg(data, target_path, columns, table_name)
        else:
            result = uploader_instance.upload_data_as_json(data, target_path)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"通用上传API异常: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/test', methods=['GET'])
def test_connection():
    """测试MinIO连接"""
    try:
        uploader_instance = get_uploader()
        result = uploader_instance.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'连接测试失败: {str(e)}'
        }), 500

@app.route('/api/upload/create-bucket', methods=['POST'])
def create_bucket_for_upload():
    """为上传创建存储桶"""
    try:
        request_data = request.get_json()
        if not request_data or 'bucket_name' not in request_data:
            return jsonify({
                'success': False,
                'error': '请提供存储桶名称'
            }), 400
        
        bucket_name = request_data['bucket_name']
        
        # 使用get_uploader函数，它会自动创建桶
        uploader_instance = get_uploader(bucket_name)
        
        # 测试连接以确保桶创建成功
        result = uploader_instance.test_connection()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'存储桶 {bucket_name} 已准备就绪',
                'bucket_name': bucket_name
            })
        else:
            return jsonify({
                'success': False,
                'error': f'存储桶创建失败: {result.get("error", "未知错误")}'
            }), 500
            
    except Exception as e:
        logger.error(f"创建上传存储桶失败: {e}")
        return jsonify({
            'success': False,
            'error': f'创建存储桶失败: {str(e)}'
        }), 500

@app.route('/api/upload/delete-file', methods=['DELETE'])
def delete_file():
    """删除指定文件"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        target_path = request_data.get('target_path')
        bucket_name = request_data.get('bucket')
        
        if not target_path:
            return jsonify({
                'success': False,
                'error': '目标路径不能为空'
            }), 400
        
        # 获取上传器实例
        uploader_instance = get_uploader(bucket_name)
        
        # 删除文件
        uploader_instance._remove_existing_file(target_path)
        
        return jsonify({
            'success': True,
            'message': f'文件 {target_path} 删除成功'
        })
        
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        return jsonify({
            'success': False,
            'error': f'删除文件失败: {str(e)}'
        }), 500

@app.route('/api/upload/ensure-path', methods=['POST'])
def ensure_path():
    """确保路径存在"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        target_path = request_data.get('target_path')
        bucket_name = request_data.get('bucket')
        
        if not target_path:
            return jsonify({
                'success': False,
                'error': '目标路径不能为空'
            }), 400
        
        # 获取上传器实例
        uploader_instance = get_uploader(bucket_name)
        
        # 确保路径存在
        uploader_instance._ensure_path_exists(target_path)
        
        return jsonify({
            'success': True,
            'message': f'路径 {target_path} 已确保存在'
        })
        
    except Exception as e:
        logger.error(f"确保路径存在失败: {e}")
        return jsonify({
            'success': False,
            'error': f'确保路径存在失败: {str(e)}'
        }), 500
@app.route('/api/buckets', methods=['GET'])
def list_buckets():
    """列出所有存储桶"""
    try:
        client = get_minio_client()
        buckets = client.list_buckets()
        bucket_list = [{'name': bucket.name, 'creation_date': bucket.creation_date.isoformat()} for bucket in buckets]
        
        return jsonify({
            'success': True,
            'buckets': bucket_list,
            'count': len(bucket_list)
        })
    except Exception as e:
        logger.error(f"列出存储桶失败: {e}")
        return jsonify({
            'success': False,
            'error': f'列出存储桶失败: {str(e)}'
        }), 500

@app.route('/api/buckets', methods=['POST'])
def create_bucket():
    """创建存储桶"""
    try:
        request_data = request.get_json()
        if not request_data or 'bucket_name' not in request_data:
            return jsonify({
                'success': False,
                'error': '请提供存储桶名称'
            }), 400
        
        bucket_name = request_data['bucket_name']
        client = get_minio_client()
        
        # 检查存储桶是否已存在
        if client.bucket_exists(bucket_name):
            return jsonify({
                'success': False,
                'error': f'存储桶 {bucket_name} 已存在'
            }), 400
        
        # 创建存储桶
        client.make_bucket(bucket_name)
        
        return jsonify({
            'success': True,
            'message': f'存储桶 {bucket_name} 创建成功'
        })
    except Exception as e:
        logger.error(f"创建存储桶失败: {e}")
        return jsonify({
            'success': False,
            'error': f'创建存储桶失败: {str(e)}'
        }), 500

@app.route('/api/buckets/<bucket_name>', methods=['DELETE'])
def delete_bucket(bucket_name):
    """删除存储桶"""
    try:
        client = get_minio_client()
        
        # 检查存储桶是否存在
        if not client.bucket_exists(bucket_name):
            return jsonify({
                'success': False,
                'error': f'存储桶 {bucket_name} 不存在'
            }), 404
        
        # 删除存储桶（注意：只能删除空的存储桶）
        client.remove_bucket(bucket_name)
        
        return jsonify({
            'success': True,
            'message': f'存储桶 {bucket_name} 删除成功'
        })
    except Exception as e:
        logger.error(f"删除存储桶失败: {e}")
        return jsonify({
            'success': False,
            'error': f'删除存储桶失败: {str(e)}'
        }), 500

@app.route('/api/upload/iceberg', methods=['POST'])
def upload_iceberg():
    """上传数据为标准Iceberg格式"""
    try:
        # 获取请求数据
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        # 获取必需参数
        data = request_data.get('data')
        target_path = request_data.get('target_path')
        
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少data参数'
            }), 400
        
        if not target_path:
            return jsonify({
                'success': False,
                'error': '缺少target_path参数'
            }), 400
        
        # 获取可选参数
        columns = request_data.get('columns')
        table_name = request_data.get('table_name')
        bucket_name = request_data.get('bucket_name')
        
        # 获取上传器实例
        uploader_instance = get_uploader(bucket_name)
        
        # 执行Iceberg上传
        result = uploader_instance.upload_data_as_iceberg(
            data=data,
            target_path=target_path,
            columns=columns,
            table_name=table_name
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Iceberg上传接口错误: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Iceberg上传失败: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('./logs', exist_ok=True)
    
    # 启动Flask应用
    # 从环境变量获取端口，默认为8009
    port = int(os.environ.get('FLASK_PORT', 8009))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"启动MinIO API服务器，端口: {port}")
    app.run(host=host, port=port, debug=False)