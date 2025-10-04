#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调度服务管理器
提供启动、停止、状态检查等功能
"""

import subprocess
import time
import sys
import os
import signal
import psutil
import requests
from pathlib import Path

class SchedulerManager:
    def __init__(self):
        self.work_dir = Path("D:/testyd/task_generator")
        self.server_url = "http://127.0.0.1:4200"
        self.log_file = self.work_dir / "scheduler.log"
        
    def is_server_running(self):
        """检查Prefect服务器是否运行"""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def find_scheduler_processes(self):
        """查找调度器相关进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if ('prefect' in cmdline.lower() or 
                    'scheduler_config.py' in cmdline or
                    'prefect_scheduler.py' in cmdline or
                    'worker start' in cmdline):
                    processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    
    def deploy_tasks(self):
        """部署任务到Prefect服务器"""
        print("📦 部署任务到Prefect服务器...")
        try:
            # 设置环境变量
            env = os.environ.copy()
            env['PREFECT_API_URL'] = f"{self.server_url}/api"
            
            # 运行部署脚本
            result = subprocess.run(
                [sys.executable, "scheduler_deploy.py"],
                cwd=self.work_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                encoding='utf-8',  # 明确指定编码
                errors='ignore'    # 忽略编码错误
            )
            
            if result.returncode == 0:
                print("✅ 任务部署成功！")
                # 显示部署结果的关键信息
                if result.stdout:
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        if 'successfully deployed' in line.lower() or '成功部署' in line:
                            print(f"   {line.strip()}")
                return True
            else:
                print("❌ 任务部署失败:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 任务部署超时（5分钟）")
            return False
        except Exception as e:
            print(f"❌ 任务部署失败: {e}")
            return False
    
    def start_server(self):
        """启动Prefect服务器"""
        if self.is_server_running():
            print("✅ Prefect服务器已在运行")
            return True
            
        print("🚀 启动Prefect服务器...")
        try:
            # Windows下真正的后台启动，不创建窗口
            if os.name == 'nt':
                subprocess.Popen(
                    [sys.executable, "-m", "prefect", "server", "start"],
                    cwd=self.work_dir,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    [sys.executable, "-m", "prefect", "server", "start"],
                    cwd=self.work_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # 等待服务器启动
            print("⏳ 等待服务器启动...")
            for i in range(30):
                if self.is_server_running():
                    print("✅ Prefect服务器启动成功！")
                    return True
                time.sleep(1)
                if (i + 1) % 5 == 0:
                    print(f"   等待中... ({i+1}/30)")
            
            print("❌ Prefect服务器启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 启动Prefect服务器失败: {e}")
            return False
    
    def start_worker(self):
        """启动Prefect Worker"""
        print("🚀 启动Prefect Worker...")
        try:
            # 设置环境变量
            env = os.environ.copy()
            env['PREFECT_API_URL'] = f"{self.server_url}/api"
            
            # Windows下真正的后台启动，不创建窗口
            if os.name == 'nt':
                # 使用 pythonw.exe 来避免创建控制台窗口
                python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not Path(python_exe).exists():
                    python_exe = sys.executable

                subprocess.Popen(
                    [python_exe, "-m", "prefect", "worker", "start", "--pool", "default-pool"],
                    cwd=self.work_dir,
                    env=env,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    [sys.executable, "-m", "prefect", "worker", "start", "--pool", "default-pool"],
                    cwd=self.work_dir,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            # 等待几秒确认进程启动
            print("⏳ 等待Worker启动...")
            time.sleep(5)

            # 检查进程是否启动
            processes = self.find_scheduler_processes()
            worker_running = any('worker start' in ' '.join(p.cmdline())
                               for p in processes)

            if worker_running:
                print("✅ Prefect Worker启动成功！")
                return True
            else:
                print("⚠️ Worker进程未检测到，但可能正在启动中...")
                print("   请稍后使用 'python scheduler_manager.py status' 检查状态")
                return True

        except Exception as e:
            print(f"❌ 启动Prefect Worker失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start_scheduler(self):
        """启动调度器（兼容旧版本）"""
        print("🚀 启动任务调度器...")
        try:
            # 创建日志文件（如果不存在）
            log_file = self.work_dir / "scheduler.log"
            log_file.touch(exist_ok=True)

            # Windows下真正的后台启动，不创建窗口
            if os.name == 'nt':
                # 使用 pythonw.exe 来避免创建控制台窗口
                python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not Path(python_exe).exists():
                    python_exe = sys.executable

                subprocess.Popen(
                    [python_exe, "scheduler_config.py"],
                    cwd=self.work_dir,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    [sys.executable, "scheduler_config.py"],
                    cwd=self.work_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            # 等待几秒确认进程启动
            print("⏳ 等待调度器启动...")
            time.sleep(3)

            # 检查进程是否启动
            processes = self.find_scheduler_processes()
            scheduler_running = any('scheduler_config.py' in ' '.join(p.cmdline())
                                   for p in processes)

            if scheduler_running:
                print("✅ 任务调度器启动成功！")
                return True
            else:
                print("⚠️ 调度器进程未检测到，但可能正在启动中...")
                print("   请稍后使用 'python scheduler_manager.py status' 检查状态")
                return True

        except Exception as e:
            print(f"❌ 启动任务调度器失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_services(self):
        """停止所有调度服务"""
        print("🛑 停止调度服务...")
        
        processes = self.find_scheduler_processes()
        if not processes:
            print("✅ 没有发现运行中的调度进程")
            return True
        
        stopped_count = 0
        for proc in processes:
            try:
                print(f"   停止进程 {proc.pid}: {proc.name()}")
                proc.terminate()
                proc.wait(timeout=5)
                stopped_count += 1
            except psutil.TimeoutExpired:
                print(f"   强制终止进程 {proc.pid}")
                proc.kill()
                stopped_count += 1
            except Exception as e:
                print(f"   停止进程 {proc.pid} 失败: {e}")
        
        print(f"✅ 已停止 {stopped_count} 个调度进程")
        return True
    
    def status(self):
        """检查服务状态"""
        print("📊 调度服务状态:")
        print("-" * 60)
        
        # 检查服务器状态
        if self.is_server_running():
            print("✅ Prefect服务器: 运行中")
            print(f"   URL: {self.server_url}")
        else:
            print("❌ Prefect服务器: 未运行")
        
        # 检查进程状态
        processes = self.find_scheduler_processes()
        if processes:
            print(f"✅ 调度进程: {len(processes)} 个运行中")
            for proc in processes:
                try:
                    cmdline = ' '.join(proc.cmdline())
                    # 只显示前80个字符
                    display_cmd = cmdline[:80] + '...' if len(cmdline) > 80 else cmdline
                    print(f"   PID {proc.pid}: {display_cmd}")
                except:
                    print(f"   PID {proc.pid}: <无法获取命令行>")
        else:
            print("❌ 调度进程: 无运行中进程")
        
        # 检查日志文件
        if self.log_file.exists():
            size = self.log_file.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"📝 日志文件: {self.log_file} ({size_mb:.2f} MB)")
        else:
            print("📝 日志文件: 不存在")
        
        print("-" * 60)
    
    def start_all(self):
        """启动完整的调度服务"""
        print("=" * 80)
        print("🚀 启动任务调度系统 (Prefect 3.0)")
        print("=" * 80)
        
        # 启动服务器
        if not self.start_server():
            return False
        
        # 等待2秒确保服务器完全启动
        time.sleep(2)
        
        # 部署任务
        if not self.deploy_tasks():
            print("⚠️ 任务部署失败，但继续启动Worker...")
        
        # 启动Worker
        if not self.start_worker():
            return False
        
        print("\n" + "=" * 80)
        print("✅ 调度服务启动完成！")
        print("=" * 80)
        print(f"📊 可视化界面: {self.server_url}")
        print(f"📝 日志文件: {self.log_file}")
        print("\n💡 重要说明:")
        print("  - 服务已在后台运行，关闭此窗口不影响服务")
        print("  - 服务会持续运行直到手动停止或重启电脑")
        print("  - 查看状态: python scheduler_manager.py status")
        print("  - 停止服务: python scheduler_manager.py stop")
        print("  - 重启服务: python scheduler_manager.py restart")
        print("  - 重新部署: python scheduler_manager.py deploy")
        print("=" * 80)
        
        return True

def main():
    manager = SchedulerManager()
    
    if len(sys.argv) < 2:
        print("=" * 80)
        print("🔧 任务调度服务管理器")
        print("=" * 80)
        print("用法: python scheduler_manager.py [命令]")
        print("\n支持的命令:")
        print("  start   - 启动调度服务（后台运行）")
        print("  stop    - 停止所有调度服务")
        print("  status  - 查看服务运行状态")
        print("  restart - 重启调度服务")
        print("  deploy  - 重新部署任务到服务器")
        print("  worker  - 仅启动Worker进程")
        print("\n示例:")
        print("  python scheduler_manager.py start")
        print("  python scheduler_manager.py status")
        print("  python scheduler_manager.py deploy")
        print("=" * 80)
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_all()
    elif command == "stop":
        manager.stop_services()
    elif command == "status":
        manager.status()
    elif command == "restart":
        print("🔄 重启调度服务...")
        manager.stop_services()
        time.sleep(3)
        manager.start_all()
    elif command == "deploy":
        print("📦 重新部署任务...")
        if manager.deploy_tasks():
            print("✅ 任务部署成功！")
        else:
            print("❌ 任务部署失败！")
    elif command == "worker":
        print("👷 启动Worker进程...")
        if manager.start_worker():
            print("✅ Worker启动成功！")
        else:
            print("❌ Worker启动失败！")
    else:
        print("❌ 未知命令。支持的命令: start, stop, status, restart, deploy, worker")
        print("💡 使用 'python scheduler_manager.py' 查看帮助")

if __name__ == "__main__":
    main()

