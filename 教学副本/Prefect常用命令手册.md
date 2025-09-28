# Prefect 常用命令手册

## 📋 目录
1. [服务管理命令](#服务管理命令)
2. [部署管理命令](#部署管理命令)
3. [流程执行命令](#流程执行命令)
4. [监控查看命令](#监控查看命令)
5. [配置管理命令](#配置管理命令)
6. [开发调试命令](#开发调试命令)
7. [实用脚本命令](#实用脚本命令)

---

## 服务管理命令

### 🚀 启动 Prefect 服务器
```bash
# 启动服务器（前台运行）
python -m prefect server start

# 启动服务器（后台运行）
python -m prefect server start &

# 指定端口启动
python -m prefect server start --port 4200

# 指定主机和端口
python -m prefect server start --host 0.0.0.0 --port 4200
```

### 🔧 配置 Prefect API
```bash
# 设置 API URL
python -m prefect config set PREFECT_API_URL="http://127.0.0.1:4200/api"

# 查看当前配置
python -m prefect config view

# 重置配置
python -m prefect config unset PREFECT_API_URL
```

### 📊 检查服务状态
```bash
# 检查服务器连接
python -c "import requests; print('✅ 服务器运行中' if requests.get('http://127.0.0.1:4200/api/health').status_code == 200 else '❌ 服务器未运行')"
```

---

## 部署管理命令

### 📋 查看部署
```bash
# 列出所有部署
python -m prefect deployment ls

# 查看特定部署详情
python -m prefect deployment inspect "流程名/部署名"

# 按标签筛选部署
python -m prefect deployment ls --tag "生产"
```

### 🚀 创建和管理部署
```bash
# 从 Python 文件创建部署
python -m prefect deployment build flows.py:my_flow -n "我的部署" -t "生产"

# 应用部署配置
python -m prefect deployment apply deployment.yaml

# 删除部署
python -m prefect deployment delete "流程名/部署名"

# 暂停部署
python -m prefect deployment pause "流程名/部署名"

# 恢复部署
python -m prefect deployment resume "流程名/部署名"
```

### ⏰ 调度管理
```bash
# 设置 cron 调度
python -m prefect deployment set-schedule "流程名/部署名" --cron "0 8 * * *" --timezone "Asia/Shanghai"

# 清除调度
python -m prefect deployment clear-schedule "流程名/部署名"
```

---

## 流程执行命令

### ▶️ 手动执行
```bash
# 手动执行部署
python -m prefect deployment run "流程名/部署名"

# 带参数执行
python -m prefect deployment run "流程名/部署名" --param key1=value1 --param key2=value2

# 执行并等待完成
python -m prefect deployment run "流程名/部署名" --watch
```

### 🔄 批量执行
```bash
# 批量执行多个部署
for deployment in "部署1" "部署2" "部署3"; do
    python -m prefect deployment run "$deployment"
done
```

---

## 监控查看命令

### 📊 查看流程运行
```bash
# 查看最近的流程运行
python -m prefect flow-run ls

# 查看指定数量的运行记录
python -m prefect flow-run ls --limit 20

# 按状态筛选
python -m prefect flow-run ls --state "Running"
python -m prefect flow-run ls --state "Completed"
python -m prefect flow-run ls --state "Failed"

# 查看特定流程的运行记录
python -m prefect flow-run ls --flow-name "我的流程"
```

### 🔍 查看运行详情
```bash
# 查看特定运行的详情
python -m prefect flow-run inspect <run-id>

# 查看运行日志
python -m prefect flow-run logs <run-id>

# 实时跟踪运行日志
python -m prefect flow-run logs <run-id> --follow
```

### 📈 查看任务运行
```bash
# 查看任务运行列表
python -m prefect task-run ls

# 查看特定任务运行详情
python -m prefect task-run inspect <task-run-id>

# 查看任务运行日志
python -m prefect task-run logs <task-run-id>
```

### 🏷️ 查看流程和任务
```bash
# 查看所有流程
python -m prefect flow ls

# 查看流程详情
python -m prefect flow inspect <flow-id>

# 按标签筛选流程
python -m prefect flow ls --tag "数据处理"
```

---

## 配置管理命令

### ⚙️ 环境配置
```bash
# 查看所有配置
python -m prefect config view

# 设置配置项
python -m prefect config set PREFECT_LOGGING_LEVEL=DEBUG
python -m prefect config set PREFECT_API_URL="http://localhost:4200/api"

# 删除配置项
python -m prefect config unset PREFECT_LOGGING_LEVEL

# 查看配置文件位置
python -c "from prefect.settings import PREFECT_HOME; print(PREFECT_HOME.value())"
```

### 🔐 密钥管理
```bash
# 创建密钥块
python -c "
from prefect.blocks.system import Secret
secret = Secret(value='my-secret-value')
secret.save('my-secret')
"

# 使用密钥
python -c "
from prefect.blocks.system import Secret
secret = Secret.load('my-secret')
print(secret.get())
"
```

---

## 开发调试命令

### 🧪 本地测试
```bash
# 直接运行 Python 文件中的流程
python my_flows.py

# 使用 Prefect 运行流程
python -c "from my_flows import my_flow; my_flow()"
```

### 🔍 调试模式
```bash
# 启用调试日志
export PREFECT_LOGGING_LEVEL=DEBUG
python my_flows.py

# 或者在代码中设置
python -c "
import logging
logging.getLogger('prefect').setLevel(logging.DEBUG)
from my_flows import my_flow
my_flow()
"
```

### 📝 验证配置
```bash
# 验证流程定义
python -m prefect flow validate my_flows.py:my_flow

# 检查部署配置
python -m prefect deployment check deployment.yaml
```

---

## 实用脚本命令

### 🔄 服务管理脚本
```bash
# 使用自定义服务管理器
python prefect_service_manager.py start    # 启动服务
python prefect_service_manager.py stop     # 停止服务
python prefect_service_manager.py restart  # 重启服务
python prefect_service_manager.py status   # 查看状态
```

### 📊 批量操作脚本
```bash
# 批量创建部署
python prefect_scheduler.py

# 批量执行部署
python -c "
import subprocess
deployments = ['部署1', '部署2', '部署3']
for dep in deployments:
    subprocess.run(['python', '-m', 'prefect', 'deployment', 'run', dep])
"
```

### 🧹 清理脚本
```bash
# 清理失败的运行记录（保留最近100个）
python -c "
import subprocess
result = subprocess.run(['python', '-m', 'prefect', 'flow-run', 'ls', '--state', 'Failed'], 
                       capture_output=True, text=True)
# 解析结果并删除旧的失败记录
"

# 清理临时文件
rm -rf temp/
mkdir temp/
```

---

## 🔧 PowerShell 专用命令（Windows）

### 服务管理
```powershell
# 启动服务（后台）
Start-Process python -ArgumentList "-m", "prefect", "server", "start" -WindowStyle Hidden

# 检查进程
Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*prefect*"}

# 停止 Prefect 进程
Get-Process | Where-Object {$_.CommandLine -like "*prefect*"} | Stop-Process -Force
```

### 批量操作
```powershell
# 批量执行部署
$deployments = @("部署1", "部署2", "部署3")
foreach ($dep in $deployments) {
    python -m prefect deployment run $dep
    Start-Sleep -Seconds 5
}

# 监控执行状态
while ($true) {
    python -m prefect flow-run ls --limit 5
    Start-Sleep -Seconds 10
}
```

---

## 📋 常用组合命令

### 🚀 完整启动流程
```bash
# 1. 启动服务器
python -m prefect server start &

# 2. 等待服务器启动
sleep 5

# 3. 创建部署
python prefect_scheduler.py

# 4. 查看部署状态
python -m prefect deployment ls

# 5. 执行测试
python -m prefect deployment run "测试流程/测试部署"
```

### 📊 监控和调试流程
```bash
# 1. 查看最近运行
python -m prefect flow-run ls --limit 10

# 2. 查看失败的运行
python -m prefect flow-run ls --state "Failed"

# 3. 查看特定运行的日志
python -m prefect flow-run logs <run-id>

# 4. 重新执行失败的任务
python -m prefect deployment run "流程名/部署名"
```

### 🔄 日常维护流程
```bash
# 1. 检查服务状态
python prefect_service_manager.py status

# 2. 查看部署列表
python -m prefect deployment ls

# 3. 查看最近执行情况
python -m prefect flow-run ls --limit 20

# 4. 清理临时文件
rm -rf temp/* logs/*.log

# 5. 重启服务（如需要）
python prefect_service_manager.py restart
```

---

## 💡 使用技巧

### 🔍 快速查找
```bash
# 查找包含特定关键词的部署
python -m prefect deployment ls | grep "数据拉取"

# 查找失败的运行
python -m prefect flow-run ls --state "Failed" | head -10

# 查找特定时间的运行
python -m prefect flow-run ls | grep "2024-01-01"
```

### 📝 日志管理
```bash
# 实时查看日志
tail -f prefect_scheduler.log

# 查看错误日志
grep -i "error" prefect_scheduler.log

# 清理日志文件
> prefect_scheduler.log
```

### 🚀 性能优化
```bash
# 设置并发限制
python -m prefect config set PREFECT_TASK_RUN_CONCURRENCY_LIMIT=10

# 设置超时时间
python -m prefect config set PREFECT_TASK_RUN_TIMEOUT_SECONDS=3600

# 启用结果持久化
python -m prefect config set PREFECT_RESULTS_PERSIST_BY_DEFAULT=true
```

---

## 🆘 故障排除命令

### 🔧 常见问题诊断
```bash
# 检查 API 连接
curl http://127.0.0.1:4200/api/health

# 检查端口占用
netstat -an | grep 4200

# 查看 Python 进程
ps aux | grep python | grep prefect

# 检查磁盘空间
df -h

# 检查内存使用
free -h
```

### 🔄 重置和恢复
```bash
# 重置 Prefect 配置
rm -rf ~/.prefect/

# 重新初始化
python -m prefect config set PREFECT_API_URL="http://127.0.0.1:4200/api"

# 重新创建部署
python prefect_scheduler.py
```

---

## 📚 参考资源

- **官方文档**: https://docs.prefect.io/
- **API 参考**: https://docs.prefect.io/api-ref/
- **社区论坛**: https://discourse.prefect.io/
- **GitHub**: https://github.com/PrefectHQ/prefect

---

**💡 提示**: 将常用命令保存为脚本或别名，提高工作效率！