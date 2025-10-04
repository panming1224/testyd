@echo off
chcp 65001 >nul
cd /d D:\testyd\task_generator
echo ========================================
echo 启动任务调度系统
echo ========================================
echo.
python scheduler_manager.py start
echo.
echo 按任意键退出...
pause >nul

