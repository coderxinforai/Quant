# A股分钟K线数据库使用文档

## 连接信息

| 参数 | 值 |
|------|------|
| 数据库类型 | ClickHouse |
| 主机 | `192.168.50.90`（Windows WSL） |
| HTTP 端口 | `8123` |
| Native 端口 | `9000` |
| 数据库名 | `stock` |
| 表名 | `minute_kline` |
| 用户名 | `default` |
| 密码 | （空） |

## 数据范围

- **时间跨度**: 2000-06 ~ 2025-10
- **数据粒度**: 分钟级
- **股票数量**: ~5400 只 A 股
- **总行数**: ~25 亿行
- **磁盘占用**: 压缩后约 40-60GB

## 表结构

### 基础字段

| 列名 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `code` | String | 股票代码（标准格式） | `600000.SH` |
| `dt` | DateTime | 时间戳（分钟级） | `2024-01-02 09:31:00` |
| `name` | String | 股票名称 | `浦发银行` |
| `open` | Float64 | 开盘价 | `6.63` |
| `close` | Float64 | 收盘价 | `6.60` |
| `high` | Float64 | 最高价 | `6.65` |
| `low` | Float64 | 最低价 | `6.60` |
| `volume` | UInt64 | 成交量（手） | `220667` |
| `amount` | Float64 | 成交额（元） | `146066604.0` |
| `pct_change` | Float32 | 涨幅（%） | `0.15` |
| `amplitude` | Float32 | 振幅（%） | `0.30` |
| `after_factor` | Float64 | 后复权因子 | `11.4` |
| `before_factor` | Float64 | 前复权因子 | `0.889` |

### 复权价格（MATERIALIZED 列）

**重要**: 这些列已物理存储，查询时无需计算，性能等同于普通列。

| 列名 | 公式 | 说明 |
|------|------|------|
| `adj_open_after` | `open * after_factor` | 后复权开盘价 |
| `adj_close_after` | `close * after_factor` | 后复权收盘价 |
| `adj_high_after` | `high * after_factor` | 后复权最高价 |
| `adj_low_after` | `low * after_factor` | 后复权最低价 |
| `adj_open_before` | `open * before_factor` | 前复权开盘价 |
| `adj_close_before` | `close * before_factor` | 前复权收盘价 |
| `adj_high_before` | `high * before_factor` | 前复权最高价 |
| `adj_low_before` | `low * before_factor` | 前复权最低价 |
| `trade_date` | `toDate(dt)` | 交易日期 |

## Python 连接示例

### 安装依赖

```bash
pip install clickhouse-connect pandas
```

### 基础连接

```python
import clickhouse_connect
import pandas as pd

# 连接 ClickHouse
client = clickhouse_connect.get_client(
    host='192.168.50.90',
    port=8123,
    database='stock'
)

# 查询示例
query = """
    SELECT * FROM minute_kline
    WHERE code = '600000.SH' AND toDate(dt) = '2024-01-02'
    LIMIT 10
"""
result = client.query(query)
df = result.result_as_pandas()
print(df)
```

## 常用查询场景

### 1. 查询单只股票的日K线数据

```sql
SELECT
    trade_date,
    argMin(open, dt) AS open,              -- 当天第一分钟的开盘价
    argMax(close, dt) AS close,            -- 当天最后一分钟的收盘价
    max(high) AS high,                     -- 当天最高价
    min(low) AS low,                       -- 当天最低价
    sum(volume) AS volume,                 -- 当天成交量
    sum(amount) AS amount,                 -- 当天成交额
    argMin(adj_close_after, dt) AS adj_open_after,
    argMax(adj_close_after, dt) AS adj_close_after
FROM stock.minute_kline
WHERE code = '600000.SH'
  AND trade_date >= '2024-01-01'
  AND trade_date <= '2024-12-31'
GROUP BY trade_date
ORDER BY trade_date
```

**Python 封装**:

