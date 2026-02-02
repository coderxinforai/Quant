# K线图系统 - 本地调试快速指南

## 快速开始（30秒）

```bash
# 终端 1: 启动SSH隧道
./start-debug.sh tunnel

# 终端 2: 启动后端
./start-debug.sh backend

# 终端 3: 启动前端
./start-debug.sh frontend

# 打开浏览器访问
# http://localhost:5173
```

## 停止服务

```bash
# 任意终端执行（会停止所有服务）
./stop-debug.sh
```

## 常见问题

### 问题1：端口被占用
如果看到 `Address already in use` 错误：

```bash
# 停止所有服务
./stop-debug.sh all

# 重新启动
./start-debug.sh tunnel
./start-debug.sh backend      # 新终端
./start-debug.sh frontend     # 新终端
```

### 问题2：无法连接到ClickHouse
- 确保 SSH 隧道正在运行：`ps aux | grep "ssh -N -L 18123"`
- 检查 WSL 连接：`ssh -v wsl 'echo OK'`
- 查看后端日志，找出具体错误信息

### 问题3：前端访问超时
- 刷新浏览器，等待前端加载完成
- 检查前端是否正确启动：`./start-debug.sh frontend`
- 查看网络标签页，确保 API 调用成功

## 完整服务检查

```bash
# 检查SSH隧道
ps aux | grep "ssh -N -L 18123" | grep -v grep

# 检查后端运行
curl http://localhost:8001/health

# 检查前端运行
curl http://localhost:5173/

# 查看后端日志
tail -f kline-backend/server.log
```

## 开发工作流

### 仅修改后端 API

```bash
# 修改代码后，后端会自动重新加载 (--reload 模式)
# 前端的 API 调用会自动请求新的数据
# 不需要重启任何服务
```

### 仅修改前端界面

```bash
# Vite 开发服务器会自动检测文件变化并热更新
# 浏览器会自动刷新
# 不需要重启任何服务
```

### 修改数据库相关代码

```bash
# 如果修改了ClickHouse连接逻辑：
./stop-debug.sh backend
./start-debug.sh backend     # 新终端

# 刷新浏览器测试
```

## 脚本说明

### start-debug.sh

启动本地调试服务

```bash
# 启动SSH隧道（后台运行）
./start-debug.sh tunnel

# 启动后端（前台运行，便于查看日志）
./start-debug.sh backend

# 启动前端（前台运行，便于查看日志）
./start-debug.sh frontend

# 启动所有服务（仅启动隧道，给出指导）
./start-debug.sh
# 或
./start-debug.sh all
```

### stop-debug.sh

停止本地调试服务

```bash
# 停止所有服务
./stop-debug.sh

# 或分别停止
./stop-debug.sh tunnel
./stop-debug.sh backend
./stop-debug.sh frontend
```

## 端口说明

| 服务 | 端口 | 用途 |
|------|------|------|
| 前端 | 5173 | React 开发服务器 |
| 后端 | 8001 | FastAPI 应用 |
| SSH 隧道 | 18123 | 本地访问远程 ClickHouse |

## API 文档

启动后端后，访问：`http://localhost:8001/docs`

## 更多信息

详见 [CLAUDE.md](./CLAUDE.md) 中的调试脚本参考部分。
