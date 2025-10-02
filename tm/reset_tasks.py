#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重置失败的badscore_status任务为待处理状态"""

import pymysql

def reset_failed_tasks():
    """重置失败的badscore_status任务为待处理状态"""
    try:
        # 连接数据库 - 使用正确的密码
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='admin123',  # 修正密码
            database='company',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 重置失败的任务为待处理状态
            sql = "UPDATE tm_tasks SET badscore_status = 'pending' WHERE badscore_status = 'failed'"
            affected_rows = cursor.execute(sql)
            connection.commit()
            
            print(f"成功重置 {affected_rows} 个失败任务为待处理状态")
            
            # 查询当前待处理任务数量
            cursor.execute("SELECT COUNT(*) FROM tm_tasks WHERE badscore_status = 'pending'")
            pending_count = cursor.fetchone()[0]
            print(f"当前待处理任务数量: {pending_count}")
            
    except Exception as e:
        print(f"重置任务失败: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    reset_failed_tasks()