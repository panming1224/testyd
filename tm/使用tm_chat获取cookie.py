# -*- coding: utf-8 -*-
import sys
import json
from datetime import datetime
from tm_chat import TmallCommentManager

def get_cookies_with_tm_chat():
    """使用tm_chat.py的浏览器方法获取cookie"""
    print("=== 使用tm_chat浏览器方法获取Cookie ===")
    
    try:
        # 创建TmallCommentManager实例
        manager = TmallCommentManager()
        
        # 修改目标URL为客服消息页面
        manager.TARGET_URL = "https://myseller.taobao.com/home.htm/app-customer-service/toolpage/Message"
        
        print(f"目标页面: {manager.TARGET_URL}")
        print("正在启动浏览器...")
        
        # 使用tm_chat的登录方法获取cookies
        cookie_str, page, context = manager.login_and_get_cookies()
        
        if cookie_str:
            print("✅ 成功获取到cookies!")
            
            # 保存cookies到文件
            with open('cookies.txt', 'w', encoding='utf-8') as f:
                f.write(cookie_str)
            
            print(f"Cookies已保存到: cookies.txt")
            print(f"Cookies长度: {len(cookie_str)} 字符")
            
            # 分析关键cookie字段
            key_cookies = {}
            for cookie in cookie_str.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    name, value = cookie.split('=', 1)
                    if name in ['_nk_', 'lgc', 'cookie2', '_tb_token_', '_m_h5_tk']:
                        key_cookies[name] = value
            
            print("\n关键Cookie字段:")
            for name, value in key_cookies.items():
                print(f"  {name}: {value[:20]}..." if len(value) > 20 else f"  {name}: {value}")
            
            # 生成报告
            report = {
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "状态": "成功",
                "目标页面": manager.TARGET_URL,
                "cookies长度": len(cookie_str),
                "关键字段": key_cookies,
                "完整cookies": cookie_str
            }
            
            # 保存报告
            report_file = f"cookie_获取报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n详细报告已保存到: {report_file}")
            
        else:
            print("❌ 获取cookies失败")
            return False
        
        # 清理资源
        try:
            if page:
                page.close()
            if context:
                context.close()
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ 执行过程中出错: {e}")
        return False

if __name__ == "__main__":
    success = get_cookies_with_tm_chat()
    if success:
        print("\n🎉 Cookie获取完成！")
    else:
        print("\n💥 Cookie获取失败！")