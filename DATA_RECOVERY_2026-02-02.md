# ClickHouse 数据恢复记录

**日期**: 2026-02-02
**问题**: ClickHouse 数据库连接失败，36.18亿行历史数据"丢失"
**影响**: K线图系统无法访问股票数据
**状态**: ✅ 已完全恢复

---

## 问题症状

### 初始报错
```
ClickHouse连接失败: Database stock does not exist. (UNKNOWN_DATABASE)
```

### 表现
- 后端启动时报告 ClickHouse 数据库连接失败
- `stock.minute_kline` 表不存在
- 系统显示只有 `stock_db.stock_min_adjusted` 表（16行测试数据）
- 前端无法加载K线数据

---

## 问题根源

### 数据路径变更
ClickHouse 配置中的数据路径在某个时间点被重置：

| 项目 | 原配置（正常） | 当前配置（问题） |
|------|---------------|-----------------|
| 数据路径 | `/home/lee/` | `/var/lib/clickhouse/` |
| 数据库名 | `stock` | `stock_db` |
| 表名 | `minute_kline` | `stock_min_adjusted` |
| 列名 | `dt`, `adj_open_after` | `time`, `open_adj_after` |

### 时间线重建

**2025-11-28**
- ClickHouse 安装，使用默认路径 `/var/lib/clickhouse/`
- 通过配置修改，数据实际存储在 `/home/lee/store/`
- 成功导入 36.18 亿行数据（144.77 GiB）

**2026-01-30 03:05-03:16**
- ClickHouse 相关操作
- 创建测试表 `stock_db.stock_min_adjusted`（16行）

**2026-01-31 15:06**
- 后端代码备份
- 配置从"直连本地"改为"SSH隧道连接"

**2026-02-02 11:42**
- ClickHouse 重启
- 配置文件可能被重置为默认值
- 数据路径变更导致无法访问历史数据

---

## 诊断过程

### 1. 初步检查（发现问题）
```bash
# 检查数据库
clickhouse-client -q 'SHOW DATABASES'
# 结果：stock_db 存在，但 stock 数据库为空

# 检查表
clickhouse-client -q 'SHOW TABLES FROM stock_db'
# 结果：只有 stock_min_adjusted（16行）

# 检查数据量
clickhouse-client -q 'SELECT COUNT(*) FROM stock_db.stock_min_adjusted'
# 结果：16 行（严重不符）
```

### 2. 查找原始数据
```bash
# 搜索数据目录
find ~ -name '*clickhouse*' -o -name '*stock*'

# 发现关键目录
~/store/2c8/2c8f8a87-9249-4217-b866-70e216c6a533/
# ✓ 包含 2366 个分片目录
# ✓ 分区从 200006 至 202510
# ✓ 总大小 146GB
```

### 3. 验证数据完整性
```bash
# 检查数据分片
ls ~/store/2c8/2c8f8a87-9249-4217-b866-70e216c6a533/ | wc -l
# 结果：2366 个分片

# 检查目录大小
du -sh ~/store/2c8/2c8f8a87-9249-4217-b866-70e216c6a533/
# 结果：146GB

# 检查符号链接
ls -la ~/data/stock/minute_kline
# 结果：指向 ~/store/2c8/2c8f8a87-9249-4217-b866-70e216c6a533
```

### 4. 确认根本原因
- ClickHouse 当前使用 `/var/lib/clickhouse/` 作为数据目录
- 历史数据位于 `/home/lee/store/`
- 配置文件 `/etc/clickhouse-server/config.xml` 中 `<path>` 被重置为默认值

---

## 解决方案

### 方案选择
采用**修改配置指向原数据路径**方案，优点：
- ✅ 最直接，数据立即可用
- ✅ 不需要移动大量数据
- ✅ 保持原有目录结构
- ❌ 需要 sudo 权限
- ❌ 使用非标准路径

### 详细步骤

#### 步骤 1: 停止 ClickHouse
```bash
# 查找并停止进程
sudo pkill -9 -f clickhouse-server

# 验证停止
ps aux | grep clickhouse-server
```

