# A股分钟数据迁移至 ClickHouse

## 数据概况

| 目录 | 大小 | 文件数 | 说明 |
|------|------|--------|------|
| `min/` | 281GB | 26个年度目录，每年~5112个CSV | 分钟K线数据 |
| `after/` | 605MB | 5758个CSV | 后复权因子 |
| `before/` | 593MB | 5758个CSV | 前复权因子 |

**分钟数据列**: 时间, 代码, 名称, 开盘价, 收盘价, 最高价, 最低价, 成交量, 成交额, 涨幅, 振幅
**复权因子列**: 股票代码, 交易日期(YYYYMMDD), 复权因子
**代码映射**: `sh600000` → `600000.SH`, `sz000001` → `000001.SZ`
**复权公式**: `复权价格 = 原始价格 * 复权因子`

## 方案概要

用 Python 脚本在 WSL 上运行，逐文件读取分钟 CSV，同时查找对应的复权因子，合并后批量写入 ClickHouse 单表。

## 1. ClickHouse 表结构

```sql
CREATE DATABASE IF NOT EXISTS stock;

CREATE TABLE stock.minute_kline (
    code         LowCardinality(String),   -- '600000.SH'
    dt           DateTime,                  -- '2024-01-02 09:30:00'
    name         LowCardinality(String),   -- '浦发银行'
    open         Float64,
    close        Float64,
    high         Float64,
    low          Float64,
    volume       UInt64,
    amount       Float64,
    pct_change   Float32,                  -- 涨幅
    amplitude    Float32,                  -- 振幅
    after_factor  Float64 DEFAULT 0,       -- 后复权因子
    before_factor Float64 DEFAULT 0,       -- 前复权因子
    -- MATERIALIZED: 自动计算，不需在INSERT中提供
    adj_open_after   Float64 MATERIALIZED open * after_factor,
    adj_close_after  Float64 MATERIALIZED close * after_factor,
    adj_high_after   Float64 MATERIALIZED high * after_factor,
    adj_low_after    Float64 MATERIALIZED low * after_factor,
    adj_open_before  Float64 MATERIALIZED open * before_factor,
    adj_close_before Float64 MATERIALIZED close * before_factor,
    adj_high_before  Float64 MATERIALIZED high * before_factor,
    adj_low_before   Float64 MATERIALIZED low * before_factor,
    trade_date Date MATERIALIZED toDate(dt)
) ENGINE = MergeTree()
  PARTITION BY toYYYYMM(dt)
  ORDER BY (code, dt)
  SETTINGS index_granularity = 8192;
```

**设计要点**:
- `LowCardinality(String)` 对 code/name 做字典编码，节省空间
- 按月分区 (`toYYYYMM`)，约300个分区，便于日期范围查询
- 排序键 `(code, dt)` 优化按股票查时间序列的场景
- MATERIALIZED 列在写入时由 ClickHouse 自动计算复权价格

## 2. Python 脚本结构

**单文件**: `migrate.py`，部署到 WSL 的 `~/migrate_to_clickhouse/`
**依赖**: `clickhouse-connect`, `tqdm`

### 核心模块

```
migrate.py
├── 代码格式转换  min_code_to_standard('sh600000') → '600000.SH'
├── 复权因子加载  按股票代码加载 after/before 因子到 dict{date_int: factor}
├── 因子缓存      FactorCache: 懒加载 + 缓存，每个股票只加载一次
├── 进度追踪      ProgressTracker: JSON文件记录已导入的文件
├── CSV解析       逐行解析分钟CSV，查找因子，组装行数据
├── ClickHouse操作 建表、批量插入(10万行/批)
├── 验证          --verify 运行校验查询
└── 命令行入口    支持 --year/--stock/--verify/--reset 参数
```

### 数据流

```
CSV文件 → 提取股票代码 → 加载复权因子(缓存) → 逐行解析+因子查找 → 批量INSERT → 标记已完成
```

## 3. 关键实现细节

### 代码格式映射
- 分钟文件名 `sh600000_2024.csv` → 提取 `sh600000` → 标准化 `600000.SH`
- 复权文件名 `600000.SH.csv` → 标准化 `600000.SH`
- ClickHouse 中统一存储标准格式 `600000.SH`

### 因子匹配
- 复权因子是日粒度，分钟数据是分钟粒度
- Python 端从 datetime 字符串提取日期整数: `'2024-01-02 09:30:00'[:10].replace('-','')` → `20240102`
- 用 dict 查找 O(1) 匹配因子
- 无匹配的因子默认为 0

### BOM 处理
- CSV 文件带 UTF-8 BOM (EF BB BF)
- 使用 `encoding='utf-8-sig'` 自动去除

### 断点续传
- `~/.migrate_progress.json` 记录已导入文件的相对路径
- 重启脚本自动跳过已导入文件
- 文件级粒度（每文件~58K行，一次批量完成）

### 命令行参数
```bash
python3 migrate.py                  # 全量导入
python3 migrate.py --year 2024      # 只导入2024年
python3 migrate.py --stock sh600000 # 只导入特定股票
python3 migrate.py --verify         # 验证数据
python3 migrate.py --reset          # 清空表和进度，重新开始
```

## 4. 文件清单

| 文件 | 位置 | 说明 |
|------|------|------|
| `migrate.py` | 项目根目录 | 主脚本 |
| `requirements.txt` | 项目根目录 | Python 依赖 |

## 5. 部署和执行步骤

```bash
# 在 WSL 上操作

# 1. 手动启动 ClickHouse
sudo clickhouse-server --daemon

# 2. 安装依赖
pip3 install clickhouse-connect tqdm

# 3. 从 Mac 拷贝脚本（或直接在 WSL 编辑）
scp user@mac:~/workspace/Quant/MigrateToDB/migrate.py ~/migrate_to_clickhouse/

# 4. 先测试单个年份
python3 migrate.py --year 2024

# 5. 验证
python3 migrate.py --verify

# 6. 全量导入
python3 migrate.py 2>&1 | tee migrate_output.log
```

## 6. 验证方案

`--verify` 执行以下检查:
- 总行数（预期约25亿行）
- 不同股票数（预期5400-5700）
- 时间范围（2000-06 到 2025-最新）
- 各年份行数分布
- 复权因子覆盖率
- 抽样对比: `600000.SH` 在 2024-01-02 的数据与 CSV 原文对比
- 前复权因子负值统计

## 7. 性能说明

- 每文件约58K行，处理约0.5秒/文件
- 共约67000个文件
- `/mnt/o/` 是 WSL 访问 Windows NTFS，读取较慢
- 如需加速可先 `cp -r /mnt/o/MinuteData/ ~/MinuteData/` 拷贝到 WSL 本地文件系统
- ClickHouse 压缩后预计占用 30-50GB 磁盘
