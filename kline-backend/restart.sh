#!/bin/bash

# K线后端服务重启脚本
# 用法: ./restart.sh [foreground|background]
#   foreground (默认): 前台运行，显示日志
#   background: 后台运行，日志写入 server.log

MODE=${1:-foreground}

echo "========== 重启 K线后端服务 =========="

# 1. 停止现有服务
echo "1. 停止现有服务..."
PIDS=$(ps aux | grep uvicorn | grep "app.main:app" | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "   找到运行中的进程: $PIDS"
    kill $PIDS
    sleep 2

    # 强制杀死未响应的进程
    PIDS=$(ps aux | grep uvicorn | grep "app.main:app" | grep -v grep | awk '{print $2}')
    if [ -n "$PIDS" ]; then
        echo "   强制停止: $PIDS"
        kill -9 $PIDS
    fi
    echo "   ✅ 已停止"
else
    echo "   ℹ️  没有运行中的服务"
fi

# 2. 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 错误: 未找到虚拟环境 venv/"
    echo "   请先创建虚拟环境: python3 -m venv venv"
    exit 1
fi

# 3. 检查 SSH 隧道
TUNNEL_PID=$(ps aux | grep "ssh -N -L 18123:localhost:8123" | grep -v grep | awk '{print $2}')
if [ -z "$TUNNEL_PID" ]; then
    echo "⚠️  警告: SSH 隧道未运行"
    echo "   请先启动隧道: ssh -N -L 18123:localhost:8123 wsl &"
fi

# 4. 启动服务
echo "2. 启动后端服务..."
cd "$(dirname "$0")"

if [ "$MODE" = "background" ]; then
    echo "   模式: 后台运行"
    # 使用虚拟环境中的完整路径
    nohup ./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > server.log 2>&1 &
    PID=$!
    sleep 3

    # 检查是否启动成功
    if ps -p $PID > /dev/null; then
        echo "   ✅ 后端已启动 (PID: $PID)"
        echo "   📄 日志文件: server.log"
        echo "   查看日志: tail -f server.log"
    else
        echo "   ❌ 启动失败，查看日志:"
        tail -20 server.log
        exit 1
    fi
else
    echo "   模式: 前台运行 (按 Ctrl+C 停止)"
    echo ""
    source venv/bin/activate
    uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
fi

echo "========================================="
