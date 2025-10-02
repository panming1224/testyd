#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多 anti-content 参数测试脚本 - 简化版
不依赖浏览器驱动，直接分析和测试anti-content生成
"""

import time
import json
import hashlib
import hmac
import base64
import random
import string
import requests
from urllib.parse import quote, unquote
import re

class AntiContentGenerator:
    """anti-content参数生成器"""
    
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        
        # 从之前分析得出的模式
        self.hex_chars = ['0', '2', 'a', 'b', 'c', 'e']
        self.common_patterns = ['0a', '0b', '0c', '0e', '2c']
        
    def generate_timestamp_based(self):
        """基于时间戳的生成方法"""
        timestamp = int(time.time())
        
        # 将时间戳转换为十六进制
        hex_timestamp = format(timestamp, 'x')
        
        # 使用时间戳作为种子
        random.seed(timestamp)
        
        # 生成基础模式
        result = ''
        base_patterns = ['0a0b0c0e', '2c0a0b0c']
        
        for i in range(12):  # 生成约96个字符
            if i == 0:
                result += '2c'  # 开始标记
            result += random.choice(base_patterns)
        
        return result[:98]  # 截取到98个字符
    
    def generate_url_based(self, url, referer=''):
        """基于URL和Referer的生成方法"""
        # 创建输入字符串
        input_str = f"{url}|{referer}|{int(time.time())}"
        
        # 计算MD5哈希
        md5_hash = hashlib.md5(input_str.encode()).hexdigest()
        
        # 将MD5转换为我们观察到的字符集
        result = ''
        for char in md5_hash:
            if char in '0123456789':
                result += '0' + random.choice(['a', 'b', 'c', 'e'])
            elif char in 'abcdef':
                result += char if char in self.hex_chars else random.choice(self.hex_chars)
            else:
                result += random.choice(self.common_patterns)
        
        return result[:98]
    
    def generate_pattern_based(self):
        """基于观察到的模式生成"""
        patterns = [
            '0a0b0c0e',  # 基础模式1
            '0a0b0c0e',  # 重复增加权重
            '2c0a0b0c',  # 基础模式2
            '0e0a0b0c',  # 变体1
            '0c0e0a0b',  # 变体2
        ]
        
        result = '0a2c'  # 固定开头
        
        while len(result) < 98:
            pattern = random.choice(patterns)
            result += pattern
        
        return result[:98]
    
    def generate_advanced_pattern(self):
        """高级模式生成 - 基于更复杂的规律"""
        # 观察到的序列：0a2c0b0c0e0a0b0c0e...
        
        # 分析：似乎有固定的循环模式
        base_sequence = '0a0b0c0e'
        separator = '2c'
        
        result = '0a' + separator  # 开始
        
        # 重复基础序列
        for i in range(23):  # 约92个字符
            result += base_sequence
        
        return result[:98]
    
    def generate_checksum_based(self, data_input):
        """基于校验和的生成方法"""
        # 使用输入数据生成校验和
        checksum = 0
        for char in data_input:
            checksum += ord(char)
        
        # 使用校验和作为种子
        random.seed(checksum % 10000)
        
        result = ''
        
        # 生成主体部分
        for i in range(49):  # 98个字符 = 49 * 2
            result += random.choice(self.common_patterns)
        
        return result[:98]

class AntiContentTester:
    """anti-content参数测试器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
    
    def test_anti_content(self, anti_content, test_url='https://mms.pinduoduo.com/mms-chat/search'):
        """测试anti-content参数"""
        print(f"测试anti-content: {anti_content[:50]}...")
        
        try:
            # 构造请求参数
            params = {
                'anti-content': anti_content,
                'q': '测试商品',
                'page': 1,
                'msfrom': 'mms_sidenav'
            }
            
            # 添加必要的头部
            headers = self.session.headers.copy()
            headers.update({
                'Referer': 'https://mms.pinduoduo.com/',
                'Origin': 'https://mms.pinduoduo.com'
            })
            
            response = self.session.get(test_url, params=params, headers=headers, timeout=10)
            
            result = {
                'anti_content': anti_content,
                'status_code': response.status_code,
                'response_length': len(response.text),
                'success': response.status_code == 200,
                'contains_data': 'data' in response.text.lower(),
                'contains_error': any(error in response.text.lower() for error in ['error', 'forbidden', 'invalid', '错误']),
                'response_headers': dict(response.headers)
            }
            
            # 检查响应内容
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    result['is_json'] = True
                    result['json_keys'] = list(json_data.keys()) if isinstance(json_data, dict) else []
                except:
                    result['is_json'] = False
            
            print(f"测试结果: 状态码={result['status_code']}, 成功={result['success']}")
            return result
            
        except Exception as e:
            print(f"测试失败: {e}")
            return {
                'anti_content': anti_content,
                'error': str(e),
                'success': False
            }
    
    def batch_test(self, anti_content_list):
        """批量测试多个anti-content参数"""
        results = []
        
        for i, anti_content in enumerate(anti_content_list):
            print(f"\n测试 {i+1}/{len(anti_content_list)}")
            result = self.test_anti_content(anti_content)
            results.append(result)
            
            # 避免请求过快
            time.sleep(1)
        
        return results

