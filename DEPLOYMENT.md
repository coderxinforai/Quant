# K线图系统部署文档

## 部署架构

```
Mac开发环境                    WSL生产环境 (192.168.50.90)
┌─────────────────┐           ┌──────────────────────────┐
│ 前端: vite dev  │  ──────→  │ Nginx: 静态文件托管      │
│ 后端: uvicorn   │  ──────→  │ Gunicorn: FastAPI服务    │
│ SSH隧道         │           │ ClickHouse: 8123         │
└─────────────────┘           │ Redis: 6379              │
                              └──────────────────────────┘
                                        ↑
                                  局域网访问
                             http://192.168.50.90
```

## 前置条件

### WSL环境检查

```bash
# SSH登录WSL
ssh wsl
# 或
ssh lee@192.168.50.90

# 检查系统
uname -a
# 应显示：Linux DESKTOP-0T135LG ...

# 检查Python版本
python3 --version
# 需要 >= 3.9

# 检查服务状态
systemctl status clickhouse-server
systemctl status redis-server
```

## 第一步：传输文件到WSL

### 在Mac上执行

```bash
# 1. 打包前端构建产物
cd /Users/lixinfei/workspace/Quant/kline-frontend
tar -czf dist.tar.gz dist/

# 2. 传输前端到WSL
scp dist.tar.gz wsl:/tmp/

# 3. 打包后端代码
cd /Users/lixinfei/workspace/Quant
tar -czf kline-backend.tar.gz kline-backend/ \
  --exclude='kline-backend/venv' \
  --exclude='kline-backend/__pycache__' \
  --exclude='kline-backend/.env' \
  --exclude='kline-backend/logs'

# 4. 传输后端到WSL
scp kline-backend.tar.gz wsl:/tmp/
```

## 第二步：WSL上部署后端

### SSH登录WSL

```bash
ssh wsl
```

### 安装系统依赖

```bash
# 更新包列表
sudo apt update

# 安装Nginx
sudo apt install nginx -y

# 检查Redis（通常已安装）
sudo systemctl status redis-server
# 如果未安装：sudo apt install redis-server -y

# 安装Python开发包
sudo apt install python3-pip python3-venv -y
```

### 部署后端应用

```bash
# 1. 解压后端代码
cd ~
tar -xzf /tmp/kline-backend.tar.gz

# 2. 创建Python虚拟环境
cd ~/kline-backend
python3 -m venv venv

# 3. 激活虚拟环境并安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. 安装Gunicorn（生产WSGI服务器）
pip install gunicorn

# 5. 复制生产环境配置
cp .env.production .env

# 6. 测试启动（前台运行）
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 访问测试：
# curl http://localhost:8000/health
# 应返回：{"status":"ok","ssh_tunnel":false}

# Ctrl+C 停止测试
```

### 配置Systemd服务

```bash
# 1. 复制systemd服务文件
sudo cp ~/kline-backend/deploy/systemd/kline-backend.service /etc/systemd/system/

# 2. 修改用户名（如果不是lee）
sudo nano /etc/systemd/system/kline-backend.service
# 修改User和Group为你的用户名

# 3. 重载systemd
sudo systemctl daemon-reload

# 4. 启用服务（开机自启）
sudo systemctl enable kline-backend

# 5. 启动服务
sudo systemctl start kline-backend

# 6. 检查状态
sudo systemctl status kline-backend

# 7. 查看日志
sudo journalctl -u kline-backend -f
```

### 验证后端服务

```bash
# 健康检查
curl http://localhost:8000/health

# 测试API
curl "http://localhost:8000/api/stocks/list?keyword=浦发&limit=5"
```

## 第三步：部署前端到Nginx

### 部署静态文件

```bash
# 1. 创建网站目录
sudo mkdir -p /var/www/html/kline

# 2. 解压前端文件
cd /tmp
tar -xzf dist.tar.gz

# 3. 复制到网站目录
sudo cp -r dist/* /var/www/html/kline/

# 4. 设置权限
sudo chown -R www-data:www-data /var/www/html/kline

# 5. 验证文件
ls -l /var/www/html/kline
# 应该看到：index.html, assets/, vite.svg
```

### 配置Nginx

```bash
# 1. 复制Nginx配置
sudo cp ~/kline-backend/deploy/nginx/kline.conf /etc/nginx/sites-available/

# 2. 创建软链接启用站点
sudo ln -s /etc/nginx/sites-available/kline.conf /etc/nginx/sites-enabled/

# 3. 删除默认站点（可选）
sudo rm /etc/nginx/sites-enabled/default

# 4. 测试Nginx配置
sudo nginx -t

# 5. 重载Nginx
sudo systemctl reload nginx

# 6. 检查Nginx状态
sudo systemctl status nginx
```

## 第四步：验证部署

### 在WSL上验证

```bash
# 1. 检查前端
curl -I http://localhost

# 2. 检查API
curl http://localhost/api/stocks/list?keyword=浦发

# 3. 检查健康状态
curl http://localhost/health
```

### 在Mac上验证

```bash
# 1. 健康检查
curl http://192.168.50.90/health

# 2. 测试API
curl "http://192.168.50.90/api/stocks/list?keyword=%E6%B5%A6%E5%8F%91&limit=5"

# 3. 浏览器访问
open http://192.168.50.90
```

