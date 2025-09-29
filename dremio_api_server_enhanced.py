# -*- coding: utf-8 -*-
import os
import psutil
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Response, send_file, make_response
from flask_cors import CORS
from functools import wraps
import time
import threading
from typing import Dict, Any, Optional, List
import json
import uuid
from io import StringIO, BytesIO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/dremio_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask应用初始化
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

class SchemaCache:
    """Schema缓存 - 负责定时刷新"""
    
    def __init__(self, refresh_interval_minutes=30):
        self.cache = {}
        self.table_details_cache = {}
        self.last_refresh = None
        self.refresh_interval = timedelta(minutes=refresh_interval_minutes)
        self.lock = threading.Lock()
    
    def get(self, catalog, schema):
        """获取缓存的schema信息"""
        with self.lock:
            key = f"{catalog}.{schema}"
            return self.cache.get(key)
    
    def set(self, catalog, schema, data):
        """设置schema缓存"""
        with self.lock:
            key = f"{catalog}.{schema}"
            self.cache[key] = data
            self.last_refresh = datetime.now()
    
    def get_table_details(self, table_path):
        """获取表详细信息缓存"""
        with self.lock:
            return self.table_details_cache.get(table_path)
    
    def set_table_details(self, table_path, data):
        """设置表详细信息缓存"""
        with self.lock:
            self.table_details_cache[table_path] = data
    
    def clear(self):
        """清空schema缓存"""
        with self.lock:
            self.cache.clear()
            self.last_refresh = None
    
    def clear_table_details(self):
        """清空表详细信息缓存"""
        with self.lock:
            self.table_details_cache.clear()
    
    def is_expired(self):
        """检查缓存是否过期"""
        if not self.last_refresh:
            return True
        return datetime.now() - self.last_refresh > self.refresh_interval
    
    def refresh_all(self, dremio_client):
        """刷新所有缓存"""
        try:
            logger.info("开始刷新Schema缓存...")
            result = dremio_client.get_complete_schema_with_columns()
            
            if result.get('success'):
                with self.lock:
                    # 清空旧缓存
                    self.cache.clear()
                    
                    # 设置新缓存
                    for catalog_name, catalog_data in result['data'].items():
                        for schema_name in catalog_data.get('schemas', {}).keys():
                            key = f"{catalog_name}.{schema_name}"
                            self.cache[key] = {
                                catalog_name: {
                                    'schemas': {schema_name: catalog_data['schemas'][schema_name]}
                                }
                            }
                    
                    self.last_refresh = datetime.now()
                    logger.info(f"Schema缓存刷新完成，共缓存 {len(self.cache)} 个schema")
            else:
                logger.error(f"刷新Schema缓存失败: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"刷新Schema缓存异常: {e}")
    
    def stats(self):
        """获取统计信息"""
        with self.lock:
            return {
                'schema_count': len(self.cache),
                'table_details_count': len(self.table_details_cache),
                'last_refresh': self.last_refresh.isoformat() if self.last_refresh else None,
                'is_expired': self.is_expired()
            }

class DremioClient:
    """Dremio客户端 - 负责获取数据集反射"""
    
    def __init__(self, host='localhost', port=9047, username='admin', password='admin123'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"http://{host}:{port}"
        self.token = None
        self.session = requests.Session()
        
        # 初始化表字段缓存
        self.table_columns_cache = {}
        
        # 移除超时限制，允许长时间查询
        # self.session.timeout = None  # 不设置超时限制
        
        # 登录获取token
        self._authenticate()
    
    def _authenticate(self):
        """认证并获取token"""
        try:
            auth_url = f"{self.base_url}/apiv2/login"
            auth_data = {
                "userName": self.username,
                "password": self.password
            }
            
            logger.info(f"正在连接Dremio: {self.base_url}")
            response = self.session.post(auth_url, json=auth_data, timeout=None)
            
            if response.status_code == 200:
                self.token = response.json().get('token')
                self.session.headers.update({
                    'Authorization': f'_dremio{self.token}',
                    'Content-Type': 'application/json'
                })
                logger.info("Dremio认证成功")
                return True
            else:
                logger.error(f"Dremio认证失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Dremio认证异常: {e}")
            return False
    
    def test_connection(self):
        """测试连接"""
        try:
            if not self.token:
                if not self._authenticate():
                    return {'success': False, 'error': '认证失败'}
            
            # 测试API调用
            response = self.session.get(f"{self.base_url}/api/v3/catalog", timeout=10)
            
            # 处理401错误 - token过期，重新认证后重试
            if response.status_code == 401:
                logger.warning("测试连接收到401错误，token可能已过期，尝试重新认证...")
                if self._authenticate():
                    logger.info("重新认证成功，重试测试连接...")
                    response = self.session.get(f"{self.base_url}/api/v3/catalog", timeout=10)
                else:
                    return {'success': False, 'error': '认证失败'}
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Dremio连接正常',
                    'server_info': {
                        'host': self.host,
                        'port': self.port,
                        'version': response.headers.get('Server', 'Unknown')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'API调用失败: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'连接测试失败: {str(e)}'
            }
    
    def get_complete_schema_with_columns(self):
        """获取完整的schema和列信息"""
        try:
            if not self.token:
                if not self._authenticate():
                    return {'success': False, 'error': '认证失败'}
            
            # 获取catalog列表
            catalog_response = self.session.get(f"{self.base_url}/api/v3/catalog", timeout=None)
            
            if catalog_response.status_code != 200:
                return {
                    'success': False,
                    'error': f'获取catalog失败: {catalog_response.status_code}'
                }
            
            catalogs = catalog_response.json().get('data', [])
            result = {}
            
            for catalog in catalogs:
                catalog_id = catalog.get('id')
                catalog_name = catalog.get('path', [])[-1] if catalog.get('path') else 'Unknown'
                
                logger.info(f"处理catalog: {catalog_name}")
                
                # 获取该catalog下的所有内容
                catalog_detail_response = self.session.get(
                    f"{self.base_url}/api/v3/catalog/{catalog_id}",
                    timeout=None
                )
                
                if catalog_detail_response.status_code == 200:
                    catalog_detail = catalog_detail_response.json()
                    
                    # 处理schemas和tables
                    schemas = {}
                    children = catalog_detail.get('children', [])
                    
                    for child in children:
                        if child.get('type') == 'CONTAINER':  # Schema
                            schema_name = child.get('path', [])[-1]
                            schema_id = child.get('id')
                            
                            # 获取schema下的表
                            tables = self._get_tables_in_schema(schema_id)
                            schemas[schema_name] = {
                                'tables': tables
                            }
                    
                    result[catalog_name] = {
                        'schemas': schemas
                    }
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"获取schema信息异常: {e}")
            return {
                'success': False,
                'error': f'获取schema信息失败: {str(e)}'
            }
    
    def _get_tables_in_schema(self, schema_id):
        """获取schema下的所有表"""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/catalog/{schema_id}", timeout=None)
            
            if response.status_code != 200:
                return {}
            
            schema_detail = response.json()
            tables = {}
            
            for child in schema_detail.get('children', []):
                if child.get('type') in ['PHYSICAL_DATASET', 'VIRTUAL_DATASET']:  # 表或视图
                    table_name = child.get('path', [])[-1]
                    table_id = child.get('id')
                    
                    # 获取表的列信息
                    columns = self._get_table_columns(table_id)
                    
                    tables[table_name] = {
                        'type': child.get('type'),
                        'columns': columns
                    }
            
            return tables
            
        except Exception as e:
            logger.error(f"获取schema表信息异常: {e}")
            return {}
    
    def _get_table_columns(self, table_id):
        """获取表的列信息"""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/catalog/{table_id}", timeout=None)
            
            if response.status_code != 200:
                return []
            
            table_detail = response.json()
            fields = table_detail.get('fields', [])
            
            columns = []
            for field in fields:
                columns.append({
                    'name': field.get('name'),
                    'type': field.get('type', {}).get('name', 'Unknown')
                })
            
            return columns
            
        except Exception as e:
            logger.error(f"获取表列信息异常: {e}")
            return []
    
    def execute_sql_query(self, sql, timeout=None):
        """执行SQL查询"""
        try:
            # 添加详细的SQL打印日志
            logger.info(f"=== SQL查询开始 ===")
            logger.info(f"原始SQL: {sql}")
            logger.info(f"SQL长度: {len(sql)}")
            logger.info(f"SQL类型: {type(sql)}")
            logger.info(f"超时设置: {'无限制' if timeout is None else f'{timeout}秒'}")
            
            if not self.token:
                logger.info("Token不存在，开始认证...")
                if not self._authenticate():
                    logger.error("认证失败")
                    return {'success': False, 'error': '认证失败'}
                logger.info("认证成功")
            
            # 构建查询请求
            query_data = {
                "sql": sql
            }
            
            logger.info(f"构建的查询数据: {query_data}")
            logger.info(f"Dremio API URL: {self.base_url}/api/v3/sql")
            
            start_time = time.time()
            
            # 提交查询 - 添加401错误重试机制
            logger.info(f"开始提交SQL查询到Dremio...")
            response = self.session.post(
                f"{self.base_url}/api/v3/sql",
                json=query_data,
                timeout=timeout
            )
            
            logger.info(f"API响应状态码: {response.status_code}")
            logger.info(f"API响应头: {dict(response.headers)}")
            
            # 处理401错误 - token过期，重新认证后重试
            if response.status_code == 401:
                logger.warning("收到401错误，token可能已过期，尝试重新认证...")
                if self._authenticate():
                    logger.info("重新认证成功，重试SQL查询...")
                    response = self.session.post(
                        f"{self.base_url}/api/v3/sql",
                        json=query_data,
                        timeout=timeout
                    )
                    logger.info(f"重试后API响应状态码: {response.status_code}")
                else:
                    logger.error("重新认证失败")
                    return {'success': False, 'error': '认证失败，无法执行查询'}
            
            if response.status_code != 200:
                logger.error(f"查询提交失败: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return {
                    'success': False,
                    'error': f'查询提交失败: {response.status_code} - {response.text}'
                }
            
            query_result = response.json()
            logger.info(f"查询提交成功，响应数据: {query_result}")
            job_id = query_result.get('id')
            logger.info(f"获取到Job ID: {job_id}")
            
            if not job_id:
                logger.error("未获取到查询作业ID")
                return {
                    'success': False,
                    'error': '未获取到查询作业ID'
                }
            
            # 等待查询完成
            if timeout is None:
                # 无超时限制，持续等待直到完成
                logger.info("开始等待Job执行完成，无超时限制")
                wait_time = 0
                while True:
                    logger.info(f"检查Job状态，已等待: {wait_time}秒")
                    job_response = self.session.get(
                        f"{self.base_url}/api/v3/job/{job_id}",
                        timeout=None
                    )
                    logger.info(f"Job状态检查响应码: {job_response.status_code}")
                    
                    if job_response.status_code == 200:
                        job_info = job_response.json()
                        job_state = job_info.get('jobState')
                        logger.info(f"Job状态: {job_state}")
                        logger.info(f"Job详细信息: {job_info}")
                        
                        if job_state == 'COMPLETED':
                            logger.info("Job执行完成，开始获取结果...")
                            # 获取查询结果
                            results_response = self.session.get(
                                f"{self.base_url}/api/v3/job/{job_id}/results",
                                timeout=None
                            )
                            logger.info(f"结果获取响应码: {results_response.status_code}")
                            
                            if results_response.status_code == 200:
                                results_data = results_response.json()
                                execution_time = time.time() - start_time
                                
                                # 调试日志：查看Dremio API返回的数据结构
                                logger.info(f"=== 查询结果详细信息 ===")
                                logger.info(f"结果数据完整内容: {results_data}")
                                logger.info(f"Dremio API返回的数据结构键: {list(results_data.keys())}")
                                logger.info(f"数据行数: {len(results_data.get('rows', []))}")
                                logger.info(f"执行时间: {round(execution_time, 2)}秒")
                                
                                if 'columns' in results_data:
                                    logger.info(f"找到columns字段: {results_data['columns']}")
                                    
                                    return {
                                        'success': True,
                                        'columns': results_data.get('columns', []),
                                        'data': results_data.get('rows', []),
                                        'row_count': len(results_data.get('rows', [])),
                                        'execution_time': round(execution_time, 2)
                                    }
                                else:
                                    logger.warning("未找到columns字段，使用默认格式")
                                    return {
                                        'success': True,
                                        'data': results_data.get('rows', []),
                                        'row_count': len(results_data.get('rows', [])),
                                        'execution_time': round(execution_time, 2)
                                    }
                            else:
                                logger.error(f"获取查询结果失败: {results_response.status_code}")
                                return {
                                    'success': False,
                                    'error': f'获取查询结果失败: {results_response.status_code}'
                                }
                        
                        elif job_state in ['FAILED', 'CANCELED']:
                            logger.error(f"Job执行失败，状态: {job_state}")
                            error_message = job_info.get('errorMessage', '未知错误')
                            return {
                                'success': False,
                                'error': f'查询失败: {error_message}'
                            }
                        
                        # 继续等待
                        time.sleep(2)
                        wait_time += 2
                    else:
                        logger.error(f"检查作业状态失败: {job_response.status_code}")
                        return {
                            'success': False,
                            'error': f'获取作业状态失败: {job_response.status_code}'
                        }
            else:
                # 有超时限制的原有逻辑
                max_wait_time = timeout
                wait_time = 0
                logger.info(f"开始等待Job执行完成，最大等待时间: {max_wait_time}秒")
                
                while wait_time < max_wait_time:
                    logger.info(f"检查Job状态，已等待: {wait_time}秒")
                    job_response = self.session.get(
                        f"{self.base_url}/api/v3/job/{job_id}",
                        timeout=10
                    )
                    logger.info(f"Job状态检查响应码: {job_response.status_code}")
                    
                    if job_response.status_code == 200:
                        job_info = job_response.json()
                        job_state = job_info.get('jobState')
                        logger.info(f"Job状态: {job_state}")
                        logger.info(f"Job详细信息: {job_info}")
                    
                        if job_state == 'COMPLETED':
                            logger.info("Job执行完成，开始获取结果...")
                            # 获取查询结果
                            results_response = self.session.get(
                                f"{self.base_url}/api/v3/job/{job_id}/results",
                                timeout=None
                            )
                            logger.info(f"结果获取响应码: {results_response.status_code}")
                            
                            if results_response.status_code == 200:
                                results_data = results_response.json()
                                execution_time = time.time() - start_time
                                
                                # 调试日志：查看Dremio API返回的数据结构
                                logger.info(f"=== 查询结果详细信息 ===")
                                logger.info(f"结果数据完整内容: {results_data}")
                                logger.info(f"Dremio API返回的数据结构键: {list(results_data.keys())}")
                                logger.info(f"数据行数: {len(results_data.get('rows', []))}")
                                logger.info(f"执行时间: {round(execution_time, 2)}秒")
                                
                                if 'columns' in results_data:
                                    logger.info(f"找到columns字段: {results_data['columns']}")
                                else:
                                    logger.warning("未找到columns字段")
                                
                                if 'rows' in results_data:
                                    logger.info(f"找到rows字段，行数: {len(results_data['rows'])}")
                                    if results_data['rows']:
                                        logger.info(f"前3行数据示例: {results_data['rows'][:3]}")
                                else:
                                    logger.warning("未找到rows字段")
                                
                                result = {
                                    'success': True,
                                    'data': results_data.get('rows', []),
                                    'columns': results_data.get('columns', []),
                                    'row_count': results_data.get('rowCount', 0),
                                    'execution_time': round(execution_time, 2)
                                }
                                logger.info(f"最终返回结果: {result}")
                                return result
                            else:
                                logger.error(f"获取查询结果失败: {results_response.status_code}")
                                logger.error(f"结果响应内容: {results_response.text}")
                                return {
                                    'success': False,
                                    'error': f'获取查询结果失败: {results_response.status_code}'
                                }
                        
                        elif job_state in ['FAILED', 'CANCELED']:
                            error_message = job_info.get('errorMessage', '查询失败')
                            return {
                                'success': False,
                                'error': f'查询失败: {error_message}'
                            }
                        
                        # 查询仍在进行中，继续等待
                        time.sleep(1)
                        wait_time += 1
                    else:
                        return {
                            'success': False,
                            'error': f'获取作业状态失败: {job_response.status_code}'
                        }
            
                # 超时
                return {
                    'success': False,
                    'error': f'查询超时 ({timeout}秒)'
                }
            
        except Exception as e:
            logger.error(f"SQL查询异常: {e}")
            return {
                'success': False,
                'error': f'查询执行失败: {str(e)}'
            }
    
    def get_table_details_by_api(self, table_path):
        """通过API获取表的详细信息"""
        try:
            if not self.token:
                if not self._authenticate():
                    return {'success': False, 'error': '认证失败'}
            
            # 解析表路径
            path_parts = table_path.strip('"').split('.')
            
            if len(path_parts) < 2:
                return {
                    'success': False,
                    'error': '表路径格式错误，应为 catalog.schema.table 或 schema.table'
                }
            
            # 构建搜索查询
            search_query = path_parts[-1]  # 表名
            
            # 搜索表
            search_response = self.session.get(
                f"{self.base_url}/api/v3/catalog/search",
                params={'filter': search_query},
                timeout=None
            )
            
            if search_response.status_code != 200:
                return {
                    'success': False,
                    'error': f'搜索表失败: {search_response.status_code}'
                }
            
            search_results = search_response.json().get('data', [])
            
            # 查找匹配的表
            target_table = None
            for result in search_results:
                result_path = '.'.join(result.get('path', []))
                if result_path.endswith(table_path) or result_path == table_path:
                    target_table = result
                    break
            
            if not target_table:
                return {
                    'success': False,
                    'error': f'未找到表: {table_path}'
                }
            
            table_id = target_table.get('id')
            
            # 获取表详细信息
            detail_response = self.session.get(
                f"{self.base_url}/api/v3/catalog/{table_id}",
                timeout=None
            )
            
            if detail_response.status_code != 200:
                return {
                    'success': False,
                    'error': f'获取表详细信息失败: {detail_response.status_code}'
                }
            
            table_detail = detail_response.json()
            
            # 提取列信息
            columns = []
            for field in table_detail.get('fields', []):
                columns.append({
                    'name': field.get('name'),
                    'type': field.get('type', {}).get('name', 'Unknown'),
                    'nullable': field.get('type', {}).get('nullable', True)
                })
            
            return {
                'success': True,
                'data': {
                    'table_name': target_table.get('path', [])[-1],
                    'full_path': '.'.join(target_table.get('path', [])),
                    'type': target_table.get('type'),
                    'columns': columns,
                    'column_count': len(columns)
                }
            }
            
        except Exception as e:
            logger.error(f"获取表详细信息异常: {e}")
            return {
                'success': False,
                'error': f'获取表详细信息失败: {str(e)}'
            }
    
    def refresh_dataset(self, dataset_path, timeout_secs=600):
        """刷新指定数据集的反射(社区版) - 使用查询方式"""
        try:
            if not self.token:
                if not self._authenticate():
                    return {'success': False, 'error': '认证失败'}
            
            logger.info(f"开始刷新数据集: {dataset_path}")
            
            # 社区版不支持直接刷新反射命令，使用查询方式触发刷新
            # 通过查询数据集来触发元数据刷新
            # 数据集路径已经包含必要的引号，直接使用
            refresh_sql = f'SELECT COUNT(*) FROM {dataset_path} LIMIT 1'
            
            result = self.execute_sql_query(refresh_sql, timeout_secs)
            
            if result['success']:
                logger.info(f"数据集 {dataset_path} 刷新成功")
                return {
                    'success': True,
                    'message': '数据集 ' + dataset_path + ' 刷新完成',
                    'execution_time': result.get('execution_time', 0)
                }
            else:
                logger.error(f"数据集 {dataset_path} 刷新失败: {result['error']}")
                return {
                    'success': False,
                    'error': f'刷新失败: {result["error"]}'
                }
                
        except Exception as e:
            logger.error(f"刷新数据集异常: {e}")
            return {
                'success': False,
                'error': f'刷新数据集失败: {str(e)}'
            }
    
    def refresh_dataset_metadata(self, dataset_path, timeout_secs=600):
        """刷新数据集元数据 - 使用ALTER PDS REFRESH METADATA命令"""
        try:
            if not self.token:
                if not self._authenticate():
                    return {'success': False, 'error': '认证失败'}
            
            logger.info(f"开始刷新数据集元数据: {dataset_path}")
            
            # 使用ALTER PDS REFRESH METADATA SQL命令
            # 确保dataset_path格式正确，处理包含连字符的数据源名称
            # dataset_path格式应该是: "minio".warehouse.ods.table_name
        # ALTER PDS语句需要的格式是: "minio"."warehouse"."ods"."table_name"
            
            # 解析dataset_path并重新构建正确的SQL格式
            if dataset_path.startswith('"minio"'):
                # 移除开头的"minio".
                remaining_path = dataset_path[len('"minio".'):]  
                # 分割剩余路径
                path_parts = remaining_path.split('.')
                # 为每个部分添加引号
                quoted_parts = [f'"{part}"' for part in path_parts]
                # 重新构建完整路径，确保所有部分都有引号
                full_path = '"minio".' + '.'.join(quoted_parts)
                refresh_sql = f'ALTER PDS {full_path} REFRESH METADATA'
            else:
                # 如果不是预期格式，按点分割并为每部分添加引号
                path_parts = dataset_path.split('.')
                quoted_parts = [f'"{part}"' for part in path_parts]
                full_path = '.'.join(quoted_parts)
                refresh_sql = f'ALTER PDS {full_path} REFRESH METADATA'
            
            logger.info(f"执行元数据刷新SQL: {refresh_sql}")
            
            result = self.execute_sql_query(refresh_sql, timeout_secs)
            
            if result['success']:
                logger.info(f"数据集 {dataset_path} 元数据刷新成功")
                return {
                    'success': True,
                    'message': f'数据集 {dataset_path} 元数据刷新成功',
                    'execution_time': result.get('execution_time', 0),
                    'sql_executed': refresh_sql
                }
            else:
                logger.error(f"数据集 {dataset_path} 元数据刷新失败: {result['error']}")
                return {
                    'success': False,
                    'error': f'元数据刷新失败: {result["error"]}',
                    'sql_executed': refresh_sql
                }
                
        except Exception as e:
            logger.error(f"刷新数据集元数据异常: {e}")
            return {
                'success': False,
                'error': f'刷新数据集元数据失败: {str(e)}'
            }
    
    def get_dataset_reflections(self, dataset_id):
        """获取数据集的反射信息"""
        try:
            if not self.token:
                if not self._authenticate():
                    return {'success': False, 'error': '认证失败'}
            
            reflection_url = f"{self.base_url}/api/v3/dataset/{dataset_id}/reflection"
            
            response = self.session.get(reflection_url, timeout=None)
            logger.info(f"反射API响应状态: {response.status_code}")
            
            if response.status_code == 200:
                reflections_data = response.json()
                reflections = []
                
                for reflection in reflections_data.get('data', []):
                    reflections.append({
                        'reflection_id': reflection.get('id'),
                        'type': reflection.get('type'),
                        'enabled': reflection.get('enabled', True),
                        'name': reflection.get('name', f"reflection_{reflection.get('id')}")
                    })
                
                logger.info(f"找到 {len(reflections)} 个反射")
                return {
                    'success': True,
                    'reflections': reflections
                }
            else:
                logger.error(f"获取反射失败: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'获取反射失败: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"获取反射异常: {e}")
            return {
                'success': False,
                'error': f'获取反射异常: {str(e)}'
            }
    
    def delete_reflection_by_sql(self, reflection_name, dataset_path):
        """使用SQL删除反射"""
        try:
            if not self.token:
                if not self._authenticate():
                    return {'success': False, 'error': '认证失败'}
            
            # 正确格式化表名
            formatted_table_name = self._format_table_name_for_sql(dataset_path)
            drop_sql = 'ALTER DATASET ' + formatted_table_name + ' DROP Reflection "' + reflection_name + '"'
            logger.info('执行删除反射SQL: ' + drop_sql)
            
            result = self.execute_sql_query(drop_sql)
            
            if result['success']:
                logger.info(f"成功删除反射: {reflection_name}")
                return {
                    'success': True,
                    'message': f'反射 {reflection_name} 删除成功'
                }
            else:
                logger.error(f"删除反射失败: {result['error']}")
                return {
                    'success': False,
                    'error': f'删除反射失败: {result["error"]}'
                }
                
        except Exception as e:
            logger.error(f"删除反射异常: {e}")
            return {
                'success': False,
                'error': f'删除反射异常: {str(e)}'
            }
    
    def create_raw_reflection_by_sql(self, dataset_path, reflection_name=None):
        """使用SQL创建新的原始反射"""
        try:
            if not self.token:
                if not self._authenticate():
                    return {'success': False, 'error': '认证失败'}
            
            # 如果没有指定反射名称，使用默认名称
            if not reflection_name:
                # 从dataset_path提取表名作为反射名称
                table_name = dataset_path.split('.')[-1].replace('"', '')
                reflection_name = table_name + '_raw_reflection'
            
            # 首先获取表的字段信息，使用get_table_fields方法过滤掉分区字段
            table_columns = self.get_table_fields(dataset_path)
            
            if not table_columns:
                logger.error(f"无法获取表 {dataset_path} 的字段信息")
                return {
                    'success': False,
                    'error': '无法获取表字段信息，无法创建反射'
                }
            
            # 构建USING DISPLAY字段列表 - 直接使用字段名，不添加引号
            display_fields = ', '.join([f'"{col}"' for col in table_columns])
            
            # 格式化表名用于SQL - 确保整个路径被正确引用
            formatted_table_name = self._format_table_name_for_sql(dataset_path)
            create_sql = f'ALTER DATASET {formatted_table_name} CREATE RAW REFLECTION "{reflection_name}" USING DISPLAY ({display_fields})'
            logger.info('执行创建反射SQL: ' + create_sql)
            logger.info('原始SQL: ' + create_sql)
            
            result = self.execute_sql_query(create_sql)
            
            if result['success']:
                logger.info(f"成功创建反射: {reflection_name}")
                return {
                    'success': True,
                    'message': f'反射 {reflection_name} 创建成功',
                    'reflection_name': reflection_name
                }
            else:
                logger.error(f"创建反射失败: {result['error']}")
                return {
                    'success': False,
                    'error': f'创建反射失败: {result["error"]}'
                }
                
        except Exception as e:
            logger.error(f"创建反射异常: {e}")
            return {
                'success': False,
                'error': f'创建反射异常: {str(e)}'
            }
    
    def _get_table_columns_for_reflection(self, dataset_path):
        """获取表的字段信息，直接使用DESCRIBE查询"""
        print(f"[DEBUG] _get_table_columns_for_reflection 被调用，dataset_path: {dataset_path}")
        try:
            # 验证输入参数
            if not dataset_path:
                logger.error("dataset_path参数为空")
                return []
                
            logger.info('开始获取表 ' + str(dataset_path) + ' 的字段信息')
            print(f"[DEBUG] 开始获取表 {dataset_path} 的字段信息")
            
            # 首先检查内存缓存
            if hasattr(self, 'table_columns_cache') and dataset_path in self.table_columns_cache:
                columns = self.table_columns_cache[dataset_path]
                logger.info('从内存缓存获取到表 ' + dataset_path + ' 的 ' + str(len(columns)) + ' 个字段')
                return columns
            
            # 缓存中没有，通过SQL查询获取
            logger.info('缓存中没有表 ' + dataset_path + ' 的字段信息，通过SQL查询获取')
            
            # 使用_format_table_name_for_sql方法正确格式化表名
            try:
                formatted_table_name = self._format_table_name_for_sql(dataset_path)
            except (ValueError, TypeError) as e:
                logger.error(f"表名格式化失败: {e}")
                print(f"[ERROR] 表名格式化失败: {e}")
                return []
                
            describe_sql = f'DESCRIBE {formatted_table_name}'
            logger.info(f"=== 重要：实际发送给Dremio的DESCRIBE SQL: {describe_sql} ===")
            logger.info(f"=== [DEBUG] dataset_path原始值: '{dataset_path}' ===")
            logger.info(f"=== [DEBUG] formatted_table_name: '{formatted_table_name}' ===")
            logger.info(f"=== [DEBUG] dataset_path类型: {type(dataset_path)} ===")
            logger.info(f"=== [DEBUG] dataset_path长度: {len(dataset_path)} ===")
            print(f"=== [DEBUG] 实际发送给Dremio的DESCRIBE SQL: {describe_sql} ===", flush=True)
            print(f"=== [DEBUG] dataset_path原始值: '{dataset_path}' ===", flush=True)
            print(f"=== [DEBUG] formatted_table_name: '{formatted_table_name}' ===", flush=True)
            print(f"=== [DEBUG] dataset_path类型: {type(dataset_path)} ===", flush=True)
            print(f"=== [DEBUG] dataset_path长度: {len(dataset_path)} ===", flush=True)
            result = self.execute_sql_query(describe_sql)
            logger.info(f"DESCRIBE查询结果: success={result.get('success')}, error={result.get('error')}, data_count={len(result.get('data', []))}")
            print(f"=== [DEBUG] DESCRIBE查询结果: success={result.get('success')}, error={result.get('error')}, data_count={len(result.get('data', []))} ===", flush=True)
            
            if not result['success']:
                error_msg = result.get('error', '未知错误')
                logger.error(f"DESCRIBE查询失败: {error_msg}")
                print(f"=== [ERROR] DESCRIBE查询失败: {error_msg} ===", flush=True)
                return []
            
            if result['success'] and result.get('data'):
                columns = []
                data = result['data']
                logger.info(f"DESCRIBE返回的数据行数: {len(data)}")
                
                # 检查数据格式 - DESCRIBE返回的是字典列表，每个字典包含COLUMN_NAME字段
                if isinstance(data, list) and len(data) > 0:
                    logger.info(f"DESCRIBE数据示例: {data[0] if data else 'empty'}")
                    for row in data:
                        if isinstance(row, dict) and 'COLUMN_NAME' in row:
                            column_name = row['COLUMN_NAME']
                            if column_name and isinstance(column_name, str):
                                columns.append(column_name)
                
                if columns:
                    logger.info('通过DESCRIBE查询获取到表 ' + dataset_path + ' 的 ' + str(len(columns)) + ' 个字段: ' + str(columns))
                    # 缓存字段信息
                    if not hasattr(self, 'table_columns_cache'):
                        self.table_columns_cache = {}
                    self.table_columns_cache[dataset_path] = columns
                    return columns
                else:
                    logger.error(f"DESCRIBE查询成功但未能提取到任何列名，原始数据示例: {data[0] if data else 'empty'}")
            else:
                logger.error(f"DESCRIBE查询失败: {result.get('error')}")
            
            # 如果DESCRIBE失败，尝试SELECT * LIMIT 0来获取字段
            logger.info(f"DESCRIBE失败，尝试使用SELECT获取字段信息")
            # 使用_format_table_name_for_sql方法正确格式化表名
            try:
                formatted_table_name_for_select = self._format_table_name_for_sql(dataset_path)
            except (ValueError, TypeError) as e:
                logger.error(f"SELECT语句表名格式化失败: {e}")
                print(f"[ERROR] SELECT语句表名格式化失败: {e}")
                return []
                
            select_sql = f'SELECT * FROM {formatted_table_name_for_select} LIMIT 0'
            logger.info(f'=== 重要：实际发送给Dremio的SELECT SQL: {select_sql} ===')
            print(f"=== [DEBUG] 实际发送给Dremio的SELECT SQL: {select_sql} ===")
            result = self.execute_sql_query(select_sql)
            logger.info(f"SELECT查询结果: success={result.get('success')}, error={result.get('error')}")
            
            if result['success']:
                # 从结果的columns信息中获取字段名
                columns_info = result.get('columns', [])
                logger.info(f"SELECT返回的列信息: {len(columns_info)} 个字段")
                if columns_info:
                    columns = [col.get('name', col.get('COLUMN_NAME', '')) for col in columns_info if col.get('name') or col.get('COLUMN_NAME')]
                    if columns:
                        logger.info(f"通过SELECT获取到表 {dataset_path} 的 {len(columns)} 个字段: {columns}")
                        if not hasattr(self, 'table_columns_cache'):
                            self.table_columns_cache = {}
                        self.table_columns_cache[dataset_path] = columns
                        return columns
            else:
                logger.error(f"SELECT查询也失败: {result.get('error')}")
            
            logger.error(f"无法获取表 {dataset_path} 的字段信息")
            return []
            
        except Exception as e:
            logger.error(f"获取表 {dataset_path} 字段信息异常: {e}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常详情: {str(e)}")
            print(f"[ERROR] 获取表 {dataset_path} 字段信息异常: {e}")
            print(f"[ERROR] 异常类型: {type(e).__name__}")
            print(f"[ERROR] 异常详情: {str(e)}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            print(f"[ERROR] 异常堆栈: {traceback.format_exc()}")
            return []
    
    def get_table_fields(self, dataset_path):
        """
        获取表的字段列表，过滤掉分区字段
        
        Args:
            dataset_path: 数据集路径，如 'minio.warehouse.ods.pdd.pdd_quality'
            
        Returns:
            List[str]: 字段名列表
        """
        try:
            # 格式化表名
            formatted_table_name = self._format_table_name_for_sql(dataset_path)
            describe_sql = f'DESCRIBE {formatted_table_name}'
            
            logger.info(f"获取表字段: {describe_sql}")
            
            # 执行DESCRIBE查询
            result = self.execute_sql_query(describe_sql)
            
            if result and result.get('success') and result.get('data'):
                # 从DESCRIBE结果中提取字段名
                all_fields = [row.get('COLUMN_NAME') for row in result['data'] if row.get('COLUMN_NAME')]
                
                # 过滤掉分区字段
                excluded_fields = ['dir0', 'dir1', 'dir2', 'dir3', 'dir4']
                fields = [field for field in all_fields if field not in excluded_fields]
                
                logger.info(f"所有字段: {all_fields}")
                logger.info(f"过滤后字段: {fields}")
                
                return fields
            else:
                logger.error(f"获取表字段失败: {result}")
                return []
                
        except Exception as e:
            logger.error(f"获取表字段异常: {e}")
            return []

    def _format_table_name_for_sql(self, dataset_path):
        """格式化表名用于SQL查询
        
        根据Dremio文档，表路径需要正确处理：
        - 如果路径包含特殊字符或空格，需要用双引号包围
        - 路径层级用点号分隔
        - 每个层级如果包含特殊字符需要单独加引号
        """
        # 验证输入参数
        if not dataset_path:
            logger.warning("dataset_path为空或None")
            raise ValueError("dataset_path不能为空")
            
        if not isinstance(dataset_path, str):
            logger.error(f"dataset_path必须是字符串类型，当前类型: {type(dataset_path)}")
            raise TypeError(f"dataset_path必须是字符串类型，当前类型: {type(dataset_path)}")
            
        # 去除首尾空白字符
        dataset_path = dataset_path.strip()
        if not dataset_path:
            logger.warning("dataset_path去除空白字符后为空")
            raise ValueError("dataset_path去除空白字符后不能为空")
            
        logger.info(f"格式化表名: {dataset_path}")
        
        # 检查是否是HTTP请求传递的字符串（被额外包装了一层引号）
        # 例如: "\"minio\".pddchat.ods" 应该变成 "minio".pddchat.ods
        # 特征：以引号开头结尾，且内部第二个字符也是引号（双引号开头）
        if (dataset_path.startswith('"') and dataset_path.endswith('"') and 
            len(dataset_path) > 3 and dataset_path[1] == '"'):
            # 去除外层引号
            dataset_path = dataset_path[1:-1]
            logger.info(f"去除HTTP传递的外层引号后: {dataset_path}")
            return dataset_path
        
        # 检查是否已经是正确格式的路径（包含引号的部分）
        if '"' in dataset_path:
            logger.info(f"路径已包含引号，直接返回: {dataset_path}")
            return dataset_path
            
        # 检查路径格式的合理性
        if len(dataset_path) > 500:  # 路径长度限制
            logger.error(f"dataset_path过长: {len(dataset_path)} 字符")
            raise ValueError(f"dataset_path过长，最大支持500字符，当前: {len(dataset_path)}")
            
        # 检查是否包含非法字符
        illegal_chars = ['\\', '|', '<', '>', '?', '*', '\n', '\r', '\t']
        for char in illegal_chars:
            if char in dataset_path:
                logger.error(f"dataset_path包含非法字符: '{char}'")
                raise ValueError(f"dataset_path包含非法字符: '{char}'")
        
        # 智能分割路径（正确处理引号）
        if '/' in dataset_path:
            # 处理路径格式如 "source/folder/table"
            parts = dataset_path.split('/')
            logger.info(f"按斜杠分割路径: {parts}")
        elif '.' in dataset_path:
            # 智能分割点号分隔的路径，保持引号完整性
            parts = self._smart_split_path(dataset_path)
            logger.info(f"按点号分割路径: {parts}")
        else:
            # 单个表名
            parts = [dataset_path]
            logger.info(f"单个表名: {parts}")
            
        # 验证分割后的部分
        if not parts or all(not part.strip() for part in parts):
            logger.error("路径分割后所有部分都为空")
            raise ValueError("路径格式无效，分割后所有部分都为空")
            
        # 格式化每个部分
        formatted_parts = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # 如果部分包含特殊字符、空格或可能的保留字，需要加引号
            needs_quotes = (
                ' ' in part or 
                '-' in part or 
                any(c in part for c in ['(', ')', '[', ']', '{', '}', ',', ';', ':', '@']) or
                part.upper() in ['SELECT', 'FROM', 'WHERE', 'ORDER', 'GROUP', 'HAVING', 'TABLE']
            )
            
            if needs_quotes:
                if not (part.startswith('"') and part.endswith('"')):
                    formatted_parts.append(f'"{part}"')
                else:
                    formatted_parts.append(part)
            else:
                formatted_parts.append(part)
                
        # 用点号连接所有部分
        result = '.'.join(formatted_parts)
        logger.info(f"格式化结果: {dataset_path} -> {result}")
        return result
        
    def _smart_split_path(self, path):
        """智能分割路径，保持引号完整性"""
        parts = []
        current_part = ""
        in_quotes = False
        i = 0
        
        while i < len(path):
            char = path[i]
            
            if char == '"':
                in_quotes = not in_quotes
                current_part += char
            elif char == '.' and not in_quotes:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            else:
                current_part += char
            
            i += 1
        
        # 添加最后一部分
        if current_part:
            parts.append(current_part)
            
        return parts
    
    def get_reflections_by_dataset_path(self, dataset_path):
        """通过SQL查询获取指定数据集的所有反射"""
        try:
            if not self.token:
                if not self._authenticate():
                    return {'success': False, 'error': '认证失败'}
            
            # 格式化数据集路径，确保与sys.reflections表中的格式一致
            formatted_path = self._format_table_name_for_sql(dataset_path)
            
            # 尝试多种格式的数据集路径查询
            dataset_formats = [
                formatted_path,  # 使用格式化后的路径
                dataset_path,    # 原始格式
            ]
            
            # 如果格式化路径不同于原始路径，添加更多变体
            if formatted_path != dataset_path:
                # 尝试不同的引号组合
                if '.' in dataset_path:
                    parts = dataset_path.split('.')
                    if len(parts) >= 3:  # 如 @admin.pdd.pdd_kpi_weekly
                        # 尝试给第一部分加双引号的格式
                        variant1 = f'"{parts[0]}".{".".join(parts[1:])}'
                        dataset_formats.append(variant1)
            
            for format_path in dataset_formats:
                # 使用SQL查询sys.reflections表获取指定数据集的反射
                # 注意：这里不再给format_path加单引号，因为format_path本身可能已经包含引号
                query_sql = f"SELECT reflection_id, dataset_name, type, status FROM sys.reflections WHERE dataset_name = '{format_path}'"
                logger.info(f"尝试查询反射SQL: {query_sql}")
                
                result = self.execute_sql_query(query_sql)
                
                if result['success']:
                    rows = result.get('data', [])
                    
                    if rows:  # 如果找到了反射
                        reflections = []
                        for row in rows:
                            # 处理字典格式的返回结果
                            if isinstance(row, dict):
                                reflections.append({
                                    'reflection_id': row.get('reflection_id'),
                                    'dataset_name': row.get('dataset_name'),
                                    'type': row.get('type'),
                                    'status': row.get('status'),
                                    'name': f"reflection_{row.get('reflection_id')}"
                                })
                            else:
                                # 处理列表格式的返回结果
                                reflections.append({
                                    'reflection_id': row[0] if len(row) > 0 else None,
                                    'dataset_name': row[1] if len(row) > 1 else None,
                                    'type': row[2] if len(row) > 2 else None,
                                    'status': row[3] if len(row) > 3 else None,
                                    'name': f"reflection_{row[0]}" if len(row) > 0 else None
                                })
                        
                        logger.info(f"通过SQL查询找到 {len(reflections)} 个反射，使用格式: {format_path}")
                        return {
                            'success': True,
                            'reflections': reflections
                        }
            
            # 如果所有格式都没找到反射
            logger.warning(f"未找到数据集 {dataset_path} 的任何反射")
            return {
                'success': True,
                'reflections': []
            }
                
        except Exception as e:
            logger.error(f"查询反射异常: {e}")
            return {
                'success': False,
                'error': f'查询反射异常: {str(e)}'
            }
    
    def refresh_reflection_by_recreate(self, dataset_path, dataset_id=None):
        """通过删除-创建方式刷新反射（终版方法）"""
        try:
            if not self.token:
                if not self._authenticate():
                    return {'success': False, 'error': '认证失败'}
            
            logger.info(f"开始使用删除-创建方式刷新数据集反射: {dataset_path}")
            
            # 1. 获取现有反射（优先使用dataset_path查询）
            existing_reflections = []
            
            # 首先尝试通过SQL查询获取反射
            reflections_result = self.get_reflections_by_dataset_path(dataset_path)
            if reflections_result['success']:
                existing_reflections = reflections_result['reflections']
                logger.info(f"通过SQL查询找到 {len(existing_reflections)} 个现有反射")
            elif dataset_id:
                # 如果SQL查询失败且提供了dataset_id，则使用API方式
                reflections_result = self.get_dataset_reflections(dataset_id)
                if reflections_result['success']:
                    existing_reflections = reflections_result['reflections']
                    logger.info(f"通过API查询找到 {len(existing_reflections)} 个现有反射")
            
            # 2. 删除所有现有反射
            deleted_count = 0
            failed_deletions = []
            
            # 首先通过SQL查询获取正确的反射名称，尝试多种格式
            formatted_dataset_path = self._format_table_name_for_sql(dataset_path)
            
            # 准备多种可能的数据集名称格式进行查询
            dataset_name_variants = [
                dataset_path,  # 原始格式
                formatted_dataset_path,  # 格式化后的格式
            ]
            
            # 对于包含@admin的路径，添加更多变体
            if '@admin' in dataset_path:
                # 去除外层引号的格式
                if dataset_path.startswith('"') and dataset_path.endswith('"'):
                    unquoted = dataset_path[1:-1]
                    dataset_name_variants.append(unquoted)
                
                # 添加不同的引号组合
                parts = dataset_path.replace('"', '').split('.')
                if len(parts) >= 3:
                    # @admin.pdd.pdd_kpi_weekly 格式
                    variant1 = '.'.join(parts)
                    dataset_name_variants.append(variant1)
                    
                    # "@admin".pdd."pdd_kpi_weekly" 格式
                    variant2 = f'"{parts[0]}".{parts[1]}."{parts[2]}"'
                    dataset_name_variants.append(variant2)
                    
                    # 关键修复：添加实际存储的格式 "@admin".pdd.pdd_kpi_weekly（最后的表名不带引号）
                    variant3 = f'"{parts[0]}".{parts[1]}.{parts[2]}'
                    dataset_name_variants.append(variant3)
            
            # 去重
            dataset_name_variants = list(set(dataset_name_variants))
            logger.info(f"尝试查询反射的数据集名称变体: {dataset_name_variants}")
            
            reflection_names_to_delete = []
            for variant in dataset_name_variants:
                query_reflections_sql = f"SELECT reflection_name FROM sys.reflections WHERE dataset_name='{variant}'"
                logger.info(f"执行反射查询SQL: {query_reflections_sql}")
                reflections_query_result = self.execute_sql_query(query_reflections_sql)
                
                if reflections_query_result['success'] and reflections_query_result['data']:
                    found_reflections = [row['reflection_name'] for row in reflections_query_result['data']]
                    reflection_names_to_delete.extend(found_reflections)
                    logger.info(f"使用格式 '{variant}' 找到 {len(found_reflections)} 个反射: {found_reflections}")
                    break  # 找到反射后就停止尝试其他格式
                else:
                    logger.info(f"使用格式 '{variant}' 未找到反射")
            
            # 去重反射名称
            reflection_names_to_delete = list(set(reflection_names_to_delete))
            logger.info(f"最终找到 {len(reflection_names_to_delete)} 个反射名称: {reflection_names_to_delete}")
            
            for reflection_name in reflection_names_to_delete:
                # 使用正确的ALTER DATASET语法删除反射
                drop_sql = f"ALTER DATASET {formatted_dataset_path} DROP REFLECTION \"{reflection_name}\""
                logger.info(f"执行删除反射SQL: {drop_sql}")
                    
                delete_result = self.execute_sql_query(drop_sql)
                
                if delete_result['success']:
                    deleted_count += 1
                    logger.info(f"成功删除反射: {reflection_name}")
                    time.sleep(1)  # 等待删除完成
                else:
                    failed_deletions.append({
                        'reflection_name': reflection_name,
                        'error': delete_result['error']
                    })
                    logger.error(f"删除反射失败: {reflection_name}, 错误: {delete_result['error']}")
            
            # 3. 创建新的原始反射
            table_name = dataset_path.split('.')[-1].replace('"', '')
            new_reflection_name = table_name + '_refreshed_reflection'
            
            create_result = self.create_raw_reflection_by_sql(dataset_path, new_reflection_name)
            
            if create_result['success']:
                logger.info(f"成功创建新反射: {new_reflection_name}")
                
                return {
                    'success': True,
                    'message': f'反射刷新完成：删除了 {deleted_count} 个旧反射，创建了新反射 {new_reflection_name}',
                    'details': {
                        'dataset_path': dataset_path,
                        'deleted_reflections': deleted_count,
                        'failed_deletions': failed_deletions,
                        'new_reflection_name': new_reflection_name,
                        'reflections_total': len(existing_reflections),
                        'reflections_refreshed': 1 if create_result['success'] else 0,
                        'reflections_failed': len(failed_deletions)
                    }
                }
            else:
                logger.error(f"创建新反射失败: {create_result['error']}")
                return {
                    'success': False,
                    'error': f'删除了 {deleted_count} 个旧反射，但创建新反射失败: {create_result["error"]}',
                    'details': {
                        'dataset_path': dataset_path,
                        'deleted_reflections': deleted_count,
                        'failed_deletions': failed_deletions,
                        'creation_error': create_result['error']
                    }
                }
                
        except Exception as e:
            logger.error(f"刷新反射异常: {e}")
            return {
                'success': False,
                'error': f'刷新反射异常: {str(e)}'
            }

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, schema_cache):
        self.schema_cache = schema_cache
        self.auto_refresh_thread = None
        self.auto_refresh_running = False
    
    def start_auto_refresh(self):
        """启动自动刷新"""
        if not self.auto_refresh_running:
            self.auto_refresh_running = True
            self.auto_refresh_thread = threading.Thread(target=self._auto_refresh_worker)
            self.auto_refresh_thread.daemon = True
            self.auto_refresh_thread.start()
            logger.info("缓存自动刷新已启动")
    
    def stop_auto_refresh(self):
        """停止自动刷新"""
        self.auto_refresh_running = False
        if self.auto_refresh_thread:
            self.auto_refresh_thread.join(timeout=5)
        logger.info("缓存自动刷新已停止")
    
    def _auto_refresh_worker(self):
        """自动刷新工作线程"""
        while self.auto_refresh_running:
            try:
                if self.schema_cache.is_expired():
                    logger.info("检测到缓存过期，开始自动刷新...")
                    self.schema_cache.refresh_all(dremio_client)
                
                # 每5分钟检查一次
                for _ in range(300):  # 5分钟 = 300秒
                    if not self.auto_refresh_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"自动刷新异常: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        stats = self.schema_cache.stats()
        stats['auto_refresh_running'] = self.auto_refresh_running
        return stats

class DownloadLinkManager:
    """下载链接管理器"""
    
    def __init__(self, link_expiry_minutes=30):
        self.links = {}  # {link_id: {sql, filename, format, created_at}}
        self.expiry_time = timedelta(minutes=link_expiry_minutes)
        self.lock = threading.Lock()
    
    def generate_link(self, sql, filename, file_format):
        """生成下载链接ID"""
        link_id = str(uuid.uuid4())
        
        with self.lock:
            self.links[link_id] = {
                'sql': sql,
                'filename': filename,
                'format': file_format,
                'created_at': datetime.now()
            }
        
        logger.info(f"生成下载链接: {link_id} for {filename}")
        return link_id
    
    def get_link_info(self, link_id):
        """获取链接信息"""
        with self.lock:
            link_info = self.links.get(link_id)
            
            if link_info:
                # 检查是否过期
                if datetime.now() - link_info['created_at'] > self.expiry_time:
                    del self.links[link_id]
                    return None
                
                return link_info
            
            return None
    
    def cleanup_expired_links(self):
        """清理过期链接"""
        with self.lock:
            current_time = datetime.now()
            expired_links = []
            
            for link_id, link_info in self.links.items():
                if current_time - link_info['created_at'] > self.expiry_time:
                    expired_links.append(link_id)
            
            for link_id in expired_links:
                del self.links[link_id]
            
            if expired_links:
                logger.info(f"清理了 {len(expired_links)} 个过期下载链接")

# 初始化组件
schema_cache = SchemaCache(refresh_interval_minutes=30)
# 从环境变量获取Dremio连接配置
dremio_host = os.environ.get('DREMIO_HOST', 'localhost')
dremio_port = int(os.environ.get('DREMIO_PORT', 9047))
dremio_username = os.environ.get('DREMIO_USERNAME', 'admin')
dremio_password = os.environ.get('DREMIO_PASSWORD', 'admin123')
dremio_client = DremioClient(host=dremio_host, port=dremio_port, username=dremio_username, password=dremio_password)
cache_manager = CacheManager(schema_cache)
download_manager = DownloadLinkManager()

# Arrow Flight客户端（用于高速数据导出）
try:
    import pyarrow.flight as flight
    import pyarrow as pa
    
    class DremioFlightClient:
        """Dremio Arrow Flight客户端 - 用于高速数据传输"""
        
        def __init__(self, host=None, port=32010, username=None, password=None):
            # 使用环境变量或默认值
            self.host = host or os.environ.get('DREMIO_HOST', 'localhost')
            self.username = username or os.environ.get('DREMIO_USERNAME', 'admin')
            self.password = password or os.environ.get('DREMIO_PASSWORD', 'admin123')
            self.port = port
            self.client = None
            self._connect()
        
        def _connect(self):
            """连接到Dremio Flight服务"""
            try:
                location = flight.Location.for_grpc_tcp(self.host, self.port)
                self.client = flight.FlightClient(location)
                
                # 认证
                auth_handler = flight.BasicAuthHandler(self.username, self.password)
                self.client.authenticate(auth_handler)
                
                logger.info(f"Arrow Flight连接成功: {self.host}:{self.port}")
                
            except Exception as e:
                logger.warning(f"Arrow Flight连接失败: {e}，将使用REST API作为备选")
                self.client = None
        
        def execute_query_to_dataframe(self, sql):
            """执行查询并返回DataFrame"""
            if not self.client:
                raise Exception("Arrow Flight客户端未连接")
            
            try:
                # 创建Flight描述符
                flight_desc = flight.FlightDescriptor.for_command(sql.encode('utf-8'))
                
                # 获取Flight信息
                flight_info = self.client.get_flight_info(flight_desc)
                
                # 读取数据
                reader = self.client.do_get(flight_info.endpoints[0].ticket)
                
                # 转换为DataFrame
                table = reader.read_all()
                df = table.to_pandas()
                
                logger.info(f"Arrow Flight查询成功，返回 {len(df)} 行数据")
                return df
                
            except Exception as e:
                logger.error(f"Arrow Flight查询失败: {e}")
                raise e
    
    # 初始化Flight客户端
    dremio_flight_client = DremioFlightClient()
    
except ImportError:
    logger.warning("PyArrow未安装，将仅使用REST API进行数据查询")
    dremio_flight_client = None

# 性能监控装饰器
def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 执行时间: {execution_time:.2f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败 ({execution_time:.2f}秒): {e}")
            raise
    return wrapper

# Flask路由

@app.route('/api/connection/test', methods=['GET'])
def test_dremio_connection():
    """测试Dremio连接"""
    result = dremio_client.test_connection()
    status_code = 200 if result.get('success') else 500
    return jsonify(result), status_code

@app.route('/api/schema', methods=['GET'])
@monitor_performance
def get_schema_info():
    """获取Schema信息（带缓存）"""
    try:
        catalog = request.args.get('catalog', 'default')
        schema = request.args.get('schema', 'default')
        
        logger.info(f"获取Schema信息请求: catalog={catalog}, schema={schema}")
        
        # 检查缓存
        cached_result = schema_cache.get(catalog, schema)
        
        if cached_result:
            logger.info(f"Schema缓存命中: {catalog}.{schema}")
            return jsonify({
                **cached_result,
                'cached': True,
                'timestamp': datetime.now().isoformat()
            })
        
        # 从Dremio获取最新数据
        result = dremio_client.get_complete_schema_with_columns()
        
        if result.get('success'):
            # 更新缓存
            schema_cache.set(catalog, schema, result['data'])
            
            return jsonify({
                **result['data'],
                'cached': False,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'error': result.get('error', '获取表结构失败'),
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"获取表结构异常: {e}")
        return jsonify({
            'error': f'服务器内部错误: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/query', methods=['POST'])
@monitor_performance
def execute_sql_query():
    """4. SQL查询功能"""
    try:
        logger.info(f"=== API路由 /api/query 收到请求 ===")
        data = request.get_json()
        logger.info(f"请求数据: {data}")
        
        if not data or 'sql' not in data:
            logger.error("请求体中缺少sql字段")
            return jsonify({
                'success': False,
                'error': '请求体中缺少sql字段',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        sql = data['sql'].strip()
        timeout = data.get('timeout', None)  # 默认无超时限制
        
        logger.info(f"=== 接收到的SQL查询详情 ===")
        logger.info(f"原始SQL: {repr(sql)}")
        logger.info(f"SQL内容: {sql}")
        logger.info(f"SQL长度: {len(sql)}")
        logger.info(f"超时设置: {'无限制' if timeout is None else f'{timeout}秒'}")
        
        if not sql:
            logger.error("SQL查询为空")
            return jsonify({
                'success': False,
                'error': 'SQL查询不能为空',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        logger.info(f"开始执行SQL查询: {sql}")
        
        # 执行查询
        result = dremio_client.execute_sql_query(sql, timeout)
        logger.info(f"SQL查询执行完成，结果: {result}")
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data', []),
                'columns': result.get('columns', []),
                'row_count': result.get('row_count', 0),
                'execution_time': result.get('execution_time', 0),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'SQL查询执行失败'),
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"SQL查询异常: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/table/details', methods=['POST'])
@monitor_performance
def get_table_details():
    """5. 获取表的详细列结构信息"""
    try:
        data = request.get_json()
        if not data or 'table_path' not in data:
            return jsonify({
                'success': False,
                'error': 'table_path is required in request body',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        table_path = data['table_path']
        
        logger.info(f"获取表详细信息请求: table_path={table_path}")
        
        # 检查缓存
        cached_result = schema_cache.get_table_details(table_path)
        
        if cached_result:
            return jsonify({
                **cached_result,
                'cached': True,
                'timestamp': datetime.now().isoformat()
            })
        
        # 从Dremio API获取表详细信息
        result = dremio_client.get_table_details_by_api(table_path)
        
        if result.get('success'):
            # 缓存结果
            schema_cache.set_table_details(table_path, result['data'])
            
            return jsonify({
                **result['data'],
                'cached': False,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '获取表详细信息失败'),
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"获取表详细信息异常: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

# 缓存管理接口
@app.route('/api/cache/refresh', methods=['POST'])
def refresh_cache():
    """手动刷新缓存"""
    try:
        schema_cache.refresh_all(dremio_client)
        return jsonify({
            'success': True,
            'message': '缓存刷新完成',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"手动刷新缓存失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """清空所有缓存"""
    try:
        cache_type = request.json.get('type', 'all') if request.json else 'all'
        
        if cache_type == 'schema':
            schema_cache.clear()
            message = 'Schema缓存已清空'
        elif cache_type == 'table_details':
            schema_cache.clear_table_details()
            message = '表详细信息缓存已清空'
        else:
            schema_cache.clear()
            schema_cache.clear_table_details()
            message = '所有缓存已清空'
        
        return jsonify({
            'success': True,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/stats', methods=['GET'])
def get_cache_stats():
    """获取缓存统计信息"""
    try:
        stats = cache_manager.get_cache_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dataset/refresh', methods=['POST'])
@monitor_performance
def refresh_dataset():
    """刷新指定数据集的反射"""
    try:
        data = request.get_json()
        
        if not data or 'dataset_path' not in data:
            return jsonify({
                'success': False,
                'error': '请求体中缺少dataset_path字段',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        dataset_path = data['dataset_path'].strip()
        timeout_secs = data.get('timeout', 600)  # 默认10分钟超时
        
        if not dataset_path:
            return jsonify({
                'success': False,
                'error': '数据集路径不能为空',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        logger.info(f"刷新数据集请求: {dataset_path}")
        
        # 执行数据集刷新
        result = dremio_client.refresh_dataset(dataset_path, timeout_secs)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message', '数据集刷新完成'),
                'execution_time': result.get('execution_time', 0),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '数据集刷新失败'),
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"数据集刷新异常: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/dataset/refresh-metadata', methods=['POST'])
@monitor_performance
def refresh_dataset_metadata():
    """刷新数据集元数据 - 使用ALTER PDS REFRESH METADATA命令"""
    try:
        data = request.get_json()
        
        if not data or 'dataset_path' not in data:
            return jsonify({
                'success': False,
                'error': '请求体中缺少dataset_path字段',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        dataset_path = data['dataset_path'].strip()
        timeout_secs = data.get('timeout', 600)  # 默认10分钟超时
        
        if not dataset_path:
            return jsonify({
                'success': False,
                'error': '数据集路径不能为空',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        logger.info(f"刷新数据集元数据请求: {dataset_path}")
        
        # 执行数据集元数据刷新
        result = dremio_client.refresh_dataset_metadata(dataset_path, timeout_secs)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message', '数据集元数据刷新完成'),
                'execution_time': result.get('execution_time', 0),
                'sql_executed': result.get('sql_executed', ''),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '数据集元数据刷新失败'),
                'sql_executed': result.get('sql_executed', ''),
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"数据集元数据刷新异常: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/export/xlsx', methods=['POST'])
def export_data_to_xlsx():
    """导出Dremio数据到XLSX文件"""
    logger.info("=== 进入 export_data_to_xlsx 函数 ===")
    try:
        data = request.get_json()
        logger.info(f"接收到导出请求数据: {data}")
        
        if not data:
            logger.error("请求数据为空")
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        sql = data.get('sql')
        # 支持两种参数名：host_path 和 output_path
        host_path = data.get('host_path') or data.get('output_path')  # 主机路径
        filename = data.get('filename', 'export_data.xlsx')
        logger.info(f"解析后的参数: sql={sql}, host_path={host_path}, filename={filename}")
        
        logger.info(f"解析参数 - SQL: {sql}, host_path: {host_path}, filename: {filename}")
        
        if not sql:
            return jsonify({
                'success': False,
                'error': 'SQL查询语句不能为空'
            }), 400
        
        if not host_path:
            return jsonify({
                'success': False,
                'error': '主机输出路径不能为空，请提供host_path或output_path参数'
            }), 400
        
        # 容器内的映射路径（固定为/host_exports）
        container_path = '/host_exports'
        
        # 确保容器内输出目录存在
        os.makedirs(container_path, exist_ok=True)
        
        # 完整的文件路径（容器内路径）
        full_path = os.path.join(container_path, filename)
        
        logger.info(f"开始执行SQL查询并导出到: {full_path}")
        
        # 使用Arrow Flight执行查询
        try:
            df = dremio_flight_client.execute_query_to_dataframe(sql)
        except Exception as flight_error:
            logger.warning(f"Arrow Flight查询失败，尝试使用REST API: {flight_error}")
            # 如果Arrow Flight失败，回退到REST API
            result = dremio_client.execute_sql_query(sql)
            if result['success']:
                # 将结果转换为DataFrame
                rows = result['data']  # data已经是rows列表
                
                if rows:
                    # 从第一行数据推断列名
                    if isinstance(rows[0], dict):
                        # 如果行是字典格式
                        df = pd.DataFrame(rows)
                    else:
                        # 如果行是列表格式，需要获取列信息
                        # 先执行一个简单查询获取列信息
                        schema_sql = f"SELECT * FROM ({sql}) LIMIT 0"
                        schema_result = dremio_client.execute_sql_query(schema_sql)
                        if schema_result['success']:
                            df = pd.DataFrame(rows)
                        else:
                            # 如果无法获取schema，使用通用列名
                            df = pd.DataFrame(rows)
                else:
                    df = pd.DataFrame()
            else:
                raise Exception(f"REST API查询也失败: {result['error']}")
        
        # 导出到XLSX
        with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
        
        logger.info(f"数据导出成功: {full_path}, 共{len(df)} 行")
        
        # 计算主机路径
        host_file_path = os.path.join(host_path, filename)
        
        return jsonify({
            'success': True,
            'message': f'数据导出成功',
            'data': {
                'host_file_path': host_file_path,  # 主机文件路径
                'container_file_path': full_path,  # 容器文件路径
                'rows_exported': len(df),
                'columns': list(df.columns) if not df.empty else [],
                'file_size_mb': round(os.path.getsize(full_path) / (1024 * 1024), 2) if os.path.exists(full_path) else 0
            }
        })
        
    except Exception as e:
        logger.error(f"数据导出失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download/csv', methods=['POST', 'OPTIONS'])
def download_csv():
    """直接触发浏览器下载CSV文件 - 专为Dify工作流优化"""
    # 处理 CORS 预检请求
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    logger.info("=== 进入 download_csv 函数 - Dify浏览器下载模式 ===")
    try:
        data = request.get_json()
        logger.info(f"接收到CSV下载请求: {data}")
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        sql = data.get('sql')
        filename = data.get('filename', 'export_data.csv')
        
        logger.info(f"解析参数 - SQL: {sql}, filename: {filename}")
        
        if not sql:
            return jsonify({
                'success': False,
                'error': 'SQL查询语句不能为空'
            }), 400
        
        logger.info(f"开始执行SQL查询并生成CSV流: {sql}")
        
        # 使用Arrow Flight执行查询
        try:
            df = dremio_flight_client.execute_query_to_dataframe(sql)
        except Exception as flight_error:
            logger.warning(f"Arrow Flight查询失败，尝试使用REST API: {flight_error}")
            # 如果Arrow Flight失败，回退到REST API
            result = dremio_client.execute_sql_query(sql)
            if result['success']:
                rows = result['data']
                if rows:
                    if isinstance(rows[0], dict):
                        df = pd.DataFrame(rows)
                    else:
                        df = pd.DataFrame(rows)
                else:
                    df = pd.DataFrame()
            else:
                raise Exception(f"REST API查询也失败: {result['error']}")
        
        logger.info(f"查询成功，共 {len(df)} 行数据，开始生成CSV")
        
        # 强制浏览器下载模式 - 生成CSV内容
        def generate_csv():
            # 使用StringIO作为缓冲区
            from io import StringIO
            output = StringIO()
            df.to_csv(output, index=False, encoding='utf-8')
            csv_content = output.getvalue()
            output.close()
            
            # 分块发送数据
            chunk_size = 8192  # 8KB chunks
            for i in range(0, len(csv_content), chunk_size):
                yield csv_content[i:i + chunk_size]
        
        # 设置强制下载的响应头
        response = Response(
            generate_csv(),
            mimetype='application/octet-stream',  # 使用通用二进制类型强制下载
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/octet-stream',  # 强制下载而非预览
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Expose-Headers': 'Content-Disposition, Content-Type',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Content-Type-Options': 'nosniff',  # 防止MIME类型嗅探
                'Content-Transfer-Encoding': 'binary'  # 明确指定二进制传输
            }
        )
        
        logger.info(f"CSV下载响应已生成: {filename}")
        return response
        
    except Exception as e:
        logger.error(f"CSV下载失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download/xlsx', methods=['POST', 'OPTIONS'])
def download_xlsx():
    """直接触发浏览器下载Excel文件 - 专为Dify工作流优化"""
    # 处理 CORS 预检请求
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    logger.info("=== 进入 download_xlsx 函数 - Dify浏览器下载模式 ===")
    try:
        data = request.get_json()
        logger.info(f"接收到Excel下载请求: {data}")
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        sql = data.get('sql')
        filename = data.get('filename', 'export_data.xlsx')
        
        logger.info(f"解析参数 - SQL: {sql}, filename: {filename}")
        
        if not sql:
            return jsonify({
                'success': False,
                'error': 'SQL查询语句不能为空'
            }), 400
        
        logger.info(f"开始执行SQL查询并生成Excel流: {sql}")
        
        # 使用Arrow Flight执行查询
        try:
            df = dremio_flight_client.execute_query_to_dataframe(sql)
        except Exception as flight_error:
            logger.warning(f"Arrow Flight查询失败，尝试使用REST API: {flight_error}")
            # 如果Arrow Flight失败，回退到REST API
            result = dremio_client.execute_sql_query(sql)
            if result['success']:
                rows = result['data']
                if rows:
                    if isinstance(rows[0], dict):
                        df = pd.DataFrame(rows)
                    else:
                        df = pd.DataFrame(rows)
                else:
                    df = pd.DataFrame()
            else:
                raise Exception(f"REST API查询也失败: {result['error']}")
        
        logger.info(f"查询成功，共 {len(df)} 行数据，开始生成Excel")
        
        # 强制浏览器下载模式 - 生成Excel内容
        def generate_excel():
            from io import BytesIO
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Data', index=False)
            
            excel_content = output.getvalue()
            output.close()
            
            # 分块发送数据
            chunk_size = 8192  # 8KB chunks
            for i in range(0, len(excel_content), chunk_size):
                yield excel_content[i:i + chunk_size]
        
        # 设置强制下载的响应头
        response = Response(
            generate_excel(),
            mimetype='application/octet-stream',  # 使用通用二进制类型强制下载
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/octet-stream',  # 强制下载而非预览
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Expose-Headers': 'Content-Disposition, Content-Type',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Content-Type-Options': 'nosniff',  # 防止MIME类型嗅探
                'Content-Transfer-Encoding': 'binary'  # 明确指定二进制传输
            }
        )
        
        logger.info(f"Excel下载响应已生成: {filename}")
        return response
        
    except Exception as e:
        logger.error(f"Excel下载失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate_download_link', methods=['POST'])
def generate_download_link():
    """生成临时下载链接"""
    logger.info("=== 进入 generate_download_link 函数 ===")
    try:
        data = request.get_json()
        logger.info(f"接收到生成下载链接请求: {data}")
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        sql = data.get('sql')
        filename = data.get('filename', 'export_data.csv')
        file_format = data.get('format', 'csv').lower()  # csv 或 xlsx
        
        if not sql:
            return jsonify({
                'success': False,
                'error': 'SQL查询语句不能为空'
            }), 400
        
        if file_format not in ['csv', 'xlsx']:
            return jsonify({
                'success': False,
                'error': '文件格式只支持 csv 或 xlsx'
            }), 400
        
        # 生成下载链接ID
        link_id = download_manager.generate_link(sql, filename, file_format)
        
        # 构建完整的下载URL
        # 强制使用localhost:8000确保浏览器可以访问
        host = 'localhost:8000'
        scheme = 'http'
        logger.info(f"使用固定主机: {host}, Scheme: {scheme}")
        download_url = f"{scheme}://{host}/api/download_file/{link_id}"
        logger.info(f"构建的完整下载URL: {download_url}")
        
        # 只返回下载URL，不返回其他内容
        return download_url, 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"生成下载链接失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download_file/<link_id>', methods=['GET'])
def download_file_by_link(link_id: str):
    """通过临时链接下载文件"""
    logger.info(f"=== 进入 download_file_by_link 函数，link_id: {link_id} ===")
    try:
        # 清理过期链接
        download_manager.cleanup_expired_links()
        
        # 获取链接信息
        link_info = download_manager.get_link_info(link_id)
        
        if not link_info:
            return jsonify({
                'success': False,
                'error': '下载链接不存在或已过期'
            }), 404
        
        sql = link_info['sql']
        filename = link_info['filename']
        file_format = link_info['format']
        
        logger.info(f"开始执行SQL查询: {sql[:100]}...")
        
        # 使用Arrow Flight执行查询
        try:
            df = dremio_flight_client.execute_query_to_dataframe(sql)
        except Exception as flight_error:
            logger.warning(f"Arrow Flight查询失败，尝试使用REST API: {flight_error}")
            # 如果Arrow Flight失败，回退到REST API
            result = dremio_client.execute_sql_query(sql)
            if result['success']:
                rows = result['data']
                if rows:
                    if isinstance(rows[0], dict):
                        df = pd.DataFrame(rows)
                    else:
                        df = pd.DataFrame(rows)
                else:
                    df = pd.DataFrame()
            else:
                raise Exception(f"REST API查询也失败: {result['error']}")
        
        logger.info(f"查询成功，共 {len(df)} 行数据，开始生成 {file_format.upper()} 文件")
        
        if file_format == 'csv':
            # 生成CSV
            output = StringIO()
            df.to_csv(output, index=False, encoding='utf-8')
            csv_content = output.getvalue()
            output.close()
            
            # 创建BytesIO对象用于send_file
            file_buffer = BytesIO(csv_content.encode('utf-8'))
            
            return send_file(
                file_buffer,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
            
        elif file_format == 'xlsx':
            # 生成Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Data', index=False)
            
            excel_content = output.getvalue()
            output.close()
            
            # 创建BytesIO对象用于send_file
            file_buffer = BytesIO(excel_content)
            
            return send_file(
                file_buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        
        else:
            return jsonify({
                'success': False,
                'error': '不支持的文件格式'
            }), 400
            
    except Exception as e:
        logger.error(f"下载文件时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'下载失败: {str(e)}'
        }), 500

@app.route('/api/reflection/refresh', methods=['POST'])
def refresh_reflection_endpoint():
    """通过删除-创建方式刷新反射端点"""
    logger.info(f"refresh_reflection_endpoint 被调用")
    try:
        # 获取请求数据
        data = request.get_json()
        logger.info(f"接收到的请求数据: {data}")
        if not data or 'dataset_path' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必需的参数: dataset_path'
            }), 400
        
        dataset_path = data['dataset_path']
        dataset_id = data.get('dataset_id')  # 可选参数
        
        logger.info(f"开始刷新反射: {dataset_path}")
        
        # 调用DremioClient的refresh_reflection_by_recreate方法
        result = dremio_client.refresh_reflection_by_recreate(dataset_path, dataset_id)
        
        if result['success']:
            logger.info(f"反射刷新成功: {dataset_path}")
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result.get('details', {})
            })
        else:
            logger.error(f"反射刷新失败: {dataset_path}, 错误: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error'],
                'data': result.get('details', {})
            }), 500
            
    except Exception as e:
        logger.error(f"刷新反射时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'刷新反射失败: {str(e)}'
        }), 500

@app.route('/api/debug/columns', methods=['POST'])
@monitor_performance
def debug_get_columns_endpoint():
    """调试获取表字段信息的API接口"""
    try:
        data = request.get_json()
        dataset_path = data.get('dataset_path')
        
        if not dataset_path:
            return jsonify({
                'success': False,
                'error': '缺少dataset_path参数'
            }), 400
        
        logger.info(f"调试获取字段信息: {dataset_path}")
        columns = dremio_client.get_table_fields(dataset_path)
        
        return jsonify({
            'success': True,
            'dataset_path': dataset_path,
            'columns': columns,
            'column_count': len(columns) if columns else 0
        })
            
    except Exception as e:
        logger.error(f"调试获取字段API异常: {e}")
        return jsonify({
            'success': False,
            'error': f'API异常: {str(e)}'
        }), 500

@app.route('/api/debug/get_columns', methods=['POST'])
@monitor_performance
def debug_get_columns_detailed():
    """详细调试获取表字段信息的API接口"""
    try:
        data = request.get_json()
        dataset_path = data.get('dataset_path')
        
        if not dataset_path:
            return jsonify({
                'success': False,
                'error': '缺少dataset_path参数'
            }), 400
        
        logger.info(f"详细调试获取字段信息: {dataset_path}")
        
        # 测试表名格式化
        formatted_name = dremio_client._format_table_name_for_sql(dataset_path)
        logger.info(f"格式化后的表名: {formatted_name}")
        
        # 测试DESCRIBE查询
        describe_sql = f'DESCRIBE {formatted_name}'
        logger.info(f"执行DESCRIBE查询: {describe_sql}")
        describe_result = dremio_client.execute_sql_query(describe_sql)
        
        # 测试SELECT查询
        select_sql = f'SELECT * FROM {formatted_name} LIMIT 0'
        logger.info(f"执行SELECT查询: {select_sql}")
        select_result = dremio_client.execute_sql_query(select_sql)
        
        # 调用获取字段方法
        columns = dremio_client.get_table_fields(dataset_path)
        
        return jsonify({
            'success': True,
            'dataset_path': dataset_path,
            'formatted_name': formatted_name,
            'describe_result': {
                'success': describe_result.get('success'),
                'data_count': len(describe_result.get('data', [])),
                'sample_data': describe_result.get('data', [])[:3],
                'columns_info': describe_result.get('columns', [])
            },
            'select_result': {
                'success': select_result.get('success'),
                'columns_info': select_result.get('columns', [])
            },
            'extracted_columns': columns,
            'column_count': len(columns) if columns else 0
        })
            
    except Exception as e:
        logger.error(f"详细调试获取字段API异常: {e}")
        return jsonify({
            'success': False,
            'error': f'API异常: {str(e)}'
        }), 500

@app.route('/api/debug/build_sql', methods=['GET', 'POST'])
@monitor_performance
def debug_build_sql():
    """调试API - 构建SQL字符串"""
    try:
        # 支持GET和POST请求
        if request.method == 'GET':
            dataset_path = request.args.get('dataset_path')
        else:
            data = request.get_json() or {}
            dataset_path = data.get('dataset_path')
        
        if not dataset_path:
            return jsonify({
                'success': False,
                'error': '缺少dataset_path参数'
            }), 400
        
        logger.info(f"调试API - 构建SQL字符串: {dataset_path}")
        
        # 格式化表名
        formatted_table_name = dremio_client._format_table_name_for_sql(dataset_path)
        
        # 构建DESCRIBE SQL
        describe_sql = f"DESCRIBE {formatted_table_name}"
        
        # 构建SELECT SQL（用于获取列信息）
        select_sql = f"SELECT * FROM {formatted_table_name} LIMIT 0"
        
        # 构建ALTER REFLECTION SQL（示例）
        # 先处理字符串替换，避免f-string中的引号问题
        clean_path = dataset_path.replace('.', '_').replace('"', '').replace('-', '_')
        reflection_name = f"reflection_{clean_path}"
        alter_sql = f"ALTER TABLE {formatted_table_name} CREATE REFLECTION {reflection_name} USING DISPLAY (col1, col2)"
        
        # 构建刷新反射SQL
        refresh_sql = f"ALTER TABLE {formatted_table_name} REFRESH REFLECTION {reflection_name}"
        
        return jsonify({
            'success': True,
            'dataset_path': dataset_path,
            'formatted_table_name': formatted_table_name,
            'sql_statements': {
                'describe_sql': describe_sql,
                'select_sql': select_sql,
                'alter_reflection_sql': alter_sql,
                'refresh_reflection_sql': refresh_sql
            },
            'debug_info': {
                'original_path': dataset_path,
                'path_parts': dataset_path.split('.'),
                'has_quotes': '"' in dataset_path,
                'path_length': len(dataset_path.split('.')),
                'formatting_method': '_format_table_name_for_sql',
                'client_info': {
                    'host': dremio_client.host,
                    'port': dremio_client.port,
                    'token_exists': bool(dremio_client.token)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"调试SQL构建异常: {e}")
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/reflection/list', methods=['POST'])
@monitor_performance
def list_reflections_endpoint():
    """获取数据集反射列表端点"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'dataset_id' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必需的参数: dataset_id'
            }), 400
        
        dataset_id = data['dataset_id']
        
        logger.info(f"获取数据集反射列表: {dataset_id}")
        
        # 调用DremioClient的get_dataset_reflections方法
        result = dremio_client.get_dataset_reflections(dataset_id)
        
        if result['success']:
            logger.info(f"成功获取反射列表: {dataset_id}, 共 {len(result['reflections'])} 个反射")
            return jsonify({
                'success': True,
                'message': f'成功获取 {len(result["reflections"])} 个反射',
                'data': {
                    'dataset_id': dataset_id,
                    'reflections': result['reflections'],
                    'count': len(result['reflections'])
                }
            })
        else:
            logger.error(f"获取反射列表失败: {dataset_id}, 错误: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"获取反射列表时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取反射列表失败: {str(e)}'
        }), 500

@app.route('/api/table/columns', methods=['GET'])
@monitor_performance
def get_table_columns_endpoint():
    """获取表字段信息端点"""
    try:
        dataset_path = request.args.get('dataset_path')
        if not dataset_path:
            return jsonify({
                'success': False,
                'error': '缺少必需的参数: dataset_path'
            }), 400
        
        logger.info(f"获取表字段信息: {dataset_path}")
        
        # 调用DremioClient的字段获取方法
        columns = dremio_client.get_table_fields(dataset_path)
        
        if columns:
            logger.info(f"成功获取表 {dataset_path} 的 {len(columns)} 个字段")
            return jsonify({
                'success': True,
                'data': columns,
                'count': len(columns)
            })
        else:
            logger.error(f"无法获取表 {dataset_path} 的字段信息")
            return jsonify({
                'success': False,
                'error': '无法获取表字段信息'
            }), 500
            
    except Exception as e:
        logger.error(f"获取表字段信息时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取表字段信息失败: {str(e)}'
        }), 500

@app.route('/api/cache/status', methods=['GET'])
@monitor_performance
def get_cache_status_endpoint():
    """获取缓存状态端点"""
    try:
        cache_info = {
            'has_table_columns_cache': hasattr(dremio_client, 'table_columns_cache'),
            'table_columns_cache_size': len(getattr(dremio_client, 'table_columns_cache', {})),
            'table_columns_cache_keys': list(getattr(dremio_client, 'table_columns_cache', {}).keys()),
            'schema_cache_stats': dremio_client.schema_cache.get_cache_stats() if hasattr(dremio_client, 'schema_cache') else None
        }
        
        return jsonify({
            'success': True,
            'data': cache_info
        })
        
    except Exception as e:
        logger.error(f"获取缓存状态时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取缓存状态失败: {str(e)}'
        }), 500

@app.route('/api/info', methods=['GET'])
@monitor_performance
def get_server_info_endpoint():
    """获取服务器信息端点"""
    try:
        import datetime
        server_info = {
            'server_name': 'Dremio API Server Enhanced',
            'version': '1.0.0',
            'timestamp': datetime.datetime.now().isoformat(),
            'dremio_connected': dremio_client.token is not None,
            'dremio_url': dremio_client.base_url
        }
        
        return jsonify({
            'success': True,
            'data': server_info
        })
        
    except Exception as e:
        logger.error(f"获取服务器信息时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取服务器信息失败: {str(e)}'
        }), 500

@app.route('/api/reflection/create', methods=['POST'])
@monitor_performance
def create_reflection_endpoint():
    """创建反射端点"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'dataset_path' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必需的参数: dataset_path'
            }), 400
        
        dataset_path = data['dataset_path']
        reflection_name = data.get('reflection_name')  # 可选参数
        
        logger.info(f"创建反射: {dataset_path}")
        
        # 调用DremioClient的create_raw_reflection_by_sql方法
        result = dremio_client.create_raw_reflection_by_sql(dataset_path, reflection_name)
        
        if result['success']:
            logger.info(f"反射创建成功: {dataset_path}")
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'dataset_path': dataset_path,
                    'reflection_name': result.get('reflection_name')
                }
            })
        else:
            logger.error(f"反射创建失败: {dataset_path}, 错误: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"创建反射时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'创建反射失败: {str(e)}'
        }), 500

@app.route('/api/test/fields', methods=['POST'])
@monitor_performance
def test_fields_endpoint():
    """测试字段获取的调试端点"""
    try:
        data = request.get_json()
        dataset_path = data.get('dataset_path')
        
        logger.info(f"测试字段获取: {dataset_path}")
        
        # 直接执行DESCRIBE查询
        formatted_table_name = dremio_client._format_table_name_for_sql(dataset_path)
        describe_sql = 'DESCRIBE ' + formatted_table_name
        logger.info(f"执行SQL: {describe_sql}")
        
        result = dremio_client.execute_sql_query(describe_sql)
        logger.info(f"DESCRIBE查询结果: {result}")
        
        # 测试字段提取逻辑
        fields = dremio_client.get_table_fields(dataset_path)
        logger.info(f"提取的字段: {fields}")
        
        return jsonify({
            'success': True,
            'sql': describe_sql,
            'raw_result': result,
            'fields': fields,
            'field_count': len(fields)
        })
        
    except Exception as e:
        logger.error(f"测试字段获取失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/columns', methods=['POST'])
def debug_get_columns():
    """调试接口：测试获取表字段信息"""
    try:
        data = request.get_json()
        dataset_path = data.get('dataset_path')
        
        if not dataset_path:
            return jsonify({'success': False, 'error': '缺少dataset_path参数'}), 400
        
        logger.info(f"调试获取表字段: {dataset_path}")
        
        # 调用字段获取方法
        columns = dremio_client.get_table_fields(dataset_path)
        
        return jsonify({
            'success': True,
            'dataset_path': dataset_path,
            'columns': columns,
            'column_count': len(columns)
        })
        
    except Exception as e:
        logger.error(f"调试获取字段失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 根路由和健康检查
@app.route('/')
def index():
    return jsonify({
        'message': 'Dremio API Server Enhanced',
        'version': '1.0.0',
        'status': 'running'
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'dremio_connected': bool(dremio_client.token),
        'timestamp': datetime.now().isoformat()
    })

# 添加请求日志中间件
@app.before_request
def log_request_info():
    logger.info(f"收到请求: {request.method} {request.url}")
    logger.info(f"请求头: {dict(request.headers)}")
    if request.is_json:
        logger.info(f"请求数据: {request.get_json()}")

@app.after_request
def log_response_info(response):
    logger.info(f"响应状态: {response.status_code}")
    return response

if __name__ == '__main__':
    # 从环境变量获取端口配置，默认8003
    api_port = int(os.environ.get('API_PORT', 8003))
    print("启动Dremio API服务器...")
    print(f"服务端口: {api_port}")
    print(f"注册的路由: {[rule.rule for rule in app.url_map.iter_rules()]}")
    app.run(host='0.0.0.0', port=api_port, debug=False)
