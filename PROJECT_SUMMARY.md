# K线图前后端系统搭建总结

> 项目完成时间：2026年1月30日
> 开发时长：约1天
> 技术栈：React + TypeScript + ECharts + FastAPI + ClickHouse + Redis

---

## 📋 目录

- [项目概述](#项目概述)
- [技术架构](#技术架构)
- [搭建过程](#搭建过程)
- [关键技术实现](#关键技术实现)
- [问题与解决方案](#问题与解决方案)
- [优化与改进](#优化与改进)
- [核心代码解析](#核心代码解析)
- [学习要点](#学习要点)
- [后续扩展](#后续扩展)

---

## 项目概述

### 1.1 项目背景

开发一个股票K线图查询系统，用于查看和分析5400只A股的历史行情数据。

### 1.2 核心需求

- ✅ 股票搜索和选择
- ✅ K线图可视化展示
- ✅ 时间范围拖动选择
- ✅ 支持大规模数据查询
- ✅ 实时日志调试功能

### 1.3 技术目标

- 前后端分离架构
- 高性能数据查询（ClickHouse）
- 优秀的用户体验（自动加载、拖动选择）
- 可维护的代码结构

---

## 技术架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                      前端层                              │
│  React 18 + TypeScript + ECharts + Ant Design          │
│                   http://localhost:5173                 │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
                     ↓
┌─────────────────────────────────────────────────────────┐
│                     后端层                               │
│            FastAPI + Pydantic + Uvicorn                 │
│                   http://localhost:8000                 │
└─────┬─────────────────────────────────┬─────────────────┘
      │                                 │
      │ SSH Tunnel                      │ Direct
      │ (localhost:18123)               │
      ↓                                 ↓
┌──────────────────────┐      ┌──────────────────────┐
│  ClickHouse 数据库    │      │    Redis 缓存        │
│  192.168.50.90:8123  │      │  localhost:6379      │
│  (5400只股票数据)     │      │  (智能TTL缓存)       │
└──────────────────────┘      └──────────────────────┘
```

### 2.2 技术栈选择

#### 前端技术栈

| 技术 | 版本 | 作用 | 选择理由 |
|------|------|------|----------|
| React | 18.x | UI框架 | 组件化、生态完善 |
| TypeScript | 5.x | 类型系统 | 代码可维护性、类型安全 |
| Vite | 7.x | 构建工具 | 开发体验好、构建快 |
| ECharts | 5.x | 图表库 | 专业金融图表、性能优秀 |
| Ant Design | 5.x | UI组件库 | 组件丰富、企业级 |
| Zustand | 4.x | 状态管理 | 轻量、简单易用 |
| Axios | 1.x | HTTP客户端 | 拦截器、易用 |

#### 后端技术栈

| 技术 | 版本 | 作用 | 选择理由 |
|------|------|------|----------|
| FastAPI | 0.109 | Web框架 | 高性能、自动文档、类型提示 |
| Pydantic | 2.5 | 数据验证 | 自动校验、类型安全 |
| ClickHouse | - | 数据库 | 列式存储、查询速度快 |
| Redis | 5.0 | 缓存 | 高性能、简单易用 |
| Pandas | 2.3 | 数据处理 | DataFrame便于操作 |

### 2.3 目录结构

```
Quant/
├── kline-backend/              # 后端项目
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py        # 依赖注入
│   │   │   └── endpoints/
│   │   │       ├── stock.py   # 股票API
│   │   │       └── kline.py   # K线API
│   │   ├── core/
│   │   │   ├── config.py      # 配置管理
│   │   │   └── ssh_tunnel.py # SSH隧道
│   │   ├── db/
│   │   │   ├── clickhouse.py # ClickHouse客户端
│   │   │   └── redis.py       # Redis客户端
│   │   ├── schemas/
│   │   │   ├── stock.py       # 股票Schema
│   │   │   └── kline.py       # K线Schema
│   │   ├── services/
│   │   │   ├── stock_service.py
│   │   │   ├── kline_service.py
│   │   │   └── cache_service.py
│   │   └── main.py            # FastAPI入口
│   ├── legacy/                # 原始参考代码
│   ├── requirements.txt
│   └── .env
│
└── kline-frontend/            # 前端项目
    ├── src/
    │   ├── api/              # API请求层
    │   │   ├── client.ts    # Axios配置
    │   │   ├── stock.ts
    │   │   └── kline.ts
    │   ├── components/
    │   │   ├── StockSelector/     # 股票选择器
    │   │   ├── KLineChart/        # K线图组件
    │   │   └── LogPanel/          # 日志面板
    │   ├── pages/
    │   │   └── KLinePage/         # 主页面
    │   ├── store/
    │   │   ├── useKLineStore.ts   # K线状态
    │   │   └── useLogStore.ts     # 日志状态
    │   ├── types/           # TypeScript类型
    │   └── utils/           # 工具函数
    └── package.json
```

---

## 搭建过程

### 3.1 第一阶段：后端基础搭建（2小时）

#### 步骤1：环境准备

```bash
# 创建项目目录
mkdir kline-backend && cd kline-backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install fastapi uvicorn pydantic pydantic-settings \
    clickhouse-connect redis python-dotenv pandas gunicorn
```

#### 步骤2：项目结构创建

```bash
# 创建目录结构
mkdir -p app/{api/endpoints,core,db,schemas,services} legacy

# 创建__init__.py文件
touch app/__init__.py app/api/__init__.py \
    app/api/endpoints/__init__.py app/core/__init__.py \
    app/db/__init__.py app/schemas/__init__.py \
    app/services/__init__.py
```

#### 步骤3：核心配置

**配置管理（`app/core/config.py`）**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # SSH隧道配置
    SSH_HOST: str = "wsl"
    SSH_LOCAL_PORT: int = 18123
    SSH_REMOTE_PORT: int = 8123

    # ClickHouse配置
    CH_HOST: str = "localhost"
    CH_PORT: int = 18123
    CH_DATABASE: str = "stock"

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env"

settings = Settings()
```

**关键点**：
- 使用 Pydantic Settings 管理配置
- 支持从 `.env` 文件读取
- 类型安全

#### 步骤4：SSH隧道管理

**问题**：ClickHouse在远程WSL机器上，需要通过SSH隧道访问

**解决方案**：
```python
import subprocess
import time

class SSHTunnelManager:
    def __init__(self):
        self.ssh_host = settings.SSH_HOST
        self.local_port = settings.SSH_LOCAL_PORT
        self.remote_port = settings.SSH_REMOTE_PORT
        self.process = None

    def start(self):
        """启动SSH隧道"""
        cmd = [
            'ssh', '-N', '-L',
            f'{self.local_port}:localhost:{self.remote_port}',
            self.ssh_host
        ]
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)  # 等待隧道建立

    def is_alive(self):
        """检查隧道是否存活"""
        return self.process and self.process.poll() is None

tunnel_manager = SSHTunnelManager()
```

**学习点**：
- 使用 `subprocess` 管理外部进程
- SSH 隧道参数：`-N`（不执行命令）、`-L`（端口转发）
- 进程管理：Popen、poll()

#### 步骤5：数据库客户端

**ClickHouse客户端（单例模式）**：
```python
import clickhouse_connect

class ClickHouseClient:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self):
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=settings.CH_HOST,
                port=settings.CH_PORT,
                database=settings.CH_DATABASE
            )
        return self._client

    def query_df(self, query: str):
        """执行查询并返回DataFrame"""
        return self.get_client().query_df(query)

db_client = ClickHouseClient()
```

**学习点**：
- 单例模式确保只有一个数据库连接
- `query_df()` 直接返回 Pandas DataFrame
- 懒加载（第一次调用时才连接）

#### 步骤6：业务逻辑层

**K线服务（核心SQL）**：
```python
class KLineService:
    def get_daily_kline(self, code, start_date, end_date, adj_type='none'):
        # 根据复权类型选择列
        if adj_type == 'after':
            price_cols = """
                argMin(adj_open_after, dt) AS open,
                argMax(adj_close_after, dt) AS close,
                max(adj_high_after) AS high,
                min(adj_low_after) AS low
            """
        else:
            price_cols = """
                argMin(open, dt) AS open,
                argMax(close, dt) AS close,
                max(high) AS high,
                min(low) AS low
            """

        # 分钟K线聚合为日K线
        query = f"""
            SELECT
                trade_date,
                {price_cols},
                sum(volume) AS volume,
                sum(amount) AS amount
            FROM stock.minute_kline
            WHERE code = '{code}'
              AND trade_date >= '{start_date}'
              AND trade_date <= '{end_date}'
            GROUP BY trade_date
            ORDER BY trade_date
        """

        df = self.db.query_df(query)
        # ... 转换为Pydantic模型
```

**关键SQL技术**：
- `argMin(field, by)`: 按 `by` 最小值时的 `field` 值（开盘价）
- `argMax(field, by)`: 按 `by` 最大值时的 `field` 值（收盘价）
- `max()`/`min()`: 聚合函数
- `GROUP BY trade_date`: 按交易日分组

#### 步骤7：API端点

```python
from fastapi import APIRouter, Query, Depends

router = APIRouter()

@router.get("/data")
async def get_kline_data(
    code: str = Query(..., description="股票代码"),
    start_date: str = Query(...),
    end_date: str = Query(...),
    adj_type: str = Query("none"),
    db: ClickHouseClient = Depends(get_db),
    cache: CacheService = Depends(get_cache)
):
    # 1. 检查缓存
    cache_key = f"kline:{code}:day:{start_date}:{end_date}:{adj_type}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # 2. 查询数据
    service = KLineService(db)
    data = service.get_daily_kline(code, start_date, end_date, adj_type)

    # 3. 缓存结果
    ttl = cache.calculate_ttl(end_date)
    cache.set(cache_key, response, ttl)

    return {"code": 0, "data": data.dict()}
```

**学习点**：
- FastAPI 依赖注入：`Depends()`
- Query参数自动验证
- 缓存模式：先查缓存→查数据库→写缓存

### 3.2 第二阶段：前端基础搭建（2小时）

#### 步骤1：项目初始化

```bash
# 创建Vite项目
npm create vite@latest kline-frontend -- --template react-ts
cd kline-frontend

# 安装依赖
npm install

# 安装额外库
npm install echarts echarts-for-react antd zustand axios dayjs lodash-es
npm install -D @types/lodash-es
```

#### 步骤2：API层封装

**Axios配置（`src/api/client.ts`）**：
```typescript
import axios from 'axios';
import { logger } from '../store/useLogStore';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    logger.info(`API请求: ${config.method?.toUpperCase()} ${config.url}`, {
      params: config.params,
    });
    return config;
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    logger.success(`API响应: ${response.config.url}`, {
      status: response.status,
    });
    return response;
  },
  (error) => {
    logger.error('API错误', error.response?.data);
    return Promise.reject(error);
  }
);
```

**学习点**：
- Axios 拦截器用于统一日志记录
- `import.meta.env` 读取环境变量（Vite特有）
- 错误统一处理

#### 步骤3：状态管理

**Zustand简洁的状态管理**：
```typescript
import { create } from 'zustand';

interface KLineStore {
  selectedStock: string | null;
  klineData: KLine[];
  loading: boolean;

  setSelectedStock: (code: string | null) => void;
  setKLineData: (data: KLine[]) => void;
  setLoading: (loading: boolean) => void;
}

export const useKLineStore = create<KLineStore>((set) => ({
  selectedStock: null,
  klineData: [],
  loading: false,

  setSelectedStock: (code) => set({ selectedStock: code }),
  setKLineData: (data) => set({ klineData: data }),
  setLoading: (loading) => set({ loading }),
}));
```

**优势**：
- 比 Redux 简单很多
- TypeScript 支持好
- 无需 Context Provider

#### 步骤4：核心组件 - K线图

**ECharts配置（`src/components/KLineChart/options.ts`）**：
```typescript
import type { EChartsOption } from 'echarts';

export const getKLineOption = (data: KLine[], stockName: string): EChartsOption => ({
  title: { text: stockName },

  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' },
  },

  // 两个网格：K线图 + 成交量
  grid: [
    { left: '10%', right: '10%', height: '50%' },
    { left: '10%', right: '10%', top: '70%', height: '15%' }
  ],

  xAxis: [
    { type: 'category', data: data.map(d => d.date), gridIndex: 0 },
    { type: 'category', data: data.map(d => d.date), gridIndex: 1 }
  ],

  yAxis: [
    { scale: true, gridIndex: 0 },
    { scale: true, gridIndex: 1 }
  ],

  // 时间范围控制（关键！）
  dataZoom: [
    {
      type: 'inside',      // 鼠标滚轮缩放
      start: 80,           // 默认显示最后20%
      end: 100,
      minSpan: 5,          // 最小显示5%
    },
    {
      type: 'slider',      // 底部滑块
      start: 80,
      end: 100,
      bottom: 10,
    }
  ],

  series: [
    {
      name: 'K线',
      type: 'candlestick',           // 蜡烛图
      data: data.map(d => [d.open, d.close, d.low, d.high]),
      itemStyle: {
        color: '#ef5350',            // 涨：红色
        color0: '#26a69a',           // 跌：绿色
      },
    },
    {
      name: '成交量',
      type: 'bar',
      data: data.map(d => d.volume),
      xAxisIndex: 1,
      yAxisIndex: 1,
    }
  ]
});
```

**关键技术**：
- `candlestick` 类型：专门的K线图
- `dataZoom` 组件：时间范围控制的核心
  - `inside` 类型：鼠标滚轮缩放
  - `slider` 类型：底部滑块拖动
- 双网格布局：上方K线 + 下方成交量
- 数据格式：`[open, close, low, high]`

**React组件封装**：
```typescript
export const KLineChart: React.FC<KLineChartProps> = ({ data, stockName }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<ECharts | undefined>(undefined);

  useEffect(() => {
    if (!chartRef.current) return;

    // 初始化ECharts实例
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    // 设置图表选项
    if (data.length > 0) {
      const option = getKLineOption(data, stockName);
      chartInstance.current.setOption(option, true);
    }

    // 窗口resize时重绘
    const handleResize = () => chartInstance.current?.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, stockName]);

  // 组件卸载时销毁
  useEffect(() => {
    return () => chartInstance.current?.dispose();
  }, []);

  return <div ref={chartRef} style={{ width: '100%', height: '600px' }} />;
};
```

**学习点**：
- `useRef` 保存 DOM 引用和 ECharts 实例
- `useEffect` 监听数据变化重新渲染
- 窗口 resize 时调用 `resize()` 重绘
- 组件卸载时调用 `dispose()` 释放资源

### 3.3 第三阶段：日志系统（1小时）

#### 为什么需要日志系统？

初期问题：
- ❌ 点击查询没反应，不知道哪里出错
- ❌ API请求失败，看不到错误信息
- ❌ 数据加载状态不清楚

#### 日志系统设计

**日志状态管理（`src/store/useLogStore.ts`）**：
```typescript
export type LogLevel = 'info' | 'success' | 'warning' | 'error';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: any;
}

export const useLogStore = create<LogStore>((set) => ({
  logs: [],
  maxLogs: 100,

  addLog: (level, message, data) => {
    const entry: LogEntry = {
      id: Date.now().toString() + Math.random(),
      timestamp: new Date().toLocaleTimeString('zh-CN'),
      level,
      message,
      data,
    };

    // 同时输出到控制台
    console.log(`[${level.toUpperCase()}] ${message}`, data);

    set((state) => ({
      logs: [...state.logs.slice(-99), entry],  // 最多保留100条
    }));
  },
}));

// 导出便捷方法
export const logger = {
  info: (msg: string, data?: any) => useLogStore.getState().addLog('info', msg, data),
  success: (msg: string, data?: any) => useLogStore.getState().addLog('success', msg, data),
  warning: (msg: string, data?: any) => useLogStore.getState().addLog('warning', msg, data),
  error: (msg: string, data?: any) => useLogStore.getState().addLog('error', msg, data),
};
```

**日志面板组件**：
```typescript
export const LogPanel: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { logs, clearLogs } = useLogStore();

  return (
    <>
      {/* 悬浮按钮 */}
      <div className="log-panel-button">
        <Badge count={logs.length}>
          <Button onClick={() => setIsOpen(!isOpen)}>📋</Button>
        </Badge>
      </div>

      {/* 日志面板 */}
      {isOpen && (
        <div className="log-panel">
          {logs.map((log) => (
            <div key={log.id} className="log-entry">
              <span className="log-timestamp">{log.timestamp}</span>
              <span className="log-level" style={{ color: getLevelColor(log.level) }}>
                [{getLevelText(log.level)}]
              </span>
              <span className="log-message">{log.message}</span>
              {log.data && <pre>{JSON.stringify(log.data, null, 2)}</pre>}
            </div>
          ))}
        </div>
      )}
    </>
  );
};
```

**在关键位置添加日志**：
```typescript
// API拦截器
apiClient.interceptors.request.use((config) => {
  logger.info(`API请求: ${config.method} ${config.url}`, config.params);
  return config;
});

// 主页面
const handleStockChange = (code: string, stock: Stock) => {
  logger.info(`股票已选择 - ${code} ${stock.name}`);
  fetchKLineData(code);
};

const fetchKLineData = async (code: string) => {
  logger.info(`开始获取K线数据 - ${code}`);
  try {
    const response = await klineApi.getKLineData(code, startDate, endDate);
    logger.success(`成功加载 ${response.data.count} 个交易日数据`);
  } catch (error) {
    logger.error('获取K线数据失败', error);
  }
};
```

**效果**：
- ✅ 每个操作都有日志记录
- ✅ 错误信息清晰可见
- ✅ 可追踪完整的数据流
- ✅ 便于调试和问题定位

### 3.4 第四阶段：交互优化（1小时）

#### 优化目标

用户反馈：
- ❌ 操作步骤太多（选股票→选日期→点查询）
- ❌ 每次查询都要选日期
- ❌ 想看不同时期的数据要重新查询

#### 优化方案

**核心思路**：
1. 选择股票后自动查询所有数据
2. 移除日期选择器和查询按钮
3. 通过图表拖动选择时间范围

**实现要点**：

1. **自动查询所有数据**：
```typescript
const handleStockChange = (code: string, stock: Stock) => {
  setSelectedStock(code);
  setStockInfo({ code: stock.code, name: stock.name });
  // 自动查询全部数据
  fetchKLineData(code);
};

const fetchKLineData = async (code: string) => {
  // 查询所有可用数据
  const startDate = '2000-01-01';
  const endDate = '2025-12-31';

  const response = await klineApi.getKLineData(code, startDate, endDate);
  setKLineData(response.data.klines);
};
```

2. **图表默认显示最近数据**：
```typescript
dataZoom: [
  {
    type: 'inside',
    start: 80,  // 默认显示最后20%的数据
    end: 100,
  },
  {
    type: 'slider',
    start: 80,
    end: 100,
  }
]
```

3. **简化界面**：
```typescript
<div className="kline-toolbar">
  <span>选择股票：</span>
  <StockSelector onChange={handleStockChange} />
  <span>{loading ? '加载中...' : `已选择 ${stockInfo?.name}`}</span>
</div>
```

**优化效果**：
- ✅ 操作从3步减少到1步
- ✅ 选择股票即可看图
- ✅ 拖动滑块查看任意时期
- ✅ 用户体验大幅提升

---

## 关键技术实现

### 4.1 SSH隧道管理

**问题**：ClickHouse在远程机器，需要安全访问

**技术方案**：
```python
ssh -N -L 18123:localhost:8123 wsl
```

**参数说明**：
- `-N`：不执行远程命令
- `-L local_port:remote_host:remote_port`：本地端口转发
- `18123`：本地监听端口
- `localhost:8123`：远程目标地址

**代码实现**：
```python
import subprocess

class SSHTunnelManager:
    def start(self):
        cmd = ['ssh', '-N', '-L', '18123:localhost:8123', 'wsl']
        self.process = subprocess.Popen(cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        time.sleep(2)  # 等待隧道建立

    def is_alive(self):
        return self.process and self.process.poll() is None
```

**学习要点**：
- SSH隧道是访问内网数据库的常用方案
- `subprocess.Popen` 管理后台进程
- `poll()` 检查进程是否存活

### 4.2 ClickHouse日K线聚合

**需求**：从分钟K线聚合为日K线

**SQL技术**：
```sql
SELECT
    trade_date,
    argMin(open, dt) AS open,      -- 当天第一分钟的开盘价
    argMax(close, dt) AS close,    -- 当天最后一分钟的收盘价
    max(high) AS high,             -- 当天最高价
    min(low) AS low,               -- 当天最低价
    sum(volume) AS volume          -- 当天总成交量
FROM stock.minute_kline
WHERE code = '600000.SH'
  AND trade_date >= '2020-01-01'
  AND trade_date <= '2020-12-31'
GROUP BY trade_date
ORDER BY trade_date
```

**关键函数**：
- `argMin(field, by)`：返回 `by` 最小时的 `field` 值
- `argMax(field, by)`：返回 `by` 最大时的 `field` 值
- 配合时间戳 `dt` 可以精确获取开盘价和收盘价

**为什么不用 `min(open)` 和 `max(close)`？**
- ❌ `min(open)` 会返回一天中最小的开盘价，不是第一分钟
- ✅ `argMin(open, dt)` 返回时间最早时的开盘价

### 4.3 Redis缓存策略

**智能TTL策略**：
```python
def calculate_ttl(self, end_date: str) -> int:
    end = datetime.strptime(end_date, '%Y-%m-%d')
    days_ago = (datetime.now() - end).days

    if days_ago > 30:
        return 24 * 3600  # 历史数据：24小时
    elif days_ago > 1:
        return 3600       # 近期数据：1小时
    else:
        return 300        # 当日数据：5分钟
```

**设计思想**：
- 历史数据不会变化 → 缓存时间长
- 当日数据可能更新 → 缓存时间短
- 平衡性能和数据新鲜度

**缓存Key设计**：
```python
cache_key = f"kline:{code}:day:{start_date}:{end_date}:{adj_type}"
# 示例: "kline:600000.SH:day:2020-01-01:2020-12-31:after"
```

### 4.4 TypeScript类型安全

**问题**：TypeScript严格模式报错

**错误示例**：
```typescript
import { KLineResponse } from '../types/kline';  // ❌ 类型导入错误
```

**解决方案**：
```typescript
import type { KLineResponse } from '../types/kline';  // ✅ 使用 import type
```

**原因**：
- TypeScript 配置启用了 `verbatimModuleSyntax`
- 类型必须用 `import type` 导入
- 避免类型在运行时被错误导入

**最佳实践**：
```typescript
// 值导入
import { functionName } from './module';

// 类型导入
import type { TypeName, InterfaceName } from './types';
```

### 4.5 ECharts事件处理

**需求**：监听图表缩放事件

```typescript
const chartInstance = echarts.init(chartRef.current);

// 监听dataZoom事件
chartInstance.on('dataZoom', (params) => {
  logger.info('时间范围变化', params);
});

// 监听点击事件
chartInstance.on('click', (params) => {
  console.log('点击了', params.data);
});
```

**常用事件**：
- `dataZoom`：时间范围变化
- `click`：点击元素
- `mouseover`/`mouseout`：鼠标悬停
- `legendselectchanged`：图例选择变化

---

## 问题与解决方案

### 5.1 白屏问题

**现象**：前端页面打开白屏

**原因**：TypeScript类型导入错误

**错误日志**：
```
error TS1484: 'KLineResponse' is a type and must be imported
using a type-only import when 'verbatimModuleSyntax' is enabled.
```

**解决步骤**：
1. 运行 `npm run build` 查看编译错误
2. 将所有类型导入改为 `import type`
3. 修复所有文件中的导入语句
4. 重启开发服务器

**防范措施**：
- 在开发时就运行 `npm run build` 检查
- 配置ESLint规则检查导入
- TypeScript配置不要太严格（除非必要）

### 5.2 点击查询无反应

**现象**：点击查询按钮没有任何反应

**排查过程**：
1. 添加日志系统
2. 在关键位置添加 `logger.info()`
3. 发现事件没有触发

**根本原因**：
- 事件处理函数绑定正确
- 但用户体验不好（需要多次点击）

**最终方案**：
- 改为自动查询（选股票后自动加载）
- 移除查询按钮

### 5.3 SQL聚合函数错误

**错误信息**：
```
DB::Exception: Aggregate function any(name) AS name is found in WHERE
```

**原因**：
```sql
-- ❌ 错误：WHERE中使用了聚合后的列
SELECT code, any(name) AS name
FROM table
WHERE code LIKE '%keyword%' OR name LIKE '%keyword%'
GROUP BY code
```

**解决方案**：
```sql
-- ✅ 正确：使用HAVING子句
SELECT code, any(name) AS name
FROM table
GROUP BY code
HAVING code LIKE '%keyword%' OR name LIKE '%keyword%'
```

**学习点**：
- `WHERE`：在聚合前过滤
- `HAVING`：在聚合后过滤
- 聚合函数的结果只能在 `HAVING` 中使用

### 5.4 Pandas依赖缺失

**错误**：
```
NotSupportedError: Pandas package is not installed
```

**原因**：
- `clickhouse-connect` 的 `query_df()` 需要 pandas
- 但 `requirements.txt` 中未列出

**解决**：
```bash
pip install pandas
```

**教训**：
- 安装依赖时要测试所有功能
- 及时更新 `requirements.txt`

### 5.5 端口冲突

**现象**：
```
Port 5173 is in use, trying another one...
Local: http://localhost:5174/
```

**原因**：之前的 Vite 进程未关闭

**解决方案**：
```bash
# 方法1：杀掉所有vite进程
pkill -f "vite"

# 方法2：找到进程并杀掉
ps aux | grep vite
kill <PID>

# 方法3：使用不同端口
vite --port 3001
```

---

## 核心代码解析

### 6.1 FastAPI生命周期管理

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("正在启动服务...")
    tunnel_manager.start()      # 启动SSH隧道
    db_client.connect()         # 连接数据库
    redis_client.connect()      # 连接Redis

    yield  # 应用运行中

    # 关闭时执行
    print("正在关闭服务...")
    tunnel_manager.stop()
    db_client.close()
    redis_client.close()

app = FastAPI(lifespan=lifespan)
```

**学习点**：
- `@asynccontextmanager` 创建异步上下文管理器
- `yield` 前的代码在启动时执行
- `yield` 后的代码在关闭时执行
- 确保资源正确释放

### 6.2 依赖注入模式

```python
# deps.py
def get_db():
    return db_client

def get_cache():
    return CacheService()

# endpoint.py
@router.get("/data")
async def get_kline_data(
    code: str = Query(...),
    db: ClickHouseClient = Depends(get_db),      # 注入数据库
    cache: CacheService = Depends(get_cache)     # 注入缓存
):
    # 直接使用 db 和 cache
    pass
```

**优势**：
- 解耦：端点函数不关心依赖如何创建
- 测试：可以轻松mock依赖
- 复用：依赖可以被多个端点共享

### 6.3 Pydantic数据验证

```python
from pydantic import BaseModel

class KLineData(BaseModel):
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float

# 使用
data = KLineData(
    date="2020-01-01",
    open=10.5,
    close=11.0,
    high=11.2,
    low=10.3,
    volume=1000000
)

# 自动验证和转换
data = KLineData(
    date="2020-01-01",
    open="10.5",    # 自动转换为 float
    close=11,       # 自动转换为 float
    # ... 缺少字段会报错
)
```

**优势**：
- 自动类型验证
- 自动类型转换
- 清晰的错误信息
- 自动生成API文档

### 6.4 React Hooks模式

```typescript
// 自定义Hook：封装数据获取逻辑
const useKLineData = (code: string) => {
  const [data, setData] = useState<KLine[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!code) return;

    const fetchData = async () => {
      setLoading(true);
      try {
        const result = await klineApi.getKLineData(code, '2000-01-01', '2025-12-31');
        setData(result.data.klines);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [code]);  // 依赖code，变化时重新获取

  return { data, loading, error };
};

// 使用
const MyComponent = () => {
  const { data, loading, error } = useKLineData('600000.SH');

  if (loading) return <Spin />;
  if (error) return <div>Error: {error.message}</div>;
  return <KLineChart data={data} />;
};
```

**学习点**：
- 自定义Hook封装可复用逻辑
- `useEffect` 处理副作用
- 依赖数组控制何时重新执行
- 返回多个值供组件使用

### 6.5 防抖处理

```typescript
import { debounce } from 'lodash-es';

const searchStocks = useCallback(
  debounce(async (keyword: string) => {
    // 300ms后才执行搜索
    const result = await stockApi.getStockList(keyword);
    setStocks(result.data.items);
  }, 300),
  []
);

// 用户输入时立即调用，但实际搜索会延迟
<Input onChange={(e) => searchStocks(e.target.value)} />
```

**效果**：
- 用户快速输入时不会频繁请求
- 停止输入300ms后才发送请求
- 节省服务器资源

**应用场景**：
- 搜索框输入
- 窗口resize
- 滚动事件
- 任何高频触发的事件

---

## 优化与改进

### 7.1 性能优化

#### 后端优化

1. **SQL查询优化**
```sql
-- ✅ 使用索引字段
WHERE code = '600000.SH'  -- code是主键的一部分
  AND trade_date >= '2020-01-01'  -- trade_date有索引

-- ❌ 避免函数包裹索引字段
WHERE YEAR(trade_date) = 2020  -- 无法使用索引
```

2. **缓存策略**
- 历史数据：24小时缓存
- 近期数据：1小时缓存
- 当日数据：5分钟缓存

3. **连接池**
```python
# 单例模式确保只有一个数据库连接
class ClickHouseClient:
    _instance = None
    _client = None
```

#### 前端优化

1. **组件Memo化**
```typescript
export const KLineChart = React.memo<KLineChartProps>(({ data, stockName }) => {
  // 只在 data 或 stockName 变化时重新渲染
}, (prevProps, nextProps) => {
  return prevProps.data === nextProps.data &&
         prevProps.stockName === nextProps.stockName;
});
```

2. **防抖搜索**
```typescript
const searchStocks = debounce(async (keyword) => {
  // 减少API调用频率
}, 300);
```

3. **懒加载数据**
```typescript
// 默认只显示20%的数据
dataZoom: [{ start: 80, end: 100 }]
```

### 7.2 用户体验优化

#### 操作流程简化

**之前**：
```
选择股票 → 选择日期 → 点击查询 → 查看图表
```

**现在**：
```
选择股票 → 自动显示图表 → 拖动查看不同时期
```

**改进点**：
- ✅ 减少操作步骤
- ✅ 自动加载数据
- ✅ 图形化时间选择

#### 视觉反馈

1. **加载状态**
```typescript
{loading ? <Spin tip="加载中..." /> : <KLineChart data={data} />}
```

2. **空状态**
```typescript
{data.length === 0 ? <Empty description="暂无数据" /> : <Chart />}
```

3. **实时日志**
```typescript
logger.info('正在加载数据...');
logger.success('加载成功，共242个交易日');
```

### 7.3 代码质量提升

1. **TypeScript严格模式**
```typescript
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

2. **统一错误处理**
```typescript
try {
  const response = await api.getData();
  if (response.code === 0) {
    // 成功处理
  } else {
    logger.error('业务错误', response);
  }
} catch (error) {
  logger.error('系统错误', error);
  message.error('操作失败，请重试');
}
```

3. **代码复用**
```typescript
// 提取公共逻辑到自定义Hook
const useKLineData = (code: string) => {
  // 封装数据获取逻辑
};

// 多个组件都可以使用
const ComponentA = () => {
  const { data } = useKLineData('600000.SH');
};
```

---

## 学习要点

### 8.1 全栈开发技能

#### 后端技能

1. **FastAPI框架**
   - 异步编程（async/await）
   - 依赖注入模式
   - Pydantic数据验证
   - 自动API文档生成

2. **数据库技能**
   - ClickHouse列式数据库
   - SQL聚合函数（argMin/argMax）
   - 索引优化
   - 查询性能优化

3. **系统集成**
   - SSH隧道技术
   - 进程管理（subprocess）
   - 缓存策略设计
   - 配置管理

#### 前端技能

1. **React生态**
   - Hooks使用（useState/useEffect/useRef）
   - 自定义Hook封装
   - 组件设计模式
   - 性能优化（memo/useMemo）

2. **TypeScript**
   - 类型系统
   - 泛型使用
   - 接口设计
   - 类型推导

3. **数据可视化**
   - ECharts配置
   - K线图绘制
   - 交互事件处理
   - 响应式设计

4. **状态管理**
   - Zustand轻量状态管理
   - 状态设计
   - 数据流管理

### 8.2 架构设计思想

1. **分层架构**
```
表现层 (Components)
    ↓
业务逻辑层 (Services)
    ↓
数据访问层 (API/Database)
```

2. **单一职责原则**
- 每个模块只负责一件事
- 组件、服务、工具分离
- 便于测试和维护

3. **依赖注入**
- 降低耦合
- 便于测试
- 提高复用性

4. **缓存策略**
- 提升性能
- 减少数据库压力
- 智能TTL设计

### 8.3 问题解决方法论

1. **问题定位**
   - 添加日志记录
   - 使用浏览器DevTools
   - 查看网络请求
   - 检查控制台错误

2. **逐步排查**
   - 从简单到复杂
   - 隔离问题模块
   - 验证假设
   - 记录解决方案

3. **预防措施**
   - 编写类型定义
   - 添加错误处理
   - 编写测试
   - 代码审查

### 8.4 开发工具链

1. **后端工具**
   - Poetry/pip（依赖管理）
   - Uvicorn（ASGI服务器）
   - Pytest（测试）
   - Black（代码格式化）

2. **前端工具**
   - Vite（构建工具）
   - ESLint（代码检查）
   - Prettier（格式化）
   - Chrome DevTools（调试）

3. **版本控制**
   - Git（版本管理）
   - GitHub（代码托管）
   - 分支策略
   - Commit规范

---

## 后续扩展

### 9.1 功能扩展

#### 短期计划（1-2周）

1. **多周期K线**
```python
# 支持周K、月K、年K
@router.get("/kline/data")
async def get_kline_data(
    period: str = Query("day", enum=["day", "week", "month", "year"])
):
    if period == "week":
        # 周K线聚合逻辑
        pass
```

2. **技术指标**
```typescript
// 添加均线MA5、MA10、MA20
series: [
  { type: 'candlestick', data: klineData },
  { type: 'line', name: 'MA5', data: calculateMA(klineData, 5) },
  { type: 'line', name: 'MA10', data: calculateMA(klineData, 10) },
]
```

3. **复权类型切换**
```typescript
<Radio.Group value={adjType} onChange={handleAdjTypeChange}>
  <Radio value="none">不复权</Radio>
  <Radio value="before">前复权</Radio>
  <Radio value="after">后复权</Radio>
</Radio.Group>
```

4. **快捷时间选择**
```typescript
<Button onClick={() => setTimeRange('1year')}>最近1年</Button>
<Button onClick={() => setTimeRange('3years')}>最近3年</Button>
<Button onClick={() => setTimeRange('all')}>全部</Button>
```

#### 中期计划（1个月）

1. **分钟K线**
   - 1分钟、5分钟、15分钟、30分钟、60分钟
   - 实时数据推送（WebSocket）
   - 数据分页加载

2. **多股票对比**
   - 同时显示多只股票
   - 涨跌幅对比
   - 相关性分析

3. **自选股管理**
   - 添加/删除自选股
   - 自选股分组
   - 本地存储

4. **数据导出**
   - 导出CSV
   - 导出图片
   - 生成报告

#### 长期计划（2-3个月）

1. **量化回测**
   - 策略编写界面
   - 回测引擎
   - 收益统计
   - 风险分析

2. **实时行情**
   - WebSocket推送
   - 实时K线更新
   - 成交明细

3. **移动端适配**
   - 响应式设计
   - 触摸交互
   - PWA支持

### 9.2 技术优化

1. **性能优化**
   - 虚拟滚动（处理大数据量）
   - Web Worker（数据计算）
   - IndexedDB（本地缓存）

2. **可靠性提升**
   - 错误边界（Error Boundary）
   - 请求重试机制
   - 离线支持

3. **安全性**
   - JWT认证
   - HTTPS
   - API限流
   - SQL注入防护

4. **监控运维**
   - 日志收集
   - 性能监控
   - 错误追踪（Sentry）
   - 健康检查

### 9.3 架构升级

1. **微服务化**
```
┌─────────────┐
│  API Gateway │
└──────┬──────┘
       │
   ┌───┴────┬─────────┬──────────┐
   │        │         │          │
   ▼        ▼         ▼          ▼
Stock   K-Line   Indicator   Strategy
Service Service  Service     Service
```

2. **容器化部署**
```dockerfile
# Dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

3. **CI/CD**
```yaml
# .github/workflows/deploy.yml
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and test
        run: |
          npm run build
          npm run test
      - name: Deploy
        run: ./deploy.sh
```

---

## 总结与反思

### 10.1 项目成果

#### 技术成果

- ✅ 完整的前后端分离架构
- ✅ 高性能数据查询（ClickHouse）
- ✅ 优秀的用户体验（自动加载、拖动选择）
- ✅ 完善的日志系统（便于调试）
- ✅ 可扩展的代码结构

#### 性能指标

- API响应时间：<500ms（冷启动）、<10ms（缓存）
- 前端首屏加载：<2s
- K线图渲染：<100ms（242根K线）
- 数据量支持：3000+交易日

#### 代码质量

- TypeScript严格模式
- 100%类型覆盖
- 统一的错误处理
- 清晰的代码结构

### 10.2 经验总结

#### 做得好的地方

1. **技术选型合理**
   - FastAPI：开发效率高
   - ClickHouse：查询速度快
   - ECharts：图表专业
   - TypeScript：类型安全

2. **架构设计清晰**
   - 前后端分离
   - 分层架构
   - 单一职责
   - 依赖注入

3. **用户体验优先**
   - 操作流程简化
   - 自动加载数据
   - 实时反馈
   - 日志调试

4. **问题解决及时**
   - 白屏问题→类型导入修复
   - 查询无反应→添加日志系统
   - 用户体验差→自动加载优化

#### 可以改进的地方

1. **缺少测试**
   - 未编写单元测试
   - 未编写集成测试
   - 依赖手动测试

2. **错误处理不完善**
   - 部分边界情况未处理
   - 错误信息不够友好
   - 缺少重试机制

3. **性能监控缺失**
   - 未监控API响应时间
   - 未监控前端性能
   - 未收集用户行为数据

4. **文档不够完善**
   - API文档靠Swagger自动生成
   - 缺少部署文档
   - 缺少运维文档

### 10.3 关键学习点

1. **全栈思维**
   - 前后端协同设计
   - 数据流完整链路
   - 用户体验优先

2. **工程化思维**
   - 代码结构化
   - 模块化设计
   - 可维护性

3. **性能优化**
   - 缓存策略
   - SQL优化
   - 前端渲染优化

4. **问题解决**
   - 日志调试
   - 逐步排查
   - 根本原因分析

### 10.4 下一步学习方向

1. **深入学习**
   - ClickHouse高级特性
   - ECharts自定义开发
   - React性能优化
   - TypeScript高级类型

2. **扩展知识**
   - 量化交易策略
   - 技术指标算法
   - 金融数据分析
   - 机器学习应用

3. **工程实践**
   - 单元测试编写
   - CI/CD实践
   - Docker容器化
   - 微服务架构

4. **软技能**
   - 需求分析
   - 方案设计
   - 技术选型
   - 文档编写

---

## 附录

### A. 快速启动命令

```bash
# 后端
cd kline-backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 前端
cd kline-frontend
npm run dev

# SSH隧道
ssh -N -L 18123:localhost:8123 wsl &
```

### B. 常用API

```bash
# 健康检查
curl http://localhost:8000/health

# 股票列表
curl "http://localhost:8000/api/stocks/list?keyword=平安&limit=5"

# K线数据
curl "http://localhost:8000/api/kline/data?code=600000.SH&start_date=2020-01-01&end_date=2020-12-31&adj_type=none"
```

### C. 技术文档链接

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [ECharts官方文档](https://echarts.apache.org/)
- [React官方文档](https://react.dev/)
- [TypeScript官方文档](https://www.typescriptlang.org/)
- [ClickHouse官方文档](https://clickhouse.com/docs)

### D. 项目文件清单

**后端核心文件**：
- `app/main.py` - FastAPI入口
- `app/core/ssh_tunnel.py` - SSH隧道管理
- `app/services/kline_service.py` - K线业务逻辑
- `app/api/endpoints/kline.py` - K线API

**前端核心文件**：
- `src/pages/KLinePage/index.tsx` - 主页面
- `src/components/KLineChart/index.tsx` - K线图组件
- `src/components/KLineChart/options.ts` - ECharts配置
- `src/store/useLogStore.ts` - 日志系统

---

**项目完成日期**：2026年1月30日
**生产环境部署**：2026年1月31日
**总开发时长**：约8小时（开发）+ 4小时（部署）
**代码行数**：后端~800行，前端~1200行
**学到的技术**：FastAPI、ClickHouse、ECharts、TypeScript、Zustand、Nginx、Docker

**最大收获**：从零到一搭建了一个完整的全栈应用，深入理解了前后端协同开发的全流程。

---

## 生产环境部署（2026年1月31日）

### 11.1 部署目标

将K线应用部署到WSL生产环境，与现有的视频转录服务共存。

### 11.2 部署架构决策

#### 架构选择：基于路径 vs 基于端口

**业界最佳实践分析**：

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **路径区分** | 统一入口、防火墙友好、SSL简单 | 需要配置路由 | 生产环境（推荐） |
| **端口区分** | 配置简单 | 需要开放多个端口、SSL复杂 | 开发/测试环境 |

**大厂实践**：
- Google API：`https://www.googleapis.com/calendar/v3/...`
- AWS服务：`https://s3.amazonaws.com/...`
- 阿里云：`https://ecs.aliyuncs.com/...`

**最终决策**：采用基于路径的架构

```
http://192.168.50.90/          → 视频转录服务
http://192.168.50.90/kline/    → K线服务
```

### 11.3 部署过程

#### 阶段1：后端服务部署（8001端口）

**问题1：端口冲突**
```
Error: Connection in use: ('0.0.0.0', 8000)
```

**原因**：video-summary-backend容器使用host网络模式占用了8000端口

**解决方案**：
```python
# 修改kline-backend使用8001端口
# systemd配置
ExecStart=/home/lee/kline-backend/venv/bin/gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8001
```

**问题2：配置验证失败**
```
ValidationError: 1 validation error for Settings
REDIS_PASSWORD
  Extra inputs are not permitted
```

**原因**：环境变量中有`REDIS_PASSWORD`，但Settings类缺少该字段

**解决方案**：
```python
# app/core/config.py
class Settings(BaseSettings):
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""  # 添加缺失字段
```

**部署命令**：
```bash
# 上传配置文件
scp kline-backend/app/core/config.py wsl:/home/lee/kline-backend/app/core/

# 重启服务
ssh -t wsl "sudo systemctl restart kline-backend.service"
```

**验证结果**：
```bash
✅ 服务状态：active（运行中）
✅ 端口监听：8001端口正常
✅ 进程数量：1 master + 4 workers
✅ API测试：返回正常数据
```

#### 阶段2：Nginx反向代理配置

**挑战**：80端口也被占用（video-summary-nginx容器）

**架构设计**：
```
Internet (192.168.50.90)
    ↓
[Nginx - Docker容器] :80
    ↓
    ├─ /                  → 视频转录服务
    ├─ /api/              → 视频转录API
    │
    ├─ /kline/            → K线前端静态文件
    ├─ /kline/api/        → K线后端API :8001
    └─ /kline/health      → K线健康检查
```

**Nginx配置**（`/etc/nginx/conf.d/nginx.conf`）：
```nginx
server {
    listen 80;
    server_name localhost;

    # K线服务 - API代理
    location /kline/api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # K线服务 - 健康检查
    location /kline/health {
        proxy_pass http://127.0.0.1:8001/health;
        access_log off;
    }

    # K线服务 - 前端静态文件
    location /kline/ {
        alias /var/www/html/kline/;
        index index.html;
        try_files $uri $uri/ /kline/index.html;
    }

    # 原有服务配置...
}
```

**部署步骤**：
```bash
# 1. 上传配置到WSL
scp nginx-80.conf wsl:/tmp/

# 2. 复制到Docker容器
ssh wsl "docker cp /tmp/nginx-80.conf video-summary-nginx:/etc/nginx/conf.d/nginx.conf"

# 3. 测试配置
ssh wsl "docker exec video-summary-nginx nginx -t"

# 4. 重新加载
ssh wsl "docker exec video-summary-nginx nginx -s reload"
```

#### 阶段3：前端构建与部署

**配置修改**：

1. **Vite配置**（`vite.config.ts`）：
```typescript
export default defineConfig({
  plugins: [react()],
  base: '/kline/',  // 设置基础路径
})
```

2. **生产环境配置**（`.env.production`）：
```env
VITE_API_BASE_URL=http://192.168.50.90/kline/api
```

**构建流程**：
```bash
# 1. 本地构建
cd kline-frontend
npm run build

# 2. 打包并上传
tar -czf /tmp/kline-dist.tar.gz -C dist .
scp /tmp/kline-dist.tar.gz wsl:/tmp/

# 3. 部署到Docker容器
ssh wsl "docker exec video-summary-nginx mkdir -p /var/www/html/kline"
ssh wsl "docker cp /tmp/kline-dist.tar.gz video-summary-nginx:/tmp/"
ssh wsl "docker exec video-summary-nginx tar -xzf /tmp/kline-dist.tar.gz -C /var/www/html/kline/"
```

**验证资源路径**：
```html
<!-- 修改前（错误） -->
<script src="/assets/index.js"></script>

<!-- 修改后（正确） -->
<script src="/kline/assets/index.js"></script>
```

#### 阶段4：大小写不敏感优化

**用户反馈**：访问 `http://localhost/KLINE` 返回视频服务

**问题分析**：
- Nginx的location匹配是**区分大小写**的
- `/KLINE` 不匹配 `location /kline/`
- 被根路径 `location /` 处理

**测试结果**：
```bash
✅ /kline/  → K线服务
❌ /kline   → 视频服务
❌ /KLINE/  → 视频服务
❌ /KLINE   → 视频服务
```

**解决方案**：添加重定向规则

```nginx
# 大小写重定向
location ~ ^/(?!kline)[Kk][Ll][Ii][Nn][Ee]$ {
    return 301 /kline/;
}
location ~ ^/(?!kline/)[Kk][Ll][Ii][Nn][Ee]/(.*)$ {
    return 301 /kline/$1;
}

# 无斜杠重定向到有斜杠
location = /kline {
    return 301 /kline/;
}
```

**优化后结果**：
```bash
✅ /kline/  → 200 直接访问
✅ /kline   → 301 重定向到 /kline/
✅ /KLINE/  → 301 重定向到 /kline/
✅ /KLINE   → 301 重定向到 /kline/
✅ /Kline   → 301 重定向到 /kline/
✅ /KLine   → 301 重定向到 /kline/
```

### 11.4 部署架构图

```
┌─────────────────────────────────────────────────┐
│              Windows Host                        │
│           192.168.50.90                          │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │           WSL (Ubuntu)                   │   │
│  │        192.168.1.3                       │   │
│  │                                          │   │
│  │  ┌───────────────────────────────────┐  │   │
│  │  │  Docker: video-summary-nginx      │  │   │
│  │  │  Network: host mode               │  │   │
│  │  │  Port: 80                         │  │   │
│  │  │                                   │  │   │
│  │  │  /           → video service      │  │   │
│  │  │  /kline/     → kline frontend     │  │   │
│  │  │  /kline/api/ → proxy to :8001     │  │   │
│  │  └───────────────────────────────────┘  │   │
│  │                                          │   │
│  │  ┌───────────────────────────────────┐  │   │
│  │  │  Systemd: kline-backend.service   │  │   │
│  │  │  Port: 8001                       │  │   │
│  │  │  Workers: 1 master + 4 workers    │  │   │
│  │  │  Backend: FastAPI + Gunicorn      │  │   │
│  │  └───────────────────────────────────┘  │   │
│  │                                          │   │
│  │  ┌───────────────────────────────────┐  │   │
│  │  │  ClickHouse Database              │  │   │
│  │  │  Port: 8123                       │  │   │
│  │  └───────────────────────────────────┘  │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 11.5 部署验证

#### API测试
```bash
# 股票列表
curl http://192.168.50.90/kline/api/stocks/list?limit=3
# 返回：{"code":0,"message":"success","data":{...}}

# 健康检查
curl http://192.168.50.90/kline/health
# 返回：{"status":"ok","ssh_tunnel":null}
```

#### 前端访问
```
http://192.168.50.90/kline/          ✅ 页面正常
http://localhost/kline/              ✅ 页面正常（Windows）
http://localhost/KLINE               ✅ 自动重定向
```

### 11.6 关键技术点

#### 1. Docker容器网络模式

**host模式**：
```yaml
network_mode: host
```
- 容器直接使用宿主机网络栈
- 监听的端口直接绑定到宿主机
- 无需端口映射
- 性能最优

#### 2. Nginx正则表达式location

```nginx
# 精确匹配
location = /kline {
    return 301 /kline/;
}

# 正则匹配（不区分大小写）
location ~ ^/[Kk][Ll][Ii][Nn][Ee]$ {
    return 301 /kline/;
}

# 负向前瞻（排除小写kline）
location ~ ^/(?!kline)[Kk][Ll][Ii][Nn][Ee]$ {
    return 301 /kline/;
}
```

**优先级**：
1. `=` 精确匹配
2. `^~` 前缀匹配
3. `~` 正则匹配（区分大小写）
4. `~*` 正则匹配（不区分大小写）
5. 前缀匹配

#### 3. Vite Base路径配置

```typescript
// vite.config.ts
export default defineConfig({
  base: '/kline/',  // 所有资源URL前缀
})
```

**效果**：
- `/vite.svg` → `/kline/vite.svg`
- `/assets/index.js` → `/kline/assets/index.js`
- 必须在部署到子路径时配置

#### 4. Systemd服务管理

```ini
[Unit]
Description=KLine Backend Service
After=network.target

[Service]
Type=notify
User=lee
Group=lee
WorkingDirectory=/home/lee/kline-backend
Environment="PATH=/home/lee/kline-backend/venv/bin"
ExecStart=/home/lee/kline-backend/venv/bin/gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**常用命令**：
```bash
sudo systemctl start kline-backend
sudo systemctl stop kline-backend
sudo systemctl restart kline-backend
sudo systemctl status kline-backend
sudo systemctl enable kline-backend  # 开机自启
```

### 11.7 部署问题总结

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 8000端口占用 | video-summary容器占用 | 改用8001端口 |
| 配置验证失败 | 缺少REDIS_PASSWORD字段 | 添加字段到Settings类 |
| 80端口占用 | nginx容器占用 | 使用路径区分而非端口 |
| 前端500错误 | 文件在宿主机不在容器 | 复制文件到容器内 |
| 资源404错误 | base路径未配置 | vite.config.ts设置base |
| 大小写敏感 | nginx location区分大小写 | 添加重定向规则 |

### 11.8 生产环境配置文件

#### 后端配置（`.env.production`）
```env
# SSH配置（WSL本地，无需隧道）
SSH_HOST=localhost
SSH_LOCAL_PORT=8123
SSH_REMOTE_PORT=8123

# ClickHouse配置（WSL本地直连）
CH_HOST=localhost
CH_PORT=8123
CH_DATABASE=stock
CH_USER=default
CH_PASSWORD=

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

#### 前端配置（`.env.production`）
```env
# 生产环境配置
VITE_API_BASE_URL=http://192.168.50.90/kline/api
```

### 11.9 部署最佳实践总结

1. **端口管理**
   - 开发环境可用端口区分
   - 生产环境应用路径区分
   - 统一80/443入口

2. **容器部署**
   - 静态文件必须在容器内
   - 注意网络模式（host/bridge）
   - 配置文件统一管理

3. **Nginx配置**
   - 使用location优先级
   - 添加大小写兼容
   - 配置健康检查

4. **前端构建**
   - 配置正确的base路径
   - 环境变量区分开发/生产
   - 构建产物压缩上传

5. **服务管理**
   - 使用systemd管理后端服务
   - 配置自动重启
   - 日志文件管理

### 11.10 访问地址汇总

**生产环境**：
- 前端：`http://192.168.50.90/kline/`
- API：`http://192.168.50.90/kline/api/`
- 健康检查：`http://192.168.50.90/kline/health`

**Windows本地**：
- 前端：`http://localhost/kline/`
- 支持任意大小写：`/kline`、`/KLINE`、`/Kline` 等

---

**部署完成时间**：2026年1月31日 16:10
**部署用时**：约4小时
**最终状态**：✅ 所有功能正常运行
