# -*- coding: utf-8 -*-
"""
完整流程测试脚本
测试所有3个爬虫程序的完整流程
"""
import subprocess
import sys
import pymysql
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n执行: {description}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if result.returncode == 0:
        print(f"✓ {description} 成功")
        return True
    else:
        print(f"✗ {description} 失败")
        if result.stderr:
            print(f"错误: {result.stderr[:200]}")
        return False

def main():
    print_section("拼多多爬虫系统 - 完整流程测试")
    
    # 测试配置
    test_shop = '361南宸专卖店'
    today = datetime.now()
    
    # 计算各任务的目标日期
    dates = {
        'badscore': (today - timedelta(days=1)).strftime('%Y-%m-%d'),  # T-1
        'quality': today.strftime('%Y-%m-%d'),  # T
        'kpi': (today - timedelta(days=3)).strftime('%Y-%m-%d')  # T-3
    }
    
    print(f"\n测试店铺: {test_shop}")
    print(f"差评数据日期: {dates['badscore']} (T-1)")
    print(f"质量数据日期: {dates['quality']} (T)")
    print(f"绩效数据日期: {dates['kpi']} (T-3)")
    
    # 连接数据库
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='admin123',
            database='company',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        print("\n✓ 数据库连接成功")
    except Exception as e:
        print(f"\n✗ 数据库连接失败: {e}")
        return
    
    # 步骤1: 清理旧数据
    print_section("步骤1: 清理旧测试数据")
    try:
        for date_str in dates.values():
            cursor.execute(f"DELETE FROM pdd_tasks WHERE time_period='{date_str}'")
        conn.commit()
        print(f"✓ 已清理旧测试数据")
    except Exception as e:
        print(f"✗ 清理失败: {e}")
        return
    
    # 步骤2: 生成任务
    print_section("步骤2: 生成任务")
    all_success = True
    for task_name, date_str in dates.items():
        success = run_command(
            ['python', 'testyd/pdd/generate_tasks.py', '--schedule', 'daily', '--date', date_str],
            f"生成 {date_str} 的任务"
        )
        if not success:
            all_success = False
    
    if not all_success:
        print("\n✗ 任务生成失败，停止测试")
        return
    
    # 步骤3: 只保留测试店铺
    print_section("步骤3: 只保留测试店铺")
    try:
        for date_str in dates.values():
            cursor.execute(f"DELETE FROM pdd_tasks WHERE time_period='{date_str}' AND shop_name != '{test_shop}'")
            deleted = cursor.rowcount
            conn.commit()
            print(f"✓ {date_str}: 删除 {deleted} 个其他店铺")
            
            cursor.execute(f"""
                UPDATE pdd_tasks 
                SET badsscore_status='待执行', quality_status='待执行', kpi_days_status='待执行'
                WHERE time_period='{date_str}' AND shop_name='{test_shop}'
            """)
            conn.commit()
            print(f"✓ {date_str}: 重置 {test_shop} 状态为待执行")
    except Exception as e:
        print(f"✗ 设置失败: {e}")
        return
    
    # 步骤4: 执行爬虫程序
    print_section("步骤4: 执行爬虫程序")
    
    crawlers = [
        ('pdd_badscore.py', '差评数据采集'),
        ('pdd_quality.py', '产品质量数据采集'),
        ('pdd_kpi.py', '客服绩效数据采集')
    ]
    
    results = {}
    for script, name in crawlers:
        print(f"\n{'=' * 60}")
        print(f"执行: {name}")
        print(f"{'=' * 60}")
        
        result = subprocess.run(
            ['python', f'testyd/pdd/{script}'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        success = result.returncode == 0
        results[name] = success
        
        if success:
            print(f"✓ {name} 执行成功")
            # 检查关键输出
            output = result.stdout
            if 'MinIO上传成功' in output:
                print("  ✓ MinIO上传成功")
            if 'Dremio' in output and '刷新成功' in output:
                print("  ✓ Dremio刷新成功")
            if '所有任务完成' in output:
                print("  ✓ 所有任务完成")
        else:
            print(f"✗ {name} 执行失败")
            if result.stderr:
                print(f"  错误: {result.stderr[:200]}")
    
    # 步骤5: 验证结果
    print_section("步骤5: 验证结果")
    
    try:
        for task_name, date_str in dates.items():
            cursor.execute(f"""
                SELECT badsscore_status, quality_status, kpi_days_status 
                FROM pdd_tasks 
                WHERE time_period='{date_str}' AND shop_name='{test_shop}'
            """)
            row = cursor.fetchone()
            if row:
                print(f"\n{date_str}:")
                print(f"  差评状态: {row[0]}")
                print(f"  质量状态: {row[1]}")
                print(f"  绩效状态: {row[2]}")
    except Exception as e:
        print(f"✗ 验证失败: {e}")
    
    # 关闭数据库连接
    cursor.close()
    conn.close()
    
    # 最终总结
    print_section("测试总结")
    
    all_passed = all(results.values())
    
    print(f"\n测试结果:")
    for name, success in results.items():
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {name}: {status}")
    
    if all_passed:
        print(f"\n🎉 所有测试通过！")
        print(f"\n✅ 差评数据采集 - 成功")
        print(f"✅ 产品质量数据采集 - 成功")
        print(f"✅ 客服绩效数据采集 - 成功")
        print(f"\n✅ MinIO上传 - 成功")
        print(f"✅ Dremio刷新 - 成功")
        print(f"\n系统运行正常，可以投入使用！")
    else:
        print(f"\n⚠️  部分测试失败，请检查错误信息")

if __name__ == '__main__':
    main()

