#!/bin/bash

# 更新 stock_info 表脚本
# 当有新股票上市或需要刷新统计数据时运行此脚本

echo "========== 更新 stock_info 表 =========="

# 清空旧数据
echo "1. 清空旧数据..."
ssh wsl "clickhouse-client -q 'TRUNCATE TABLE stock.stock_info'"

# 从 minute_kline 重新提取数据
echo "2. 从 minute_kline 提取数据..."
ssh wsl "clickhouse-client -q \"
INSERT INTO stock.stock_info (code, name, market, records, first_date, last_date)
SELECT
    code,
    any(name) AS name,
    CASE
        WHEN code LIKE '%.SH' THEN 'SH'
        WHEN code LIKE '%.SZ' THEN 'SZ'
        WHEN code LIKE '%.BJ' THEN 'BJ'
        ELSE 'UNKNOWN'
    END AS market,
    count() AS records,
    min(trade_date) AS first_date,
    max(trade_date) AS last_date
FROM stock.minute_kline
GROUP BY code
\""

# 验证数据
echo "3. 验证数据..."
STOCK_COUNT=$(ssh wsl "clickhouse-client -q 'SELECT count(*) FROM stock.stock_info'")
echo "✅ 股票信息表已更新，共 $STOCK_COUNT 只股票"

echo "========== 更新完成 =========="