### 在浏览器中测试

1. 访问：http://192.168.50.90
2. 搜索股票："600000" 或 "浦发"
3. 选择股票后自动加载K线图
4. 拖动底部滑块测试时间范围选择
5. 打开日志面板（右下角📋按钮）查看运行日志

## 常见问题排查

### 后端无法启动

```bash
# 查看详细日志
sudo journalctl -u kline-backend -n 50 --no-pager

# 检查端口占用
sudo lsof -i:8000

# 检查ClickHouse连接
clickhouse-client --query "SELECT 1"

# 检查Redis连接
redis-cli ping
```

### Nginx 502错误

```bash
# 检查后端服务状态
sudo systemctl status kline-backend

# 检查Nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 检查后端是否监听8000端口
netstat -tlnp | grep 8000
```

### 前端白屏或404

```bash
# 检查文件是否存在
ls -l /var/www/html/kline/

# 检查Nginx配置
sudo nginx -t

# 查看Nginx访问日志
sudo tail -f /var/log/nginx/access.log
```

### API请求失败

```bash
# 检查后端日志
tail -f ~/kline-backend/logs/app.log

# 检查Gunicorn日志
tail -f ~/kline-backend/logs/gunicorn-error.log

# 检查Nginx代理配置
sudo cat /etc/nginx/sites-enabled/kline.conf | grep -A 10 "location /api"
```

## 服务管理命令

### 后端服务

```bash
# 启动
sudo systemctl start kline-backend

# 停止
sudo systemctl stop kline-backend

# 重启
sudo systemctl restart kline-backend

# 查看状态
sudo systemctl status kline-backend

# 查看日志
sudo journalctl -u kline-backend -f
```

### Nginx服务

```bash
# 重载配置（不中断服务）
sudo systemctl reload nginx

# 重启
sudo systemctl restart nginx

# 测试配置
sudo nginx -t
```

## 更新部署

### 更新前端

```bash
# Mac上重新构建
cd /Users/lixinfei/workspace/Quant/kline-frontend
npm run build
tar -czf dist.tar.gz dist/
scp dist.tar.gz wsl:/tmp/

# WSL上更新
cd /tmp
tar -xzf dist.tar.gz
sudo rm -rf /var/www/html/kline/*
sudo cp -r dist/* /var/www/html/kline/
sudo chown -R www-data:www-data /var/www/html/kline
```

### 更新后端

```bash
# Mac上打包
cd /Users/lixinfei/workspace/Quant
tar -czf kline-backend.tar.gz kline-backend/ --exclude='kline-backend/venv'
scp kline-backend.tar.gz wsl:/tmp/

# WSL上更新
cd ~
# 备份旧版本
mv kline-backend kline-backend.bak.$(date +%Y%m%d)
tar -xzf /tmp/kline-backend.tar.gz
cd kline-backend

# 复用旧的虚拟环境（如果依赖没变）
cp -r ~/kline-backend.bak.*/venv .
# 或重新创建
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo systemctl restart kline-backend
```

## 监控和维护

### 日志位置

```bash
# 应用日志
~/kline-backend/logs/app.log
~/kline-backend/logs/error.log

# Gunicorn日志
~/kline-backend/logs/gunicorn-access.log
~/kline-backend/logs/gunicorn-error.log

# Nginx日志
/var/log/nginx/access.log
/var/log/nginx/error.log

# Systemd日志
sudo journalctl -u kline-backend
```

### 性能监控

```bash
# 检查CPU和内存使用
htop

# 检查磁盘使用
df -h

# 检查日志文件大小
du -sh ~/kline-backend/logs/*

# 检查网络连接
netstat -tlnp | grep -E '(8000|80|6379|8123)'
```

### 日志清理

```bash
# 清理旧日志（保留最近7天）
find ~/kline-backend/logs -name "*.log" -type f -mtime +7 -delete

# 或使用logrotate自动管理
```

## 安全建议

1. **防火墙配置**（可选）
   ```bash
   # 只允许局域网访问
   sudo ufw allow from 192.168.50.0/24 to any port 80
   sudo ufw enable
   ```

2. **定期更新**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

3. **备份数据库**
   ```bash
   # ClickHouse备份
   clickhouse-client --query "BACKUP DATABASE stock TO Disk('backups', 'stock_backup.zip')"
   ```

## 性能优化

1. **Nginx Gzip压缩**
   ```nginx
   # 在/etc/nginx/nginx.conf中启用
   gzip on;
   gzip_types text/plain text/css application/json application/javascript;
   ```

2. **增加Gunicorn工作进程**
   ```bash
   # 修改 /etc/systemd/system/kline-backend.service
   # 将 -w 4 改为 -w 8（根据CPU核心数调整）
   ```

3. **Redis持久化配置**
   ```bash
   # 编辑 /etc/redis/redis.conf
   save 900 1
   save 300 10
   save 60 10000
   ```

---

**部署完成后访问**: http://192.168.50.90

**技术支持**: 查看 `/Users/lixinfei/workspace/Quant/PROJECT_SUMMARY.md`
