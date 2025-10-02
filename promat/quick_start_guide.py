#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多 anti-content 参数快速开始指南
Quick Start Guide for Pinduoduo anti-content Parameter

本文件提供了最简单的使用方式和示例代码
This file provides the simplest usage and example code
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def quick_demo():
    """快速演示 - Quick Demo"""
    print("=== 拼多多 anti-content 参数快速演示 ===")
    print("=== Pinduoduo anti-content Parameter Quick Demo ===\n")
    
    try:
        # 导入生产环境客户端
        from production_ready_anti_content import ProductionPddClient
        
        # 创建客户端
        print("1. 创建客户端...")
        client = ProductionPddClient()
        
        # 搜索商品示例
        print("2. 搜索商品示例...")
        search_terms = ["手机", "电脑", "耳机"]
        
        for term in search_terms:
            print(f"\n搜索: {term}")
            try:
                result = client.search_products(term)
                if result and result.get('success'):
                    print(f"✅ 成功 - 状态码: {result.get('status_code')}")
                    print(f"   响应长度: {len(str(result.get('data', '')))} 字符")
                else:
                    print(f"❌ 失败 - {result}")
            except Exception as e:
                print(f"❌ 错误: {e}")
        
        # 显示统计信息
        print("\n3. 统计信息:")
        stats = client.get_stats()
        if isinstance(stats, dict):
            print(f"   总请求数: {stats.get('total_requests', 0)}")
            print(f"   成功请求数: {stats.get('successful_requests', 0)}")
            print(f"   成功率: {stats.get('success_rate', 0):.1%}")
            print(f"   平均响应时间: {stats.get('average_response_time', 0):.3f}秒")
        else:
            print(f"   总请求数: {stats.total_requests}")
            print(f"   成功请求数: {stats.successful_requests}")
            print(f"   成功率: {stats.success_rate:.1%}")
            print(f"   平均响应时间: {stats.average_response_time:.3f}秒")
        
    except ImportError:
        print("❌ 未找到生产环境模块，尝试使用基础版本...")
        try:
            from final_anti_content_solution import PddRequestHelper
            
            print("1. 创建请求助手...")
            helper = PddRequestHelper()
            
            print("2. 搜索商品示例...")
            result = helper.search_products("手机")
            if result:
                print(f"✅ 成功 - 状态码: {result.get('status_code')}")
            else:
                print("❌ 请求失败")
                
        except ImportError:
            print("❌ 未找到任何可用模块，请确保文件完整")

def simple_usage_example():
    """简单使用示例 - Simple Usage Example"""
    print("\n=== 简单使用示例代码 ===")
    print("=== Simple Usage Example Code ===\n")
    
    example_code = '''
# 方式1: 使用生产环境客户端（推荐）
from production_ready_anti_content import ProductionPddClient

client = ProductionPddClient()
result = client.search_products("手机")
print(f"搜索结果: {result}")

# 方式2: 使用基础版本
from final_anti_content_solution import PddRequestHelper

helper = PddRequestHelper()
result = helper.search_products("电脑")
print(f"搜索结果: {result}")

# 方式3: 自定义请求
result = client.make_request(
    url="https://mms.pinduoduo.com/saturn/api/search",
    params={"keyword": "耳机", "page": 1}
)
print(f"自定义请求结果: {result}")
'''
    
    print(example_code)

def advanced_usage_example():
    """高级使用示例 - Advanced Usage Example"""
    print("\n=== 高级使用示例 ===")
    print("=== Advanced Usage Example ===\n")
    
    try:
        from production_ready_anti_content import ProductionPddClient, AntiContentMonitor
        
        print("1. 启动监控...")
        client = ProductionPddClient()
        monitor = AntiContentMonitor(client)
        monitor.start_monitoring()
        
        print("2. 批量搜索...")
        products = ["手机壳", "数据线", "充电器", "蓝牙耳机", "移动电源"]
        
        results = []
        for product in products:
            print(f"   搜索: {product}")
            result = client.search_products(product)
            results.append({
                'product': product,
                'success': result.get('success', False) if result else False,
                'status_code': result.get('status_code') if result else None
            })
        
        print("\n3. 批量结果:")
        for r in results:
            status = "✅" if r['success'] else "❌"
            print(f"   {status} {r['product']} - 状态码: {r['status_code']}")
        
        print("\n4. 最终统计:")
        stats = client.get_stats()
        if isinstance(stats, dict):
            print(f"   成功率: {stats.get('success_rate', 0):.1%}")
            print(f"   平均响应时间: {stats.get('average_response_time', 0):.3f}秒")
        else:
            print(f"   成功率: {stats.success_rate:.1%}")
            print(f"   平均响应时间: {stats.average_response_time:.3f}秒")
        
        # 停止监控
        monitor.stop_monitoring()
        
    except ImportError:
        print("❌ 高级功能需要完整的生产环境模块")

def troubleshooting_guide():
    """故障排除指南 - Troubleshooting Guide"""
    print("\n=== 故障排除指南 ===")
    print("=== Troubleshooting Guide ===\n")
    
    guide = '''
常见问题和解决方案:

1. 导入错误 (ImportError)
   - 确保所有必要文件在同一目录
   - 检查 Python 路径设置
   - 安装必要依赖: pip install requests

2. 请求失败 (Request Failed)
   - 检查网络连接
   - 验证目标网站可访问性
   - 查看错误日志文件 anti_content.log

3. 成功率低 (Low Success Rate)
   - 检查 anti-content 生成算法
   - 验证请求头设置
   - 尝试不同的生成方法

4. 响应时间慢 (Slow Response)
   - 检查网络延迟
   - 启用缓存功能
   - 调整重试策略

5. 内存使用高 (High Memory Usage)
   - 清理缓存: client.clear_cache()
   - 减少并发请求数
   - 定期重启应用

联系支持:
- 查看项目文档: project_summary.md
- 检查日志文件: anti_content.log
- 运行测试脚本: batch_test_anti_content.py
'''
    
    print(guide)

def main():
    """主函数 - Main Function"""
    print("拼多多 anti-content 参数 - 快速开始指南")
    print("Pinduoduo anti-content Parameter - Quick Start Guide")
    print("=" * 60)
    
    # 快速演示
    quick_demo()
    
    # 使用示例
    simple_usage_example()
    
    # 高级示例
    advanced_usage_example()
    
    # 故障排除
    troubleshooting_guide()
    
    print("\n" + "=" * 60)
    print("快速开始指南完成！")
    print("Quick Start Guide Complete!")

if __name__ == "__main__":
    main()