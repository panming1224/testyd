import pandas as pd
import requests
import json
from datetime import datetime
from pathlib import Path

# MinIO API配置
MINIO_API_URL = "http://127.0.0.1:8009/api/upload"
MINIO_BUCKET = "warehouse"

def upload_existing_merged_file(file_path: str, date_str: str) -> bool:
    """
    上传已存在的合并文件到MinIO
    """
    try:
        print(f"🔄 开始上传文件: {file_path}")
        
        # 检查文件是否存在
        if not Path(file_path).exists():
            print(f"[错误] 文件不存在: {file_path}")
            return False
        
        # 读取Excel文件
        print("📖 正在读取Excel文件...")
        df = pd.read_excel(file_path)
        print(f"[成功] 文件读取成功，共 {len(df)} 行数据")
        
        # 处理NaN值 - 将NaN替换为None，这样在JSON序列化时会变成null
        print("🔧 正在处理数据中的NaN值...")
        df = df.where(pd.notnull(df), None)
        print("[成功] NaN值处理完成")
        
        # 构建MinIO路径：ods/pdd/pdd_quality/dt=日期/merged_quality_data.parquet
        minio_path = f"ods/pdd/pdd_quality/dt={date_str}/merged_quality_data.parquet"
        print(f"📁 目标MinIO路径: {minio_path}")
        
        # 准备上传数据
        upload_data = {
            "data": df.to_dict('records'),
            "target_path": minio_path,
            "format": "parquet",
            "bucket": MINIO_BUCKET
        }
        
        print(f"📊 准备上传 {len(df)} 条记录...")
        
        # 发送POST请求到MinIO API
        headers = {'Content-Type': 'application/json'}
        print("🔄 正在发送请求到MinIO API...")
        
        response = requests.post(MINIO_API_URL, json=upload_data, headers=headers, timeout=60)
        
        print(f"📡 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📡 响应内容: {result}")
            
            if result.get('success'):
                print(f"[成功] 成功上传合并文件到MinIO!")
                print(f"📁 文件路径: {minio_path}")
                print(f"📊 数据行数: {result.get('rows_count', 'N/A')}")
                print(f"📏 文件大小: {result.get('file_size', 'N/A')} bytes")
                return True
            else:
                print(f"[错误] MinIO上传失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"[错误] MinIO API请求失败: {response.status_code}")
            print(f"[错误] 错误详情: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[错误] 请求超时，MinIO API响应缓慢")
        return False
    except requests.exceptions.ConnectionError:
        print("[错误] 连接错误，无法连接到MinIO API")
        return False
    except Exception as e:
        print(f"[错误] 上传文件时出错: {str(e)}")
        return False

def refresh_dremio_dataset_and_reflection():
    """刷新Dremio数据集和反射"""
    print('🔄 正在刷新数据集...')
    try:
        refresh_dataset_response = requests.post(
            "http://localhost:8003/api/dataset/refresh-metadata",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.pdd.pdd_quality"}
        )
        if refresh_dataset_response.status_code == 200:
            print('[成功] 数据集刷新成功')
        else:
            print(f'[警告]  数据集刷新失败: {refresh_dataset_response.status_code}')
    except Exception as e:
        print(f'[错误] 数据集刷新异常: {e}')
    
    print('🔄 正在刷新反射...')
    try:
        refresh_reflection_response = requests.post(
            "http://localhost:8003/api/reflection/refresh",
            headers={"Content-Type": "application/json"},
            json={"dataset_path": "minio.warehouse.ods.pdd.pdd_quality"}
        )
        if refresh_reflection_response.status_code == 200:
            print('[成功] 反射刷新成功')
        else:
            print(f'[警告]  反射刷新失败: {refresh_reflection_response.status_code}')
    except Exception as e:
        print(f'[错误] 反射刷新异常: {e}')

if __name__ == '__main__':
    # 上传2025-09-27的合并文件
    date_str = "2025-09-27"
    file_path = f"D:/pdd/合并文件/产品质量体验存档/{date_str}.xlsx"
    
    print(f"🎯 开始上传 {date_str} 的产品质量合并文件")
    
    success = upload_existing_merged_file(file_path, date_str)
    
    if success:
        print("[成功] 文件上传成功，开始刷新Dremio...")
        refresh_dremio_dataset_and_reflection()
        print("🎉 所有任务完成！")
    else:
        print("💥 文件上传失败")
