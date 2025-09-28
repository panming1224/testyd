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
    """拼多多爬虫通用数据库接口 - 优化版本"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, shops_table='shops', tasks_table='tasks', platform='company'):
        """单例模式 - 支持参数传递"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, shops_table='pdd_shops', tasks_table='pdd_tasks', platform='pdd'):
        """
        初始化数据库连接池
        
        Args:
            shops_table: 店铺表名，默认'shops'
            tasks_table: 任务表名，默认'tasks'  
            platform: 平台标识，默认'company'，用于数据库名
        """
        if hasattr(self, '_initialized'):
            return
        
        # 表名配置 - 支持动态传入
        self.shops_table = shops_table
        self.tasks_table = tasks_table
        self.platform = platform
        
        self.db_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'admin123',  # 使用正确的密码
            'database': 'company',  # 使用company数据库
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
        
        self._initialize_database()
        self._initialized = True
        logger.info("数据库连接池初始化完成")
    
    def _initialize_database(self):
        """初始化数据库和表结构"""
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                # 创建数据库
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.execute(f"USE {self.db_config['database']}")
                
                # 创建店铺表 - 扩展字段支持完整店铺信息管理
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.shops_table} (
                        shop_name VARCHAR(255) PRIMARY KEY COMMENT '店铺名称',
                        account VARCHAR(255) COMMENT '登录账号',
                        password VARCHAR(255) COMMENT '登录密码',
                        contact_person VARCHAR(100) COMMENT '联系人',
                        contact_phone VARCHAR(20) COMMENT '联系电话',
                        shop_group VARCHAR(100) DEFAULT 'default' COMMENT '店铺分组',
                        sub_account VARCHAR(255) COMMENT '子账号',
                        sub_password VARCHAR(255) COMMENT '子账号密码',
                        sub_phone VARCHAR(20) COMMENT '子账号手机号',
                        cookie TEXT COMMENT '登录Cookie',
                        folder_path VARCHAR(500) COMMENT '文件夹路径',
                        status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '店铺状态',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                        INDEX idx_shop_status (status),
                        INDEX idx_shop_group (shop_group),
                        INDEX idx_contact_person (contact_person)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='店铺信息表'
                """)
                
                # 创建任务表 - 支持灵活时间范围和动态表名
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.tasks_table} (
                        time_period VARCHAR(50) NOT NULL COMMENT '时间周期（支持日期、周度、月度等格式）',
                        shop_name VARCHAR(255) NOT NULL COMMENT '店铺名称',
                        task_data JSON COMMENT '任务数据（JSON格式）',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                        PRIMARY KEY (time_period, shop_name),
                        FOREIGN KEY (shop_name) REFERENCES {self.shops_table}(shop_name) ON DELETE CASCADE ON UPDATE CASCADE,
                        INDEX idx_time_period (time_period),
                        INDEX idx_shop_name (shop_name)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务管理表'
                """)
                
            conn.commit()
            logger.info("数据库表结构初始化完成")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库初始化失败: {e}")
            raise
        finally:
            conn.close()
    
    def import_shops_from_excel(self, excel_path: str, folder_column: str = None) -> int:
        """
        从Excel或CSV文件导入店铺基础信息
        Args:
            excel_path: Excel或CSV文件路径
            folder_column: 文件夹列名（可选）
        Returns:
            导入的店铺数量
        """
        try:
            # 根据文件扩展名选择读取方式
            if excel_path.lower().endswith('.csv'):
                df = pd.read_csv(excel_path, encoding='utf-8')
            else:
                df = pd.read_excel(excel_path)
            
            if 'shop_name' not in df.columns:
                raise ValueError("文件必须包含'shop_name'列")
            
            conn = self.pool.connection()
            imported_count = 0
            
            try:
                with conn.cursor() as cursor:
                    for _, row in df.iterrows():
                        shop_name = str(row['shop_name']).strip()
                        if not shop_name:
                            continue
                        
                        # 构建插入数据
                        insert_data = {'shop_name': shop_name}
                        
                        # 处理可选字段
                        optional_fields = ['account', 'password', 'contact_person', 'contact_phone', 
                                         'shop_group', 'sub_account', 'sub_password', 'sub_phone', 
                                         'cookie', 'folder_path']
                        
                        for field in optional_fields:
                            if field in df.columns and pd.notna(row[field]):
                                insert_data[field] = str(row[field]).strip()
                        
                        # 特殊处理folder_path
                        if folder_column and folder_column in df.columns:
                            if pd.notna(row[folder_column]):
                                insert_data['folder_path'] = str(row[folder_column]).strip()
                        
                        # 构建SQL
                        columns = ', '.join(insert_data.keys())
                        placeholders = ', '.join(['%s'] * len(insert_data))
                        values = list(insert_data.values())
                        
                        cursor.execute(f"""
                            INSERT INTO {self.shops_table} ({columns})
                            VALUES ({placeholders})
                            ON DUPLICATE KEY UPDATE
                                account = VALUES(account),
                                password = VALUES(password),
                                contact_person = VALUES(contact_person),
                                contact_phone = VALUES(contact_phone),
                                shop_group = VALUES(shop_group),
                                sub_account = VALUES(sub_account),
                                sub_password = VALUES(sub_password),
                                sub_phone = VALUES(sub_phone),
                                cookie = VALUES(cookie),
                                folder_path = VALUES(folder_path),
                                updated_at = CURRENT_TIMESTAMP
                        """, values)
                        
                        if cursor.rowcount > 0:
                            imported_count += 1
                
                conn.commit()
                logger.info(f"成功导入/更新 {imported_count} 个店铺")
                return imported_count
                
            except Exception as e:
                conn.rollback()
                logger.error(f"导入店铺失败: {e}")
                raise
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise
    
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
            with conn.cursor(DictCursor) as cursor:
                # 获取所有店铺
                cursor.execute(f"SELECT shop_name FROM {self.shops_table}")
                shops = cursor.fetchall()
                
                if not shops:
                    logger.warning("没有找到任何店铺数据")
                    return 0
                
                # 构建批量插入数据
                batch_data = []
                task_data_json = json.dumps({col: None for col in task_columns}, ensure_ascii=False)
                
                for shop in shops:
                    batch_data.append((time_period, shop['shop_name'], task_data_json))
                
                # 批量插入，使用 executemany 提高性能
                cursor.executemany(f"""
                    INSERT INTO {self.tasks_table} (time_period, shop_name, task_data) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        task_data = JSON_MERGE_PATCH(task_data, VALUES(task_data)),
                        updated_at = CURRENT_TIMESTAMP
                """, batch_data)
                
                # 计算新创建的任务数（总影响行数 - 更新的行数）
                # 由于 ON DUPLICATE KEY UPDATE 的特性，新插入返回1，更新返回2
                total_affected = cursor.rowcount
                # 简化计算：假设大部分是新插入的任务
                created_count = len(batch_data) if total_affected > 0 else 0
                
            conn.commit()
            logger.info(f"为时间周期 {time_period} 创建了 {created_count} 个新任务")
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
            with conn.cursor(DictCursor) as cursor:
                # 构建查询SQL
                sql = f"""
                    SELECT dt.time_period, dt.shop_name, s.account, s.password, s.contact_person, 
                           s.contact_phone, s.shop_group, s.sub_account, s.sub_password, s.sub_phone,
                           s.cookie, s.folder_path, dt.task_data
                    FROM {self.tasks_table} dt
                    JOIN {self.shops_table} s ON dt.shop_name = s.shop_name
                    WHERE dt.time_period = %s 
                      AND JSON_EXTRACT(dt.task_data, '$.{task_column}') IS NULL
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
                # 使用JSON_SET更新指定字段
                cursor.execute(f"""
                    UPDATE {self.tasks_table} 
                    SET task_data = JSON_SET(task_data, %s, %s),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE time_period = %s AND shop_name = %s
                """, (f'$.{task_column}', status, time_period, shop_name))
                
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
                    "UPDATE shops SET cookie = %s, updated_at = CURRENT_TIMESTAMP WHERE shop_name = %s",
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
    
    def get_shop_cookie(self, shop_name: str) -> Optional[str]:
        """
        获取店铺Cookie
        Args:
            shop_name: 店铺名称
        Returns:
            Cookie值或None
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT cookie FROM shops WHERE shop_name = %s", (shop_name,))
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"获取店铺cookie失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_shop_folder(self, shop_name: str) -> Optional[str]:
        """
        获取店铺文件夹路径
        Args:
            shop_name: 店铺名称
        Returns:
            文件夹路径或None
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT folder_path FROM shops WHERE shop_name = %s", (shop_name,))
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"获取店铺文件夹失败: {e}")
            raise
        finally:
            conn.close()
    
    def update_shop_folder(self, shop_name: str, folder_path: str) -> bool:
        """
        更新店铺文件夹路径
        Args:
            shop_name: 店铺名称
            folder_path: 文件夹路径
        Returns:
            是否更新成功
        """
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE shops SET folder_path = %s, updated_at = CURRENT_TIMESTAMP WHERE shop_name = %s",
                    (folder_path, shop_name)
                )
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"更新店铺文件夹成功: shop_name={shop_name}")
                else:
                    logger.warning(f"未找到店铺: {shop_name}")
                
                return success
                
        except Exception as e:
            conn.rollback()
            logger.error(f"更新店铺文件夹失败: {e}")
            raise
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
                          AND JSON_EXTRACT(task_data, '$.{task_column}') = %s
                    """, (time_period, "已完成"))
                    
                    completed = cursor.fetchone()['completed_count']
                    
                    # 统计待处理任务
                    cursor.execute(f"""
                        SELECT COUNT(*) as pending_count
                        FROM {self.tasks_table}
                        WHERE time_period = %s 
                          AND JSON_EXTRACT(task_data, '$.{task_column}') IS NULL
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
        执行自定义SQL语句的通用方法
        
        Args:
            sql: SQL语句
            params: SQL参数，默认None
            fetch_type: 返回类型 'all'(所有结果), 'one'(单条结果), 'count'(影响行数), 'none'(无返回)
        
        Returns:
            根据fetch_type返回不同类型的结果
        """
        conn = self.pool.connection()
        try:
            with conn.cursor(DictCursor) as cursor:
                # 执行SQL语句
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                # 根据fetch_type返回不同结果
                if fetch_type == 'all':
                    result = cursor.fetchall()
                elif fetch_type == 'one':
                    result = cursor.fetchone()
                elif fetch_type == 'count':
                    result = cursor.rowcount
                elif fetch_type == 'none':
                    result = None
                else:
                    raise ValueError(f"不支持的fetch_type: {fetch_type}")
                
                # 如果是修改操作，需要提交事务
                if sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                    conn.commit()
                    logger.info(f"SQL执行成功，影响行数: {cursor.rowcount}")
                
                return result
                
        except Exception as e:
            conn.rollback()
            logger.error(f"执行自定义SQL失败: {e}")
            logger.error(f"SQL语句: {sql}")
            logger.error(f"参数: {params}")
            raise
        finally:
            conn.close()

    def close_pool(self):
        """关闭连接池（程序退出时调用）"""
        if hasattr(self, 'pool'):
            self.pool.close()
            logger.info("数据库连接池已关闭")

# 示例用法
if __name__ == "__main__":
    # 初始化数据库接口
    db = CrawlerDBInterface()
    
    # 生成今日任务（支持自定义任务列）
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 自定义任务列
    custom_tasks = ['chat_status', 'quality_status', 'badreview_status', 'kpi_status', 'new_task_status']
    created_count = db.generate_daily_tasks(today, custom_tasks)
    print(f"创建了 {created_count} 个新任务")
    
    # 获取待处理任务
    pending_tasks = db.get_pending_tasks(today, 'badreview_status', limit=5)
    print(f"待处理差评任务: {len(pending_tasks)} 个")
    
    # 获取统计信息
    stats = db.get_task_statistics(today, custom_tasks)
    print(f"任务统计: {stats}")
    
    print("优化版数据库接口测试完成！")