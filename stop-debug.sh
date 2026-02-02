#!/bin/bash

# K线图系统本地调试停止脚本
# 用法: ./stop-debug.sh [component]
# 参数:
#   无参数: 停止所有服务
#   tunnel: 仅停止SSH隧道
#   backend: 仅停止后端
#   frontend: 仅停止前端

COMPONENT="${1:-all}"
TUNNEL_PORT=18123
BACKEND_PORT=8001

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_header() {
    echo -e "${BLUE}========== $1 ==========${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 停止进程
kill_process() {
    local pattern=$1
    local name=$2

    pids=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}')
    if [ ! -z "$pids" ]; then
        echo "$pids" | xargs kill -15 2>/dev/null
        sleep 1
        # 如果还没停止，使用 -9 强制杀死
        remaining=$(echo "$pids" | xargs ps -p 2>/dev/null | wc -l)
        if [ $remaining -gt 1 ]; then
            echo "$pids" | xargs kill -9 2>/dev/null
        fi
        print_success "$name 已停止"
    else
        print_warning "$name 未运行"
    fi
}

# 停止SSH隧道
stop_tunnel() {
    print_info "停止SSH隧道..."
    kill_process "ssh -N -L $TUNNEL_PORT" "SSH隧道"
}

# 停止后端
stop_backend() {
    print_info "停止后端服务..."
    kill_process "uvicorn app.main:app" "后端服务"
}

# 停止前端
stop_frontend() {
    print_info "停止前端服务..."
    # Vite 前端进程名称可能是 node 或 vite
    kill_process "vite" "前端服务"
    kill_process "npm run dev" "前端服务"
}

# 停止所有服务
stop_all() {
    print_header "K线图系统停止"
    echo ""

    print_info "停止前端服务..."
    kill_process "vite" "前端服务"
    kill_process "npm run dev" "前端服务"
    echo ""

    print_info "停止后端服务..."
    kill_process "uvicorn app.main:app" "后端服务"
    echo ""

    print_info "停止SSH隧道..."
    kill_process "ssh -N -L $TUNNEL_PORT" "SSH隧道"
    echo ""

    print_header "所有服务已停止"
}

# 验证组件参数
case "$COMPONENT" in
    tunnel)
        print_header "停止SSH隧道"
        echo ""
        stop_tunnel
        ;;
    backend)
        print_header "停止后端服务"
        echo ""
        stop_backend
        ;;
    frontend)
        print_header "停止前端服务"
        echo ""
        stop_frontend
        ;;
    all)
        stop_all
        ;;
    *)
        echo "用法: $0 [component]"
        echo ""
        echo "参数:"
        echo "  all       - 停止所有服务 (默认)"
        echo "  tunnel    - 仅停止SSH隧道"
        echo "  backend   - 仅停止后端"
        echo "  frontend  - 仅停止前端"
        echo ""
        echo "示例:"
        echo "  $0              # 停止所有服务"
        echo "  $0 backend      # 停止后端服务"
        echo "  $0 frontend     # 停止前端开发服务器"
        exit 1
        ;;
esac
