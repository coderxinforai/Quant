#!/bin/bash

# K线图系统启动脚本

echo "========== K线图系统启动 =========="
echo ""

# 1. 启动SSH隧道
echo "1. 检查SSH隧道..."
if ps aux | grep "ssh -N -L 18123" | grep -v grep > /dev/null; then
    echo "   ✅ SSH隧道已运行"
else
    echo "   启动SSH隧道..."
    ssh -N -L 18123:localhost:8123 wsl &
    sleep 2
    echo "   ✅ SSH隧道已启动"
fi
echo ""

# 2. 启动后端
echo "2. 检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ 后端服务已运行"
else
    echo "   启动后端服务..."
    cd kline-backend
    source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
    cd ..
    sleep 3
    echo "   ✅ 后端服务已启动"
fi
echo ""

# 3. 启动前端
echo "3. 检查前端服务..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "   ✅ 前端服务已运行"
else
    echo "   启动前端服务..."
    cd kline-frontend
    nohup npm run dev > frontend.log 2>&1 &
    cd ..
    sleep 3
    echo "   ✅ 前端服务已启动"
fi
echo ""

# 4. 显示访问地址
echo "========== 系统已就绪 =========="
echo ""
echo "📊 前端界面: http://localhost:5173"
echo "📡 后端API:  http://localhost:8000"
echo "📖 API文档:  http://localhost:8000/docs"
echo ""
echo "提示: 在浏览器中打开前端地址开始使用"
echo "======================================"
