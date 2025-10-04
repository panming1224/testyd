#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有调度任务
"""
import sys
sys.path.append(r'D:\testyd\task_generator')

from scheduler_flows import (
    unified_task_generation_daily_flow,
    unified_task_generation_weekly_flow,
    unified_task_generation_monthly_flow,
    pdd_quality_flow,
    pdd_badscore_flow,
    pdd_chat_flow,
    pdd_kpi_flow,
    pdd_kpi_weekly_flow,
    pdd_kpi_monthly_flow,
    tm_cookie_flow,
    tm_badscore_flow,
    tm_chat_flow,
    tm_kpi_flow,
    erp_store_flow,
    jd_store_flow
)

def test_flow(flow_func, flow_name):
    """测试单个流程"""
    print(f"\n{'='*80}")
    print(f"测试: {flow_name}")
    print(f"{'='*80}")
    
    try:
        result = flow_func()
        if result:
            print(f"✅ {flow_name} - 测试通过")
            return True
        else:
            print(f"❌ {flow_name} - 测试失败")
            return False
    except Exception as e:
        print(f"❌ {flow_name} - 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("="*80)
    print("开始测试所有调度任务")
    print("="*80)
    
    test_cases = [
        # 任务生成流程
        (unified_task_generation_daily_flow, "统一任务生成-每日"),
        
        # 天猫任务流程（按执行顺序）
        (tm_cookie_flow, "天猫Cookie获取"),
        (tm_badscore_flow, "天猫差评数据"),
        (tm_chat_flow, "天猫聊天数据"),
        (tm_kpi_flow, "天猫KPI数据"),
        
        # PDD任务流程
        (pdd_quality_flow, "PDD质量数据"),
        (pdd_badscore_flow, "PDD差评数据"),
        (pdd_chat_flow, "PDD聊天数据"),
        (pdd_kpi_flow, "PDDKPI数据"),
        
        # 其他平台任务
        (erp_store_flow, "ERP门店数据"),
        (jd_store_flow, "京东门店数据"),
    ]
    
    results = []
    for flow_func, flow_name in test_cases:
        result = test_flow(flow_func, flow_name)
        results.append((flow_name, result))
    
    # 打印测试总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for flow_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {flow_name}")
    
    print(f"\n总计: {success_count}/{total_count} 个任务测试通过")
    
    if success_count == total_count:
        print("\n🎉 所有任务测试通过！")
    else:
        print(f"\n⚠️  有 {total_count - success_count} 个任务测试失败")

if __name__ == "__main__":
    main()

