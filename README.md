# K线图前后端系统

一个完整的股票K线图查询系统，支持5400只A股的日K线数据查询和可视化。

## 系统架构

```
前端 (React + ECharts)  ←→  后端 (FastAPI)  ←→  ClickHouse (通过SSH隧道)
http://localhost:5173       http://localhost:8000       192.168.50.90:8123
                                    ↓
                               Redis缓存
```

## 当前状态

✅ 后端API: http://localhost:8000
✅ 前端界面: http://localhost:5173
✅ API文档: http://localhost:8000/docs
✅ SSH隧道: localhost:18123 → wsl:8123

## 快速开始

### 1. 访问前端界面

在浏览器中打开:
```
http://localhost:5173
```

### 2. 使用系统

1. **选择股票**
   - 在股票选择器中输入代码或名称（如"600000"或"浦发"）
   - 从下拉列表中选择股票

2. **选择日期范围**
   - 默认显示最近3个月
   - 可以自定义开始和结束日期

3. **查询K线**
   - 点击"查询"按钮
   - 系统会显示K线图和成交量

4. **交互功能**
   - 拖动底部滑块缩放时间范围
   - 鼠标滚轮放大缩小
   - 悬停查看详细数据

## API测试示例

### 获取股票列表
```bash
curl "http://localhost:8000/api/stocks/list?keyword=平安&limit=5"
```

### 获取K线数据
```bash
curl "http://localhost:8000/api/kline/data?code=000001.SZ&start_date=2010-01-01&end_date=2010-12-31&adj_type=after"
```

## 项目结构

```
Quant/
├── kline-backend/          # 后端FastAPI项目
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心配置（SSH隧道）
│   │   ├── db/            # 数据库客户端（ClickHouse, Redis）
│   │   ├── schemas/       # Pydantic模型
│   │   ├── services/      # 业务逻辑
│   │   └── main.py        # FastAPI入口
│   ├── legacy/            # 原始参考代码
│   └── requirements.txt
│
└── kline-frontend/        # 前端React项目
    ├── src/
    │   ├── api/          # API客户端
    │   ├── components/   # React组件
    │   │   ├── StockSelector/
    │   │   ├── KLineChart/
    │   │   └── DateRangePicker/
    │   ├── pages/        # 页面
    │   ├── store/        # Zustand状态管理
    │   └── types/        # TypeScript类型
    └── package.json
```

## 技术栈

### 后端
- FastAPI 0.109.0
- ClickHouse Connect 0.10.0
- Redis 5.0.1
- Pandas 2.3.3

### 前端
- React 18 + TypeScript
- Vite 7.3.1
- ECharts (K线图渲染)
- Ant Design (UI组件)
- Zustand (状态管理)
- Axios (HTTP客户端)

## 维护命令

### 检查服务状态
```bash
# 检查后端
curl http://localhost:8000/health

# 检查前端
curl http://localhost:5173

# 查看SSH隧道
ps aux | grep "ssh -N -L 18123"
```

### 重启服务

**后端:**
```bash
cd kline-backend
# 找到进程并停止
ps aux | grep uvicorn | grep -v grep
kill <PID>
# 重新启动
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

**前端:**
```bash
cd kline-frontend
# 找到进程并停止
ps aux | grep vite | grep -v grep
kill <PID>
# 重新启动
nohup npm run dev > frontend.log 2>&1 &
```

**SSH隧道:**
```bash
# 停止
ps aux | grep "ssh -N -L 18123" | grep -v grep
kill <PID>
# 重新启动
ssh -N -L 18123:localhost:8123 wsl &
```

## 数据说明

- **数据源**: ClickHouse数据库 (stock.minute_kline表)
- **股票数量**: 5400只A股
- **复权方式**: 支持后复权/前复权/不复权
- **K线类型**: 当前支持日K线（分钟/周/月K线待后续迭代）

## 已完成功能

- ✅ 股票搜索（支持代码和名称模糊搜索）
- ✅ 日K线图显示（ECharts candlestick）
- ✅ 成交量柱状图
- ✅ 时间范围拖动选择（dataZoom）
- ✅ 后复权价格显示
- ✅ Redis缓存（智能TTL策略）
- ✅ SSH隧道自动管理

## 待开发功能

- [ ] 周K/月K/年K线支持
- [ ] 技术指标（MA/MACD/KDJ/RSI/BOLL）
- [ ] 分钟级K线
- [ ] 复权类型切换UI
- [ ] 多股票对比
- [ ] 量化策略回测

## 开发者

基于实施计划开发，参考文档:
- 原始代码: `kline_plot/plot_kline_ssh.py`
- 数据库文档: `MigrateToDB/DATABASE_USAGE.md`

## License

MIT
