#!/bin/bash

# K线图系统一键启动脚本（单窗口）
# 用法: ./start-simple.sh
# 说明:
#   - SSH隧道 + 后端在后台运行（日志文件保存）
#   - 前端在前台运行（可见输出）
#   - 所有服务在一个终端窗口中启动

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT=8001
TUNNEL_PORT=18123

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========== $1 ==========${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 清理函数（当脚本退出时）
cleanup() {
    echo ""
    print_header "清理服务"
    print_info "停止所有服务..."

    # 停止前端（已在前台，Ctrl-C自动停止）

    # 停止后端
    pids=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')
    if [ ! -z "$pids" ]; then
        echo "$pids" | xargs kill 2>/dev/null || true
        print_success "后端已停止"
    fi

    # 停止SSH隧道
    pids=$(ps aux | grep "ssh -N -L $TUNNEL_PORT" | grep -v grep | awk '{print $2}')
    if [ ! -z "$pids" ]; then
        echo "$pids" | xargs kill 2>/dev/null || true
        print_success "SSH隧道已停止"
    fi

    print_header "所有服务已停止"
}

# 注册退出处理
trap cleanup EXIT

print_header "K线图系统一键启动"
echo ""

# 1. 启动SSH隧道
print_info "启动 SSH 隧道..."
if ps aux | grep "ssh -N -L $TUNNEL_PORT" | grep -v grep > /dev/null; then
    print_success "SSH隧道已在运行"
else
    ssh -N -L $TUNNEL_PORT:localhost:8123 wsl > /dev/null 2>&1 &
    sleep 2
    print_success "SSH隧道已启动"
fi
echo ""

# 2. 启动后端（后台）
print_info "启动后端服务..."
cd "$SCRIPT_DIR/kline-backend"

# 检查端口是否被占用
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t > /dev/null 2>&1; then
    print_success "后端已在运行"
else
    # 后台启动后端，日志写入文件
    export PYTHONUNBUFFERED=1
    "$SCRIPT_DIR/kline-backend/venv/bin/python" -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --reload \
        --log-level info > "$SCRIPT_DIR/kline-backend/server.log" 2>&1 &

    sleep 3

    # 检查后端是否启动成功
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        print_success "后端已启动 (http://localhost:$BACKEND_PORT)"
    else
        print_info "后端启动中，查看日志: tail -f kline-backend/server.log"
    fi
fi
echo ""

# 3. 显示访问信息
print_header "服务已启动"
echo ""
echo "  ${GREEN}前端地址:${NC} http://localhost:5173"
echo "  ${GREEN}后端API:${NC} http://localhost:$BACKEND_PORT"
echo "  ${GREEN}API文档:${NC} http://localhost:$BACKEND_PORT/docs"
echo ""
echo "  ${YELLOW}查看后端日志:${NC}"
echo "    tail -f kline-backend/server.log"
echo ""
echo "  ${YELLOW}停止所有服务:${NC}"
echo "    按 Ctrl-C 停止前端，所有服务会自动清理"
echo ""
print_header "启动前端开发服务器"
echo ""

# 4. 启动前端（前台）
cd "$SCRIPT_DIR/kline-frontend"
npm run dev
