# Git推送完整教学指南

## 基本流程

### 1. 初始化Git仓库
```bash
git init
```

### 2. 配置用户信息
```bash
git config --global user.name "你的用户名"
git config --global user.email "你的邮箱"
```

### 3. 添加文件到暂存区
```bash
git add .
```

### 4. 提交到本地仓库
```bash
git commit -m "初始提交"
```

### 5. 创建GitHub仓库
在GitHub网站上创建新仓库

### 6. 添加远程仓库（使用你的token）
```bash
git remote add origin https://用户名:你的token@github.com/用户名/仓库名.git
```

### 7. 推送到GitHub
```bash
git push -u origin master
```

## 网络优化配置

如果推送过程中遇到网络问题，可以尝试以下配置：

### 1. 使用HTTP/1.1协议
```bash
git config --global http.version HTTP/1.1
```

### 2. 禁用SSL验证（仅在必要时使用）
```bash
git config --global http.sslVerify false
```

### 3. 增加缓冲区大小
```bash
git config --global http.postBuffer 524288000
```

### 4. 设置超时时间
```bash
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999
```

## 常见问题解决

### 推送被拒绝
如果推送被拒绝，可能是因为：
1. 远程仓库有新的提交
2. 分支保护规则
3. 文件包含敏感信息

### 解决方案
1. 先拉取远程更新：`git pull origin master`
2. 检查并解决冲突
3. 重新推送：`git push origin master`