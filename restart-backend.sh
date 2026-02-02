#!/bin/bash

# K线后端快捷重启脚本（项目根目录）
# 用法: ./restart-backend.sh [foreground|background]

cd "$(dirname "$0")/kline-backend"
./restart.sh "$@"
