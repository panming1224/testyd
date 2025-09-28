#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件合并工具
功能：将指定文件夹中的所有Excel文件合并成一个大文件，并将原文件名作为shop列
"""

import os
import pandas as pd
import glob
from pathlib import Path
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('merge_excel.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExcelMerger:
    """Excel文件合并器"""
    
    def __init__(self, folder_path, output_dir=None, exclude_patterns=None):
        """
        初始化合并器
        
        Args:
            folder_path (str): 包含Excel文件的文件夹路径
            output_dir (str, optional): 输出目录路径，如果不指定则使用源文件夹
            exclude_patterns (list, optional): 要排除的文件名模式列表
        """
        self.folder_path = Path(folder_path)
        self.output_dir = Path(output_dir) if output_dir else self.folder_path
        self.supported_extensions = ['.xlsx', '.xls', '.xlsm']
        
        # 默认排除模式：日期格式的文件名和常见的合并文件名
        self.exclude_patterns = exclude_patterns or [
            r'^\d{4}-\d{2}-\d{2}\.xlsx?$',  # 日期格式文件
            r'.*合并.*\.xlsx?$',              # 包含"合并"的文件
            r'^merged.*\.xlsx?$',            # 以merged开头的文件
            r'.*_merged\.xlsx?$',            # 以_merged结尾的文件
        ]
        
    def find_excel_files(self):
        """
        查找文件夹中的所有Excel文件，排除临时合并文件
        
        Returns:
            list: Excel文件路径列表
        """
        import re
        
        excel_files = []
        
        for ext in self.supported_extensions:
            pattern = str(self.folder_path / f"*{ext}")
            files = glob.glob(pattern)
            
            # 过滤掉匹配排除模式的文件
            filtered_files = []
            for file_path in files:
                file_name = Path(file_path).name
                should_exclude = False
                
                for exclude_pattern in self.exclude_patterns:
                    if re.match(exclude_pattern, file_name, re.IGNORECASE):
                        logger.info(f"排除文件: {file_name} (匹配模式: {exclude_pattern})")
                        should_exclude = True
                        break
                
                if not should_exclude:
                    filtered_files.append(file_path)
            
            excel_files.extend(filtered_files)
            
        logger.info(f"找到 {len(excel_files)} 个有效Excel文件")
        return excel_files
    
    def read_excel_file(self, file_path):
        """
        读取单个Excel文件
        
        Args:
            file_path (str): Excel文件路径
            
        Returns:
            pd.DataFrame: 读取的数据框，如果失败返回None
        """
        try:
            # 获取文件名（不含扩展名）作为shop名称
            shop_name = Path(file_path).stem
            
            # 检测文件实际格式
            def detect_excel_format(file_path):
                """检测Excel文件的实际格式"""
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(4)
                    
                    # 老版本Excel格式 (.xls) 的文件头
                    if header == b'\xd0\xcf\x11\xe0':
                        return 'xlrd'
                    # 新版本Excel格式 (.xlsx) 的文件头 (ZIP格式)
                    elif header == b'PK\x03\x04':
                        return 'openpyxl'
                    else:
                        # 根据扩展名判断
                        if file_path.endswith('.xlsx') or file_path.endswith('.xlsm'):
                            return 'openpyxl'
                        else:
                            return 'xlrd'
                except:
                    # 如果检测失败，根据扩展名判断
                    if file_path.endswith('.xlsx') or file_path.endswith('.xlsm'):
                        return 'openpyxl'
                    else:
                        return 'xlrd'
            
            # 自动检测并选择合适的引擎
            engine = detect_excel_format(file_path)
            logger.info(f"检测到文件 {file_path} 使用引擎: {engine}")
            
            # 尝试读取Excel文件
            df = pd.read_excel(file_path, engine=engine)
            
            # 添加shop列
            df['shop'] = shop_name
            
            logger.info(f"成功读取文件: {file_path}, 数据行数: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {str(e)}")
            # 如果第一次失败，尝试另一个引擎
            try:
                alternative_engine = 'xlrd' if 'openpyxl' in str(e) else 'openpyxl'
                logger.info(f"尝试使用备用引擎 {alternative_engine} 读取文件: {file_path}")
                df = pd.read_excel(file_path, engine=alternative_engine)
                df['shop'] = Path(file_path).stem
                logger.info(f"使用备用引擎成功读取文件: {file_path}, 数据行数: {len(df)}")
                return df
            except Exception as e2:
                logger.error(f"使用备用引擎也失败 {file_path}: {str(e2)}")
                return None
    
    def merge_excel_files(self, output_filename="merged_data.xlsx"):
        """
        合并所有Excel文件
        
        Args:
            output_filename (str): 输出文件名
            
        Returns:
            bool: 合并是否成功
        """
        try:
            # 查找所有Excel文件
            excel_files = self.find_excel_files()
            
            if not excel_files:
                logger.warning("未找到任何Excel文件")
                return False
            
            # 存储所有数据框
            all_dataframes = []
            
            # 逐个读取Excel文件
            for file_path in excel_files:
                df = self.read_excel_file(file_path)
                if df is not None:
                    all_dataframes.append(df)
            
            if not all_dataframes:
                logger.error("没有成功读取任何Excel文件")
                return False
            
            # 合并所有数据框
            logger.info("开始合并数据...")
            merged_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
            
            # 将shop列移到第一列
            cols = merged_df.columns.tolist()
            if 'shop' in cols:
                cols.remove('shop')
                cols.insert(0, 'shop')
                merged_df = merged_df[cols]
            
            # 保存合并后的文件到指定的输出目录
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.output_dir / output_filename
            merged_df.to_excel(output_path, index=False, engine='openpyxl')
            
            logger.info(f"合并完成！")
            logger.info(f"输出文件: {output_path}")
            logger.info(f"总行数: {len(merged_df)}")
            logger.info(f"总列数: {len(merged_df.columns)}")
            logger.info(f"包含的店铺: {merged_df['shop'].unique().tolist()}")
            
            return True
            
        except Exception as e:
            logger.error(f"合并过程中发生错误: {str(e)}")
            return False
    
    def get_summary(self):
        """
        获取文件夹中Excel文件的摘要信息
        
        Returns:
            dict: 摘要信息
        """
        excel_files = self.find_excel_files()
        summary = {
            'total_files': len(excel_files),
            'files': []
        }
        
        for file_path in excel_files:
            try:
                if file_path.endswith('.xlsx') or file_path.endswith('.xlsm'):
                    df = pd.read_excel(file_path, engine='openpyxl')
                else:
                    df = pd.read_excel(file_path, engine='xlrd')
                
                file_info = {
                    'filename': Path(file_path).name,
                    'shop_name': Path(file_path).stem,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': df.columns.tolist()
                }
                summary['files'].append(file_info)
                
            except Exception as e:
                logger.warning(f"无法读取文件摘要 {file_path}: {str(e)}")
        
        return summary

def main(folder_path=None, output_path=None, show_summary=False):
    """
    主函数 - 支持直接传入参数或命令行参数
    
    Args:
        folder_path (str): 包含Excel文件的文件夹路径
        output_path (str): 输出文件路径
        show_summary (bool): 是否显示文件摘要信息
        
    Returns:
        bool: 合并是否成功
    """
    # 如果没有传入参数，则使用命令行参数
    if folder_path is None:
        parser = argparse.ArgumentParser(description='合并Excel文件工具')
        parser.add_argument('folder_path', help='包含Excel文件的文件夹路径')
        parser.add_argument('-o', '--output', default='merged_data.xlsx', help='输出文件名 (默认: merged_data.xlsx)')
        parser.add_argument('-s', '--summary', action='store_true', help='显示文件摘要信息')
        
        args = parser.parse_args()
        folder_path = args.folder_path
        output_path = args.output
        show_summary = args.summary
    
    # 如果没有指定输出路径，使用默认值
    if output_path is None:
        output_path = 'merged_data.xlsx'
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        logger.error(f"文件夹不存在: {folder_path}")
        return False
    
    # 创建合并器
    merger = ExcelMerger(folder_path)
    
    # 如果需要显示摘要
    if show_summary:
        logger.info("获取文件摘要信息...")
        summary = merger.get_summary()
        logger.info(f"文件夹: {folder_path}")
        logger.info(f"Excel文件总数: {summary['total_files']}")
        
        for file_info in summary['files']:
            logger.info(f"  文件: {file_info['filename']}")
            logger.info(f"    店铺名: {file_info['shop_name']}")
            logger.info(f"    行数: {file_info['rows']}")
            logger.info(f"    列数: {file_info['columns']}")
            logger.info(f"    列名: {file_info['column_names']}")
            logger.info("")
    
    # 执行合并
    success = merger.merge_excel_files(output_path)
    
    if success:
        logger.info("Excel文件合并成功！")
        return True
    else:
        logger.error("Excel文件合并失败！")
        return False

if __name__ == "__main__":
    # 如果直接运行脚本，可以在这里设置默认参数进行测试
    import sys
    
    if len(sys.argv) == 1:
        # 交互式模式
        print("Excel文件合并工具")
        print("=" * 50)
        
        folder_path = input("请输入包含Excel文件的文件夹路径: ").strip()
        if not folder_path:
            print("未输入文件夹路径，退出程序")
            sys.exit(1)
        
        output_filename = input("请输入输出文件名 (默认: merged_data.xlsx): ").strip()
        if not output_filename:
            output_filename = "merged_data.xlsx"
        
        show_summary = input("是否显示文件摘要? (y/n, 默认: n): ").strip().lower()
        
        # 检查文件夹是否存在
        if not os.path.exists(folder_path):
            print(f"错误: 文件夹不存在 - {folder_path}")
            sys.exit(1)
        
        # 创建合并器并执行
        merger = ExcelMerger(folder_path)
        
        if show_summary == 'y':
            print("\n获取文件摘要信息...")
            summary = merger.get_summary()
            print(f"文件夹: {folder_path}")
            print(f"Excel文件总数: {summary['total_files']}")
            
            for file_info in summary['files']:
                print(f"  文件: {file_info['filename']}")
                print(f"    店铺名: {file_info['shop_name']}")
                print(f"    行数: {file_info['rows']}")
                print(f"    列数: {file_info['columns']}")
                print("")
        
        print("开始合并Excel文件...")
        success = merger.merge_excel_files(output_filename)
        
        if success:
            print("Excel文件合并成功！")
        else:
            print("Excel文件合并失败！")
    else:
        # 命令行模式
        main()