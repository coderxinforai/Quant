#!/usr/bin/env python3
"""K线图绘制示例代码"""

from plot_kline import get_client, get_daily_kline, get_stock_name, plot_kline
from datetime import datetime, timedelta

# 连接数据库
client = get_client()
print("已连接到数据库")

# 示例1: 绘制浦发银行最近3个月K线图
print("\n示例1: 浦发银行最近3个月")
code = '600000.SH'
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

df = get_daily_kline(client, code, start_date, end_date, use_adj=True)
stock_name = get_stock_name(client, code)
print(f"获取到 {len(df)} 个交易日的数据")
print(df.head())

# 绘制并保存
title = f"{stock_name} {code} K线图（后复权）"
plot_kline(df, title, save_path='浦发银行_3个月.png')
print("已保存至: 浦发银行_3个月.png")


# 示例2: 绘制平安银行2024年K线图
print("\n示例2: 平安银行2024年")
code = '000001.SZ'
df = get_daily_kline(client, code, '2024-01-01', '2024-12-31', use_adj=True)
stock_name = get_stock_name(client, code)
print(f"获取到 {len(df)} 个交易日的数据")

title = f"{stock_name} {code} 2024年K线图"
plot_kline(df, title, save_path='平安银行_2024.png', style='yahoo')
print("已保存至: 平安银行_2024.png")


# 示例3: 绘制贵州茅台最近半年K线图（不显示成交量）
print("\n示例3: 贵州茅台最近半年")
code = '600519.SH'
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

df = get_daily_kline(client, code, start_date, end_date, use_adj=True)
stock_name = get_stock_name(client, code)
print(f"获取到 {len(df)} 个交易日的数据")

# 添加均线
df['ma5'] = df['close'].rolling(window=5).mean()
df['ma10'] = df['close'].rolling(window=10).mean()
df['ma20'] = df['close'].rolling(window=20).mean()

title = f"{stock_name} {code} 最近半年K线图"
plot_kline(df, title, save_path='贵州茅台_半年.png', style='nightclouds', volume=False)
print("已保存至: 贵州茅台_半年.png")


print("\n所有示例完成！")
