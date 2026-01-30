#!/usr/bin/env python3
"""A股分钟K线数据迁移至 ClickHouse"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import clickhouse_connect
from tqdm import tqdm

# ── 配置 ──────────────────────────────────────────────────────────────────────

DATA_ROOT = Path("/mnt/o/MinuteData")
MIN_DIR = DATA_ROOT / "min"
AFTER_DIR = DATA_ROOT / "after"
BEFORE_DIR = DATA_ROOT / "before"

PROGRESS_FILE = Path.home() / ".migrate_progress.json"
BATCH_SIZE = 100_000

CH_HOST = "localhost"
CH_PORT = 8123
CH_DATABASE = "stock"

CREATE_DB_SQL = "CREATE DATABASE IF NOT EXISTS stock"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock.minute_kline (
    code         LowCardinality(String),
    dt           DateTime,
    name         LowCardinality(String),
    open         Float64,
    close        Float64,
    high         Float64,
    low          Float64,
    volume       UInt64,
    amount       Float64,
    pct_change   Float32,
    amplitude    Float32,
    after_factor  Float64 DEFAULT 0,
    before_factor Float64 DEFAULT 0,
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
  SETTINGS index_granularity = 8192
"""

COLUMN_NAMES = [
    "code", "dt", "name", "open", "close", "high", "low",
    "volume", "amount", "pct_change", "amplitude",
    "after_factor", "before_factor",
]


# ── 代码格式转换 ──────────────────────────────────────────────────────────────

def min_code_to_standard(raw: str) -> str:
    """'sh600000' → '600000.SH', 'sz000001' → '000001.SZ'"""
    prefix = raw[:2].upper()  # SH / SZ
    num = raw[2:]
    return f"{num}.{prefix}"


def extract_code_from_filename(filename: str) -> str:
    """'sh600000_2024.csv' → 'sh600000'"""
    return filename.split("_")[0]


# ── 复权因子加载 ──────────────────────────────────────────────────────────────

class FactorCache:
    """懒加载 + 缓存复权因子，每个股票只从文件读取一次"""

    def __init__(self):
        self._after: dict[str, dict[int, float]] = {}   # code → {date_int: factor}
        self._before: dict[str, dict[int, float]] = {}

    def _load_factor_file(self, filepath: Path) -> dict[int, float]:
        """加载单个复权因子 CSV，返回 {date_int: factor}"""
        factors: dict[int, float] = {}
        if not filepath.exists():
            return factors
        with open(filepath, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                return factors
            for row in reader:
                if len(row) < 3:
                    continue
                # 列: 股票代码, 交易日期(YYYYMMDD), 复权因子
                try:
                    date_int = int(row[1])
                    factor = float(row[2])
                    factors[date_int] = factor
                except (ValueError, IndexError):
                    continue
        return factors

    def get_after(self, std_code: str, date_int: int) -> float:
        if std_code not in self._after:
            self._after[std_code] = self._load_factor_file(
                AFTER_DIR / f"{std_code}.csv"
            )
        return self._after[std_code].get(date_int, 0.0)

    def get_before(self, std_code: str, date_int: int) -> float:
        if std_code not in self._before:
            self._before[std_code] = self._load_factor_file(
                BEFORE_DIR / f"{std_code}.csv"
            )
        return self._before[std_code].get(date_int, 0.0)


# ── 进度追踪 ──────────────────────────────────────────────────────────────────

class ProgressTracker:
    """JSON 文件记录已导入的文件路径（相对于 MIN_DIR）"""

    def __init__(self, filepath: Path = PROGRESS_FILE):
        self.filepath = filepath
        self.done: set[str] = set()
        self._load()

    def _load(self):
        if self.filepath.exists():
            with open(self.filepath, encoding="utf-8") as f:
                data = json.load(f)
            self.done = set(data.get("done", []))

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump({"done": sorted(self.done)}, f, ensure_ascii=False)

    def is_done(self, rel_path: str) -> bool:
        return rel_path in self.done

    def mark_done(self, rel_path: str):
        self.done.add(rel_path)

    def reset(self):
        self.done.clear()
        if self.filepath.exists():
            self.filepath.unlink()


# ── CSV 解析 ──────────────────────────────────────────────────────────────────

def parse_minute_csv(filepath: Path, std_code: str, factor_cache: FactorCache) -> list[tuple]:
    """
    解析一个分钟 CSV 文件，返回行列表。
    CSV 列: 时间, 代码, 名称, 开盘价, 收盘价, 最高价, 最低价, 成交量, 成交额, 涨幅, 振幅
    """
    rows: list[tuple] = []
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader, None)  # 跳过表头
        for row in reader:
            if len(row) < 11:
                continue
            try:
                dt_str = row[0]         # '2024-01-02 09:31:00'
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                name = row[2]
                open_ = float(row[3])
                close = float(row[4])
                high = float(row[5])
                low = float(row[6])
                volume = int(float(row[7]))
                amount = float(row[8])
                pct_change = float(row[9])
                amplitude = float(row[10])

                # 提取日期整数用于因子查找
                date_int = int(dt_str[:10].replace("-", ""))
                af = factor_cache.get_after(std_code, date_int)
                bf = factor_cache.get_before(std_code, date_int)

                rows.append((
                    std_code, dt, name,
                    open_, close, high, low,
                    volume, amount,
                    pct_change, amplitude,
                    af, bf,
                ))
            except (ValueError, IndexError):
                continue
    return rows


