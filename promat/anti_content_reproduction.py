#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多 anti-content 参数复现实现
基于技术分析和开源项目研究的复现尝试
"""

import base64
import hashlib
import json
import time
import random
import string
import hmac
from urllib.parse import urlparse, parse_qs
import struct
import zlib

class PddAntiContentGenerator:
    """拼多多 anti-content 参数生成器"""
    
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        self.screen_width = 1920
        self.screen_height = 1080
        self.timezone_offset = -480  # 中国时区 UTC+8
        
    def get_browser_fingerprint(self):
        """获取浏览器指纹信息"""
        return {
            "userAgent": self.user_agent,
            "language": "zh-CN",
            "platform": "Win32",
            "cookieEnabled": True,
            "screenWidth": self.screen_width,
            "screenHeight": self.screen_height,
            "colorDepth": 24,
            "timezoneOffset": self.timezone_offset,
            "plugins": ["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client"],
            "webgl": "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "canvas": self._generate_canvas_fingerprint()
        }
    
    def _generate_canvas_fingerprint(self):
        """生成Canvas指纹"""
        # 模拟Canvas渲染结果的哈希值
        canvas_text = f"Canvas fingerprint {time.time()}"
        return hashlib.md5(canvas_text.encode()).hexdigest()[:16]
    
    def get_timing_info(self):
        """获取页面时间信息"""
        current_time = int(time.time() * 1000)
        return {
            "navigationStart": current_time - random.randint(1000, 5000),
            "loadEventEnd": current_time - random.randint(100, 1000),
            "domContentLoadedEventEnd": current_time - random.randint(500, 2000),
            "currentTime": current_time
        }
    
    def generate_random_values(self):
        """生成随机值"""
        return {
            "random1": random.random(),
            "random2": random.randint(100000, 999999),
            "uuid": ''.join(random.choices(string.ascii_lowercase + string.digits, k=32)),
            "sessionId": ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        }
    
    def method1_simple_encoding(self, url, referer=""):
        """方法1: 简单编码方式"""
        print("尝试方法1: 简单时间戳+随机数编码")
        
        timestamp = int(time.time())
        random_num = random.randint(100000, 999999)
        
        # 构造原始字符串
        raw_data = f"{timestamp}_{random_num}_{url}_{self.user_agent}_{referer}"
        
        # 尝试不同编码
        encodings = [
            base64.b64encode(raw_data.encode()).decode(),
            hashlib.sha256(raw_data.encode()).hexdigest(),
            self._custom_encode(raw_data)
        ]
        
        for i, encoded in enumerate(encodings, 1):
            print(f"  编码方式{i}: {encoded[:50]}...")
            
        return encodings[0]  # 返回Base64编码结果
    
    def method2_complex_fingerprint(self, url, referer=""):
        """方法2: 复杂指纹信息编码"""
        print("尝试方法2: 复杂浏览器指纹编码")
        
        fingerprint = self.get_browser_fingerprint()
        timing = self.get_timing_info()
        random_vals = self.generate_random_values()
        
        # 构造复杂数据结构
        data = {
            "url": url,
            "referer": referer,
            "timestamp": int(time.time() * 1000),
            "fingerprint": fingerprint,
            "timing": timing,
            "random": random_vals,
            "version": "1.0.0"
        }
        
        # 序列化并编码
        json_str = json.dumps(data, separators=(',', ':'), sort_keys=True)
        
        # 多层编码
        step1 = base64.b64encode(json_str.encode()).decode()
        step2 = self._apply_custom_transform(step1)
        step3 = self._add_checksum(step2)
        
        print(f"  复杂编码结果: {step3[:50]}...")
        return step3
    
    def method3_webpack_simulation(self, url, referer=""):
        """方法3: 模拟webpack打包的加密方式"""
        print("尝试方法3: 模拟webpack加密算法")
        
        # 模拟webpack模块化的数据收集
        modules = {
            "timing": self.get_timing_info(),
            "navigator": {
                "userAgent": self.user_agent,
                "language": "zh-CN",
                "platform": "Win32",
                "cookieEnabled": True
            },
            "screen": {
                "width": self.screen_width,
                "height": self.screen_height,
                "colorDepth": 24
            },
            "location": {
                "href": url,
                "origin": urlparse(url).netloc,
                "pathname": urlparse(url).path
            },
            "document": {
                "referrer": referer,
                "title": "拼多多商家后台",
                "readyState": "complete"
            }
        }
        
        # 模拟复杂的加密过程
        serialized = self._serialize_modules(modules)
        encrypted = self._simulate_encryption(serialized)
        
        print(f"  Webpack模拟结果: {encrypted[:50]}...")
        return encrypted
    
    def _custom_encode(self, data):
        """自定义编码方法"""
        # 简单的字符替换和重排
        encoded = base64.b64encode(data.encode()).decode()
        # 字符替换
        encoded = encoded.replace('+', '-').replace('/', '_').replace('=', '')
        return encoded
    
    def _apply_custom_transform(self, data):
        """应用自定义变换"""
        # 模拟复杂的字符串变换
        result = ""
        for i, char in enumerate(data):
            if i % 3 == 0:
                result += char.upper()
            elif i % 3 == 1:
                result += char.lower()
            else:
                result += char
        return result
    
    def _add_checksum(self, data):
        """添加校验和"""
        checksum = hashlib.md5(data.encode()).hexdigest()[:8]
        return f"{checksum}{data}"
    
    def _serialize_modules(self, modules):
        """序列化模块数据"""
        # 按特定顺序序列化
        ordered_data = []
        for key in sorted(modules.keys()):
            if isinstance(modules[key], dict):
                for subkey in sorted(modules[key].keys()):
                    ordered_data.append(f"{key}.{subkey}={modules[key][subkey]}")
            else:
                ordered_data.append(f"{key}={modules[key]}")
        
        return "|".join(ordered_data)
    
    def _simulate_encryption(self, data):
        """模拟加密过程"""
        # 多步加密模拟
        step1 = hashlib.sha256(data.encode()).digest()
        step2 = zlib.compress(step1)
        step3 = base64.b64encode(step2).decode()
        
        # 添加随机前缀（模拟版本标识）
        prefix = random.choice(['0a', '0b', '0c', '1a', '1b'])
        return prefix + step3.replace('+', '-').replace('/', '_').replace('=', '')
    
    def generate_anti_content(self, url, referer="", method="all"):
        """生成 anti-content 参数"""
        print(f"为URL生成anti-content: {url}")
        print(f"Referer: {referer}")
        print("-" * 60)
        
        results = {}
        
        if method in ["all", "1"]:
            results["method1"] = self.method1_simple_encoding(url, referer)
            
        if method in ["all", "2"]:
            results["method2"] = self.method2_complex_fingerprint(url, referer)
            
        if method in ["all", "3"]:
            results["method3"] = self.method3_webpack_simulation(url, referer)
        
        return results
    
    def validate_against_sample(self, generated, sample):
        """与样本进行对比验证"""
        print("\n=== 验证结果 ===")
        print(f"样本长度: {len(sample)}")
        print(f"样本开头: {sample[:20]}")
        print(f"样本结尾: {sample[-20:]}")
        
        for method, result in generated.items():
            print(f"\n{method}:")
            print(f"  生成长度: {len(result)}")
            print(f"  生成开头: {result[:20]}")
            print(f"  生成结尾: {result[-20:]}")
            
            # 长度匹配检查
            if len(result) == len(sample):
                print("  ✓ 长度匹配")
            else:
                print(f"  ✗ 长度不匹配 (差异: {len(result) - len(sample)})")
            
            # 开头匹配检查
            if result[:10] == sample[:10]:
                print("  ✓ 开头匹配")
            elif result[:5] == sample[:5]:
                print("  ~ 部分开头匹配")
            else:
                print("  ✗ 开头不匹配")
            
            # 字符集检查
            result_chars = set(result)
            sample_chars = set(sample)
            common_chars = result_chars & sample_chars
            print(f"  字符集重叠度: {len(common_chars)}/{len(sample_chars)} ({len(common_chars)/len(sample_chars)*100:.1f}%)")

def main():
    """主函数"""
    # 从原始文件中提取的样本
    sample_anti_content = "0asAfqnygjSgygd9l4e8dO8QdVo7KTwTvty8uJNxxKHBN6_-5entRFsa5DefOoHeOuHjtT64EGCfpd7wEzPxenZg0xbZhwTfzjuG2rgvZltO0kjlTKACIbdIbGXa0mNJMHYDaVBZ4YyI62IcQB0TEy5p88rKGYnSBza4MbBkR2QzbodaAoH0I69z89poXicUYDbVnyZ6W9FR3dHWBWTzJk0vXsoIgv1b4i8Zup2XoAXzl9ZOyZkb6lcTOICgomDuN9JJ2bcrY0SQDAf1R9MYHtjWwcbocNqOH4QbfyzCYD2fI52omGOvIWcnAL9rq4hoXHCZjo2v79nIPBIJ41cCi8fDNQgwrc6cJHXSCRlqhrpL7YAXghxotke0UQffZhIH2yf7AOBRVfKtmRDHKwGKXiS3-xljbPT5KOtdH3tvi4fIWITTlFCxpeN82NTwGhpLw_uCFnycWKgMqWCNo-iQFgXR4lFCAFlRXE21kCdG3B46ODMsvzvAPi0SQEEJtKWnAMEs2dsVi2QPA2jiil4jijG2aj0FzQqYtZ_3YycMNQFKWDwbkMaRendvpPqQ_mMXMSo0k7VkpPoc1s2uisfkvDtt7iG_oeKTqc1TMfgsvPsjEZXeQzbfLLr3yTY3f-X7VZWB9oQ2nxt3lehejDSoJiljvntFMibtt_mjplxckVoWg5PpE_ZPvlm6yasCbRoom0J6VJIcDZlQc9o2Qy2LroIENZTqEHh"
    
    # 目标URL和Referer
    target_url = "https://mms.pinduoduo.com/latitude/search/message/getMessagesUsers"
    referer = "https://mms.pinduoduo.com/mms-chat/search?msfrom=mms_sidenav"
    
    # 创建生成器
    generator = PddAntiContentGenerator()
    
    print("拼多多 Anti-Content 参数复现尝试")
    print("=" * 60)
    
    # 生成anti-content参数
    results = generator.generate_anti_content(target_url, referer)
    
    # 验证结果
    generator.validate_against_sample(results, sample_anti_content)
    
    print("\n" + "=" * 60)
    print("复现尝试完成！")
    print("\n说明:")
    print("1. 以上是基于技术分析的复现尝试")
    print("2. 真实的anti-content算法可能更加复杂")
    print("3. 需要获取拼多多的实际JavaScript代码进行精确分析")
    print("4. 建议使用浏览器自动化工具获取真实参数")
    
    # 返回最佳匹配结果
    return results

if __name__ == "__main__":
    main()