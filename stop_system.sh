#!/bin/bash

# K线图系统停止脚本

echo "========== 停止K线图系统 =========="
echo ""

# 1. 停止前端
echo "1. 停止前端服务..."
pids=$(ps aux | grep "vite" | grep -v grep | awk '{print $2}')
if [ ! -z "$pids" ]; then
    echo "$pids" | xargs kill
    echo "   ✅ 前端服务已停止"
else
    echo "   ⚠️  前端服务未运行"
fi
echo ""

# 2. 停止后端
echo "2. 停止后端服务..."
pids=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')
if [ ! -z "$pids" ]; then
    echo "$pids" | xargs kill
    echo "   ✅ 后端服务已停止"
else
    echo "   ⚠️  后端服务未运行"
fi
echo ""

# 3. 停止SSH隧道
echo "3. 停止SSH隧道..."
pids=$(ps aux | grep "ssh -N -L 18123" | grep -v grep | awk '{print $2}')
if [ ! -z "$pids" ]; then
    echo "$pids" | xargs kill
    echo "   ✅ SSH隧道已停止"
else
    echo "   ⚠️  SSH隧道未运行"
fi
echo ""

echo "======================================"
echo "系统已完全停止"
echo "======================================"