```python
def get_daily_kline(client, code, start_date, end_date):
    """获取日K线数据"""
    query = f"""
        SELECT
            trade_date,
            argMin(open, dt) AS open,
            argMax(close, dt) AS close,
            max(high) AS high,
            min(low) AS low,
            sum(volume) AS volume,
            sum(amount) AS amount,
            argMin(adj_close_after, dt) AS adj_open_after,
            argMax(adj_close_after, dt) AS adj_close_after
        FROM stock.minute_kline
        WHERE code = '{code}'
          AND trade_date >= '{start_date}'
          AND trade_date <= '{end_date}'
        GROUP BY trade_date
        ORDER BY trade_date
    """
    return client.query(query).result_as_pandas()

# 使用
df = get_daily_kline(client, '600000.SH', '2024-01-01', '2024-12-31')
```

### 2. 查询分钟K线（用于绘图）

```sql
SELECT
    dt,
    open,
    close,
    high,
    low,
    volume,
    adj_close_after  -- 后复权收盘价
FROM stock.minute_kline
WHERE code = '600000.SH'
  AND dt >= '2024-01-02 09:30:00'
  AND dt <= '2024-01-02 15:00:00'
ORDER BY dt
```

**Python 封装**:

```python
def get_minute_kline(client, code, start_dt, end_dt, use_adj=True):
    """
    获取分钟K线数据

    Args:
        code: 股票代码
        start_dt: 开始时间 'YYYY-MM-DD HH:MM:SS'
        end_dt: 结束时间
        use_adj: 是否使用后复权价格
    """
    price_cols = """
        adj_open_after AS open,
        adj_close_after AS close,
        adj_high_after AS high,
        adj_low_after AS low
    """ if use_adj else "open, close, high, low"

    query = f"""
        SELECT dt, {price_cols}, volume
        FROM stock.minute_kline
        WHERE code = '{code}'
          AND dt >= '{start_dt}'
          AND dt <= '{end_dt}'
        ORDER BY dt
    """
    return client.query(query).result_as_pandas()

# 使用
df = get_minute_kline(client, '600000.SH',
                       '2024-01-02 09:30:00',
                       '2024-01-05 15:00:00',
                       use_adj=True)
```

### 3. 全市场选股（技术指标筛选）

```sql
-- 示例：查找今日收盘价创20日新高的股票
WITH daily_data AS (
    SELECT
        code,
        trade_date,
        argMax(close, dt) AS close,
        sum(volume) AS volume
    FROM stock.minute_kline
    WHERE trade_date >= today() - 30
    GROUP BY code, trade_date
)
SELECT
    code,
    close AS latest_close,
    max(close) OVER (
        PARTITION BY code
        ORDER BY trade_date
        ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
    ) AS high_20d
FROM daily_data
WHERE trade_date = today()
  AND close > high_20d
ORDER BY latest_close DESC
```

**Python 封装**:

```python
def screen_stocks(client, condition_sql):
    """
    全市场选股

    Args:
        condition_sql: 筛选条件的 SQL 片段

    Example:
        screen_stocks(client, "close > high_20d AND volume > 100000")
    """
    query = f"""
        WITH daily_data AS (
            SELECT
                code,
                trade_date,
                argMax(close, dt) AS close,
                sum(volume) AS volume
            FROM stock.minute_kline
            WHERE trade_date >= today() - 30
            GROUP BY code, trade_date
        )
        SELECT
            code,
            close AS latest_close,
            volume AS latest_volume,
            max(close) OVER (
                PARTITION BY code
                ORDER BY trade_date
                ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
            ) AS high_20d
        FROM daily_data
        WHERE trade_date = today()
          AND ({condition_sql})
        ORDER BY latest_close DESC
    """
    return client.query(query).result_as_pandas()
```

### 4. 计算移动平均线

