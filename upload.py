# 使用提醒:
# 1. xbot包提供软件自动化、数据表格、Excel、日志、AI等功能
# 2. package包提供访问当前应用数据的功能，如获取元素、访问全局变量、获取资源文件等功能
# 3. 当此模块作为流程独立运行时执行main函数
# 4. 可视化流程中可以通过"调用模块"的指令使用此模块

import xbot
from xbot import print, sleep
from .import package
from .package import variables as glv
import os
import sys
import pandas as pd
from minio import Minio, S3Error
import io
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rpa_uploader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedExcelUploader:
    """增强Excel上传器 - 影刀RPA版本（支持Excel原文件和Parquet格式）"""
    
    def __init__(self, minio_endpoint="localhost:9002", access_key="admin", secret_key="admin123", bucket_name="warehouse"):
        """初始化MinIO客户端"""
        self.minio_endpoint = minio_endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        
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
    
    def test_connection(self) -> bool:
        """测试MinIO连接"""
        try:
            return self._ensure_bucket_exists()
        except Exception as e:
            logger.error(f"MinIO连接失败: {e}")
            return False
    
    def remove_existing_file(self, object_path):
        """删除已存在的同名文件"""
        try:
            # 检查文件是否存在
            self.minio_client.stat_object(self.bucket_name, object_path)
            # 如果文件存在，删除它
            self.minio_client.remove_object(self.bucket_name, object_path)
            logger.info(f"删除已存在的同名文件: {object_path}")
        except S3Error as e:
            if e.code == 'NoSuchKey':
                logger.debug(f"文件不存在，无需删除: {object_path}")
            else:
                logger.error(f"检查文件时出错: {e}")
        except Exception as e:
            logger.error(f"删除文件时出错: {e}")
    
    def ensure_path_exists(self, target_path):
        """确保路径存在（通过创建标记文件）"""
        try:
            # 获取目录路径
            dir_path = '/'.join(target_path.split('/')[:-1])
            if dir_path:
                marker_path = f"{dir_path}/.path_marker"
                
                # 检查标记文件是否已存在
                try:
                    self.minio_client.stat_object(self.bucket_name, marker_path)
                    logger.debug(f"路径标记已存在: {dir_path}")
                except S3Error:
                    # 标记文件不存在，创建它
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
    
    def upload_excel_file(self, excel_file_path: str, target_path: str) -> Dict[str, Any]:
        """上传Excel原文件到MinIO
        
        Args:
            excel_file_path: Excel文件路径
            target_path: MinIO中的目标路径（包含分区信息）
        
        Returns:
            Dict: 上传结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(excel_file_path):
                return {
                    'success': False,
                    'message': f'Excel文件不存在: {excel_file_path}'
                }
            
            # 使用传入的目标路径
            file_name = os.path.basename(excel_file_path)
            
            logger.info(f"开始上传Excel文件: {target_path}")
            
            # 检查并删除同名文件
            self.remove_existing_file(target_path)
            
            # 确保路径存在
            self.ensure_path_exists(target_path)
            
            # 上传文件
            self.minio_client.fput_object(
                self.bucket_name,
                target_path,
                excel_file_path,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            logger.info(f"Excel文件上传成功: {target_path}")
            return {
                'success': True,
                'message': f'Excel文件上传成功: {target_path}',
                'target_path': target_path,
                'file_type': 'excel'
            }
            
        except Exception as e:
            logger.error(f"上传Excel失败: {e}")
            return {
                'success': False,
                'message': f'上传Excel失败: {str(e)}'
            }
    
    def _convert_to_parquet(self, file_path: str, output_dir: str = "temp_conversion") -> str:
        """将文件转换为Parquet格式
        
        Args:
            file_path: 输入文件路径
            output_dir: 输出目录
        
        Returns:
            str: 转换后的Parquet文件路径
        """
        # 创建临时转换目录
        os.makedirs(output_dir, exist_ok=True)
        
        file_ext = Path(file_path).suffix.lower()
        base_name = Path(file_path).stem
        output_path = os.path.join(output_dir, f"{base_name}.parquet")
        
        try:
            if file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                logger.info(f"成功读取Excel文件: {file_path}")
            elif file_ext == '.parquet':
                # 如果已经是Parquet格式，直接返回原文件
                logger.info(f"文件已是Parquet格式: {file_path}")
                return file_path
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}，仅支持Excel(.xlsx/.xls)和Parquet(.parquet)格式")
            
            # 保存为Parquet格式
            df.to_parquet(output_path, index=False, engine='pyarrow')
            logger.info(f"文件转换成功: {file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"文件转换失败: {e}")
            raise
    
    def upload_excel_as_parquet(self, excel_file_path: str, target_path: str, 
                               sheet_name: int = 0) -> Dict[str, Any]:
        """读取Excel并转换为Parquet格式上传到MinIO
        
        Args:
            excel_file_path: Excel文件路径
            target_path: MinIO中的目标路径（包含分区信息）
            sheet_name: Excel工作表索引
        
        Returns:
            Dict: 上传结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(excel_file_path):
                return {
                    'success': False,
                    'message': f'Excel文件不存在: {excel_file_path}'
                }
            
            # 使用传入的目标路径
            file_name = os.path.splitext(os.path.basename(excel_file_path))[0]
            
            logger.info(f"开始转换并上传Parquet数据: {target_path}")
            
            # 转换为Parquet格式
            parquet_file = self._convert_to_parquet(excel_file_path)
            
            # 检查并删除同名文件
            self.remove_existing_file(target_path)
            
            # 确保路径存在
            self.ensure_path_exists(target_path)
            
            # 上传Parquet文件
            self.minio_client.fput_object(
                self.bucket_name,
                target_path,
                parquet_file,
                content_type='application/octet-stream'
            )
            
            # 清理临时文件（如果是转换生成的）
            if parquet_file != excel_file_path and os.path.exists(parquet_file):
                os.remove(parquet_file)
                logger.info(f"清理临时文件: {parquet_file}")
            
            logger.info(f"Parquet文件上传成功: {target_path}")
            return {
                'success': True,
                'message': f'Parquet文件上传成功: {target_path}',
                'target_path': target_path,
                'file_type': 'parquet'
            }
            
        except Exception as e:
            logger.error(f"上传Parquet失败: {e}")
            return {
                'success': False,
                'message': f'上传Parquet失败: {str(e)}'
            }
    
    def upload_request_data(self, request_data, filename: str, target_path: str,
                           data_format: str = "parquet") -> Dict[str, Any]:
        """将request数据（JSON格式）上传到MinIO
        
        Args:
            request_data: 请求数据，可以是字典、字典列表或JSON字符串
            filename: 文件名（不含扩展名）
            target_path: MinIO中的目标路径（包含分区信息）
            data_format: 数据格式，支持 'parquet' 或 'json'
        
        Returns:
            Dict: 上传结果
        """
        try:
            # 处理输入数据
            if isinstance(request_data, str):
                # 如果是JSON字符串，解析为Python对象
                import json
                data = json.loads(request_data)
            else:
                data = request_data
            
            # 确保数据是DataFrame格式
            if isinstance(data, dict):
                # 单个字典转换为包含一行的DataFrame
                df = pd.DataFrame([data])
            elif isinstance(data, list):
                # 字典列表转换为DataFrame
                df = pd.DataFrame(data)
            else:
                raise ValueError(f"不支持的数据类型: {type(data)}")
            
            logger.info(f"处理request数据成功，共 {len(df)} 行数据")
            
            # 使用传入的目标路径
            
            # 根据格式处理数据
            if data_format == "parquet":
                # 转换为Parquet格式
                buffer = io.BytesIO()
                df.to_parquet(buffer, index=False, engine='pyarrow')
                buffer.seek(0)
                content_type = 'application/octet-stream'
                data_size = len(buffer.getvalue())
            else:
                # 保存为JSON格式
                import json
                json_str = df.to_json(orient='records', ensure_ascii=False, indent=2)
                buffer = io.BytesIO(json_str.encode('utf-8'))
                content_type = 'application/json'
                data_size = len(buffer.getvalue())
            
            # 检查并删除同名文件
            self.remove_existing_file(target_path)
            
            # 确保路径存在
            self.ensure_path_exists(target_path)
            
            # 上传到MinIO
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=target_path,
                data=buffer,
                length=data_size,
                content_type=content_type
            )
            
            logger.info(f"Request数据上传成功: {target_path}")
            return {
                'success': True,
                'message': f'Request数据上传成功: {target_path}',
                'target_path': target_path,
                'file_size': data_size,
                'rows_count': len(df),
                'data_format': data_format
            }
            
        except Exception as e:
            error_msg = f"Request数据上传失败: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'error': str(e)
            }
    