def analyze_generation_methods():
    """分析不同的生成方法"""
    print("分析anti-content生成方法")
    print("=" * 50)
    
    generator = AntiContentGenerator()
    
    # 生成测试样本
    methods = [
        ('时间戳方法', generator.generate_timestamp_based),
        ('URL方法', lambda: generator.generate_url_based('https://mms.pinduoduo.com/mms-chat/search', 'https://mms.pinduoduo.com/')),
        ('模式方法', generator.generate_pattern_based),
        ('高级模式', generator.generate_advanced_pattern),
        ('校验和方法', lambda: generator.generate_checksum_based('test_input_data'))
    ]
    
    generated_samples = []
    
    for method_name, method_func in methods:
        try:
            sample = method_func()
            generated_samples.append({
                'method': method_name,
                'sample': sample,
                'length': len(sample),
                'unique_chars': len(set(sample)),
                'char_distribution': {char: sample.count(char) for char in set(sample)}
            })
            print(f"{method_name}: {sample[:60]}...")
        except Exception as e:
            print(f"{method_name} 失败: {e}")
    
    return generated_samples

def compare_with_original():
    """与原始样本比较"""
    original_sample = "0a2c0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e"
    
    print(f"\n原始样本分析:")
    print(f"长度: {len(original_sample)}")
    print(f"字符集: {sorted(set(original_sample))}")
    print(f"样本: {original_sample}")
    
    # 分析模式
    patterns = {}
    for i in range(len(original_sample) - 1):
        pattern = original_sample[i:i+2]
        patterns[pattern] = patterns.get(pattern, 0) + 1
    
    print(f"2字符模式: {patterns}")
    
    # 查找重复序列
    for length in [4, 6, 8]:
        sequences = {}
        for i in range(len(original_sample) - length + 1):
            seq = original_sample[i:i+length]
            sequences[seq] = sequences.get(seq, 0) + 1
        
        repeated = {seq: count for seq, count in sequences.items() if count > 1}
        if repeated:
            print(f"{length}字符重复序列: {repeated}")

def main():
    """主函数"""
    print("拼多多 anti-content 参数生成与测试")
    print("=" * 60)
    
    # 1. 分析原始样本
    compare_with_original()
    
    # 2. 生成测试样本
    print("\n" + "=" * 60)
    generated_samples = analyze_generation_methods()
    
    # 3. 测试生成的样本
    print("\n" + "=" * 60)
    print("测试生成的anti-content参数")
    
    tester = AntiContentTester()
    
    # 选择最有希望的几个样本进行测试
    test_samples = [sample['sample'] for sample in generated_samples[:3]]
    
    # 添加原始样本作为对照
    original_sample = "0a2c0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e0a0b0c0e"
    test_samples.append(original_sample)
    
    test_results = tester.batch_test(test_samples)
    
    # 4. 保存结果
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'generated_samples': generated_samples,
        'test_results': test_results,
        'summary': {
            'total_methods': len(generated_samples),
            'total_tests': len(test_results),
            'successful_tests': len([r for r in test_results if r.get('success', False)])
        }
    }
    
    output_file = 'd:\\testyd\\promat\\anti_content_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试结果已保存到: {output_file}")
    
    # 5. 总结
    successful_tests = [r for r in test_results if r.get('success', False)]
    print(f"\n总结:")
    print(f"生成方法数量: {len(generated_samples)}")
    print(f"测试样本数量: {len(test_results)}")
    print(f"成功测试数量: {len(successful_tests)}")
    
    if successful_tests:
        print("\n成功的测试:")
        for result in successful_tests:
            print(f"- {result['anti_content'][:50]}... (状态码: {result['status_code']})")

if __name__ == "__main__":
    main()