```python
def calculate_ma(client, code, start_date, end_date, windows=[5, 10, 20, 60]):
    """计算日线均线"""
    # 先获取日K线数据
    df = get_daily_kline(client, code, start_date, end_date)

    # 使用 pandas 计算均线
    for window in windows:
        df[f'ma{window}'] = df['close'].rolling(window=window).mean()

    return df

# 使用
df = calculate_ma(client, '600000.SH', '2024-01-01', '2024-12-31')
```

### 5. 查询特定时间段的集合竞价数据

```sql
-- 查询开盘集合竞价（9:25-9:30）
SELECT
    dt,
    code,
    name,
    open,
    close,
    volume
FROM stock.minute_kline
WHERE toTime(dt) >= '09:25:00'
  AND toTime(dt) <= '09:30:00'
  AND trade_date = '2024-01-02'
ORDER BY code, dt
```

### 6. 批量获取多只股票数据

```python
def get_multiple_stocks(client, codes, start_date, end_date):
    """批量获取多只股票的日K线"""
    codes_str = "','".join(codes)
    query = f"""
        SELECT
            code,
            trade_date,
            argMin(open, dt) AS open,
            argMax(close, dt) AS close,
            max(high) AS high,
            min(low) AS low,
            sum(volume) AS volume
        FROM stock.minute_kline
        WHERE code IN ('{codes_str}')
          AND trade_date >= '{start_date}'
          AND trade_date <= '{end_date}'
        GROUP BY code, trade_date
        ORDER BY code, trade_date
    """
    return client.query(query).result_as_pandas()

# 使用
codes = ['600000.SH', '000001.SZ', '600519.SH']
df = get_multiple_stocks(client, codes, '2024-01-01', '2024-12-31')
```

## 绘制K线图示例

### 使用 mplfinance

```python
import mplfinance as mpf

def plot_kline(client, code, start_date, end_date):
    """绘制K线图"""
    # 获取日K线数据
    df = get_daily_kline(client, code, start_date, end_date)

    # 转换为 mplfinance 需要的格式
    df.set_index('trade_date', inplace=True)
    df.index = pd.to_datetime(df.index)

    # 重命名列以符合 mplfinance 要求
    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)

    # 绘制K线图
    mpf.plot(df, type='candle', volume=True,
             title=f'{code} K线图',
             style='charles',
             figsize=(12, 6))

# 使用
plot_kline(client, '600000.SH', '2024-01-01', '2024-03-31')
```

### 使用 plotly（交互式）

```python
import plotly.graph_objects as go

def plot_interactive_kline(client, code, start_date, end_date):
    """绘制交互式K线图"""
    df = get_daily_kline(client, code, start_date, end_date)

    fig = go.Figure(data=[go.Candlestick(
        x=df['trade_date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    )])

    fig.update_layout(
        title=f'{code} K线图',
        xaxis_title='日期',
        yaxis_title='价格',
        xaxis_rangeslider_visible=False
    )

    fig.show()

# 使用
plot_interactive_kline(client, '600000.SH', '2024-01-01', '2024-03-31')
```

## 量化策略示例

### 简单双均线策略

```python
def backtest_ma_cross(client, code, start_date, end_date, fast=5, slow=20):
    """
    双均线交叉策略回测

    Args:
        fast: 快速均线周期
        slow: 慢速均线周期
    """
    # 获取数据
    df = get_daily_kline(client, code, start_date, end_date)

    # 计算均线
    df[f'ma{fast}'] = df['adj_close_after'].rolling(window=fast).mean()
    df[f'ma{slow}'] = df['adj_close_after'].rolling(window=slow).mean()

    # 生成信号：快线上穿慢线买入，下穿卖出
    df['signal'] = 0
    df.loc[df[f'ma{fast}'] > df[f'ma{slow}'], 'signal'] = 1  # 持仓
    df['position'] = df['signal'].diff()  # 1: 买入, -1: 卖出

    # 计算收益
    df['returns'] = df['adj_close_after'].pct_change()
    df['strategy_returns'] = df['returns'] * df['signal'].shift(1)

    # 统计
    total_return = (1 + df['strategy_returns']).prod() - 1
    sharpe = df['strategy_returns'].mean() / df['strategy_returns'].std() * (252 ** 0.5)

    print(f"策略总收益: {total_return:.2%}")
    print(f"夏普比率: {sharpe:.2f}")

    return df

# 使用
result = backtest_ma_cross(client, '600000.SH', '2023-01-01', '2024-12-31')
```

