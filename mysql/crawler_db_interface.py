#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多爬虫通用数据库接口 - 优化版本
提供数据库连接池、任务生成、状态管理等核心功能
支持动态任务类型和高性能数据操作
"""

import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Optional, Union
import threading
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskStatus:
    """任务状态常量 - 简化版本"""
    COMPLETED = "已完成"
    # null值表示待处理状态

class CrawlerDBInterface:
    """通用爬虫数据库接口 - 支持多平台和动态表名"""
    
    # 移除单例模式，支持多实例
    def __init__(self, shops_table='shops', tasks_table='tasks', platform='company', database='company'):
        """
        初始化数据库连接池
        
        Args:
            shops_table: 店铺表名，如 'pdd_shops', 'tm_shops' 等
            tasks_table: 任务表名，如 'pdd_tasks', 'tm_tasks' 等
            platform: 平台标识，用于日志标识
            database: 数据库名，默认'company'
        """
        # 表名配置 - 支持动态传入
        self.shops_table = shops_table
        self.tasks_table = tasks_table
        self.platform = platform
        self.database = database
        self.db_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'admin123',
            'database': self.database,  # 使用动态数据库名
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        # 创建连接池
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=20,
            mincached=2,
            maxcached=10,
            maxshared=20,
            blocking=True,
            maxusage=None,
            setsession=[],
            ping=0,
            **self.db_config
        )
        
        logger.info(f"数据库连接池初始化完成 - 平台: {self.platform}, 店铺表: {self.shops_table}, 任务表: {self.tasks_table}")
    
    def get_all_shops(self) -> List[Dict]:
        """获取所有店铺信息"""
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.shops_table}")
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            logger.error(f"获取店铺信息失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_shop_by_name(self, shop_name: str) -> Dict:
        """根据店铺名称获取店铺信息"""
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.shops_table} WHERE shop_name = %s", (shop_name,))
                columns = [desc[0] for desc in cursor.description]
                result = cursor.fetchone()
                return dict(zip(columns, result)) if result else {}
        except Exception as e:
            logger.error(f"获取店铺信息失败: {e}")
            return {}
        finally:
            conn.close()
    
    def update_shop_cookies(self, shop_name: str, qncookie: str = None, sycmcookie: str = None) -> bool:
        """更新店铺的Cookie信息（支持天猫店铺的双Cookie）"""
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                # 检查表是否有qncookie和sycmcookie字段
                cursor.execute(f"SHOW COLUMNS FROM {self.shops_table}")
                columns = [row[0] for row in cursor.fetchall()]
                
                update_fields = []
                params = []
                
                if qncookie is not None and 'qncookie' in columns:
                    update_fields.append("qncookie = %s")
                    params.append(qncookie)
                
                if sycmcookie is not None and 'sycmcookie' in columns:
                    update_fields.append("sycmcookie = %s")
                    params.append(sycmcookie)
                
                # 如果没有专门的cookie字段，使用通用cookie字段
                if not update_fields and (qncookie or sycmcookie):
                    update_fields.append("cookie = %s")
                    params.append(qncookie or sycmcookie)
                
                if update_fields:
                    params.append(shop_name)
                    sql = f"UPDATE {self.shops_table} SET {', '.join(update_fields)} WHERE shop_name = %s"
                    cursor.execute(sql, params)
                    conn.commit()
                    logger.info(f"店铺 {shop_name} Cookie更新成功")
                    return True
                else:
                    logger.warning(f"没有找到合适的Cookie字段进行更新")
                    return False
                    
        except Exception as e:
            conn.rollback()
            logger.error(f"更新店铺Cookie失败: {e}")
            return False
        finally:
            conn.close()
    
    def generate_tasks(self, time_period: str, task_columns: List[str] = None) -> int:
        """
        为所有店铺生成指定时间周期的任务
        
        Args:
            time_period: 时间周期，支持多种格式：
                        - 日期：'2025-09-28'
                        - 周度：'2025-09-01_2025-09-06'  
                        - 月度：'2025-09'
            task_columns: 任务列名列表，如 ['badreview_status', 'chat_status']
        
        Returns:
            int: 创建的新任务数量
        """
        if task_columns is None:
            task_columns = ['badreview_status', 'chat_status', 'quality_status', 'kpi_status']
        
        conn = self.pool.connection()
        created_count = 0
        
        try:
            with conn.cursor() as cursor:
                # 获取所有店铺
                cursor.execute(f"SELECT shop_name FROM {self.shops_table}")
                shops = cursor.fetchall()
                
                if not shops:
                    logger.warning("没有找到任何店铺数据")
                    return 0
                
                # 检查表结构，判断使用哪种字段格式
                cursor.execute(f"SHOW COLUMNS FROM {self.tasks_table}")
                columns = [row[0] for row in cursor.fetchall()]
                
                has_task_data = 'task_data' in columns
                
                if has_task_data:
                    # 使用JSON格式的task_data字段
                    batch_data = []
                    task_data_json = json.dumps({col: None for col in task_columns}, ensure_ascii=False)
                    
                    for shop in shops:
                        batch_data.append((time_period, shop[0], task_data_json))
                    
                    cursor.executemany(f"""
                        INSERT INTO {self.tasks_table} (time_period, shop_name, task_data) 
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            task_data = JSON_MERGE_PATCH(task_data, VALUES(task_data)),
                            update_time = CURRENT_TIMESTAMP
                    """, batch_data)
                else:
                    # 使用传统的枚举字段格式
                    # 构建动态插入SQL
                    available_columns = [col for col in task_columns if col in columns]
                    if not available_columns:
                        logger.warning(f"表 {self.tasks_table} 中没有找到任何指定的任务列: {task_columns}")
                        return 0

                    # 新策略：使用 INSERT IGNORE + UPDATE WHERE 精确控制
                    # 1. 先用 INSERT IGNORE 确保记录存在（所有任务字段默认为NULL）
                    # 2. 再用 UPDATE WHERE 只更新指定的任务字段为"待执行"

                    # 步骤1: INSERT IGNORE 确保记录存在
                    insert_data = [(time_period, shop[0]) for shop in shops]
                    cursor.executemany(f"""
                        INSERT IGNORE INTO {self.tasks_table} (time_period, shop_name)
                        VALUES (%s, %s)
                    """, insert_data)

                    # 步骤2: UPDATE WHERE 只更新指定的任务字段
                    # 只更新 NULL 或空值的字段为"待执行"，已完成的保持不变
                    for col in available_columns:
                        update_sql = f"""
                            UPDATE {self.tasks_table}
                            SET {col} = '待执行'
                            WHERE time_period = %s
                              AND ({col} IS NULL OR {col} = '')
                        """
                        cursor.execute(update_sql, (time_period,))
                        logger.info(f"更新了 {cursor.rowcount} 个店铺的 {col} 字段为待执行")

                    created_count = len(shops)

            conn.commit()
            logger.info(f"为时间周期 {time_period} 创建了 {created_count} 个任务记录")
            return created_count
            
        except Exception as e:
            conn.rollback()
            logger.error(f"生成任务失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_pending_tasks(self, time_period: str, task_column: str, limit: int = None) -> List[Dict]:
        """
        获取指定时间周期和任务类型的待处理任务
        
        Args:
            time_period: 时间周期，支持多种格式
            task_column: 任务列名，如 'badreview_status'
            limit: 限制返回数量
        
        Returns:
            List[Dict]: 待处理任务列表
        """
        conn = self.pool.connection()
        
        try:
            with conn.cursor() as cursor:
                # 检查表结构
                cursor.execute(f"SHOW COLUMNS FROM {self.tasks_table}")
                task_columns = [row[0] for row in cursor.fetchall()]
                has_task_data = 'task_data' in task_columns
                
                if has_task_data:
                    # 使用JSON格式的task_data字段
                    sql = f"""
                        SELECT dt.time_period, dt.shop_name, s.*
                        FROM {self.tasks_table} dt
                        JOIN {self.shops_table} s ON dt.shop_name = s.shop_name
                        WHERE dt.time_period = %s
                          AND JSON_EXTRACT(dt.task_data, '$.{task_column}') = '待执行'
                    """
                else:
                    # 使用传统的枚举字段格式
                    if task_column not in task_columns:
                        logger.warning(f"任务列 {task_column} 不存在于表 {self.tasks_table} 中")
                        return []

                    sql = f"""
                        SELECT dt.time_period, dt.shop_name, s.*
                        FROM {self.tasks_table} dt
                        JOIN {self.shops_table} s ON dt.shop_name = s.shop_name
                        WHERE dt.time_period = %s
                          AND dt.{task_column} = '待执行'
                    """
                
                if limit:
                    sql += f" LIMIT {limit}"
                
                cursor.execute(sql, (time_period,))
                tasks = cursor.fetchall()
                
                return tasks
                
        except Exception as e:
            logger.error(f"获取待处理任务失败: {e}")
            raise
        finally:
            conn.close()
    
    def update_task_status(self, time_period: str, shop_name: str, task_column: str, status: str) -> bool:
        """
        更新指定任务的状态
        
        Args:
            time_period: 时间周期
            shop_name: 店铺名称
            task_column: 任务列名
            status: 新状态值
        
        Returns:
            bool: 更新是否成功
        """
        conn = self.pool.connection()
        
        try:
            with conn.cursor() as cursor:
                # 检查表结构
                cursor.execute(f"SHOW COLUMNS FROM {self.tasks_table}")
                task_columns = [row[0] for row in cursor.fetchall()]
                has_task_data = 'task_data' in task_columns
                
                if has_task_data:
                    # 使用JSON格式的task_data字段
                    cursor.execute(f"""
                        UPDATE {self.tasks_table} 
                        SET task_data = JSON_SET(task_data, %s, %s),
                            update_time = CURRENT_TIMESTAMP
                        WHERE time_period = %s AND shop_name = %s
                    """, (f'$.{task_column}', status, time_period, shop_name))
                else:
                    # 使用传统的枚举字段格式
                    if task_column not in task_columns:
                        logger.warning(f"任务列 {task_column} 不存在于表 {self.tasks_table} 中")
                        return False
                    
                    cursor.execute(f"""
                        UPDATE {self.tasks_table} 
                        SET {task_column} = %s,
                            update_time = CURRENT_TIMESTAMP
                        WHERE time_period = %s AND shop_name = %s
                    """, (status, time_period, shop_name))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"更新任务状态成功: {time_period}-{shop_name}-{task_column} -> {status}")
                    return True
                else:
                    logger.warning(f"未找到匹配的任务记录: {time_period}-{shop_name}")
                    return False
                    
        except Exception as e:
            conn.rollback()
            logger.error(f"更新任务状态失败: {e}")
            raise
        finally:
            conn.close()
    
    def update_shop_cookie(self, shop_name: str, cookie: str) -> bool:
        """
        更新店铺Cookie
        Args:
            shop_name: 店铺名称
            cookie: 新的Cookie值
        Returns:
            是否更新成功
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"UPDATE {self.shops_table} SET cookie = %s, update_time = CURRENT_TIMESTAMP WHERE shop_name = %s",
                    (cookie, shop_name)
                )
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"更新店铺cookie成功: shop_name={shop_name}")
                else:
                    logger.warning(f"未找到店铺: {shop_name}")
                
                return success
                
        except Exception as e:
            conn.rollback()
            logger.error(f"更新店铺cookie失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_shop_cookie(self, shop_name: str) -> str:
        """
        获取指定店铺的Cookie
        
        Args:
            shop_name: 店铺名称
            
        Returns:
            str: Cookie字符串，如果不存在返回None
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT cookie FROM {self.shops_table} WHERE shop_name = %s", (shop_name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"获取店铺Cookie失败: {e}")
            return None
        finally:
            conn.close()
    
    def get_shop_folder(self, shop_name: str) -> str:
        """
        获取指定店铺的文件夹路径
        
        Args:
            shop_name: 店铺名称
            
        Returns:
            str: 文件夹路径，如果不存在返回None
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT folder_path FROM {self.shops_table} WHERE shop_name = %s", (shop_name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"获取店铺文件夹路径失败: {e}")
            return None
        finally:
            conn.close()
    
    def update_shop_folder(self, shop_name: str, folder_path: str) -> bool:
        """
        更新指定店铺的文件夹路径
        
        Args:
            shop_name: 店铺名称
            folder_path: 文件夹路径
            
        Returns:
            bool: 更新是否成功
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"UPDATE {self.shops_table} SET folder_path = %s, update_time = CURRENT_TIMESTAMP WHERE shop_name = %s",
                    (folder_path, shop_name)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"店铺 {shop_name} 文件夹路径更新成功")
                    return True
                else:
                    logger.warning(f"店铺 {shop_name} 不存在")
                    return False
                    
        except Exception as e:
            conn.rollback()
            logger.error(f"更新店铺文件夹路径失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_task_statistics(self, time_period: str, task_columns: List[str] = None) -> Dict:
        """
        获取指定时间周期的任务统计信息
        
        Args:
            time_period: 时间周期
            task_columns: 任务列名列表
        
        Returns:
            Dict: 统计信息
        """
        if task_columns is None:
            task_columns = ['badreview_status', 'chat_status', 'quality_status', 'kpi_status']
        
        conn = self.pool.connection()
        
        try:
            with conn.cursor(DictCursor) as cursor:
                stats = {}
                
                for task_column in task_columns:
                    # 统计已完成任务
                    cursor.execute(f"""
                        SELECT COUNT(*) as completed_count
                        FROM {self.tasks_table}
                        WHERE time_period = %s 
                          AND {task_column} = %s
                    """, (time_period, "已完成"))
                    
                    completed = cursor.fetchone()['completed_count']
                    
                    # 统计待处理任务
                    cursor.execute(f"""
                        SELECT COUNT(*) as pending_count
                        FROM {self.tasks_table}
                        WHERE time_period = %s 
                          AND {task_column} IS NULL
                    """, (time_period,))
                    
                    pending = cursor.fetchone()['pending_count']
                    
                    stats[task_column] = {
                        'completed': completed,
                        'pending': pending,
                        'total': completed + pending
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            raise
        finally:
            conn.close()
    
    def execute_custom_sql(self, sql: str, params: tuple = None, fetch_type: str = 'all') -> Union[List[Dict], Dict, int, None]:
        """
        执行自定义SQL查询 - 通用数据库操作方法
        
        Args:
            sql: SQL语句
            params: SQL参数
            fetch_type: 返回类型 ('all', 'one', 'count', 'execute')
            
        Returns:
            根据fetch_type返回不同类型的结果
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                
                if fetch_type == 'all':
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    results = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in results] if columns else results
                elif fetch_type == 'one':
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    result = cursor.fetchone()
                    return dict(zip(columns, result)) if result and columns else result
                elif fetch_type == 'count':
                    return cursor.rowcount
                elif fetch_type == 'execute':
                    conn.commit()
                    return cursor.rowcount
                else:
                    return None
                    
        except Exception as e:
            if fetch_type == 'execute':
                conn.rollback()
            logger.error(f"执行SQL失败: {e}")
            raise
        finally:
            conn.close()
    
    def insert_record(self, table_name: str, data: Dict) -> bool:
        """
        通用插入记录方法
        
        Args:
            table_name: 表名
            data: 要插入的数据字典
            
        Returns:
            bool: 插入是否成功
        """
        if not data:
            return False
            
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())
        
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            result = self.execute_custom_sql(sql, tuple(values), 'execute')
            return result > 0
        except Exception as e:
            logger.error(f"插入记录失败: {e}")
            return False
    
    def update_record(self, table_name: str, data: Dict, where_condition: str, where_params: tuple = None) -> bool:
        """
        通用更新记录方法
        
        Args:
            table_name: 表名
            data: 要更新的数据字典
            where_condition: WHERE条件
            where_params: WHERE条件参数
            
        Returns:
            bool: 更新是否成功
        """
        if not data:
            return False
            
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        values = list(data.values())
        
        if where_params:
            values.extend(where_params)
            
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_condition}"
        
        try:
            result = self.execute_custom_sql(sql, tuple(values), 'execute')
            return result > 0
        except Exception as e:
            logger.error(f"更新记录失败: {e}")
            return False
    
    def delete_record(self, table_name: str, where_condition: str, where_params: tuple = None) -> bool:
        """
        通用删除记录方法
        
        Args:
            table_name: 表名
            where_condition: WHERE条件
            where_params: WHERE条件参数
            
        Returns:
            bool: 删除是否成功
        """
        sql = f"DELETE FROM {table_name} WHERE {where_condition}"
        
        try:
            result = self.execute_custom_sql(sql, where_params, 'execute')
            return result > 0
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            return False
    
    def select_records(self, table_name: str, columns: str = "*", where_condition: str = None, where_params: tuple = None, order_by: str = None, limit: int = None) -> List[Dict]:
        """
        通用查询记录方法
        
        Args:
            table_name: 表名
            columns: 要查询的列，默认为*
            where_condition: WHERE条件
            where_params: WHERE条件参数
            order_by: 排序条件
            limit: 限制返回数量
            
        Returns:
            List[Dict]: 查询结果列表
        """
        sql = f"SELECT {columns} FROM {table_name}"
        
        if where_condition:
            sql += f" WHERE {where_condition}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"
            
        try:
            return self.execute_custom_sql(sql, where_params, 'all')
        except Exception as e:
            logger.error(f"查询记录失败: {e}")
            return []

    def close_pool(self):
        """关闭连接池（程序退出时调用）"""
        if hasattr(self, 'pool'):
            self.pool.close()
            logger.info("数据库连接池已关闭")
    
    def check_and_reset_daily_status(self) -> int:
        """
        检查店铺的更新时间，如果不是今天则清空status列
        
        Returns:
            int: 重置的店铺数量
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                # 检查表是否有status和update_time字段
                cursor.execute(f"SHOW COLUMNS FROM {self.shops_table}")
                columns = [row[0] for row in cursor.fetchall()]
                
                if 'status' not in columns or 'update_time' not in columns:
                    logger.warning(f"表 {self.shops_table} 缺少 status 或 update_time 字段")
                    return 0
                
                # 重置不是今天更新的店铺的status
                sql = f"""
                UPDATE {self.shops_table} 
                SET status = NULL 
                WHERE DATE(update_time) != CURDATE() AND status IS NOT NULL
                """
                cursor.execute(sql)
                reset_count = cursor.rowcount
                conn.commit()
                
                if reset_count > 0:
                    logger.info(f"重置了 {reset_count} 个店铺的status状态")
                
                return reset_count
                
        except Exception as e:
            logger.error(f"检查和重置每日状态失败: {e}")
            return 0
        finally:
            conn.close()
    
    def update_shop_status(self, shop_name: str, status: str) -> bool:
        """
        更新店铺的status状态
        
        Args:
            shop_name: 店铺名称
            status: 状态值
            
        Returns:
            bool: 更新是否成功
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                # 检查表是否有status字段
                cursor.execute(f"SHOW COLUMNS FROM {self.shops_table}")
                columns = [row[0] for row in cursor.fetchall()]
                
                if 'status' not in columns:
                    logger.warning(f"表 {self.shops_table} 缺少 status 字段")
                    return False
                
                sql = f"UPDATE {self.shops_table} SET status = %s WHERE shop_name = %s"
                cursor.execute(sql, (status, shop_name))
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"更新店铺 {shop_name} 状态为: {status}")
                else:
                    logger.warning(f"未找到店铺: {shop_name}")
                
                return success
                
        except Exception as e:
            logger.error(f"更新店铺状态失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_shops_need_retry(self) -> List[Dict]:
        """
        获取需要重试的店铺（status为空的店铺）
        
        Returns:
            List[Dict]: 需要重试的店铺列表
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                # 检查表是否有status字段
                cursor.execute(f"SHOW COLUMNS FROM {self.shops_table}")
                columns = [row[0] for row in cursor.fetchall()]
                
                if 'status' not in columns:
                    logger.warning(f"表 {self.shops_table} 缺少 status 字段")
                    return self.get_all_shops()  # 如果没有status字段，返回所有店铺
                
                cursor.execute(f"SELECT * FROM {self.shops_table} WHERE status IS NULL OR status = ''")
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                shops = [dict(zip(columns, row)) for row in results]
                
                logger.info(f"找到 {len(shops)} 个需要重试的店铺")
                return shops
                
        except Exception as e:
            logger.error(f"获取需要重试的店铺失败: {e}")
            return []
        finally:
            conn.close()

# 示例用法
if __name__ == "__main__":
    # 初始化数据库接口
    db = CrawlerDBInterface()
    
    # 生成今日任务（支持自定义任务列）
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 自定义任务列
    custom_tasks = ['chat_status', 'quality_status', 'badreview_status', 'kpi_status', 'new_task_status']
    created_count = db.generate_tasks(today, custom_tasks)
    print(f"创建了 {created_count} 个新任务")
    
    # 获取待处理任务
    pending_tasks = db.get_pending_tasks(today, 'badreview_status', limit=5)
    print(f"待处理差评任务: {len(pending_tasks)} 个")
    
    # 获取统计信息
    stats = db.get_task_statistics(today, custom_tasks)
    print(f"任务统计: {stats}")
    
    print("优化版数据库接口测试完成！")