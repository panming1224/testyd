# -*- coding: utf-8 -*-
"""
列出Flask应用的所有路由
"""

import requests
import json

def list_flask_routes():
    """通过访问API来检查可用的路由"""
    
    base_url = "http://localhost:8009"
    
    # 测试已知的路由
    known_routes = [
        "/health",
        "/api/test",
        "/api/upload/parquet",
        "/api/upload/json", 
        "/api/upload/iceberg",
        "/api/buckets",
        "/api/buckets/create",
        "/api/buckets/delete"
    ]
    
    print("检查MinIO API服务的可用路由:")
    print("=" * 50)
    
    for route in known_routes:
        try:
            url = f"{base_url}{route}"
            
            # 对于GET路由，直接访问
            if route in ["/health", "/api/test", "/api/buckets"]:
                response = requests.get(url, timeout=5)
            else:
                # 对于POST路由，发送空的POST请求来检查是否存在
                response = requests.post(url, json={}, timeout=5)
            
            if response.status_code == 404:
                print(f"❌ {route} - 不存在")
            elif response.status_code in [200, 400, 405]:  # 400表示参数错误但路由存在，405表示方法不允许但路由存在
                print(f"✅ {route} - 存在 (状态码: {response.status_code})")
            else:
                print(f"⚠️  {route} - 状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {route} - 连接错误: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    list_flask_routes()