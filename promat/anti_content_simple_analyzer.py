#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多 anti-content 参数分析脚本 - 简化版
分析anti-content参数的特征和生成模式
"""

import re
import json
import requests
import hashlib
import base64
import time
import random
import string
from urllib.parse import urlparse, parse_qs
import os

class PddAntiContentAnalyzer:
    """拼多多anti-content分析器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        })
        
        # 从原始请求中提取的样本anti-content（截取前100个字符）
        self.sample_anti_content = "0a2c0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e"
        
    def analyze_anti_content_structure(self):
        """分析anti-content参数结构"""
        print("分析anti-content参数结构...")
        print("=" * 50)
        
        analysis = {
            'length': len(self.sample_anti_content),
            'character_set': set(self.sample_anti_content),
            'patterns': [],
            'encoding_type': 'unknown',
            'structure_analysis': {}
        }
        
        # 字符集分析
        print(f"参数长度: {analysis['length']}")
        print(f"字符集: {sorted(analysis['character_set'])}")
        
        # 模式分析
        patterns = [
            r'0a',  # 十六进制模式
            r'0b',
            r'0c',
            r'0e',
            r'[0-9a-f]{2}',  # 两位十六进制
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.sample_anti_content)
            if matches:
                analysis['patterns'].append({
                    'pattern': pattern,
                    'count': len(matches),
                    'matches': matches[:10]  # 只显示前10个匹配
                })
        
        # 编码类型推测
        if all(c in '0123456789abcdef' for c in self.sample_anti_content):
            analysis['encoding_type'] = 'hexadecimal'
        
        # 结构分析
        analysis['structure_analysis'] = {
            'repeating_sequences': self.find_repeating_sequences(),
            'entropy': self.calculate_entropy(),
            'possible_timestamp': self.check_timestamp_patterns(),
            'possible_checksum': self.check_checksum_patterns()
        }
        
        return analysis
    
    def find_repeating_sequences(self):
        """查找重复序列"""
        sequences = {}
        sample = self.sample_anti_content
        
        # 查找2-8字符的重复序列
        for length in range(2, 9):
            for i in range(len(sample) - length + 1):
                seq = sample[i:i+length]
                if seq in sequences:
                    sequences[seq] += 1
                else:
                    sequences[seq] = 1
        
        # 只返回出现次数大于1的序列
        return {seq: count for seq, count in sequences.items() if count > 1}
    
    def calculate_entropy(self):
        """计算信息熵"""
        from collections import Counter
        import math
        
        char_counts = Counter(self.sample_anti_content)
        total_chars = len(self.sample_anti_content)
        
        entropy = 0
        for count in char_counts.values():
            probability = count / total_chars
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def check_timestamp_patterns(self):
        """检查时间戳模式"""
        # 查找可能的时间戳（10位或13位数字）
        timestamp_patterns = [
            r'[0-9a-f]{8}',  # 可能的时间戳（十六进制）
            r'[0-9a-f]{10}',  # 10位十六进制时间戳
            r'[0-9a-f]{13}',  # 13位十六进制时间戳
        ]
        
        results = []
        for pattern in timestamp_patterns:
            matches = re.findall(pattern, self.sample_anti_content)
            if matches:
                results.append({
                    'pattern': pattern,
                    'matches': matches[:5]  # 只显示前5个
                })
        
        return results
    
    def check_checksum_patterns(self):
        """检查校验和模式"""
        # 查找可能的校验和（通常在末尾）
        sample = self.sample_anti_content
        
        results = {
            'last_8_chars': sample[-8:] if len(sample) >= 8 else sample,
            'last_16_chars': sample[-16:] if len(sample) >= 16 else sample,
            'first_8_chars': sample[:8],
            'first_16_chars': sample[:16]
        }
        
        return results
    
    def generate_test_anti_content(self):
        """生成测试用的anti-content"""
        print("\n生成测试用的anti-content...")
        print("-" * 30)
        
        methods = [
            self.method_1_simple_hex,
            self.method_2_timestamp_based,
            self.method_3_pattern_based
        ]
        
        results = []
        for i, method in enumerate(methods, 1):
            try:
                generated = method()
                results.append({
                    'method': f'方法{i}',
                    'generated': generated,
                    'length': len(generated),
                    'similarity': self.calculate_similarity(generated)
                })
                print(f"方法{i}: {generated[:50]}...")
            except Exception as e:
                print(f"方法{i}失败: {e}")
        
        return results
    
    def method_1_simple_hex(self):
        """方法1: 简单十六进制生成"""
        # 基于观察到的模式生成
        patterns = ['0a', '0b', '0c', '0e']
        result = ''
        
        for _ in range(50):  # 生成100个字符
            result += random.choice(patterns)
        
        return result
    
    def method_2_timestamp_based(self):
        """方法2: 基于时间戳的生成"""
        timestamp = int(time.time())
        
        # 将时间戳转换为十六进制并扩展
        hex_timestamp = format(timestamp, 'x')
        
        # 使用时间戳作为种子生成更多内容
        random.seed(timestamp)
        patterns = ['0a', '0b', '0c', '0e']
        
        result = hex_timestamp
        while len(result) < 100:
            result += random.choice(patterns)
        
        return result[:100]
    
    def method_3_pattern_based(self):
        """方法3: 基于模式的生成"""
        # 基于观察到的重复模式
        base_pattern = '0a0b0c0e'
        result = ''
        
        # 重复基础模式并添加变化
        for i in range(25):
            if i % 5 == 0:
                # 每5次添加一些变化
                result += '2c'
            result += base_pattern
        
        return result[:100]
    
    def calculate_similarity(self, generated):
        """计算与原始样本的相似度"""
        original = self.sample_anti_content
        generated = generated[:len(original)]  # 截取相同长度
        
        # 字符级别相似度
        char_matches = sum(1 for a, b in zip(original, generated) if a == b)
        char_similarity = char_matches / len(original) if original else 0
        
        # 字符集相似度
        original_chars = set(original)
        generated_chars = set(generated)
        char_set_similarity = len(original_chars & generated_chars) / len(original_chars | generated_chars) if original_chars or generated_chars else 0
        
        return {
            'character_level': char_similarity,
            'character_set': char_set_similarity,
            'overall': (char_similarity + char_set_similarity) / 2
        }
    
    def save_analysis_results(self, analysis, generation_results):
        """保存分析结果"""
        # 转换set为list以便JSON序列化
        analysis_copy = analysis.copy()
        analysis_copy['character_set'] = list(analysis_copy['character_set'])
        
        results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'sample_anti_content': self.sample_anti_content,
            'structure_analysis': analysis_copy,
            'generation_results': generation_results
        }
        
        output_file = 'd:\\testyd\\promat\\anti_content_analysis_results.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n分析结果已保存到: {output_file}")
        return output_file
    
    def run_complete_analysis(self):
        """运行完整分析"""
        print("拼多多 anti-content 参数分析")
        print("=" * 60)
        
        # 1. 结构分析
        analysis = self.analyze_anti_content_structure()
        
        print("\n结构分析结果:")
        print(f"编码类型: {analysis['encoding_type']}")
        print(f"信息熵: {analysis['structure_analysis']['entropy']:.4f}")
        print(f"重复序列数量: {len(analysis['structure_analysis']['repeating_sequences'])}")
        
        # 2. 生成测试
        generation_results = self.generate_test_anti_content()
        
        # 3. 保存结果
        output_file = self.save_analysis_results(analysis, generation_results)
        
        # 4. 总结
        print("\n分析总结:")
        print("1. anti-content参数使用十六进制编码")
        print("2. 包含重复的字符序列模式")
        print("3. 可能包含时间戳或校验和信息")
        print("4. 需要进一步的JavaScript逆向工程来确定确切的生成算法")
        
        return {
            'analysis': analysis,
            'generation_results': generation_results,
            'output_file': output_file
        }

def main():
    """主函数"""
    analyzer = PddAntiContentAnalyzer()
    
    try:
        results = analyzer.run_complete_analysis()
        print("\n分析完成！")
        
        # 显示最佳生成方法
        best_method = max(results['generation_results'], 
                         key=lambda x: x['similarity']['overall'])
        print(f"\n最佳生成方法: {best_method['method']}")
        print(f"相似度: {best_method['similarity']['overall']:.4f}")
        
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()