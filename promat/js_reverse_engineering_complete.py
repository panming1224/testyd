#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多 JavaScript 逆向工程分析脚本
用于分析拼多多前端JavaScript代码，寻找anti-content生成逻辑
"""

import re
import json
import requests
import hashlib
import base64
import time
from urllib.parse import urlparse, parse_qs
import subprocess
import os

class PddJSAnalyzer:
    """拼多多JavaScript代码分析器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        })
        
    def fetch_page_source(self, url):
        """获取页面源码"""
        print(f"获取页面源码: {url}")
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"获取页面源码失败: {e}")
            return None
    
    def extract_js_urls(self, html_content):
        """从HTML中提取JavaScript文件URL"""
        print("提取JavaScript文件URL...")
        
        js_urls = []
        
        # 匹配script标签中的src属性
        script_pattern = r'<script[^>]*src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(script_pattern, html_content, re.IGNORECASE)
        
        for match in matches:
            if match.startswith('//'):
                js_urls.append('https:' + match)
            elif match.startswith('/'):
                js_urls.append('https://mms.pinduoduo.com' + match)
            elif match.startswith('http'):
                js_urls.append(match)
        
        print(f"发现 {len(js_urls)} 个JavaScript文件")
        return js_urls
    
    def download_js_files(self, js_urls, output_dir='d:\\testyd\\promat\\js_files'):
        """下载JavaScript文件"""
        print(f"下载JavaScript文件到: {output_dir}")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        downloaded_files = []
        
        for i, url in enumerate(js_urls):
            try:
                print(f"下载 {i+1}/{len(js_urls)}: {url}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # 生成文件名
                filename = f"script_{i+1}_{hashlib.md5(url.encode()).hexdigest()[:8]}.js"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                downloaded_files.append({
                    'url': url,
                    'filepath': filepath,
                    'size': len(response.text)
                })
                
            except Exception as e:
                print(f"下载失败 {url}: {e}")
        
        print(f"成功下载 {len(downloaded_files)} 个文件")
        return downloaded_files
    
    def analyze_js_content(self, js_files):
        """分析JavaScript文件内容"""
        print("分析JavaScript文件内容...")
        
        analysis_results = []
        
        # 关键词列表 - 扩展更多反爬虫相关关键词
        keywords = [
            'anti-content', 'anticontent', 'anti_content',
            'encrypt', 'encode', 'hash', 'signature',
            'timestamp', 'random', 'nonce',
            'header', 'request', 'ajax', 'fetch',
            'navigator', 'screen', 'location',
            'fingerprint', 'canvas', 'webgl', 'device'
        ]
        
        for file_info in js_files:
            print(f"分析文件: {file_info['filepath']}")
            
            try:
                with open(file_info['filepath'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_analysis = {
                    'url': file_info['url'],
                    'filepath': file_info['filepath'],
                    'size': file_info['size'],
                    'keywords_found': {},
                    'suspicious_functions': [],
                    'obfuscated': self.detect_obfuscation(content),
                    'webpack_bundle': 'webpack' in content.lower()
                }
                
                # 搜索关键词
                for keyword in keywords:
                    matches = re.findall(rf'\b{re.escape(keyword)}\b', content, re.IGNORECASE)
                    if matches:
                        file_analysis['keywords_found'][keyword] = len(matches)
                
                # 查找可疑函数
                file_analysis['suspicious_functions'] = self.find_suspicious_functions(content)
                
                # 如果发现相关内容，保存详细分析
                if file_analysis['keywords_found'] or file_analysis['suspicious_functions']:
                    detailed_filepath = file_info['filepath'].replace('.js', '_analysis.txt')
                    self.save_detailed_analysis(content, file_analysis, detailed_filepath)
                
                analysis_results.append(file_analysis)
                
            except Exception as e:
                print(f"分析文件失败 {file_info['filepath']}: {e}")
        
        return analysis_results
    
    def detect_obfuscation(self, js_content):
        """检测JavaScript代码是否被混淆"""
        obfuscation_indicators = [
            r'_0x[a-f0-9]+',  # 十六进制变量名
            r'\\x[a-f0-9]{2}',  # 十六进制字符串
            r'eval\s*\(',  # eval函数
            r'String\.fromCharCode',  # 字符编码
            r'[a-zA-Z_$][a-zA-Z0-9_$]{0,2}\s*\[\s*["\'][^"\']{1,3}["\']\s*\]',  # 短属性访问
        ]
        
        obfuscation_score = 0
        for pattern in obfuscation_indicators:
            matches = re.findall(pattern, js_content)
            obfuscation_score += len(matches)
        
        return {
            'score': obfuscation_score,
            'likely_obfuscated': obfuscation_score > 10
        }
    
    def find_suspicious_functions(self, js_content):
        """查找可疑的函数定义"""
        suspicious_functions = []
        
        # 查找函数定义
        function_patterns = [
            r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*{[^}]*(?:anti|encrypt|encode|hash|signature)[^}]*}',
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*[:=]\s*function\s*\([^)]*\)\s*{[^}]*(?:anti|encrypt|encode|hash|signature)[^}]*}',
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*[:=]\s*\([^)]*\)\s*=>\s*{[^}]*(?:anti|encrypt|encode|hash|signature)[^}]*}'
        ]
        
        for pattern in function_patterns:
            matches = re.finditer(pattern, js_content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                function_name = match.group(1) if match.group(1) else 'anonymous'
                suspicious_functions.append({
                    'name': function_name,
                    'start_pos': match.start(),
                    'content': match.group(0)[:200] + '...' if len(match.group(0)) > 200 else match.group(0)
                })
        
        return suspicious_functions
    
    def save_detailed_analysis(self, js_content, analysis, filepath):
        """保存详细分析结果"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("JavaScript文件详细分析\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"文件URL: {analysis['url']}\n")
            f.write(f"文件大小: {analysis['size']} 字符\n")
            f.write(f"是否混淆: {analysis['obfuscated']['likely_obfuscated']}\n")
            f.write(f"混淆评分: {analysis['obfuscated']['score']}\n")
            f.write(f"Webpack打包: {analysis['webpack_bundle']}\n\n")
            
            if analysis['keywords_found']:
                f.write("发现的关键词:\n")
                for keyword, count in analysis['keywords_found'].items():
                    f.write(f"  {keyword}: {count} 次\n")
                f.write("\n")
            
            if analysis['suspicious_functions']:
                f.write("可疑函数:\n")
                for func in analysis['suspicious_functions']:
                    f.write(f"  函数名: {func['name']}\n")
                    f.write(f"  位置: {func['start_pos']}\n")
                    f.write(f"  内容预览: {func['content']}\n\n")
            
            # 保存相关代码片段
            f.write("相关代码片段:\n")
            f.write("-" * 30 + "\n")
            
            keywords_pattern = r'.{0,100}(?:anti-content|anticontent|anti_content|encrypt|signature).{0,100}'
            matches = re.finditer(keywords_pattern, js_content, re.IGNORECASE)
            
            for i, match in enumerate(matches):
                if i >= 10:  # 限制输出数量
                    break
                f.write(f"片段 {i+1}:\n{match.group(0)}\n\n")

class PddAntiContentReverser:
    """拼多多anti-content逆向分析器"""
    
    def __init__(self):
        self.analyzer = PddJSAnalyzer()
    
    def reverse_engineer_anti_content(self):
        """逆向工程anti-content生成逻辑"""
        print("开始逆向工程anti-content生成逻辑")
        print("=" * 60)
        
        # 1. 获取页面源码
        target_url = "https://mms.pinduoduo.com/mms-chat/search?msfrom=mms_sidenav"
        html_content = self.analyzer.fetch_page_source(target_url)
        
        if not html_content:
            print("无法获取页面源码，尝试备用方案...")
            return self.analyze_known_patterns()
        
        # 2. 提取JavaScript文件URL
        js_urls = self.analyzer.extract_js_urls(html_content)
        
        if not js_urls:
            print("未发现JavaScript文件，分析内联脚本...")
            return self.analyze_inline_scripts(html_content)
        
        # 3. 下载JavaScript文件
        js_files = self.analyzer.download_js_files(js_urls)
        
        # 4. 分析JavaScript内容
        analysis_results = self.analyzer.analyze_js_content(js_files)
        
        # 5. 生成分析报告
        self.generate_analysis_report(analysis_results)
        
        # 6. 尝试提取anti-content生成逻辑
        return self.extract_generation_logic(analysis_results)
    
    def analyze_inline_scripts(self, html_content):
        """分析内联JavaScript脚本"""
        print("分析内联JavaScript脚本...")
        
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        inline_analysis = []
        for i, script in enumerate(scripts):
            if 'anti' in script.lower() or 'encrypt' in script.lower():
                analysis = {
                    'script_index': i,
                    'content': script,
                    'size': len(script),
                    'contains_anti_logic': True
                }
                inline_analysis.append(analysis)
                
                # 保存内联脚本
                with open(f'd:\\testyd\\promat\\inline_script_{i}.js', 'w', encoding='utf-8') as f:
                    f.write(script)
        
        return inline_analysis
    
    def analyze_known_patterns(self):
        """分析已知的anti-content模式"""
        print("分析已知的anti-content模式...")
        
        # 从原始请求中提取的anti-content
        sample_anti_content = "0a2c0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b