def main(LOCAL_EXCEL_FILE,MINIO_TARGET_PATH_EXCEL,MINIO_TARGET_PATH_PARQUET,MINIO_BUCKET):
    """影刀RPA主函数 - Excel文件上传到MinIO（支持Excel和Request格式）"""
    
    # ==================== 配置区域 ====================
    # 本地文件路径配置
    # LOCAL_EXCEL_FILE = r"C:\Users\Desktop\Excel文件\数据文件.xlsx"  # 本地Excel文件路径
    
    # # MinIO目标路径配置（分区信息直接写在路径中）
    # MINIO_TARGET_PATH_EXCEL = "ods/dt=2025-09-10/数据文件.xlsx"     # Excel文件在MinIO中的目标路径
    # MINIO_TARGET_PATH_PARQUET = "ods/dt=2025-09-10/数据文件.parquet" # Parquet文件在MinIO中的目标路径
    
    # MinIO连接配置
    MINIO_ENDPOINT = "100.120.50.34:9002"  # MinIO服务地址
    MINIO_ACCESS_KEY = "admin"         # MinIO访问密钥
    MINIO_SECRET_KEY = "admin123"      # MinIO密钥
    # MINIO_BUCKET = "pddchat"         # MinIO存储桶名称
    
    # ==================== 执行区域 ====================
    
    try:
        print("开始执行Excel文件上传任务...")
        
        # 初始化上传器
        uploader = EnhancedExcelUploader(
            minio_endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            bucket_name=MINIO_BUCKET
        )
        
        # 测试连接
        if not uploader.test_connection():
            print("❌ MinIO连接失败，请检查配置")
            return False
        
        print("✅ MinIO连接成功")
        
        # 检查本地文件是否存在
        if not os.path.exists(LOCAL_EXCEL_FILE):
            print(f"❌ 本地Excel文件不存在: {LOCAL_EXCEL_FILE}")
            return False
        
        print(f"📁 找到本地Excel文件: {LOCAL_EXCEL_FILE}")
        
        # 方式1: 上传Excel原文件（便于人工查看和审计）
        print("\n🔄 开始上传Excel原文件...")
        excel_result = uploader.upload_excel_file(
            excel_file_path=LOCAL_EXCEL_FILE,
            target_path=MINIO_TARGET_PATH_EXCEL
        )
        
        if excel_result['success']:
            print(f"✅ {excel_result['message']}")
        else:
            print(f"❌ {excel_result['message']}")
            return False
        
        # 等待1秒
        sleep(1)
        
        # 方式2: 转换为Parquet并上传（推荐，性能最佳）
        print("\n🔄 开始转换并上传Parquet文件...")
        parquet_result = uploader.upload_excel_as_parquet(
            excel_file_path=LOCAL_EXCEL_FILE,
            target_path=MINIO_TARGET_PATH_PARQUET,
            sheet_name=0  # 使用第一个工作表
        )
        
        if parquet_result['success']:
            print(f"✅ {parquet_result['message']}")
        else:
            print(f"❌ {parquet_result['message']}")
            return False
        
        
        print("\n🎉 所有文件上传完成！")
        print(f"📊 Excel原文件路径: {excel_result['target_path']}")
        print(f"📊 Parquet文件路径: {parquet_result['target_path']}")
        # print(f"📊 Request数据路径: {request_result['target_path']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 上传过程中发生错误: {e}")
        logger.error(f"影刀RPA执行失败: {e}")
        return False