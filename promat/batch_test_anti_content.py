#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量测试 anti-content 参数的稳定性和成功率
验证不同方法在多次请求中的表现
"""

import time
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from final_anti_content_solution import PddAntiContentSolution, PddRequestHelper
import statistics

class AntiContentBatchTester:
    """anti-content参数批量测试器"""
    
    def __init__(self):
        self.solution = PddAntiContentSolution()
        self.helper = PddRequestHelper()
        self.test_urls = [
            'https://mms.pinduoduo.com/mms-chat/search',
            'https://mms.pinduoduo.com/api/search',
            'https://mms.pinduoduo.com/goods/search'
        ]
        
    def single_test(self, method_name, method_func, test_id):
        """单次测试"""
        start_time = time.time()
        
        try:
            # 生成anti-content
            anti_content = method_func()
            
            # 验证格式
            is_valid, message = self.solution.validate_anti_content(anti_content)
            
            if not is_valid:
                return {
                    'test_id': test_id,
                    'method': method_name,
                    'success': False,
                    'error': f'格式验证失败: {message}',
                    'duration': time.time() - start_time
                }
            
            # 发起请求测试
            result = self.helper.search_products(f"测试商品{test_id}")
            
            return {
                'test_id': test_id,
                'method': method_name,
                'success': result['success'],
                'status_code': result.get('status_code', 0),
                'anti_content': anti_content,
                'duration': time.time() - start_time,
                'response_length': len(result['response'].text) if result['success'] else 0,
                'error': result.get('error', '')
            }
            
        except Exception as e:
            return {
                'test_id': test_id,
                'method': method_name,
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def batch_test_method(self, method_name, method_func, test_count=10):
        """批量测试单个方法"""
        print(f"测试方法: {method_name} (共{test_count}次)")
        
        results = []
        
        # 使用线程池并发测试
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self.single_test, method_name, method_func, i+1)
                for i in range(test_count)
            ]
            
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                results.append(result)
                
                # 实时显示进度
                success_count = len([r for r in results if r['success']])
                print(f"  进度: {len(results)}/{test_count}, 成功: {success_count}, "
                      f"成功率: {success_count/len(results)*100:.1f}%")
        
        return results
    
    def analyze_results(self, results):
        """分析测试结果"""
        total_tests = len(results)
        successful_tests = [r for r in results if r['success']]
        failed_tests = [r for r in results if not r['success']]
        
        success_rate = len(successful_tests) / total_tests * 100 if total_tests > 0 else 0
        
        # 计算响应时间统计
        durations = [r['duration'] for r in results]
        avg_duration = statistics.mean(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # 状态码统计
        status_codes = {}
        for r in successful_tests:
            code = r.get('status_code', 0)
            status_codes[code] = status_codes.get(code, 0) + 1
        
        # 错误统计
        errors = {}
        for r in failed_tests:
            error = r.get('error', '未知错误')
            errors[error] = errors.get(error, 0) + 1
        
        return {
            'total_tests': total_tests,
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'success_rate': success_rate,
            'avg_duration': avg_duration,
            'min_duration': min_duration,
            'max_duration': max_duration,
            'status_codes': status_codes,
            'errors': errors
        }
    
    def comprehensive_test(self, test_count_per_method=20):
        """综合测试所有方法"""
        print("开始综合测试 anti-content 参数")
        print("=" * 60)
        
        methods = [
            ('模式方法', self.solution.generate_method_1_pattern_based),
            ('增强模式', self.solution.generate_method_2_enhanced_pattern),
            ('时间戳混合', self.solution.generate_method_3_timestamp_hybrid),
            ('校验和增强', lambda: self.solution.generate_method_4_checksum_enhanced(
                'https://mms.pinduoduo.com/mms-chat/search',
                'https://mms.pinduoduo.com/'
            ))
        ]
        
        all_results = {}
        
        for method_name, method_func in methods:
            print(f"\n{'-' * 40}")
            
            # 批量测试
            test_results = self.batch_test_method(method_name, method_func, test_count_per_method)
            
            # 分析结果
            analysis = self.analyze_results(test_results)
            
            all_results[method_name] = {
                'test_results': test_results,
                'analysis': analysis
            }
            
            # 显示分析结果
            print(f"\n{method_name} 测试结果:")
            print(f"  总测试数: {analysis['total_tests']}")
            print(f"  成功数: {analysis['successful_tests']}")
            print(f"  失败数: {analysis['failed_tests']}")
            print(f"  成功率: {analysis['success_rate']:.2f}%")
            print(f"  平均响应时间: {analysis['avg_duration']:.3f}秒")
            print(f"  状态码分布: {analysis['status_codes']}")
            
            if analysis['errors']:
                print(f"  错误统计: {analysis['errors']}")
        
        return all_results
    
    def stability_test(self, duration_minutes=5):
        """稳定性测试 - 持续一段时间的测试"""
        print(f"开始稳定性测试 (持续{duration_minutes}分钟)")
        print("=" * 60)
        
        start_time = time.time()
        end_time = start_time + duration_minutes * 60
        
        test_count = 0
        success_count = 0
        results = []
        
        while time.time() < end_time:
            test_count += 1
            
            # 使用最佳方法
            result = self.single_test(
                '模式方法', 
                self.solution.generate_method_1_pattern_based, 
                test_count
            )
            
            results.append(result)
            
            if result['success']:
                success_count += 1
            
            # 每10次测试显示一次进度
            if test_count % 10 == 0:
                elapsed = time.time() - start_time
                remaining = end_time - time.time()
                current_success_rate = success_count / test_count * 100
                
                print(f"进度: {elapsed/60:.1f}/{duration_minutes}分钟, "
                      f"测试: {test_count}, 成功率: {current_success_rate:.1f}%")
            
            # 间隔1秒
            time.sleep(1)
        
        # 分析稳定性结果
        analysis = self.analyze_results(results)
        
        print(f"\n稳定性测试完成:")
        print(f"  测试时长: {duration_minutes}分钟")
        print(f"  总测试数: {analysis['total_tests']}")
        print(f"  成功率: {analysis['success_rate']:.2f}%")
        print(f"  平均响应时间: {analysis['avg_duration']:.3f}秒")
        
        return {
            'duration_minutes': duration_minutes,
            'results': results,
            'analysis': analysis
        }

def main():
    """主函数"""
    tester = AntiContentBatchTester()
    
    print("拼多多 anti-content 参数批量测试")
    print("=" * 60)
    
    # 1. 综合测试
    print("\n1. 综合测试 (每种方法测试20次)")
    comprehensive_results = tester.comprehensive_test(20)
    
    # 2. 稳定性测试
    print("\n2. 稳定性测试 (持续3分钟)")
    stability_results = tester.stability_test(3)
    
    # 3. 保存结果
    final_results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'comprehensive_test': comprehensive_results,
        'stability_test': stability_results,
        'summary': {
            'best_method': None,
            'best_success_rate': 0,
            'recommendations': []
        }
    }
    
    # 找出最佳方法
    best_method = None
    best_rate = 0
    
    for method_name, data in comprehensive_results.items():
        rate = data['analysis']['success_rate']
        if rate > best_rate:
            best_rate = rate
            best_method = method_name
    
    final_results['summary']['best_method'] = best_method
    final_results['summary']['best_success_rate'] = best_rate
    
    # 生成建议
    recommendations = []
    
    if best_rate >= 95:
        recommendations.append("所有方法表现优秀，推荐使用模式方法")
    elif best_rate >= 80:
        recommendations.append(f"推荐使用{best_method}，成功率较高")
    else:
        recommendations.append("需要进一步优化算法，当前成功率偏低")
    
    if stability_results['analysis']['success_rate'] >= 90:
        recommendations.append("稳定性测试通过，适合生产环境使用")
    else:
        recommendations.append("稳定性需要改进，建议增加重试机制")
    
    final_results['summary']['recommendations'] = recommendations
    
    # 保存结果
    output_file = 'd:\\testyd\\promat\\batch_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n批量测试结果已保存到: {output_file}")
    
    # 显示总结
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"最佳方法: {best_method} (成功率: {best_rate:.2f}%)")
    print(f"稳定性: {stability_results['analysis']['success_rate']:.2f}%")
    print("建议:")
    for rec in recommendations:
        print(f"  - {rec}")

if __name__ == "__main__":
    main()