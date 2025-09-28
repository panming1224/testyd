#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多店铺MySQL任务调度器
集成现有爬虫脚本，使用MySQL管理任务状态
"""

import time
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import logging
from simple_pdd_mysql_manager import SimplePDDMySQLManager, ShopStatus

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDDMySQLScheduler:
    """拼多多MySQL任务调度器"""
    
    def __init__(self, max_workers=3):
        """初始化调度器"""
        self.max_workers = max_workers
        self.task_queue = Queue()
        self.mysql_manager = SimplePDDMySQLManager()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        
    def start(self):
        """启动调度器"""
        logger.info("启动MySQL任务调度器...")
        
        # 连接数据库
        if not self.mysql_manager.connect():
            logger.error("数据库连接失败，调度器启动失败")
            return False
        
        self.running = True
        
        # 启动任务加载线程
        threading.Thread(target=self._load_tasks_loop, daemon=True).start()
        
        # 启动任务处理线程
        threading.Thread(target=self._process_tasks_loop, daemon=True).start()
        
        logger.info(f"调度器启动成功，最大并发数: {self.max_workers}")
        return True
    
    def _load_tasks_loop(self):
        """任务加载循环"""
        while self.running:
            try:
                # 获取待处理的店铺
                pending_shops = self.mysql_manager.get_pending_shops(limit=10)
                
                for shop in pending_shops:
                    if not self.running:
                        break
                    
                    # 将任务加入队列
                    self.task_queue.put(shop)
                    logger.info(f"加载任务: {shop['shop_name']} (ID: {shop['id']})")
                
                # 每30秒检查一次新任务
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"加载任务失败: {e}")
                time.sleep(10)
    
    def _process_tasks_loop(self):
        """任务处理循环"""
        while self.running:
            try:
                # 从队列获取任务
                if not self.task_queue.empty():
                    shop = self.task_queue.get(timeout=5)
                    
                    # 提交任务到线程池
                    future = self.executor.submit(self._process_shop_task, shop)
                    
                    # 可以在这里添加回调处理结果
                    future.add_done_callback(lambda f: self._task_completed(f))
                else:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"处理任务失败: {e}")
                time.sleep(5)
    
    def _process_shop_task(self, shop):
        """处理单个店铺任务"""
        shop_id = shop['id']
        shop_name = shop['shop_name']
        cookie = shop['cookie']
        
        logger.info(f"开始处理店铺: {shop_name} (ID: {shop_id})")
        
        try:
            # 这里集成现有的爬虫逻辑
            # 模拟任务处理（实际应该调用pdd_badscore.py的相关函数）
            success = self._simulate_crawl_task(shop_name, cookie)
            
            if success:
                # 更新状态为已完成
                self.mysql_manager.update_shop_status(shop_id, ShopStatus.COMPLETED)
                logger.info(f"店铺 {shop_name} 处理成功")
                return True
            else:
                # 更新状态为失败
                self.mysql_manager.update_shop_status(shop_id, ShopStatus.FAILED, "爬取失败")
                logger.error(f"店铺 {shop_name} 处理失败")
                return False
                
        except Exception as e:
            # 更新状态为失败
            error_msg = f"处理异常: {str(e)}"
            self.mysql_manager.update_shop_status(shop_id, ShopStatus.FAILED, error_msg)
            logger.error(f"店铺 {shop_name} 处理异常: {e}")
            return False
    
    def _simulate_crawl_task(self, shop_name, cookie):
        """模拟爬虫任务（实际应该调用真实的爬虫函数）"""
        # 检查cookie是否有效
        if not cookie or cookie.strip() == "" or "nan" in str(cookie).lower():
            logger.warning(f"店铺 {shop_name} cookie无效，跳过处理")
            return False
        
        # 模拟处理时间
        time.sleep(2)
        
        # 模拟成功率（实际应该是真实的爬虫逻辑）
        import random
        return random.random() > 0.2  # 80%成功率
    
    def _task_completed(self, future):
        """任务完成回调"""
        try:
            result = future.result()
            if result:
                logger.debug("任务执行成功")
            else:
                logger.debug("任务执行失败")
        except Exception as e:
            logger.error(f"任务执行异常: {e}")
    
    def get_status(self):
        """获取调度器状态"""
        stats = self.mysql_manager.get_shop_stats()
        queue_size = self.task_queue.qsize()
        
        status = {
            "running": self.running,
            "queue_size": queue_size,
            "shop_stats": stats,
            "max_workers": self.max_workers
        }
        
        return status
    
    def stop(self):
        """停止调度器"""
        logger.info("停止调度器...")
        self.running = False
        
        # 等待线程池完成
        self.executor.shutdown(wait=True)
        
        # 关闭数据库连接
        self.mysql_manager.close()
        
        logger.info("调度器已停止")

def main():
    """主函数"""
    scheduler = PDDMySQLScheduler(max_workers=2)
    
    try:
        # 启动调度器
        if not scheduler.start():
            print("调度器启动失败")
            return
        
        print("调度器已启动，按 Ctrl+C 停止...")
        
        # 定期显示状态
        while True:
            time.sleep(10)
            status = scheduler.get_status()
            print(f"状态: 队列大小={status['queue_size']}, 店铺统计={status['shop_stats']}")
            
    except KeyboardInterrupt:
        print("\n收到停止信号...")
    finally:
        scheduler.stop()
        print("调度器已停止")

if __name__ == "__main__":
    main()