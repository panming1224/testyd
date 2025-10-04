# -*- coding: utf-8 -*-
"""
调度器部署脚本 - 将任务部署到Prefect服务器
"""
import sys
import os
import logging
from datetime import datetime
from prefect import flow

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入任务配置
from scheduler_config import TASK_CONFIGS, logger

def deploy_tasks():
    """部署所有任务到Prefect服务器"""
    try:
        logger.info("🚀 开始部署任务到Prefect服务器...")
        
        deployed_count = 0
        
        for config in TASK_CONFIGS:
            if not config.get('enabled', True):
                logger.info(f"跳过禁用的任务: {config['name']}")
                continue
            
            try:
                # 获取flow对象
                flow_func = config['flow']
                
                # 使用from_source创建部署，指定本地路径
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
                # 使用函数的实际名称而不是显示名称
                func_name = flow_func.__name__
                
                deployment_flow = flow.from_source(
                    source=current_dir,
                    entrypoint=f"scheduler_flows.py:{func_name}"
                )
                
                # 部署流
                deployment_id = deployment_flow.deploy(
                    name=config['name'],
                    work_pool_name="default-pool",
                    cron=config.get('cron'),
                    description=config.get('description', ''),
                    tags=config.get('tags', [])
                )
                
                deployed_count += 1
                logger.info(f"✅ 部署成功: {config['name']} (ID: {deployment_id})")
                
            except Exception as e:
                logger.error(f"❌ 部署失败 {config['name']}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info(f"🎉 部署完成！成功部署 {deployed_count} 个任务")
        return deployed_count
        
    except Exception as e:
        logger.error(f"❌ 部署过程出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0

def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("📦 任务部署工具")
    logger.info("=" * 80)
    
    # 运行部署
    deployed_count = deploy_tasks()
    
    if deployed_count > 0:
        logger.info("=" * 80)
        logger.info("✅ 部署完成！")
        logger.info(f"📊 可视化界面: http://127.0.0.1:4200")
        logger.info("=" * 80)
    else:
        logger.error("❌ 部署失败，请检查日志")

if __name__ == "__main__":
    main()