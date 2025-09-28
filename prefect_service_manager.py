#!/usr/bin/env python3
"""
Prefect服务管理器
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

class PrefectServiceManager:
    def __init__(self):
        self.work_dir = Path("D:/testyd")
        self.server_url = "http://127.0.0.1:4200"
        self.log_file = self.work_dir / "prefect_scheduler.log"
        
    def is_server_running(self):
        """检查Prefect服务器是否运行"""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def find_prefect_processes(self):
        """查找Prefect相关进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if ('prefect' in cmdline.lower() or 
                    'prefect_scheduler.py' in cmdline):
                    processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    
    def start_server(self):
        """启动Prefect服务器"""
        if self.is_server_running():
            print("✅ Prefect服务器已在运行")
            return True
            
        print("🚀 启动Prefect服务器...")
        try:
            # Windows下真正的后台启动，不创建窗口
            if os.name == 'nt':
                # 使用DETACHED_PROCESS标志创建完全独立的进程
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
            for i in range(30):  # 最多等待30秒
                if self.is_server_running():
                    print("✅ Prefect服务器启动成功！")
                    return True
                time.sleep(1)
                print(f"   等待中... ({i+1}/30)")
            
            print("❌ Prefect服务器启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 启动Prefect服务器失败: {e}")
            return False
    
    def start_scheduler(self):
        """启动Prefect调度器"""
        print("🚀 启动Prefect调度器...")
        try:
            # Windows下真正的后台启动，不创建窗口
            if os.name == 'nt':
                # 使用DETACHED_PROCESS标志创建完全独立的进程
                subprocess.Popen(
                    [sys.executable, "prefect_scheduler.py"],
                    cwd=self.work_dir,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    [sys.executable, "prefect_scheduler.py"],
                    cwd=self.work_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            print("✅ Prefect调度器启动成功！")
            return True
            
        except Exception as e:
            print(f"❌ 启动Prefect调度器失败: {e}")
            return False
    
    def stop_services(self):
        """停止所有Prefect服务"""
        print("🛑 停止Prefect服务...")
        
        processes = self.find_prefect_processes()
        if not processes:
            print("✅ 没有发现运行中的Prefect进程")
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
        
        print(f"✅ 已停止 {stopped_count} 个Prefect进程")
        return True
    
    def status(self):
        """检查服务状态"""
        print("📊 Prefect服务状态:")
        print("-" * 40)
        
        # 检查服务器状态
        if self.is_server_running():
            print("✅ Prefect服务器: 运行中")
            print(f"   URL: {self.server_url}")
        else:
            print("❌ Prefect服务器: 未运行")
        
        # 检查进程状态
        processes = self.find_prefect_processes()
        if processes:
            print(f"✅ Prefect进程: {len(processes)} 个运行中")
            for proc in processes:
                try:
                    cmdline = ' '.join(proc.cmdline())
                    print(f"   PID {proc.pid}: {cmdline[:80]}...")
                except:
                    print(f"   PID {proc.pid}: <无法获取命令行>")
        else:
            print("❌ Prefect进程: 无运行中进程")
        
        # 检查日志文件
        if self.log_file.exists():
            size = self.log_file.stat().st_size
            print(f"📝 日志文件: {self.log_file} ({size} bytes)")
        else:
            print("📝 日志文件: 不存在")
    
    def start_all(self):
        """启动完整的Prefect服务 - 真正后台运行"""
        print("=" * 60)
        print("🚀 启动Prefect数据拉取调度系统")
        print("=" * 60)
        
        # 启动服务器
        if not self.start_server():
            return False
        
        # 启动调度器
        if not self.start_scheduler():
            return False
        
        print("\n" + "=" * 60)
        print("✅ Prefect服务启动完成！")
        print("=" * 60)
        print(f"📊 可视化界面: {self.server_url}")
        print(f"📝 日志文件: {self.log_file}")
        print("\n💡 重要说明:")
        print("  - 服务已在后台运行，关闭此窗口不影响服务")
        print("  - 服务会持续运行直到手动停止或重启电脑")
        print("  - 查看状态: python prefect_service_manager.py status")
        print("  - 停止服务: python prefect_service_manager.py stop")
        print("  - 重启服务: python prefect_service_manager.py restart")
        print("=" * 60)
        
        return True

def main():
    manager = PrefectServiceManager()
    
    if len(sys.argv) < 2:
        print("=" * 60)
        print("🔧 Prefect服务管理器")
        print("=" * 60)
        print("用法: python prefect_service_manager.py [命令]")
        print("\n支持的命令:")
        print("  start   - 启动Prefect服务（后台运行）")
        print("  stop    - 停止所有Prefect服务")
        print("  status  - 查看服务运行状态")
        print("  restart - 重启Prefect服务")
        print("\n示例:")
        print("  python prefect_service_manager.py start")
        print("  python prefect_service_manager.py status")
        print("=" * 60)
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_all()
    elif command == "stop":
        manager.stop_services()
    elif command == "status":
        manager.status()
    elif command == "restart":
        print("🔄 重启Prefect服务...")
        manager.stop_services()
        time.sleep(3)  # 增加等待时间确保进程完全停止
        manager.start_all()
    else:
        print("❌ 未知命令。支持的命令: start, stop, status, restart")
        print("💡 使用 'python prefect_service_manager.py' 查看帮助")

if __name__ == "__main__":
    main()