#### 步骤 2: 修改配置文件
```bash
# 备份配置
sudo cp /etc/clickhouse-server/config.xml \
  /etc/clickhouse-server/config.xml.bak.$(date +%Y%m%d_%H%M%S)

# 修改数据路径
sudo sed -i 's|<path>/var/lib/clickhouse/</path>|<path>/home/lee/</path>|g' \
  /etc/clickhouse-server/config.xml

# 验证修改
sudo grep '<path>' /etc/clickhouse-server/config.xml | head -3
# 输出：<path>/home/lee/</path>
```

#### 步骤 3: 重启 ClickHouse
```bash
# 启动服务
sudo -u clickhouse clickhouse-server \
  --config-file=/etc/clickhouse-server/config.xml \
  --daemon

# 等待启动
sleep 5

# 验证运行
ps aux | grep clickhouse-server
```

#### 步骤 4: 附加数据表
```bash
# 附加原始表
clickhouse-client -q "
ATTACH TABLE stock.minute_kline UUID '2c8f8a87-9249-4217-b866-70e216c6a533'
(
    code LowCardinality(String),
    dt DateTime,
    name LowCardinality(String),
    open Float64,
    close Float64,
    high Float64,
    low Float64,
    volume UInt64,
    amount Float64,
    pct_change Float32,
    amplitude Float32,
    after_factor Float64 DEFAULT 0,
    before_factor Float64 DEFAULT 0,
    adj_open_after Float64 MATERIALIZED open * after_factor,
    adj_close_after Float64 MATERIALIZED close * after_factor,
    adj_high_after Float64 MATERIALIZED high * after_factor,
    adj_low_after Float64 MATERIALIZED low * after_factor,
    adj_open_before Float64 MATERIALIZED open * before_factor,
    adj_close_before Float64 MATERIALIZED close * before_factor,
    adj_high_before Float64 MATERIALIZED high * before_factor,
    adj_low_before Float64 MATERIALIZED low * before_factor,
    trade_date Date MATERIALIZED toDate(dt)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(dt)
ORDER BY (code, dt)
SETTINGS index_granularity = 8192
"
```

#### 步骤 5: 创建符号链接（解决路径映射问题）
```bash
# ClickHouse Atomic 引擎使用固定的 store 路径
# 需要创建符号链接

# DETACH 表
clickhouse-client -q "DETACH TABLE stock.minute_kline"

# 删除空目录
sudo rm -rf /var/lib/clickhouse/store/2c8/2c8f8a87-9249-4217-b866-70e216c6a533

# 创建符号链接
sudo ln -s /home/lee/store/2c8/2c8f8a87-9249-4217-b866-70e216c6a533 \
  /var/lib/clickhouse/store/2c8/2c8f8a87-9249-4217-b866-70e216c6a533

# 修改所有者
sudo chown -h clickhouse:clickhouse \
  /var/lib/clickhouse/store/2c8/2c8f8a87-9249-4217-b866-70e216c6a533

# 修改数据目录权限
sudo chown -R clickhouse:clickhouse /home/lee/store/
sudo chmod -R 755 /home/lee/store/
sudo chmod 755 /home/lee

# 重新 ATTACH
clickhouse-client -q "ATTACH TABLE stock.minute_kline UUID '2c8f8a87-9249-4217-b866-70e216c6a533'"
```

#### 步骤 6: 验证数据恢复
```bash
# 统计总行数
clickhouse-client -q 'SELECT COUNT(*) FROM stock.minute_kline'
# 结果：3,618,210,795 行 ✅

# 统计股票数量和时间范围
clickhouse-client -q '
  SELECT
    COUNT(DISTINCT code) as stocks,
    MIN(dt) as earliest,
    MAX(dt) as latest
  FROM stock.minute_kline'
# 结果：
# stocks: 5,417
# earliest: 2000-06-09 09:30:00
# latest: 2025-10-20 15:00:00 ✅

# 检查数据大小
clickhouse-client -q '
  SELECT formatReadableSize(sum(bytes_on_disk)) as size
  FROM system.parts
  WHERE database = '\''stock'\'' AND table = '\''minute_kline'\'' AND active'
# 结果：144.77 GiB ✅

# 测试查询
clickhouse-client -q '
  SELECT code, name, COUNT(*) as records
  FROM stock.minute_kline
  GROUP BY code, name
  ORDER BY code
  LIMIT 10'
# 结果：返回正常 ✅
```

