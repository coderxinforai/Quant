#!/bin/bash

# K线后端停止脚本
# 用法: ./stop-backend.sh

echo "========== 停止 K线后端服务 =========="

PIDS=$(ps aux | grep uvicorn | grep "app.main:app" | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "找到运行中的进程: $PIDS"
    kill $PIDS
    sleep 2

    # 强制杀死未响应的进程
    PIDS=$(ps aux | grep uvicorn | grep "app.main:app" | grep -v grep | awk '{print $2}')
    if [ -n "$PIDS" ]; then
        echo "强制停止: $PIDS"
        kill -9 $PIDS
    fi
    echo "✅ 后端服务已停止"
else
    echo "ℹ️  没有运行中的后端服务"
fi

echo "======================================"