# ── ClickHouse 操作 ───────────────────────────────────────────────────────────

def get_client() -> clickhouse_connect.driver.Client:
    return clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT)


def init_database(client):
    client.command(CREATE_DB_SQL)
    client.command(CREATE_TABLE_SQL)
    print("数据库和表已就绪")


def insert_rows(client, rows: list[tuple]):
    """批量插入数据"""
    if not rows:
        return
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        client.insert(
            "stock.minute_kline",
            batch,
            column_names=COLUMN_NAMES,
        )


def reset_table(client):
    client.command("DROP TABLE IF EXISTS stock.minute_kline")
    client.command(CREATE_TABLE_SQL)
    print("表已重建")


# ── 文件收集 ──────────────────────────────────────────────────────────────────

def collect_csv_files(year: str | None = None, stock: str | None = None) -> list[Path]:
    """收集待处理的 CSV 文件列表。年份目录格式: 2024_1min"""
    files: list[Path] = []

    if year:
        # 支持传入 '2024' 或 '2024_1min'
        year_dir_name = year if "_" in year else f"{year}_1min"
        year_dirs = [MIN_DIR / year_dir_name]
    else:
        year_dirs = sorted(
            d for d in MIN_DIR.iterdir() if d.is_dir()
        )

    for yd in year_dirs:
        if not yd.exists():
            print(f"警告: 目录不存在 {yd}")
            continue
        for csv_file in sorted(yd.glob("*.csv")):
            if stock:
                raw_code = extract_code_from_filename(csv_file.name)
                if raw_code != stock:
                    continue
            files.append(csv_file)

    return files


# ── 验证 ──────────────────────────────────────────────────────────────────────