#### 步骤 7: 修复后端配置
```bash
# 修改 .env 文件
cd kline-backend
vim .env
# 修改：CH_DATABASE=stock_db → CH_DATABASE=stock

# 修复代码列名
# kline_service.py 中：
# time → dt
# open_adj_after → adj_open_after
# (等等)

# 重启后端
pkill -f uvicorn
cd kline-backend
venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
```

#### 步骤 8: 测试 API
```bash
# 测试健康检查
curl http://localhost:8001/health
# 结果：{"status":"ok","ssh_tunnel":true} ✅

# 测试股票搜索
curl "http://localhost:8001/api/stocks/list?keyword=000001&limit=3"
# 结果：找到平安银行，1,443,590 条记录 ✅

# 测试K线数据
curl "http://localhost:8001/api/kline/data?code=000001.SZ&start_date=2024-01-01&end_date=2024-01-10&adj_type=none&period=day"
# 结果：返回 7 个交易日数据 ✅
```

---

## 最终状态

### 数据库状态
```
数据库: stock
表名: minute_kline
总行数: 3,618,210,795 (36.18 亿)
股票数: 5,417 只
数据大小: 144.77 GiB (压缩后)
时间范围: 2000-06-09 至 2025-10-20
分片数: 2,366 个分区
```

### 系统架构
```
数据存储: /home/lee/store/2c8/2c8f8a87-9249-4217-b866-70e216c6a533/
符号链接: /var/lib/clickhouse/store/2c8/... -> ~/store/2c8/...
配置路径: /home/lee/ (config.xml)
数据库引擎: Atomic
表引擎: MergeTree
分区策略: PARTITION BY toYYYYMM(dt)
排序键: ORDER BY (code, dt)
```

### 服务状态
- ✅ ClickHouse 运行正常
- ✅ SSH 隧道连接正常
- ✅ 后端 API 正常响应
- ✅ 前端加载数据正常
- ⚠️ Redis 连接失败（不影响核心功能）

---

## 问题原因总结

1. **配置文件重置**: `/etc/clickhouse-server/config.xml` 中的 `<path>` 被重置为默认值
2. **服务重启**: ClickHouse 在重启时使用了新的默认配置
3. **路径不匹配**: 数据在 `/home/lee/store/`，但 ClickHouse 在 `/var/lib/clickhouse/` 查找
4. **表未关联**: `stock` 数据库存在但为空，历史表未被加载

**可能触发原因**：
- ClickHouse 升级或重装
- 系统更新导致配置重置
- 手动修改后未正确恢复
- WSL 环境重置

---

## 经验教训

### 1. 配置管理
- ❌ 关键配置文件未备份
- ❌ 使用非标准路径但未文档化
- ❌ 配置变更未记录版本

**改进措施**：
```bash
# 备份关键配置
sudo cp /etc/clickhouse-server/config.xml ~/backups/config.xml.$(date +%Y%m%d)

# 使用版本控制
cd /etc/clickhouse-server
sudo git init
sudo git add config.xml
sudo git commit -m "Initial config"
```

### 2. 数据路径规范
- ❌ 混用标准路径和自定义路径
- ❌ 符号链接未文档化
- ❌ 权限设置复杂

**改进措施**：
- 统一使用标准路径，或彻底使用自定义路径
- 文档化所有路径映射关系
- 简化权限模型

### 3. 监控告警
- ❌ 无数据量监控
- ❌ 无配置变更告警
- ❌ 无服务健康检查

**改进措施**：
```python
# 添加数据量监控脚本
def check_data_integrity():
    count = clickhouse_client.query('SELECT COUNT(*) FROM stock.minute_kline')
    if count < 3_000_000_000:  # 少于30亿行
        send_alert(f"数据量异常: {count} 行")
```

### 4. 文档完善
- ❌ 系统架构未文档化
- ❌ 数据恢复流程缺失
- ❌ 应急预案不完整

**改进措施**：
- ✅ 创建本文档
- ✅ 补充架构图
- ✅ 编写运维手册

---

## 预防措施

