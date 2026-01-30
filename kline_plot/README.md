# A股K线图绘制工具

这是一个从ClickHouse数据库读取A股分钟数据并绘制K线图的Python工具。

## 安装依赖

```bash
cd kline_plot
pip install -r requirements.txt
```

## 使用方法

### 1. 列出可用股票

```bash
python plot_kline.py --list
```

### 2. 绘制K线图（最近90天）

```bash
# 使用默认参数（后复权，最近90天）
python plot_kline.py --code 600000.SH

# 指定天数
python plot_kline.py --code 600000.SH --days 180
```

### 3. 指定日期范围

```bash
python plot_kline.py --code 600000.SH --start 2024-01-01 --end 2024-12-31
```

### 4. 保存图片

```bash
python plot_kline.py --code 600000.SH --save kline.png
```

### 5. 使用不复权价格

```bash
python plot_kline.py --code 600000.SH --no-adj
```

### 6. 自定义图表样式

```bash
# 可选样式: charles, yahoo, nightclouds, sas, starsandstripes
python plot_kline.py --code 600000.SH --style yahoo
```

### 7. 不显示成交量

```bash
python plot_kline.py --code 600000.SH --no-volume
```

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--code` | 股票代码（必需） | `600000.SH` |
| `--start` | 开始日期 | `2024-01-01` |
| `--end` | 结束日期 | `2024-12-31` |
| `--days` | 最近N天（默认90） | `180` |
| `--no-adj` | 不使用复权价格 | - |
| `--save` | 保存图片路径 | `kline.png` |
| `--style` | 图表风格 | `charles` |
| `--no-volume` | 不显示成交量 | - |
| `--list` | 列出可用股票 | - |

## 常用股票代码格式

- 上海股票：`600000.SH`（浦发银行）
- 深圳股票：`000001.SZ`（平安银行）
- 创业板：`300750.SZ`（宁德时代）

## 示例

### 绘制茅台最近一年K线图并保存

```bash
python plot_kline.py --code 600519.SH --days 365 --save 茅台K线.png
```

### 绘制平安银行2024年K线图（不复权）

```bash
python plot_kline.py --code 000001.SZ --start 2024-01-01 --end 2024-12-31 --no-adj
```

### 对比不同风格

```bash
python plot_kline.py --code 600000.SH --style nightclouds
```

## 数据来源

数据来自ClickHouse数据库：
- 主机：192.168.50.90
- 数据库：stock
- 表：minute_kline
- 数据范围：2000-06 至 2025-10
- 数据粒度：分钟级（自动聚合为日K线）

## 注意事项

1. 确保ClickHouse数据库可访问（192.168.50.90:8123）
2. 默认使用后复权价格，适合长期分析
3. 如需原始价格，使用 `--no-adj` 参数
4. 图表支持中文显示
5. 如果显示乱码，请确保系统安装了中文字体
