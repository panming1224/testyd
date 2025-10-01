#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天猫Cookie获取工具 - 数据库集成版本
支持自动登录、Cookie获取和数据库更新
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# 导入数据库接口
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mysql'))
from crawler_db_interface import CrawlerDBInterface

# 导入Cookie优化器
from cookie_optimizer import CookieOptimizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TmallCookieGetter:
    """天猫Cookie获取器 - 支持数据库集成和重试机制"""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        """
        初始化Cookie获取器
        
        Args:
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试间隔时间（秒），默认5秒
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.db = CrawlerDBInterface(shops_table='tm_shops', platform='天猫')
        self.context: Optional[BrowserContext] = None
        self.playwright = None  # 添加playwright实例管理
        self.cookie_optimizer = CookieOptimizer()  # 初始化Cookie优化器
        
        logger.info(f"天猫Cookie获取器初始化完成 - 最大重试次数: {max_retries}, 重试间隔: {retry_delay}秒")
    
    async def init_browser(self, shop_info=None):
        """初始化浏览器"""
        if self.context is None:
            self.playwright = await async_playwright().start()
            
            # 根据店铺信息动态设置用户数据目录和配置文件目录
            USER_DATA_DIR = r"C:\Users\1\AppData\Local\Chromium\User Data"
            if shop_info and shop_info.get('profile'):
                # 使用店铺的profile作为配置文件目录名
                profile_name = shop_info['profile']
            else:
                # 默认配置文件
                profile_name = 'Default'
            
            # 确保目录存在
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            
            # 使用launch_persistent_context启动浏览器
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                args=[
                    "--start-maximized",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    f"--profile-directory={profile_name}",
                ],
                no_viewport=True,
                ignore_https_errors=True,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # 添加反检测脚本
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en'],
                });
                
                window.chrome = {
                    runtime: {},
                };
                
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' }),
                    }),
                });
            """)
            
            logger.info("浏览器初始化完成")
    
    async def close_browser(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
            self.context = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        logger.info("浏览器已关闭")
    
    async def get_cookies_for_shop(self, shop_info: dict) -> bool:
        """
        为单个店铺获取Cookie
        
        Args:
            shop_info: 店铺信息字典
            
        Returns:
            bool: 是否成功获取并更新Cookie
        """
        shop_name = shop_info.get('shop_name', '未知店铺')
        account = shop_info.get('account', '')
        password = shop_info.get('password', '')
        
        if not account or not password:
            logger.warning(f"店铺 {shop_name} 缺少账号或密码信息")
            return False
        
        try:
            await self.init_browser(shop_info)
            
            # 获取千牛Cookie
            qncookie = await self._get_qianniu_cookie(account, password)
            
            # 获取生意参谋Cookie
            sycmcookie = await self._get_sycm_cookie(account, password)
            
            
            # 更新数据库
            success = self.db.update_shop_cookies(shop_name, qncookie, sycmcookie)
            
            if success:
                # 更新状态为active
                self.db.update_shop_status(shop_name, 'active')
                logger.info(f"店铺 {shop_name} Cookie获取并更新成功")
                return True
            else:
                logger.error(f"店铺 {shop_name} 数据库更新失败")
                return False
            
        except Exception as e:
            logger.error(f"店铺 {shop_name} Cookie获取失败: {e}")
            return False
        finally:
            # 每个店铺处理完后关闭浏览器
            await self.close_browser()
    
    async def _get_qianniu_cookie(self, account: str, password: str) -> Optional[str]:
        """获取千牛Cookie"""
        try:
            page = await self.context.new_page()
            
            # 访问千牛登录页面
            await page.goto('https://login.taobao.com/member/login.jhtml')
            await page.wait_for_timeout(1000)
            
            # 输入账号密码
            await page.fill('#fm-login-id', account)
            time.sleep(0.5)
            await page.fill('#fm-login-password', password)
            time.sleep(0.4)
            
            # 点击登录
            await page.click('#login-form button[type="submit"]')
            await page.wait_for_timeout(500)
            
            # 检查是否有确认对话框，如果有则点击确认
            try:
                confirm_button = page.locator('button.dialog-btn-ok')
                if await confirm_button.is_visible(timeout=500):
                    await confirm_button.click()
                    await page.wait_for_timeout(500)
            except:
                # 如果没有确认按钮，继续执行
                pass
            
            # 等待登录完成，检查页面是否跳转
            await page.wait_for_timeout(500)
           
            # 获取Cookie
            cookies = await page.context.cookies('https://myseller.taobao.com/home.htm/comment-manage/list')
            
            # 定义必要的cookie字段
            essential_fields = ['_m_h5_tk', '_m_h5_tk_enc', 't', 'xlly_s', 'mtop_partitioned_detect', '_tb_token_', '_samesite_flag_', '3PcFlag', 'cookie2', 'sgcookie', 'unb', 'sn', 'uc1', 'csg', '_cc_', 'cancelledSubSites', 'skt', 'cna', 'tfstk']
            
            # 过滤出必要的cookie字段
            essential_cookies = []
            for cookie in cookies:
                if cookie['name'] in essential_fields:
                    essential_cookies.append(f"{cookie['name']}={cookie['value']}")
            
            # 构建cookie字符串
            cookie_str = '; '.join(essential_cookies)
            
            # 记录获取到的cookie信息
            logger.info(f"获取到 {len(essential_cookies)} 个必要cookie字段")
            logger.info(f"Cookie字段: {[cookie['name'] for cookie in cookies if cookie['name'] in essential_fields]}")
            
            await page.wait_for_timeout(500)
            
            await page.close()
            return cookie_str
            
        except Exception as e:
            logger.error(f"获取千牛Cookie失败: {e}")
            return None
    
    async def _get_sycm_cookie(self, account: str, password: str) -> Optional[str]:
        """获取生意参谋Cookie"""
        try:
            page = await self.context.new_page()
            
            # 访问生意参谋登录页面
            await page.goto('https://sycm.taobao.com/qos/service/self_made_report#/self_made_report')
            await page.wait_for_timeout(3000)
            
            # 获取Cookie
            cookies = await page.context.cookies()
            cookie_str = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            
            await page.close()
            return cookie_str
            
        except Exception as e:
            logger.error(f"获取生意参谋Cookie失败: {e}")
            return None
    
    def process_shop_with_retry(self, shop_info: Dict) -> bool:
        """
        带重试机制的店铺处理
        
        Args:
            shop_info: 店铺信息
            
        Returns:
            bool: 处理是否成功
        """
        shop_name = shop_info.get('shop_name', '未知店铺')
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"店铺 {shop_name} - 第 {attempt} 次尝试")
                
                # 异步获取Cookie
                result = asyncio.run(self.get_cookies_for_shop(shop_info))
                
                if result:
                    logger.info(f"店铺 {shop_name} - Cookie获取成功")
                    return True
                else:
                    logger.warning(f"店铺 {shop_name} - 第 {attempt} 次尝试失败")
                    
            except Exception as e:
                logger.error(f"店铺 {shop_name} - 第 {attempt} 次尝试出错: {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries:
                logger.info(f"店铺 {shop_name} - {self.retry_delay} 秒后重试")
                time.sleep(self.retry_delay)
        
        logger.error(f"店铺 {shop_name} - 所有重试均失败")
        return False
    
    def run_daily_process(self):
        """
        执行每日处理流程
        
        1. 检查并重置非今日更新的店铺状态
        2. 获取需要重试的店铺
        3. 处理店铺Cookie获取和更新
        """
        try:
            logger.info("开始执行每日Cookie获取流程")
            
            # 1. 检查并重置每日状态
            reset_count = self.db.check_and_reset_daily_status()
            logger.info(f"重置了 {reset_count} 个店铺的状态")
            
            # 2. 获取需要重试的店铺
            retry_shops = self.db.get_shops_need_retry()
            
            if not retry_shops:
                logger.info("没有需要处理的店铺")
                return
            
            logger.info(f"找到 {len(retry_shops)} 个需要处理的店铺")
            
            # 3. 处理每个店铺
            success_count = 0
            for shop_info in retry_shops:
                shop_name = shop_info.get('shop_name', '未知店铺')
                logger.info(f"开始处理店铺: {shop_name}")
                
                if self.process_shop_with_retry(shop_info):
                    success_count += 1
                
                # 每个店铺处理完后稍作休息
                time.sleep(2)
            
            logger.info(f"每日处理完成 - 成功: {success_count}/{len(retry_shops)}")
            
        except Exception as e:
            logger.error(f"每日处理流程出错: {e}")
        finally:
            # 关闭数据库连接
            self.db.close_pool()

def main():
    """主函数"""
    try:
        # 创建Cookie获取器
        cookie_getter = TmallCookieGetter(max_retries=3, retry_delay=5)
        
        # 执行每日处理流程
        cookie_getter.run_daily_process()
        
    except Exception as e:
        logger.error(f"程序执行出错: {e}")

if __name__ == "__main__":
    main()