### 1. 定期备份
```bash
#!/bin/bash
# backup-clickhouse-config.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backups/clickhouse

mkdir -p $BACKUP_DIR

# 备份配置文件
sudo cp /etc/clickhouse-server/config.xml $BACKUP_DIR/config-$DATE.xml

# 备份数据库元数据
clickhouse-client -q "SHOW CREATE DATABASE stock" > $BACKUP_DIR/stock-schema-$DATE.sql
clickhouse-client -q "SHOW CREATE TABLE stock.minute_kline" >> $BACKUP_DIR/stock-schema-$DATE.sql

# 保留最近30天的备份
find $BACKUP_DIR -name "*.xml" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
```

### 2. 健康检查脚本
```bash
#!/bin/bash
# check-clickhouse-health.sh

# 检查服务状态
if ! pgrep -f clickhouse-server > /dev/null; then
    echo "❌ ClickHouse 服务未运行"
    exit 1
fi

# 检查数据量
COUNT=$(clickhouse-client -q "SELECT COUNT(*) FROM stock.minute_kline" 2>/dev/null)
if [ "$COUNT" -lt 3000000000 ]; then
    echo "❌ 数据量异常: $COUNT 行 (期望 > 30亿)"
    exit 1
fi

# 检查数据路径
CONFIG_PATH=$(sudo grep '<path>' /etc/clickhouse-server/config.xml | head -1)
if [[ "$CONFIG_PATH" != *"/home/lee/"* ]]; then
    echo "⚠️ 数据路径配置异常: $CONFIG_PATH"
    exit 1
fi

echo "✅ ClickHouse 健康检查通过"
echo "  - 数据量: $(numfmt --to=si $COUNT) 行"
echo "  - 配置: $CONFIG_PATH"
```

### 3. 配置锁定
```bash
# 防止配置文件被意外修改
sudo chattr +i /etc/clickhouse-server/config.xml

# 解锁（需要时）
sudo chattr -i /etc/clickhouse-server/config.xml
```

### 4. 文档更新
在 `CLAUDE.md` 中添加：
```markdown
## ClickHouse 关键配置

### 数据路径
- 配置文件: `/etc/clickhouse-server/config.xml`
- 配置项: `<path>/home/lee/</path>`
- 实际数据: `~/store/2c8/2c8f8a87-9249-4217-b866-70e216c6a533/`
- 符号链接: `/var/lib/clickhouse/store/2c8/... -> ~/store/2c8/...`

⚠️ **警告**: 修改 `<path>` 配置会导致数据无法访问！

### 数据恢复
如数据丢失，参考: `DATA_RECOVERY_2026-02-02.md`
```

---

## 快速参考命令

### 检查数据状态
```bash
# 数据量
clickhouse-client -q 'SELECT COUNT(*) FROM stock.minute_kline'

# 数据大小
clickhouse-client -q 'SELECT formatReadableSize(sum(bytes_on_disk)) FROM system.parts WHERE database='\''stock'\'' AND active'

# 股票数量
clickhouse-client -q 'SELECT COUNT(DISTINCT code) FROM stock.minute_kline'
```

### 查看配置
```bash
# 数据路径
sudo grep '<path>' /etc/clickhouse-server/config.xml

# 数据库列表
clickhouse-client -q 'SHOW DATABASES'

# 表结构
clickhouse-client -q 'SHOW CREATE TABLE stock.minute_kline'
```

### 服务管理
```bash
# 停止服务
sudo pkill -9 -f clickhouse-server

# 启动服务
sudo -u clickhouse clickhouse-server --config-file=/etc/clickhouse-server/config.xml --daemon

# 查看进程
ps aux | grep clickhouse-server
```

---

## 联系人与参考

**责任人**: lixinfei
**恢复日期**: 2026-02-02
**恢复时长**: ~4 小时
**协助**: Claude Sonnet 4.5

**相关文档**:
- ClickHouse 官方文档: https://clickhouse.com/docs
- 项目架构: `CLAUDE.md`
- 部署文档: `DOCKER.md`
- 开发流程: `DEVELOPMENT.md`

---

**文档版本**: 1.0
**最后更新**: 2026-02-02 13:30
