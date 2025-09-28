# Prefect 完整教学指南

## 📚 目录
1. [Prefect 基础概念](#prefect-基础概念)
2. [Task 和 Flow 的区别](#task-和-flow-的区别)
3. [基础语法和装饰器](#基础语法和装饰器)
4. [常用函数和方法](#常用函数和方法)
5. [实际示例](#实际示例)
6. [注册和部署](#注册和部署)
7. [启动和管理](#启动和管理)
8. [最佳实践](#最佳实践)

---

## Prefect 基础概念

### 🎯 什么是 Prefect？
Prefect 是一个现代化的工作流编排工具，用于构建、调度和监控数据管道。

### 🏗️ 核心组件
- **Task**: 工作流中的单个工作单元
- **Flow**: 由多个 Task 组成的工作流
- **Deployment**: 可调度的 Flow 实例
- **Work Queue**: 任务执行队列

---

## Task 和 Flow 的区别

### 📋 Task（任务）
```python
from prefect import task

@task
def my_task(name: str):
    """单个工作单元"""
    print(f"Hello, {name}!")
    return f"Processed {name}"
```

**特点：**
- 最小的工作单元
- 可以有输入参数和返回值
- 可以配置重试、超时等策略
- 可以被多个 Flow 复用

### 🌊 Flow（流程）
```python
from prefect import flow

@flow
def my_flow():
    """由多个 Task 组成的工作流"""
    result1 = my_task("Alice")
    result2 = my_task("Bob")
    return [result1, result2]
```

**特点：**
- 由多个 Task 组成
- 定义任务之间的依赖关系
- 可以包含条件逻辑和循环
- 是部署和调度的基本单位

---

## 基础语法和装饰器

### 🎨 Task 装饰器参数
```python
@task(
    name="自定义任务名称",           # 任务名称
    description="任务描述",         # 任务描述
    tags=["数据处理", "ETL"],       # 标签
    retries=3,                     # 重试次数
    retry_delay_seconds=60,        # 重试延迟
    timeout_seconds=300,           # 超时时间
    log_prints=True               # 记录 print 输出
)
def process_data(data):
    # 任务逻辑
    return processed_data
```

### 🌊 Flow 装饰器参数
```python
@flow(
    name="数据处理流程",
    description="完整的数据处理工作流",
    tags=["生产", "每日"],
    timeout_seconds=3600,
    log_prints=True,
    persist_result=True           # 持久化结果
)
def data_pipeline():
    # 流程逻辑
    pass
```

---

## 常用函数和方法

### 🔧 导入模块
```python
from prefect import task, flow
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from prefect.blocks.system import Secret
from pathlib import Path
import subprocess
```

### 📊 状态管理
```python
from prefect import get_run_logger
from prefect.exceptions import SKIP

@task
def conditional_task():
    logger = get_run_logger()
    
    if condition_not_met:
        logger.info("条件不满足，跳过任务")
        raise SKIP("跳过执行")
    
    logger.info("开始执行任务")
    # 任务逻辑
```

### 🔄 任务依赖
```python
@flow
def dependent_flow():
    # 串行执行
    result1 = task_a()
    result2 = task_b(result1)  # 依赖 task_a 的结果
    
    # 并行执行
    results = []
    for i in range(3):
        result = task_c.submit(i)  # 使用 submit 并行执行
        results.append(result)
    
    # 等待所有并行任务完成
    final_results = [r.result() for r in results]
    return final_results
```

---

## 实际示例

### 📝 简单示例
```python
from prefect import task, flow
import subprocess
from pathlib import Path

@task(
    name="执行Python脚本",
    retries=2,
    retry_delay_seconds=30,
    timeout_seconds=600
)
def run_python_script(script_path: str):
    """执行指定的Python脚本"""
    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            cwd=Path(script_path).parent,
            timeout=600
        )
        
        if result.returncode == 0:
            print(f"✅ 脚本执行成功: {script_path}")
            return result.stdout
        else:
            print(f"❌ 脚本执行失败: {result.stderr}")
            raise Exception(f"脚本执行失败: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        raise Exception(f"脚本执行超时: {script_path}")

@flow(
    name="数据拉取流程",
    description="执行数据拉取脚本",
    tags=["数据拉取", "自动化"]
)
def data_extraction_flow():
    """数据拉取工作流"""
    # 执行拼多多质量数据拉取
    pdd_result = run_python_script("pdd_quality.py")
    
    # 执行ERP数据拉取
    erp_result = run_python_script("erp_store.py")
    
    return {
        "pdd_quality": pdd_result,
        "erp_store": erp_result
    }

# 测试运行
if __name__ == "__main__":
    # 本地测试
    result = data_extraction_flow()
    print("流程执行完成:", result)
```

### 🔄 复杂示例（带条件和循环）
```python
@task
def check_data_availability(source: str):
    """检查数据源是否可用"""
    # 检查逻辑
    return True  # 或 False

@task
def process_batch(batch_data):
    """处理单个批次的数据"""
    # 处理逻辑
    return f"处理完成: {len(batch_data)} 条记录"

@flow
def complex_data_flow():
    """复杂的数据处理流程"""
    sources = ["source_a", "source_b", "source_c"]
    
    # 检查所有数据源
    availability_checks = []
    for source in sources:
        check = check_data_availability.submit(source)
        availability_checks.append(check)
    
    # 等待检查完成
    available_sources = []
    for i, check in enumerate(availability_checks):
        if check.result():
            available_sources.append(sources[i])
    
    if not available_sources:
        print("❌ 没有可用的数据源")
        return None
    
    # 处理可用的数据源
    results = []
    for source in available_sources:
        # 模拟获取批次数据
        batches = [f"{source}_batch_{i}" for i in range(3)]
        
        # 并行处理批次
        batch_results = []
        for batch in batches:
            result = process_batch.submit(batch)
            batch_results.append(result)
        
        # 收集结果
        source_results = [r.result() for r in batch_results]
        results.extend(source_results)
    
    return results
```

---

## 注册和部署

### 📋 创建部署
```python
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

# 方法1: 在代码中创建部署
deployment = Deployment.build_from_flow(
    flow=data_extraction_flow,
    name="数据拉取-定时执行",
    description="每天08:00执行数据拉取",
    tags=["生产", "定时", "数据拉取"],
    schedule=CronSchedule(
        cron="0 8 * * *",
        timezone="Asia/Shanghai"
    ),
    work_queue_name="default"
)

# 应用部署
deployment.apply()
```

### 🚀 使用调度器脚本
```python
# prefect_scheduler.py
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from prefect_flows import data_extraction_flow

def create_deployments():
    """创建所有部署"""
    deployments = []
    
    # 定时执行部署
    scheduled_deployment = Deployment.build_from_flow(
        flow=data_extraction_flow,
        name="数据拉取-定时执行",
        description="每天08:00自动执行",
        tags=["定时", "生产"],
        schedule=CronSchedule(
            cron="0 8 * * *",
            timezone="Asia/Shanghai"
        )
    )
    deployments.append(scheduled_deployment)
    
    # 手动执行部署
    manual_deployment = Deployment.build_from_flow(
        flow=data_extraction_flow,
        name="数据拉取-手动执行",
        description="手动触发执行",
        tags=["手动", "测试"]
    )
    deployments.append(manual_deployment)
    
    return deployments

def main():
    """主函数"""
    print("🚀 开始创建 Prefect 部署...")
    
    deployments = create_deployments()
    
    for deployment in deployments:
        deployment.apply()
        print(f"✅ 部署创建成功: {deployment.name}")
    
    print("🎉 所有部署创建完成!")

if __name__ == "__main__":
    main()
```

---

## 启动和管理

### 🖥️ 服务管理脚本
```python
# prefect_service_manager.py
import subprocess
import sys
import time
import psutil

class PrefectServiceManager:
    def __init__(self):
        self.server_process = None
        self.scheduler_process = None
    
    def start_server(self):
        """启动 Prefect 服务器"""
        print("🚀 启动 Prefect 服务器...")
        self.server_process = subprocess.Popen(
            [sys.executable, "-m", "prefect", "server", "start"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(5)  # 等待服务器启动
        print("✅ Prefect 服务器已启动")
    
    def start_scheduler(self):
        """启动调度器"""
        print("📅 启动调度器...")
        self.scheduler_process = subprocess.Popen(
            [sys.executable, "prefect_scheduler.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✅ 调度器已启动")
    
    def stop_all(self):
        """停止所有服务"""
        print("🛑 停止所有 Prefect 服务...")
        
        # 查找并终止 Prefect 相关进程
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'prefect' in cmdline.lower():
                    proc.terminate()
                    print(f"🔄 终止进程: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        print("✅ 所有服务已停止")
    
    def status(self):
        """检查服务状态"""
        print("📊 Prefect 服务状态:")
        
        # 检查服务器状态
        try:
            import requests
            response = requests.get("http://127.0.0.1:4200/api/health")
            if response.status_code == 200:
                print("✅ Prefect 服务器: 运行中")
                print("   URL: http://127.0.0.1:4200")
            else:
                print("❌ Prefect 服务器: 异常")
        except:
            print("❌ Prefect 服务器: 未运行")
        
        # 检查进程
        prefect_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'prefect' in cmdline.lower():
                    prefect_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if prefect_processes:
            print(f"✅ Prefect 进程: {len(prefect_processes)} 个运行中")
            for proc in prefect_processes[:5]:  # 只显示前5个
                print(f"   PID {proc['pid']}: {' '.join(proc['cmdline'][:3])}...")
        else:
            print("❌ 没有运行中的 Prefect 进程")

def main():
    manager = PrefectServiceManager()
    
    if len(sys.argv) < 2:
        print("用法: python prefect_service_manager.py [start|stop|restart|status]")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_server()
        manager.start_scheduler()
    elif command == "stop":
        manager.stop_all()
    elif command == "restart":
        manager.stop_all()
        time.sleep(3)
        manager.start_server()
        manager.start_scheduler()
    elif command == "status":
        manager.status()
    else:
        print("未知命令。支持的命令: start, stop, restart, status")

if __name__ == "__main__":
    main()
```

### 📋 命令行操作
```bash
# 启动服务
python prefect_service_manager.py start

# 检查状态
python prefect_service_manager.py status

# 创建部署
python prefect_scheduler.py

# 手动执行流程
python -m prefect deployment run "数据拉取流程/数据拉取-手动执行"

# 查看部署列表
python -m prefect deployment ls

# 查看流程运行历史
python -m prefect flow-run ls --limit 10
```

---

## 最佳实践

### ✅ 代码组织
```
project/
├── flows/
│   ├── __init__.py
│   ├── data_extraction.py    # 数据拉取流程
│   ├── data_processing.py    # 数据处理流程
│   └── reporting.py          # 报告生成流程
├── tasks/
│   ├── __init__.py
│   ├── common.py            # 通用任务
│   ├── database.py          # 数据库操作
│   └── file_operations.py   # 文件操作
├── deployments/
│   ├── __init__.py
│   └── scheduler.py         # 部署配置
├── config/
│   ├── __init__.py
│   └── settings.py          # 配置文件
└── main.py                  # 主入口
```

### 🔧 配置管理
```python
# config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    database_url: str = "sqlite:///data.db"
    
    # API 配置
    api_timeout: int = 300
    api_retries: int = 3
    
    # 调度配置
    timezone: str = "Asia/Shanghai"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 📊 日志记录
```python
from prefect import get_run_logger

@task
def logged_task():
    logger = get_run_logger()
    
    logger.info("任务开始执行")
    try:
        # 任务逻辑
        result = do_something()
        logger.info(f"任务执行成功: {result}")
        return result
    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}")
        raise
```

### 🔒 错误处理
```python
from prefect.exceptions import SKIP, FAIL

@task(retries=3, retry_delay_seconds=60)
def robust_task():
    try:
        # 任务逻辑
        return result
    except TemporaryError:
        # 临时错误，可以重试
        raise
    except PermanentError:
        # 永久错误，不应重试
        raise FAIL("永久性错误，停止重试")
    except SkippableError:
        # 可跳过的错误
        raise SKIP("条件不满足，跳过执行")
```

---

## 🎯 总结

1. **Task** 是最小工作单元，**Flow** 是工作流容器
2. 使用装饰器 `@task` 和 `@flow` 定义组件
3. 通过 `Deployment` 创建可调度的实例
4. 使用服务管理脚本统一管理 Prefect 服务
5. 遵循最佳实践，保持代码清晰和可维护

现在你可以开始构建自己的 Prefect 工作流了！🚀