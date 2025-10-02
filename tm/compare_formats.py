#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较Excel文件格式
"""

import pandas as pd
import os

def compare_formats():
    """比较两个Excel文件的格式"""
    
    # 当前生成的文件
    current_file = r'd:\yingdao\tm\天猫客服聊天记录\2025-09-18\草本初色潮搭旗舰店_2025-09-18_112729.xlsx'
    # 参考文件
    reference_file = r'd:\pdd\文件存档\2025-09-29\俞兆林儿童袜子旗舰店.xlsx'
    
    print("🔍 格式比较分析:")
    print("=" * 80)
    
    # 检查当前文件
    if os.path.exists(current_file):
        try:
            df_current = pd.read_excel(current_file)
            print("📊 当前生成的文件:")
            print(f"  文件: {current_file}")
            print(f"  行数: {len(df_current)}")
            print(f"  列数: {len(df_current.columns)}")
            print(f"  列名: {list(df_current.columns)}")
            print("  前2行数据:")
            for i in range(min(2, len(df_current))):
                print(f"    第{i+1}行: {dict(df_current.iloc[i])}")
        except Exception as e:
            print(f"❌ 读取当前文件失败: {e}")
    else:
        print(f"❌ 当前文件不存在: {current_file}")
    
    print("\n" + "-" * 80)
    
    # 检查参考文件
    if os.path.exists(reference_file):
        try:
            df_ref = pd.read_excel(reference_file)
            print("📋 参考文件格式:")
            print(f"  文件: {reference_file}")
            print(f"  行数: {len(df_ref)}")
            print(f"  列数: {len(df_ref.columns)}")
            print(f"  列名: {list(df_ref.columns)}")
            print("  前2行数据:")
            for i in range(min(2, len(df_ref))):
                row_data = {}
                for col in df_ref.columns:
                    value = str(df_ref.iloc[i][col])
                    if len(value) > 100:
                        value = value[:100] + "..."
                    row_data[col] = value
                print(f"    第{i+1}行: {row_data}")
        except Exception as e:
            print(f"❌ 读取参考文件失败: {e}")
    else:
        print(f"❌ 参考文件不存在: {reference_file}")
    
    print("\n" + "=" * 80)
    print("🎯 问题分析:")
    print("当前生成的文件列名不是期望的 ['客户', '聊天记录'] 格式")
    print("需要修改代码以生成正确的两列格式")

if __name__ == "__main__":
    compare_formats()