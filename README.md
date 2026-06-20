# stock-screening - A股实时筛选工具 (仅限中国)

基于实时行情数据，自动筛选满足技术形态条件的A股股票，支持董监高增持次数过滤。

## 功能特性

- **多数据源容错**：自动依次尝试新浪财经 → 东方财富 → 雪球 → akshare，确保数据获取的稳定性
- **三大技术筛选条件**：
  1. **今开 > 昨收 × (1 + 允许低开幅度)** — 过滤大幅低开
  2. **现价 > 昨收 × (1 + 允许收盘跌幅)** — 过滤大幅收跌
  3. **现价 > 今开 × (1 + 允许假阴线幅度)** — 过滤假阴线
- **董监高增持过滤**：获取近半年董监高增持数据，按增持次数筛选（可选）
- **结果导出**：筛选结果自动保存为 CSV 文件，方便后续分析
- **交互式参数设置**：运行时可自定义各项筛选阈值

## 环境依赖

- Python 3.8+
- [akshare](https://github.com/akfamily/akshare)
- [pandas](https://pandas.pydata.org/)
- [curl_cffi](https://github.com/yifeikong/curl_cffi)

## 安装

```bash
pip install akshare pandas curl_cffi
```

## 使用方法

```bash
python dzh.py
```

运行后按提示输入筛选参数，直接回车可使用默认值：

```
请设置筛选条件（直接回车使用默认值）
============================================================

  允许低开幅度 [今开 > 昨收 × (1 + 此值)] (默认 -3.0%):
  允许收盘跌幅 [现价 > 昨收 × (1 + 此值)] (默认 -2.0%):
  允许假阴线幅度 [现价 > 今开 × (1 + 此值)] (默认 -3.0%):

  近半年增持最少次数 (默认 1, 输入 0 跳过此条件):
```

### 默认筛选条件

| 参数 | 默认值 | 含义 |
|------|--------|------|
| 允许低开幅度 | -3.0% | 允许今日开盘价比昨日收盘价最多低开 3% |
| 允许收盘跌幅 | -2.0% | 允许最新价比昨日收盘价最多跌 2% |
| 允许假阴线幅度 | -3.0% | 允许最新价比今日开盘价最多低 3%（假阴线） |
| 增持最少次数 | 1 | 近半年董监高增持至少 1 次（输入 0 可跳过） |

## 输出字段

筛选结果包含以下字段：

| 字段 | 说明 |
|------|------|
| 股票代码 | 6位股票代码 |
| 股票名称 | 股票简称 |
| 今日开盘 | 今日开盘价 |
| 今日收盘 | 最新价（收盘价） |
| 昨日收盘 | 昨日收盘价 |
| 开盘涨幅% | 今日开盘相对昨收的涨幅 |
| 收盘涨幅% | 最新价相对昨收的涨幅 |
| 阳线实体% | 收盘价相对开盘价的涨幅 |
| 近半年增持 | 近半年董监高增持次数（启用时显示） |

结果会保存为 `selected_stocks_YYYYMMDD_HHMM.csv` 文件。

## 数据源架构

程序采用多级降级策略获取数据：

```
新浪财经 ──失败──→ 东方财富 ──失败──→ 雪球 ──失败──→ akshare
```

董监高增持数据同样采用双源备份：

```
雪球直连接口 ──失败──→ akshare 雪球接口
```

## 注意事项

- 运行时需要网络连接
- 如遇数据获取失败，建议等待 30 分钟后重试或更换网络环境
- 参数输入支持两种格式：`-3`（表示 -3%）和 `-0.03`（小数形式）
- 雪球接口通过模拟浏览器请求获取数据，无需真实账号

---

# stock-screening - A-Share Real-Time Stock Screener (China only)

Automatically screen A-share stocks that meet specific technical pattern criteria based on real-time market data, with insider (directors, supervisors, and senior management) share purchase filtering support.

## Features

- **Multi-source fault tolerance**: Automatically falls back through Sina Finance → East Money → Xueqiu → akshare to ensure stable data retrieval
- **Three technical screening conditions**:
  1. **Today's Open > Yesterday's Close × (1 + allowed gap)** — Filter large gap-down opens
  2. **Current Price > Yesterday's Close × (1 + allowed decline)** — Filter significant closing declines
  3. **Current Price > Today's Open × (1 + allowed fake-candlestick range)** — Filter bearish fake candlesticks
- **Insider share purchase filtering**: Fetches the last 6 months of insider buy/sell records and filters by purchase count (optional)
- **Result export**: Screening results are automatically saved as CSV files for further analysis
- **Interactive parameter input**: Customize all screening thresholds at runtime

## Requirements

- Python 3.8+
- [akshare](https://github.com/akfamily/akshare)
- [pandas](https://pandas.pydata.org/)
- [curl_cffi](https://github.com/yifeikong/curl_cffi)

## Installation

```bash
pip install akshare pandas curl_cffi
```

## Usage

```bash
python dzh.py
```

After launching, follow the prompts to enter screening parameters. Press Enter to accept the default values:

```
请设置筛选条件（直接回车使用默认值）
============================================================

  允许低开幅度 [今开 > 昨收 × (1 + 此值)] (默认 -3.0%):
  允许收盘跌幅 [现价 > 昨收 × (1 + 此值)] (默认 -2.0%):
  允许假阴线幅度 [现价 > 今开 × (1 + 此值)] (默认 -3.0%):

  近半年增持最少次数 (默认 1, 输入 0 跳过此条件):
```

### Default Screening Criteria

| Parameter | Default | Description |
|-----------|---------|-------------|
| Allowed open gap | -3.0% | Today's open can be up to 3% below yesterday's close |
| Allowed closing decline | -2.0% | Current price can be up to 2% below yesterday's close |
| Allowed fake bearish candle range | -3.0% | Current price can be up to 3% below today's open (fake bearish candle) |
| Minimum insider purchases | 1 | At least 1 insider purchase in the last 6 months (enter 0 to skip) |

## Output Fields

Screening results contain the following columns:

| Field | Description |
|-------|-------------|
| 股票代码 (Stock Code) | 6-digit stock ticker |
| 股票名称 (Stock Name) | Stock abbreviation |
| 今日开盘 (Today's Open) | Opening price |
| 今日收盘 (Today's Close) | Current / closing price |
| 昨日收盘 (Yesterday's Close) | Previous closing price |
| 开盘涨幅% (Open Change %) | Open price change relative to yesterday's close |
| 收盘涨幅% (Close Change %) | Current price change relative to yesterday's close |
| 阳线实体% (Candle Body %) | Close price change relative to open price |
| 近半年增持 (Insider Purchases) | Number of insider purchases in the last 6 months (shown when enabled) |

Results are saved as `selected_stocks_YYYYMMDD_HHMM.csv`.

## Data Source Architecture

The program uses a multi-level fallback strategy for data retrieval:

```
Sina Finance ──fail──→ East Money ──fail──→ Xueqiu ──fail──→ akshare
```

Insider purchase data also uses a dual-source backup:

```
Xueqiu direct API ──fail──→ akshare Xueqiu API
```

## Notes

- An active internet connection is required
- If data retrieval fails, wait 30 minutes and retry, or switch to a different network
- Parameter input supports two formats: `-3` (meaning -3%) or `-0.03` (decimal form)
- The Xueqiu API fetches data by simulating browser requests; no real account is needed