def verify(client):
    print("=" * 60)
    print("数据验证")
    print("=" * 60)

    # 总行数
    total = client.command("SELECT count() FROM stock.minute_kline")
    print(f"\n总行数: {total:,}")

    # 不同股票数
    codes = client.command("SELECT uniq(code) FROM stock.minute_kline")
    print(f"不同股票数: {codes}")

    # 时间范围
    min_dt = client.command("SELECT min(dt) FROM stock.minute_kline")
    max_dt = client.command("SELECT max(dt) FROM stock.minute_kline")
    print(f"时间范围: {min_dt} ~ {max_dt}")

    # 各年份行数
    print("\n各年份行数:")
    result = client.query(
        "SELECT toYear(dt) AS y, count() AS c FROM stock.minute_kline GROUP BY y ORDER BY y"
    )
    for row in result.result_rows:
        print(f"  {row[0]}: {row[1]:,}")

    # 复权因子覆盖率
    total_rows = client.command("SELECT count() FROM stock.minute_kline")
    after_nonzero = client.command(
        "SELECT count() FROM stock.minute_kline WHERE after_factor != 0"
    )
    before_nonzero = client.command(
        "SELECT count() FROM stock.minute_kline WHERE before_factor != 0"
    )
    if total_rows > 0:
        print(f"\n后复权因子覆盖率: {after_nonzero / total_rows * 100:.2f}%")
        print(f"前复权因子覆盖率: {before_nonzero / total_rows * 100:.2f}%")

    # 抽样: 600000.SH 在 2024-01-02
    print("\n抽样数据 (600000.SH, 2024-01-02 前5行):")
    sample = client.query(
        "SELECT code, dt, name, open, close, high, low, volume, amount, "
        "pct_change, amplitude, after_factor, before_factor "
        "FROM stock.minute_kline "
        "WHERE code = '600000.SH' AND toDate(dt) = '2024-01-02' "
        "ORDER BY dt LIMIT 5"
    )
    for row in sample.result_rows:
        print(f"  {row}")

    # 前复权因子负值统计
    neg_before = client.command(
        "SELECT count() FROM stock.minute_kline WHERE before_factor < 0"
    )
    print(f"\n前复权因子负值行数: {neg_before}")

    print("\n" + "=" * 60)


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    global DATA_ROOT, MIN_DIR, AFTER_DIR, BEFORE_DIR, CH_HOST, CH_PORT

    parser = argparse.ArgumentParser(description="A股分钟K线数据迁移至 ClickHouse")
    parser.add_argument("--year", type=str, help="只导入指定年份 (如 2024)")
    parser.add_argument("--stock", type=str, help="只导入指定股票 (如 sh600000)")
    parser.add_argument("--verify", action="store_true", help="验证已导入数据")
    parser.add_argument("--reset", action="store_true", help="清空表和进度，重新开始")
    parser.add_argument("--host", type=str, default=CH_HOST, help="ClickHouse 主机")
    parser.add_argument("--port", type=int, default=CH_PORT, help="ClickHouse 端口")
    parser.add_argument("--data-root", type=str, default=str(DATA_ROOT), help="数据根目录")
    args = parser.parse_args()

    # 允许覆盖路径和连接参数
    data_root = Path(args.data_root)
    DATA_ROOT = data_root
    MIN_DIR = data_root / "min"
    AFTER_DIR = data_root / "after"
    BEFORE_DIR = data_root / "before"
    CH_HOST = args.host
    CH_PORT = args.port

    client = clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT)

    if args.reset:
        reset_table(client)
        ProgressTracker().reset()
        print("已重置，可重新导入")
        return

    init_database(client)

    if args.verify:
        verify(client)
        return

    # ── 导入流程 ──
    factor_cache = FactorCache()
    tracker = ProgressTracker()

    csv_files = collect_csv_files(year=args.year, stock=args.stock)
    if not csv_files:
        print("未找到匹配的 CSV 文件")
        return

    print(f"待处理文件: {len(csv_files)} 个")
    skipped = 0
    imported = 0
    total_rows = 0
    errors = 0

    for csv_file in tqdm(csv_files, desc="导入进度", unit="文件"):
        rel_path = str(csv_file.relative_to(MIN_DIR))

        if tracker.is_done(rel_path):
            skipped += 1
            continue

        raw_code = extract_code_from_filename(csv_file.name)
        std_code = min_code_to_standard(raw_code)

        try:
            rows = parse_minute_csv(csv_file, std_code, factor_cache)
            insert_rows(client, rows)
            tracker.mark_done(rel_path)
            imported += 1
            total_rows += len(rows)

            # 每100个文件保存一次进度
            if imported % 100 == 0:
                tracker.save()
        except Exception as e:
            errors += 1
            tqdm.write(f"错误 [{csv_file}]: {e}")

    tracker.save()
    print(f"\n完成: 导入 {imported} 个文件, 跳过 {skipped} 个, 错误 {errors} 个, 共 {total_rows:,} 行")


if __name__ == "__main__":
    main()
