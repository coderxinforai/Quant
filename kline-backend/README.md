# K线图后端API服务

基于FastAPI的股票K线图数据API服务。

## 功能特性

- 股票列表查询（支持关键词搜索）
- 日K线数据查询（支持后复权/前复权/不复权）
- SSH隧道自动管理（连接WSL的ClickHouse）
- Redis缓存（智能TTL策略）
- 自动健康检查和重连

## 技术栈

- FastAPI 0.109.0
- ClickHouse Driver 0.2.6
- Redis 5.0.1
- Python 3.9+

## 安装与运行

### 1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

### 3. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --port 8000

# 生产模式（Gunicorn）
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 4. 访问文档

- Swagger文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API端点

### 获取股票列表

```http
GET /api/stocks/list?keyword=浦发&limit=50
```

### 获取K线数据

```http
GET /api/kline/data?code=600000.SH&start_date=2010-01-01&end_date=2010-12-31&adj_type=after
```

## 项目结构

```
kline-backend/
├── app/
│   ├── api/endpoints/       # API端点
│   ├── core/                # 核心配置
│   ├── db/                  # 数据库客户端
│   ├── schemas/             # Pydantic模型
│   ├── services/            # 业务逻辑
│   └── main.py              # FastAPI入口
├── legacy/                  # 原始代码参考
├── requirements.txt
└── .env
```

## 开发说明

后端代码从 `legacy/plot_kline_ssh.py` 迁移而来，保留了原有的SQL查询逻辑。
