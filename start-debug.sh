#!/bin/bash

# K线图系统本地调试启动脚本
# 用法: ./start-debug.sh [component]
# 参数:
#   无参数: 启动所有服务 (SSH隧道 + 后端 + 前端)
#   tunnel: 仅启动SSH隧道
#   backend: 仅启动后端
#   frontend: 仅启动前端

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPONENT="${1:-all}"
BACKEND_PORT=8001
TUNNEL_PORT=18123

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

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查进程是否已运行
is_port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t > /dev/null 2>&1
}

# 启动SSH隧道
start_tunnel() {
    print_header "启动 SSH 隧道"

    if ps aux | grep "ssh -N -L $TUNNEL_PORT" | grep -v grep > /dev/null; then
        print_success "SSH隧道已在运行"
    else
        print_info "正在建立SSH隧道 (localhost:$TUNNEL_PORT → wsl:8123)..."
        ssh -N -L $TUNNEL_PORT:localhost:8123 wsl &
        sleep 2

        if ps aux | grep "ssh -N -L $TUNNEL_PORT" | grep -v grep > /dev/null; then
            print_success "SSH隧道已建立"
        else
            print_error "SSH隧道启动失败"
            return 1
        fi
    fi
    echo ""
}

# 启动后端
start_backend() {
    print_header "启动后端服务"

    if is_port_in_use $BACKEND_PORT; then
        print_warning "端口 $BACKEND_PORT 已被占用"
        print_info "已有进程在使用此端口，尝试使用该进程或停止它后重试"
        return 1
    fi

    print_info "启动 FastAPI 后端 (http://localhost:$BACKEND_PORT)..."
    cd "$SCRIPT_DIR/kline-backend"

    # 使用虚拟环境的完整路径来运行 python
    export PYTHONUNBUFFERED=1
    "$SCRIPT_DIR/kline-backend/venv/bin/python" -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --reload \
        --log-level info

    # 注: 这个函数在前台运行，不会返回
}

# 启动前端
start_frontend() {
    print_header "启动前端服务"

    print_info "启动 React 开发服务器..."
    cd "$SCRIPT_DIR/kline-frontend"

    # 检查端口是否被占用，npm 会自动尝试其他端口
    npm run dev

    # 注: 这个函数在前台运行，不会返回
}

# 启动所有服务
start_all() {
    print_header "K线图系统本地调试启动"
    echo ""

    # 启动SSH隧道（后台）
    start_tunnel
    if [ $? -ne 0 ]; then
        print_error "无法启动SSH隧道，中止启动"
        exit 1
    fi

    # 检查ClickHouse连接
    print_info "检查 ClickHouse 连接..."
    sleep 1
    if curl -s http://localhost:$TUNNEL_PORT > /dev/null 2>&1; then
        print_success "ClickHouse 连接正常"
    else
        print_warning "ClickHouse 连接检查超时，继续启动..."
    fi
    echo ""

    # 启动后端和前端（需要在不同终端）
    print_header "后续步骤"
    echo ""
    print_info "由于后端和前端需要独立的终端窗口，请在新终端中运行:"
    echo ""
    echo "  ${GREEN}后端:${NC}"
    echo "    cd $SCRIPT_DIR"
    echo "    ./start-debug.sh backend"
    echo ""
    echo "  ${GREEN}前端:${NC}"
    echo "    cd $SCRIPT_DIR"
    echo "    ./start-debug.sh frontend"
    echo ""
    echo "  ${GREEN}或同时启动（需要tmux或screen）:${NC}"
    echo "    tmux new-session -d -s quant -c $SCRIPT_DIR './start-debug.sh backend'"
    echo "    tmux new-window -t quant -c $SCRIPT_DIR './start-debug.sh frontend'"
    echo ""
    print_success "SSH隧道已启动，请按上述步骤启动后端和前端"
}

# 验证组件参数
case "$COMPONENT" in
    tunnel)
        start_tunnel
        ;;
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    all)
        start_all
        ;;
    *)
        echo "用法: $0 [component]"
        echo ""
        echo "参数:"
        echo "  all       - 启动所有服务 (默认)"
        echo "  tunnel    - 仅启动SSH隧道"
        echo "  backend   - 仅启动后端"
        echo "  frontend  - 仅启动前端"
        echo ""
        echo "示例:"
        echo "  $0              # 启动SSH隧道，给出启动后端和前端的指导"
        echo "  $0 backend      # 启动后端服务"
        echo "  $0 frontend     # 启动前端开发服务器"
        exit 1
        ;;
esac
