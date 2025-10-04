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
            # 注意：headless=False 因为淘宝可能检测无头浏览器并拒绝生成_m_h5_tk
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,  # 改为非静默模式，淘宝可能检测headless
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-gpu",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    f"--profile-directory={profile_name}",
                ],
                viewport={'width': 1920, 'height': 1080},  # 设置视口大小
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
            
            logger.info("浏览器初始化完成（可见模式 - 用于获取_m_h5_tk）")
    
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
            await page.wait_for_timeout(2000)
            
            # 输入账号密码
            await page.fill('#fm-login-id', account)
            await page.wait_for_timeout(500)
            await page.fill('#fm-login-password', password)
            await page.wait_for_timeout(500)
            
            # 点击登录
            await page.click('#login-form button[type="submit"]')
            await page.wait_for_timeout(2000)
            
            # 检查是否有确认对话框，如果有则点击确认
            try:
                confirm_button = page.locator('button.dialog-btn-ok')
                if await confirm_button.is_visible(timeout=1000):
                    await confirm_button.click()
                    await page.wait_for_timeout(1000)
            except:
                # 如果没有确认按钮，继续执行
                pass
            
            # 等待登录完成，然后访问千牛工作台来触发_m_h5_tk生成
            try:
                # 访问千牛工作台
                await page.goto('https://qianniu.taobao.com/index.htm')
                await page.wait_for_timeout(3000)

                # 访问卖家中心来确保获取完整Cookie
                await page.goto('https://myseller.taobao.com/home.htm')
                await page.wait_for_timeout(3000)

                # 关键：触发MTop API调用来生成_m_h5_tk
                # 方法1：访问一个会调用MTop API的页面
                await page.goto('https://myseller.taobao.com/home.htm/comment-manage/list')
                await page.wait_for_timeout(3000)

                # 方法2：直接调用MTop API端点来强制生成token
                # 这个请求会失败，但会触发_m_h5_tk的生成
                try:
                    await page.evaluate("""
                        fetch('https://h5api.m.taobao.com/h5/mtop.taobao.idle.item.resell/1.0/', {
                            method: 'GET',
                            credentials: 'include'
                        }).catch(() => {});
                    """)
                    await page.wait_for_timeout(2000)
                except:
                    pass

                # 方法3：访问手机版淘宝页面（更容易触发_m_h5_tk）
                try:
                    await page.goto('https://h5.m.taobao.com/mlapp/mytaobao.html')
                    await page.wait_for_timeout(3000)
                except:
                    pass

            except Exception as e:
                logger.warning(f"访问千牛页面时出错，继续获取Cookie: {e}")
           
            # 获取所有域名的Cookie
            all_cookies = []
            
            # 获取淘宝相关域名的Cookie
            domains = [
                'https://taobao.com',
                'https://www.taobao.com', 
                'https://myseller.taobao.com',
                'https://qianniu.taobao.com',
                'https://login.taobao.com'
            ]
            
            for domain in domains:
                try:
                    domain_cookies = await page.context.cookies(domain)
                    all_cookies.extend(domain_cookies)
                except:
                    continue
            
            # 定义必要的cookie字段
            essential_fields = ['_m_h5_tk', '_m_h5_tk_enc', 't', 'xlly_s', 'mtop_partitioned_detect', '_tb_token_', '_samesite_flag_', '3PcFlag', 'cookie2', 'sgcookie', 'unb', 'sn', 'uc1', 'csg', '_cc_', 'cancelledSubSites', 'skt', 'cna', 'tfstk']
            
            # 去重并过滤出必要的cookie字段
            cookie_dict = {}
            for cookie in all_cookies:
                if cookie['name'] in essential_fields:
                    cookie_dict[cookie['name']] = cookie['value']
            
            # 构建cookie字符串
            essential_cookies = [f"{name}={value}" for name, value in cookie_dict.items()]
            cookie_str = '; '.join(essential_cookies)
            
            # 检查是否获取到_m_h5_tk
            has_m_h5_tk = '_m_h5_tk' in cookie_dict
            
            # 记录获取到的cookie信息
            logger.info(f"获取到 {len(essential_cookies)} 个必要cookie字段")
            logger.info(f"Cookie字段: {list(cookie_dict.keys())}")
            logger.info(f"是否包含_m_h5_tk: {has_m_h5_tk}")
            
            if not has_m_h5_tk:
                logger.warning("未获取到_m_h5_tk，尝试多种方法触发生成")

                # 方法1：访问手机版淘宝首页
                try:
                    logger.info("尝试方法1：访问手机版淘宝")
                    await page.goto('https://main.m.taobao.com/index.html')
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    logger.warning(f"方法1失败: {e}")

                # 方法2：访问我的淘宝页面
                try:
                    logger.info("尝试方法2：访问我的淘宝")
                    await page.goto('https://h5.m.taobao.com/mlapp/mytaobao.html')
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    logger.warning(f"方法2失败: {e}")

                # 方法3：直接调用MTop API触发token生成
                try:
                    logger.info("尝试方法3：调用MTop API")
                    await page.evaluate("""
                        async function triggerMTopToken() {
                            const endpoints = [
                                'https://h5api.m.taobao.com/h5/mtop.user.getusersimple/1.0/',
                                'https://h5api.m.taobao.com/h5/mtop.taobao.idle.item.resell/1.0/',
                                'https://h5api.m.taobao.com/h5/mtop.relationrecommend.wirelessrecommend.recommend/2.0/'
                            ];

                            for (const endpoint of endpoints) {
                                try {
                                    await fetch(endpoint, {
                                        method: 'GET',
                                        credentials: 'include',
                                        headers: {
                                            'Accept': 'application/json'
                                        }
                                    });
                                    await new Promise(resolve => setTimeout(resolve, 1000));
                                } catch (e) {
                                    // 忽略错误，我们只是为了触发token生成
                                }
                            }
                        }
                        triggerMTopToken();
                    """)
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    logger.warning(f"方法3失败: {e}")

                # 重新获取Cookie
                all_cookies = []
                for domain in domains:
                    try:
                        domain_cookies = await page.context.cookies(domain)
                        all_cookies.extend(domain_cookies)
                    except:
                        continue

                # 重新构建Cookie
                cookie_dict = {}
                for cookie in all_cookies:
                    if cookie['name'] in essential_fields:
                        cookie_dict[cookie['name']] = cookie['value']

                essential_cookies = [f"{name}={value}" for name, value in cookie_dict.items()]
                cookie_str = '; '.join(essential_cookies)

                has_m_h5_tk = '_m_h5_tk' in cookie_dict
                logger.info(f"多次尝试后是否包含_m_h5_tk: {has_m_h5_tk}")

                if not has_m_h5_tk:
                    logger.error("所有方法都无法获取_m_h5_tk，可能需要手动登录或检查账号状态")
            
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
            logger.info("访问生意参谋页面...")
            await page.goto('https://sycm.taobao.com/qos/service/self_made_report#/self_made_report', wait_until='networkidle')
            await page.wait_for_timeout(5000)  # 增加等待时间，确保页面完全加载

            # 检查是否需要登录（检查页面标题或特定元素）
            try:
                # 等待页面加载完成的标志
                await page.wait_for_selector('body', timeout=5000)
                page_title = await page.title()
                logger.info(f"页面标题: {page_title}")

                # 检查是否在登录页面
                page_url = page.url
                if 'login' in page_url.lower():
                    logger.warning("检测到登录页面，可能需要重新登录")
                    # 尝试等待自动跳转
                    await page.wait_for_timeout(5000)
                    page_url = page.url
                    if 'login' in page_url.lower():
                        logger.error("仍在登录页面，Cookie可能无效")

            except Exception as e:
                logger.warning(f"检查页面状态时出错: {e}")

            # 多次尝试获取完整的Cookie
            max_attempts = 3
            best_cookies = None
            best_cookie_count = 0

            for attempt in range(max_attempts):
                logger.info(f"第 {attempt + 1} 次获取Cookie...")

                # 等待一段时间让Cookie完全生成
                await page.wait_for_timeout(2000)

                # 获取所有域名的Cookie
                all_cookies = []
                domains = [
                    'https://sycm.taobao.com',
                    'https://taobao.com',
                    'https://www.taobao.com'
                ]

                for domain in domains:
                    try:
                        domain_cookies = await page.context.cookies(domain)
                        all_cookies.extend(domain_cookies)
                    except:
                        continue

                # 定义生意参谋必要的cookie字段
                essential_sycm_fields = [
                    'DI_T_', 't', 'xlly_s', '3pc_partitioned', 'lid', 'cookie2',
                    '_tb_token_', '_samesite_flag_', '3PcFlag', 'sgcookie', 'unb',
                    'sn', 'uc1', 'csg', '_cc_', 'cancelledSubSites', 'skt', 'cna',
                    '_euacm_ac_l_uid_', '_euacm_ac_c_uid_', '_euacm_ac_rs_uid_',
                    '_portal_version_', 'cc_gray', 'XSRF-TOKEN', '_euacm_ac_rs_sid_',
                    'mtop_partitioned_detect', '_m_h5_tk', '_m_h5_tk_enc', 'JSESSIONID', 'tfstk'
                ]

                # 去重并过滤出必要的cookie字段
                cookie_dict = {}
                for cookie in all_cookies:
                    if cookie['name'] in essential_sycm_fields:
                        cookie_dict[cookie['name']] = cookie['value']

                # 如果这次获取的cookie更多，就保存
                if len(cookie_dict) > best_cookie_count:
                    best_cookie_count = len(cookie_dict)
                    best_cookies = cookie_dict
                    logger.info(f"本次获取到 {len(cookie_dict)} 个cookie字段")

                # 如果已经获取到足够的cookie，提前退出
                if len(cookie_dict) >= 20:  # 至少需要20个关键字段
                    logger.info("已获取足够的cookie字段，提前退出")
                    break

            # 使用最好的cookie结果
            if best_cookies:
                essential_cookies = [f"{name}={value}" for name, value in best_cookies.items()]
                cookie_str = '; '.join(essential_cookies)

                # 记录获取到的cookie信息
                logger.info(f"✓ 最终获取到 {len(essential_cookies)} 个必要生意参谋cookie字段")
                logger.info(f"生意参谋Cookie字段: {list(best_cookies.keys())}")
                logger.info(f"生意参谋Cookie长度: {len(cookie_str)} 字符")

                # 检查关键字段是否存在
                critical_fields = ['unb', 'sn', 'uc1', 'csg', '_tb_token_', 'cookie2', 'sgcookie']
                missing_fields = [field for field in critical_fields if field not in best_cookies]
                if missing_fields:
                    logger.warning(f"⚠️ 缺少关键cookie字段: {missing_fields}")
                else:
                    logger.info("✓ 所有关键cookie字段都已获取")

                await page.close()
                return cookie_str
            else:
                logger.error("未能获取到任何有效的cookie")
                await page.close()
                return None

        except Exception as e:
            logger.error(f"获取生意参谋Cookie失败: {e}")
            import traceback
            traceback.print_exc()
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

        1. 获取需要处理的店铺（status为NULL或空的店铺）
        2. 处理店铺Cookie获取和更新
        3. 更新店铺状态为"已完成"

        注意：任务生成由统一任务生成器负责（task_generator/generate_all_tasks.py）
        """
        try:
            logger.info("=== 天猫Cookie获取程序启动 ===")

            # 1. 获取需要处理的店铺（status为NULL或空）
            retry_shops = self.db.get_shops_need_retry()

            if not retry_shops:
                logger.info("✓ 没有需要处理的店铺")
                logger.info("\n提示：如需重新执行，请先运行统一任务生成器:")
                logger.info("  cd D:\\testyd\\task_generator")
                logger.info("  python generate_all_tasks.py --schedule daily")
                return

            logger.info(f"找到 {len(retry_shops)} 个需要处理的店铺")

            # 2. 处理每个店铺
            success_count = 0
            for shop_info in retry_shops:
                shop_name = shop_info.get('shop_name', '未知店铺')
                logger.info(f"\n=== 处理店铺: {shop_name} ===")

                if self.process_shop_with_retry(shop_info):
                    success_count += 1
                    # 更新店铺状态为"已完成"
                    self.db.update_shop_status(shop_name, '已完成')
                else:
                    logger.error(f"店铺 {shop_name} Cookie获取失败")

                # 每个店铺处理完后稍作休息
                time.sleep(2)

            logger.info(f"\n=== Cookie获取完成 ===")
            logger.info(f"成功: {success_count}/{len(retry_shops)} 个店铺")

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