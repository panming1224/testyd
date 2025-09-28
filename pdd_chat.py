# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import time
import json
import requests
import uuid
import os
import pandas as pd
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 配置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 添加merge_excel_files模块路径
sys.path.append(r'D:\testyd')
from merge_excel_files import ExcelMerger

TARGET_API = "/latitude/search/message/getMessages"   # 你要监听的接口

def on_response(res):
    if TARGET_API in res.url:
        data = res.json()
        print("【接口返回】", data)

def main():
    USER_DATA_DIR = r"C:\\Users\\1\AppData\\Local\\Chromium\\User Data"
    TARGET_URL = "https://mms.pinduoduo.com/mms-chat/search?msfrom=mms_sidenav"
    #最大化登录，使用用户目录
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=[
                "--start-maximized",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--profile-directory=Default",
            ],
            no_viewport=True,
            ignore_https_errors=True
        )
                
        page = context.new_page()
        page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
        page.on("response", on_response)
        # 点击日期框
        page.locator('input[data-testid="beast-core-rangePicker-htmlInput"]').click()  
        time.sleep(0.3)      
        #点击开始日期
        page.locator('td[role="date-cell"] div[title="17"]:not(.RPR_disabled_1198e34)').click()
        time.sleep(0.3)   
        #点击结束日期
        page.locator('td[role="date-cell"] div[title="18"]:not(.RPR_disabled_1198e34)').click()
        time.sleep(0.3)   
        #点击确认
        page.locator('button:has-text("确认")').click()
        time.sleep(0.3)   
        #点击查询
        page.locator('button:has-text("查询")').click()
        time.sleep(0.3)  
        MAX_PAGES=2
        current_page=1
        while current_page<=MAX_PAGES:
            print(f"***************第{current_page}页***************")
            page.wait_for_load_state("domcontentloaded")
            # 等「下一页按钮」出现（局部元素）
            # page.wait_for_selector('li[data-testid="beast-core-pagination-next"]', state="visible", timeout=10000)
            # ② 读总页数（max 属性）
            max_page_input = page.locator('input[data-testid="beast-core-inputNumber-htmlInput"]')
            total_pages = int(max_page_input.get_attribute("max"))
            print(f"  总页数：{total_pages}")   

            # ③ 拿「非激活」用户（跳过第一个）
            items = page.locator('.user-item:not(.is-active)').all()
            print(f"  待点击 {len(items)} 个")

            # ④ 循环点本页
            for idx, item in enumerate(items, 1):
                item.click()
                time.sleep(0.2)          # 防风控
                resp = page.wait_for_event(
                    "response",
                    predicate=lambda r: "/getMessages" in r.url,
                    timeout=10000
                )
                data = resp.json()
                if data.get("error_code") == 43001:
                    print(f"  用户 {idx} 被踢，提前结束")
                    break
                time.sleep(0.2)

            # ⑤ 判断是否还有下一页（或已达上限）
            if current_page >= total_pages or current_page >= MAX_PAGES:
                print("  已达最后一页或 20 页上限，结束")
                break

            # ⑥ 点「下一页」
            next_btn = page.locator('li[data-testid="beast-core-pagination-next"]:not(.PGT_disabled_1198e34)')
            if next_btn.count() == 0:
                print("  无下一页按钮，结束")
                break
            next_btn.click()
            current_page += 1
            time.sleep(1)          # 等翻页动画

        # 监听函数已打印结果，继续下一个
        page.remove_listener("response", on_response)
        # input()

        # # ===== 新增：逐行调试入口（不删你任何原有代码） =====
        # print(">>> 浏览器已保持，登录态在目录里 <<<")
        # print("逐行写命令，q 退出；示例：")
        # print("  page.locator('查询').click()")
        # print("  page.screenshot(path='a.png')")
        # while True:
        #     cmd = input(">>> ").strip()
        #     if cmd == "q":
        #         break
        #     try:
        #         exec(cmd)          # 立即执行你敲的代码
        #     except Exception as e:
        #         print("❌", e)

        # cookies=context.cookies(TARGET_URL)
        # cookie_str='; '.join(f"{c['name']}={c['value']}" for c in cookies)
        # print(cookie_str)
        # time.sleep(5)
        # page.close()
        # time.sleep(3)
        # context.close()

if __name__ == "__main__":
    main()