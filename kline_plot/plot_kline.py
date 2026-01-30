#!/usr/bin/env python3
"""A股K线图绘制工具"""

import argparse
from datetime import datetime, timedelta
import clickhouse_connect
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt

# 配置
CH_HOST = '192.168.50.90'
CH_PORT = 8123
CH_DATABASE = 'stock'

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def get_client():
    """连接ClickHouse数据库"""
    return clickhouse_connect.get_client(
        host=CH_HOST,
        port=CH_PORT,
        database=CH_DATABASE
    )


def get_daily_kline(client, code, start_date, end_date, use_adj=True):
    """
    获取日K线数据

    Args:
        client: ClickHouse客户端
        code: 股票代码，如 '600000.SH'
        start_date: 开始日期，格式 'YYYY-MM-DD'
        end_date: 结束日期，格式 'YYYY-MM-DD'
        use_adj: 是否使用后复权价格

    Returns:
        DataFrame: 日K线数据
    """
    if use_adj:
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

    result = client.query(query)
    df = result.result_as_pandas()

    if df.empty:
        raise ValueError(f"未找到股票 {code} 在 {start_date} 至 {end_date} 的数据")

    return df


def get_stock_name(client, code):
    """获取股票名称"""
    query = f"""
        SELECT name
        FROM stock.minute_kline
        WHERE code = '{code}'
        LIMIT 1
    """
    result = client.query(query)
    rows = result.result_rows
    if rows:
        return rows[0][0]
    return code


def plot_kline(df, title, save_path=None, style='charles', volume=True):
    """
    绘制K线图

    Args:
        df: K线数据DataFrame
        title: 图表标题
        save_path: 保存路径，None则显示
        style: 图表风格，可选 'charles', 'yahoo', 'nightclouds' 等
        volume: 是否显示成交量
    """
    # 设置索引
    df_plot = df.copy()
    df_plot.set_index('trade_date', inplace=True)
    df_plot.index = pd.to_datetime(df_plot.index)

    # 重命名列以符合mplfinance要求
    df_plot.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)

    # 选择必需的列
    df_plot = df_plot[['Open', 'High', 'Low', 'Close', 'Volume']]

    # 绘制K线图
    kwargs = {
        'type': 'candle',
        'volume': volume,
        'title': title,
        'style': style,
        'figsize': (14, 8),
        'ylabel': '价格',
        'ylabel_lower': '成交量',
    }

    if save_path:
        kwargs['savefig'] = save_path
    else:
        kwargs['show_nontrading'] = False

    mpf.plot(df_plot, **kwargs)

    if not save_path:
        plt.show()


def list_stocks(client, limit=20):
    """列出数据库中的股票"""
    query = f"""
        SELECT code, any(name) AS name, count() AS records
        FROM stock.minute_kline
        GROUP BY code
        ORDER BY code
        LIMIT {limit}
    """
    result = client.query(query)
    df = result.result_as_pandas()
    print("\n股票列表（前{}只）:".format(limit))
    print(df.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description='A股K线图绘制工具')
    parser.add_argument('--code', type=str, help='股票代码，如 600000.SH')
    parser.add_argument('--start', type=str, help='开始日期，格式 YYYY-MM-DD')
    parser.add_argument('--end', type=str, help='结束日期，格式 YYYY-MM-DD')
    parser.add_argument('--days', type=int, default=90, help='最近N天（默认90天）')
    parser.add_argument('--no-adj', action='store_true', help='不使用复权价格')
    parser.add_argument('--save', type=str, help='保存图片路径')
    parser.add_argument('--style', type=str, default='charles',
                       choices=['charles', 'yahoo', 'nightclouds', 'sas', 'starsandstripes'],
                       help='图表风格')
    parser.add_argument('--no-volume', action='store_true', help='不显示成交量')
    parser.add_argument('--list', action='store_true', help='列出可用股票')

    args = parser.parse_args()

    # 连接数据库
    print("正在连接数据库...")
    try:
        client = get_client()
        print(f"已连接到 {CH_HOST}:{CH_PORT}/{CH_DATABASE}")
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return

    # 列出股票
    if args.list:
        list_stocks(client)
        return

    # 检查必需参数
    if not args.code:
        print("错误: 请指定股票代码 --code")
        print("提示: 使用 --list 查看可用股票")
        return

    # 确定日期范围
    if args.end:
        end_date = args.end
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')

    if args.start:
        start_date = args.start
    else:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=args.days)
        start_date = start_dt.strftime('%Y-%m-%d')

    # 获取数据
    print(f"正在获取 {args.code} 从 {start_date} 到 {end_date} 的数据...")
    try:
        df = get_daily_kline(client, args.code, start_date, end_date, use_adj=not args.no_adj)
        print(f"获取到 {len(df)} 个交易日的数据")
    except Exception as e:
        print(f"获取数据失败: {e}")
        return

    # 获取股票名称
    try:
        stock_name = get_stock_name(client, args.code)
    except:
        stock_name = args.code

    # 绘制K线图
    adj_text = "（后复权）" if not args.no_adj else ""
    title = f"{stock_name} {args.code} K线图{adj_text}"

    print("正在绘制K线图...")
    try:
        plot_kline(df, title,
                  save_path=args.save,
                  style=args.style,
                  volume=not args.no_volume)
        if args.save:
            print(f"图表已保存至: {args.save}")
        else:
            print("图表已显示")
    except Exception as e:
        print(f"绘制失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