## 性能优化建议

### 1. 日期范围过滤

```sql
-- 好：使用 trade_date（MATERIALIZED 列）
WHERE trade_date >= '2024-01-01' AND trade_date <= '2024-12-31'

-- 差：对 dt 提取日期再过滤（需要全表扫描）
WHERE toDate(dt) >= '2024-01-01' AND toDate(dt) <= '2024-12-31'
```

### 2. 利用主键排序

表的 ORDER BY 是 `(code, dt)`，所以：

```sql
-- 好：利用主键排序
WHERE code = '600000.SH' AND dt >= '2024-01-01'

-- 差：先过滤日期再过滤股票
WHERE dt >= '2024-01-01' AND code = '600000.SH'
```

### 3. 批量查询

```python
# 好：一次查询多只股票
codes = ['600000.SH', '000001.SZ', '600519.SH']
query = f"SELECT * FROM minute_kline WHERE code IN {tuple(codes)}"

# 差：循环单独查询
for code in codes:
    query = f"SELECT * FROM minute_kline WHERE code = '{code}'"
```

### 4. 使用 PREWHERE（ClickHouse 特性）

```sql
-- PREWHERE 会先过滤数据再读取其他列，减少 IO
SELECT * FROM stock.minute_kline
PREWHERE code = '600000.SH'  -- 先用 PREWHERE 过滤主键
WHERE trade_date >= '2024-01-01'
```

## 常见问题

### Q: 如何区分上海和深圳股票？

```sql
-- 上海股票
WHERE endsWith(code, '.SH')

-- 深圳股票
WHERE endsWith(code, '.SZ')
```

### Q: 如何获取所有股票代码列表？

```sql
SELECT DISTINCT code
FROM stock.minute_kline
ORDER BY code
```

### Q: 复权因子为 0 怎么办？

复权因子为 0 表示该日期无复权数据。查询时可以过滤：

```sql
WHERE after_factor != 0 AND before_factor != 0
```

或者在 Python 中使用原始价格：

```python
df['adj_close'] = df.apply(
    lambda x: x['close'] * x['after_factor'] if x['after_factor'] != 0 else x['close'],
    axis=1
)
```

### Q: 如何处理停牌数据？

停牌期间没有分钟数据。如果需要连续的日期序列，需在应用层填充：

```python
# 创建完整日期范围
date_range = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
df = df.set_index('trade_date').reindex(date_range)
df.fillna(method='ffill', inplace=True)  # 前向填充
```

## 数据更新

当前数据已导入至 2025-10。如需更新新数据：

```bash
# 在 WSL 上运行
cd ~/workspace/quant
python3 migrate.py --year 2025  # 只导入新年份
python3 migrate.py --verify      # 验证数据
```

## 备份与恢复

```bash
# 备份（导出为 Parquet）
clickhouse-client --query "
    SELECT * FROM stock.minute_kline
    INTO OUTFILE '/path/to/backup.parquet'
    FORMAT Parquet
"

# 恢复
clickhouse-client --query "
    INSERT INTO stock.minute_kline
    FROM INFILE '/path/to/backup.parquet'
    FORMAT Parquet
"
```

## 联系与支持

- 迁移脚本: `/Users/lixinfei/workspace/Quant/MigrateToDB/migrate.py`
- 数据源: `/mnt/o/MinuteData/`
- 文档更新日期: 2026-01-30
