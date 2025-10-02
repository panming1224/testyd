#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多 anti-content 参数分析脚本
基于搜索结果和技术文档的分析
"""

import base64
import hashlib
import json
import time
import random
import string
from urllib.parse import urlparse
import re

class AntiContentAnalyzer:
    """拼多多 anti-content 参数分析器"""
    
    def __init__(self):
        self.sample_anti_content = "0asAfqnygjSgygd9l4e8dO8QdVo7KTwTvty8uJNxxKHBN6_-5entRFsa5DefOoHeOuHjtT64EGCfpd7wEzPxenZg0xbZhwTfzjuG2rgvZltO0kjlTKACIbdIbGXa0mNJMHYDaVBZ4YyI62IcQB0TEy5p88rKGYnSBza4MbBkR2QzbodaAoH0I69z89poXicUYDbVnyZ6W9FR3dHWBWTzJk0vXsoIgv1b4i8Zup2XoAXzl9ZOyZkb6lcTOICgomDuN9JJ2bcrY0SQDAf1R9MYHtjWwcbocNqOH4QbfyzCYD2fI52omGOvIWcnAL9rq4hoXHCZjo2v79nIPBIJ41cCi8fDNQgwrc6cJHXSCRlqhrpL7YAXghxotke0UQffZhIH2yf7AOBRVfKtmRDHKwGKXiS3-xljbPT5KOtdH3tvi4fIWITTlFCxpeN82NTwGhpLw_uCFnycWKgMqWCNo-iQFgXR4lFCAFlRXE21kCdG3B46ODMsvzvAPi0SQEEJtKWnAMEs2dsVi2QPA2jiil4jijG2aj0FzQqYtZ_3YycMNQFKWDwbkMaRendvpPqQ_mMXMSo0k7VkpPoc1s2uisfkvDtt7iG_oeKTqc1TMfgsvPsjEZXeQzbfLLr3yTY3f-X7VZWB9oQ2nxt3lehejDSoJiljvntFMibtt_mjplxckVoWg5PpE_ZPvlm6yasCbRoom0J6VJIcDZlQc9o2Qy2LroIENZTqEHh"
        
    def analyze_structure(self):
        """分析 anti-content 参数的结构特征"""
        print("=== Anti-Content 参数结构分析 ===")
        print(f"样本长度: {len(self.sample_anti_content)}")
        print(f"开头字符: {self.sample_anti_content[:10]}")
        print(f"结尾字符: {self.sample_anti_content[-10:]}")
        
        # 字符集分析
        chars = set(self.sample_anti_content)
        print(f"使用的字符集: {sorted(chars)}")
        print(f"字符种类数: {len(chars)}")
        
        # 检查是否为Base64编码
        try:
            decoded = base64.b64decode(self.sample_anti_content + '==')  # 添加padding
            print(f"可能的Base64解码长度: {len(decoded)}")
            print(f"Base64解码前20字节: {decoded[:20]}")
        except Exception as e:
            print(f"Base64解码失败: {e}")
            
        # 分析模式
        self._analyze_patterns()
        
    def _analyze_patterns(self):
        """分析字符串中的模式"""
        print("\n=== 模式分析 ===")
        
        # 查找重复子串
        for length in [2, 3, 4, 5]:
            substrings = {}
            for i in range(len(self.sample_anti_content) - length + 1):
                substr = self.sample_anti_content[i:i+length]
                substrings[substr] = substrings.get(substr, 0) + 1
            
            repeated = {k: v for k, v in substrings.items() if v > 1}
            if repeated:
                print(f"长度{length}的重复子串: {repeated}")
    
    def analyze_generation_factors(self):
        """分析可能影响生成的因素"""
        print("\n=== 生成因素分析 ===")
        
        # 根据搜索结果，anti-content可能包含以下信息：
        factors = {
            "时间戳": int(time.time()),
            "随机数": random.randint(100000, 999999),
            "URL信息": "https://mms.pinduoduo.com/latitude/search/message/getMessagesUsers",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "屏幕信息": {"width": 1920, "height": 1080},
            "Referer": "https://mms.pinduoduo.com/mms-chat/search?msfrom=mms_sidenav",
            "页面加载时间": int(time.time() * 1000),
        }
        
        print("可能的生成因素:")
        for key, value in factors.items():
            print(f"  {key}: {value}")
            
        return factors
    
    def simulate_generation_attempt(self):
        """尝试模拟生成过程"""
        print("\n=== 模拟生成尝试 ===")
        
        factors = self.analyze_generation_factors()
        
        # 尝试不同的组合方式
        combinations = [
            # 方式1: 简单拼接后编码
            f"{factors['时间戳']}{factors['随机数']}{factors['URL信息']}",
            
            # 方式2: JSON格式
            json.dumps(factors, separators=(',', ':')),
            
            # 方式3: 特定格式拼接
            f"{factors['时间戳']}|{factors['User-Agent']}|{factors['屏幕信息']['width']}x{factors['屏幕信息']['height']}",
        ]
        
        for i, combo in enumerate(combinations, 1):
            print(f"\n尝试组合 {i}:")
            print(f"原始数据: {combo[:100]}...")
            
            # 尝试不同编码方式
            encodings = [
                ("Base64", lambda x: base64.b64encode(x.encode()).decode()),
                ("MD5", lambda x: hashlib.md5(x.encode()).hexdigest()),
                ("SHA256", lambda x: hashlib.sha256(x.encode()).hexdigest()),
            ]
            
            for enc_name, enc_func in encodings:
                try:
                    encoded = enc_func(combo)
                    print(f"  {enc_name}: {encoded[:50]}...")
                    
                    # 检查是否与样本相似
                    if len(encoded) == len(self.sample_anti_content):
                        print(f"    ✓ 长度匹配!")
                    
                    if encoded[:10] == self.sample_anti_content[:10]:
                        print(f"    ✓ 开头匹配!")
                        
                except Exception as e:
                    print(f"  {enc_name} 编码失败: {e}")
    
    def research_known_methods(self):
        """基于搜索结果的已知方法研究"""
        print("\n=== 已知方法研究 ===")
        
        print("根据技术文档和社区分析，anti-content参数特点:")
        print("1. 每次请求都需要重新生成，不可复用")
        print("2. 与浏览器环境强相关（UA、屏幕尺寸、时间戳等）")
        print("3. 可能包含页面URL、Referer等信息")
        print("4. 使用复杂的JavaScript混淆和加密算法")
        print("5. 需要模拟完整的浏览器环境才能正确生成")
        
        print("\n技术要点:")
        print("- 需要分析拼多多的前端JavaScript代码")
        print("- 通常涉及webpack打包的混淆代码")
        print("- 可能需要补全浏览器环境（window、document、navigator等）")
        print("- 算法可能包含时间相关的随机因子")
        
    def create_reproduction_framework(self):
        """创建复现框架的基础结构"""
        print("\n=== 复现框架设计 ===")
        
        framework = {
            "环境模拟": {
                "浏览器对象": ["window", "document", "navigator", "location"],
                "用户代理": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "屏幕信息": {"width": 1920, "height": 1080},
                "时区": "Asia/Shanghai"
            },
            "数据收集": {
                "当前时间戳": int(time.time()),
                "页面URL": "https://mms.pinduoduo.com/latitude/search/message/getMessagesUsers",
                "引用页面": "https://mms.pinduoduo.com/mms-chat/search",
                "会话信息": "需要从cookie中提取"
            },
            "算法步骤": [
                "1. 收集环境信息",
                "2. 生成时间相关随机数",
                "3. 构造原始数据字符串",
                "4. 应用加密/编码算法",
                "5. 返回最终的anti-content值"
            ]
        }
        
        print("复现框架结构:")
        print(json.dumps(framework, indent=2, ensure_ascii=False))
        
        return framework

def main():
    """主函数"""
    analyzer = AntiContentAnalyzer()
    
    print("拼多多 Anti-Content 参数分析")
    print("=" * 50)
    
    # 执行各种分析
    analyzer.analyze_structure()
    analyzer.analyze_generation_factors()
    analyzer.simulate_generation_attempt()
    analyzer.research_known_methods()
    analyzer.create_reproduction_framework()
    
    print("\n" + "=" * 50)
    print("分析完成！")
    print("\n建议下一步:")
    print("1. 获取拼多多前端JavaScript源码进行详细分析")
    print("2. 使用浏览器开发者工具跟踪anti-content生成过程")
    print("3. 搭建Node.js环境来模拟浏览器环境")
    print("4. 参考开源项目中的相关实现")

if __name__ == "__main__":
    main()