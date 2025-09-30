# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

import pymysql

def check_table_structure():
    """检查数据库表结构"""
    print("=== 检查数据库表结构 ===")
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='admin123',
            database='company',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 检查tm_tasks表结构
        print("\n--- tm_tasks表结构 ---")
        cursor.execute("DESCRIBE tm_tasks")
        tasks_columns = cursor.fetchall()
        
        for column in tasks_columns:
            print(f"  {column[0]} - {column[1]} - {column[2]} - {column[3]}")
        
        # 检查tm_shops表结构
        print("\n--- tm_shops表结构 ---")
        cursor.execute("DESCRIBE tm_shops")
        shops_columns = cursor.fetchall()
        
        for column in shops_columns:
            print(f"  {column[0]} - {column[1]} - {column[2]} - {column[3]}")
        
        # 检查tm_tasks表中的数据样本
        print("\n--- tm_tasks表数据样本 ---")
        cursor.execute("SELECT * FROM tm_tasks LIMIT 5")
        sample_tasks = cursor.fetchall()
        
        if sample_tasks:
            print(f"样本数据 ({len(sample_tasks)}条):")
            for i, task in enumerate(sample_tasks):
                print(f"  {i+1}. {task}")
        else:
            print("  无数据")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_table_structure()