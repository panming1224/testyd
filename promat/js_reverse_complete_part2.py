#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多 JavaScript 逆向工程分析脚本 - 第二部分
继续完成JavaScript分析和anti-content生成逻辑提取
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

class PddAntiContentReverser:
    """拼多多anti-content逆向分析器"""
    
    def __init__(self):
        from js_reverse_engineering_complete import PddJSAnalyzer
        self.analyzer = PddJSAnalyzer()
    
    def generate_analysis_report(self, analysis_results):
        """生成分析报告"""
        print("生成分析报告...")
        
        report_path = 'd:\\testyd\\promat\\anti_content_analysis_report.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("拼多多 anti-content 逆向工程分析报告\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"分析时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"分析文件数量: {len(analysis_results)}\n\n")
            
            # 统计信息
            total_keywords = 0
            total_functions = 0
            obfuscated_files = 0
            webpack_files = 0
            
            for result in analysis_results:
                total_keywords += sum(result['keywords_found'].values())
                total_functions += len(result['suspicious_functions'])
                if result['obfuscated']['likely_obfuscated']:
                    obfuscated_files += 1
                if result['webpack_bundle']:
                    webpack_files += 1
            
            f.write("统计信息:\n")
            f.write(f"  发现关键词总数: {total_keywords}\n")
            f.write(f"  可疑函数总数: {total_functions}\n")
            f.write(f"  混淆文件数量: {obfuscated_files}\n")
            f.write(f"  Webpack打包文件: {webpack_files}\n\n")
            
            # 详细分析结果
            f.write("详细分析结果:\n")
            f.write("-" * 40 + "\n\n")
            
            for i, result in enumerate(analysis_results):
                f.write(f"文件 {i+1}:\n")
                f.write(f"  URL: {result['url']}\n")
                f.write(f"  大小: {result['size']} 字符\n")
                f.write(f"  混淆评分: {result['obfuscated']['score']}\n")
                f.write(f"  是否混淆: {result['obfuscated']['likely_obfuscated']}\n")
                f.write(f"  Webpack打包: {result['webpack_bundle']}\n")
                
                if result['keywords_found']:
                    f.write("  发现的关键词:\n")
                    for keyword, count in result['keywords_found'].items():
                        f.write(f"    {keyword}: {count} 次\n")
                
                if result['suspicious_functions']:
                    f.write("  可疑函数:\n")
                    for func in result['suspicious_functions'][:3]:  # 只显示前3个
                        f.write(f"    {func['name']} (位置: {func['start_pos']})\n")
                
                f.write("\n")
        
        print(f"分析报告已保存到: {report_path}")
        return report_path
    
    def extract_generation_logic(self, analysis_results):
        """提取anti-content生成逻辑"""
        print("提取anti-content生成逻辑...")
        
        # 寻找最有可能包含anti-content逻辑的文件
        candidate_files = []
        
        for result in analysis_results:
            score = 0
            
            # 关键词权重评分
            keyword_weights = {
                'anti-content': 10, 'anticontent': 10, 'anti_content': 10,
                'encrypt': 5, 'encode': 5, 'hash': 5, 'signature': 8,
                'timestamp': 3, 'random': 2, 'nonce': 4,
                'header': 2, 'request': 2, 'fingerprint': 6
            }
            
            for keyword, count in result['keywords_found'].items():
                if keyword in keyword_weights:
                    score += keyword_weights[keyword] * count
            
            # 可疑函数加分
            score += len(result['suspicious_functions']) * 3
            
            # 混淆文件可能性更高
            if result['obfuscated']['likely_obfuscated']:
                score += 5
            
            if score > 0:
                candidate_files.append({
                    'result': result,
                    'score': score
                })
        
        # 按评分排序
        candidate_files.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"发现 {len(candidate_files)} 个候选文件")
        
        # 分析前3个最有希望的文件
        extraction_results = []
        
        for i, candidate in enumerate(candidate_files[:3]):
            print(f"分析候选文件 {i+1}: {candidate['result']['url']}")
            
            try:
                with open(candidate['result']['filepath'], 'r', encoding='utf-8') as f:
                    js_content = f.read()
                
                # 提取可能的anti-content生成函数
                extracted_functions = self.extract_anti_content_functions(js_content)
                
                extraction_results.append({
                    'file_info': candidate['result'],
                    'score': candidate['score'],
                    'extracted_functions': extracted_functions
                })
                
            except Exception as e:
                print(f"分析文件失败: {e}")
        
        # 保存提取结果
        self.save_extraction_results(extraction_results)
        
        return extraction_results
    
    def extract_anti_content_functions(self, js_content):
        """从JavaScript代码中提取anti-content相关函数"""
        extracted_functions = []
        
        # 模式1: 直接包含anti-content的函数
        pattern1 = r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*{[^}]*anti[^}]*}'
        matches1 = re.finditer(pattern1, js_content, re.IGNORECASE | re.DOTALL)
        
        for match in matches1:
            extracted_functions.append({
                'type': 'direct_anti_function',
                'name': match.group(1),
                'content': match.group(0),
                'start_pos': match.start()
            })
        
        # 模式2: 加密/编码函数
        pattern2 = r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*{[^}]*(?:encrypt|encode|hash|signature)[^}]*}'
        matches2 = re.finditer(pattern2, js_content, re.IGNORECASE | re.DOTALL)
        
        for match in matches2:
            extracted_functions.append({
                'type': 'crypto_function',
                'name': match.group(1),
                'content': match.group(0),
                'start_pos': match.start()
            })
        
        # 模式3: 请求头生成函数
        pattern3 = r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*{[^}]*header[^}]*}'
        matches3 = re.finditer(pattern3, js_content, re.IGNORECASE | re.DOTALL)
        
        for match in matches3:
            extracted_functions.append({
                'type': 'header_function',
                'name': match.group(1),
                'content': match.group(0),
                'start_pos': match.start()
            })
        
        # 模式4: 浏览器指纹函数
        pattern4 = r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*{[^}]*(?:navigator|screen|canvas|webgl)[^}]*}'
        matches4 = re.finditer(pattern4, js_content, re.IGNORECASE | re.DOTALL)
        
        for match in matches4:
            extracted_functions.append({
                'type': 'fingerprint_function',
                'name': match.group(1),
                'content': match.group(0),
                'start_pos': match.start()
            })
        
        return extracted_functions
    
    def save_extraction_results(self, extraction_results):
        """保存提取结果"""
        results_path = 'd:\\testyd\\promat\\anti_content_extraction_results.json'
        
        # 准备保存的数据
        save_data = []
        
        for result in extraction_results:
            save_data.append({
                'file_url': result['file_info']['url'],
                'file_path': result['file_info']['filepath'],
                'score': result['score'],
                'extracted_functions': [
                    {
                        'type': func['type'],
                        'name': func['name'],
                        'start_pos': func['start_pos'],
                        'content_preview': func['content'][:500] + '...' if len(func['content']) > 500 else func['content']
                    }
                    for func in result['extracted_functions']
                ]
            })
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"提取结果已保存到: {results_path}")
        
        # 同时保存详细的函数代码
        functions_path = 'd:\\testyd\\promat\\extracted_functions.js'
        
        with open(functions_path, 'w', encoding='utf-8') as f:
            f.write("// 从拼多多JavaScript中提取的可能相关函数\n")
            f.write("// " + "=" * 60 + "\n\n")
            
            for i, result in enumerate(extraction_results):
                f.write(f"// 文件 {i+1}: {result['file_info']['url']}\n")
                f.write(f"// 评分: {result['score']}\n")
                f.write("// " + "-" * 40 + "\n\n")
                
                for j, func in enumerate(result['extracted_functions']):
                    f.write(f"// 函数 {j+1} - 类型: {func['type']}\n")
                    f.write(f"// 函数名: {func['name']}\n")
                    f.write(f"// 位置: {func['start_pos']}\n")
                    f.write(func['content'])
                    f.write("\n\n")
        
        print(f"提取的函数代码已保存到: {functions_path}")

def main():
    """主函数"""
    print("拼多多 anti-content 逆向工程分析")
    print("=" * 50)
    
    reverser = PddAntiContentReverser()
    
    try:
        # 执行逆向工程分析
        results = reverser.reverse_engineer_anti_content()
        
        if results:
            print("\n分析完成！")
            print("请查看生成的分析报告和提取结果文件。")
        else:
            print("\n分析未能获得有效结果。")
            print("建议尝试以下方案：")
            print("1. 使用浏览器开发者工具手动分析")
            print("2. 使用Selenium等工具获取动态生成的JavaScript")
            print("3. 参考开源的拼多多爬虫项目")
    
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()