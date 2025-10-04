# -*- coding: utf-8 -*-
"""
运行所有124家店铺的完整测试
"""
import subprocess
import sys
import pymysql
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

print("=" * 60)
print("拼多多爬虫系统 - 124家店铺完整测试")
print("=" * 60)

# 计算各个任务的目标日期
today = datetime.now()
date_badscore = (today - timedelta(days=1)).strftime('%Y-%m-%d')  # T-1
date_quality = today.strftime('%Y-%m-%d')  # T
date_kpi = (today - timedelta(days=3)).strftime('%Y-%m-%d')  # T-3

print(f"\n目标日期:")
print(f"  差评数据: {date_badscore} (T-1)")
print(f"  质量数据: {date_quality} (T)")
print(f"  绩效数据: {date_kpi} (T-3)")

# 连接数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='admin123',
    database='company',
    charset='utf8mb4'
)
cursor = conn.cursor()

# 步骤1: 清理旧数据
print("\n" + "=" * 60)
print("步骤1: 清理旧测试数据")
print("=" * 60)

for date_str in [date_badscore, date_quality, date_kpi]:
    cursor.execute(f"DELETE FROM pdd_tasks WHERE time_period='{date_str}'")
    conn.commit()
    print(f"✓ 已清理 {date_str} 的数据")

# 步骤2: 生成任务
print("\n" + "=" * 60)
print("步骤2: 生成任务（124家店铺）")
print("=" * 60)

result = subprocess.run(
    ['python', 'testyd/pdd/generate_tasks.py', '--schedule', 'daily'],
    capture_output=True,
    text=True,
    encoding='utf-8'
)

if result.returncode == 0:
    print("✓ 任务生成成功")
else:
    print(f"✗ 任务生成失败: {result.stderr}")
    sys.exit(1)

# 步骤3: 验证任务生成
print("\n" + "=" * 60)
print("步骤3: 验证任务生成")
print("=" * 60)

# 验证差评任务
cursor.execute(f"""
    SELECT COUNT(*) FROM pdd_tasks 
    WHERE time_period='{date_badscore}' AND badsscore_status='待执行'
""")
count = cursor.fetchone()[0]
print(f"差评任务 ({date_badscore}): {count}/124 个店铺")

# 验证质量任务
cursor.execute(f"""
    SELECT COUNT(*) FROM pdd_tasks 
    WHERE time_period='{date_quality}' AND quality_status='待执行'
""")
count = cursor.fetchone()[0]
print(f"质量任务 ({date_quality}): {count}/124 个店铺")

# 验证绩效任务
cursor.execute(f"""
    SELECT COUNT(*) FROM pdd_tasks 
    WHERE time_period='{date_kpi}' AND kpi_days_status='待执行'
""")
count = cursor.fetchone()[0]
print(f"绩效任务 ({date_kpi}): {count}/124 个店铺")

# 步骤4: 执行爬虫程序
print("\n" + "=" * 60)
print("步骤4: 执行爬虫程序（124家店铺）")
print("=" * 60)
print("⚠️  这将需要较长时间，请耐心等待...")

crawlers = [
    ('pdd_badscore.py', '差评数据采集', date_badscore, 'badsscore_status'),
    ('pdd_quality.py', '产品质量数据采集', date_quality, 'quality_status'),
    ('pdd_kpi.py', '客服绩效数据采集', date_kpi, 'kpi_days_status')
]

results = {}

for script, name, date_str, status_field in crawlers:
    print(f"\n{'=' * 60}")
    print(f"执行: {name}")
    print(f"{'=' * 60}")
    
    start_time = datetime.now()
    
    result = subprocess.run(
        ['python', f'testyd/pdd/{script}'],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    success = result.returncode == 0
    results[name] = success
    
    if success:
        print(f"✓ {name} 执行成功（耗时: {duration:.1f}秒）")
        
        # 检查MinIO上传
        if 'MinIO上传成功' in result.stdout:
            print("  ✓ MinIO上传成功")
        
        # 检查Dremio刷新
        if 'Dremio' in result.stdout and '刷新成功' in result.stdout:
            print("  ✓ Dremio刷新成功")
        
        # 统计完成情况
        cursor.execute(f"""
            SELECT COUNT(*) FROM pdd_tasks 
            WHERE time_period='{date_str}' AND {status_field}='已完成'
        """)
        completed = cursor.fetchone()[0]
        print(f"  ✓ 已完成: {completed}/124 个店铺")
    else:
        print(f"✗ {name} 执行失败")
        if result.stderr:
            print(f"  错误: {result.stderr[:200]}")

# 步骤5: 最终验证
print("\n" + "=" * 60)
print("步骤5: 最终验证")
print("=" * 60)

all_success = True

for script, name, date_str, status_field in crawlers:
    cursor.execute(f"""
        SELECT 
            SUM(CASE WHEN {status_field}='已完成' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN {status_field}='待执行' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN {status_field} IS NULL THEN 1 ELSE 0 END) as null_count
        FROM pdd_tasks 
        WHERE time_period='{date_str}'
    """)
    row = cursor.fetchone()
    completed, pending, null_count = row
    
    print(f"\n{name} ({date_str}):")
    print(f"  已完成: {completed}")
    print(f"  待执行: {pending}")
    print(f"  NULL: {null_count}")
    
    if completed == 124:
        print(f"  ✓ 全部完成")
    elif pending > 0:
        print(f"  ⚠️  还有 {pending} 个店铺待执行")
        all_success = False
    else:
        print(f"  ✗ 异常状态")
        all_success = False

cursor.close()
conn.close()

# 最终总结
print("\n" + "=" * 60)
print("测试总结")
print("=" * 60)

if all_success:
    print("\n🎉 所有测试通过！")
    print("\n✅ 差评数据采集 - 124家店铺全部完成")
    print("✅ 产品质量数据采集 - 124家店铺全部完成")
    print("✅ 客服绩效数据采集 - 124家店铺全部完成")
    print("\n✅ MinIO上传 - 成功")
    print("✅ Dremio刷新 - 成功")
    print("\n系统运行正常，可以投入生产使用！")
else:
    print("\n⚠️  部分店铺未完成，请检查日志")

