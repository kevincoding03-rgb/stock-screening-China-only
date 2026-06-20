import akshare as ak
import pandas as pd
import time
import random
from datetime import datetime, timedelta
from curl_cffi import requests as curl_requests

# ========== 默认参数（交互输入时直接回车使用） ==========
# open_gap: -0.03 (允许低开3%)
# close_up: -0.02 (允许微跌2%)
# close_above_open: -0.03 (允许假阴线3%)
# =================================================

def fetch_all_stocks_robustly():
    """使用 curl_cffi + 新浪财经接口获取全市场数据"""
    url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
    page_size = 80  # 新浪每页最多80条

    for attempt in range(3):
        try:
            time.sleep(random.uniform(2, 4))
            print(f"正在获取数据（第 {attempt+1} 次尝试）...")

            all_rows = []
            page = 1
            while True:
                req_params = {
                    "page": str(page),
                    "num": str(page_size),
                    "sort": "symbol",
                    "asc": "1",
                    "node": "hs_a",
                    "symbol": "",
                    "_s_r_a": "sort",
                }
                response = curl_requests.get(
                    url,
                    params=req_params,
                    impersonate="chrome",
                    timeout=30,
                )
                response.raise_for_status()
                rows = response.json()

                if not rows:
                    break

                all_rows.extend(rows)
                if page == 1:
                    print(f"  分页获取中...")
                if page % 10 == 0 or len(rows) < page_size:
                    print(f"  第 {page} 页: 累计 {len(all_rows)} 只")

                if len(rows) < page_size:
                    break
                page += 1
                time.sleep(random.uniform(0.5, 1.0))

            if all_rows:
                df = pd.DataFrame(all_rows)
                df = df.rename(columns={
                    "code": "代码", "name": "名称",
                    "open": "今开", "trade": "最新价", "settlement": "昨收",
                })
                df = df[["代码", "名称", "今开", "最新价", "昨收"]]
                return df
            else:
                print("返回数据为空，重试中...")
        except Exception as e:
            print(f"第 {attempt+1} 次尝试失败: {e}")
            if attempt < 2:
                time.sleep(5 * (attempt + 1))

    # 备用：尝试东方财富接口
    print("新浪接口失败，尝试东方财富接口...")
    try:
        url_em = "https://push2.eastmoney.com/api/qt/clist/get"
        params_em = {
            "pn": "1", "pz": "500", "po": "1", "np": "1",
            "fltt": "2", "invt": "2", "fid": "f12",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
            "fields": "f2,f12,f14,f17,f18",
        }
        all_rows = []
        page = 1
        while True:
            params_em["pn"] = str(page)
            response = curl_requests.get(url_em, params=params_em, impersonate="chrome", timeout=30)
            response.raise_for_status()
            data = response.json()
            if not data.get("data") or not data["data"].get("diff"):
                break
            rows = data["data"]["diff"]
            all_rows.extend(rows)
            total = data["data"].get("total", 0)
            if page % 5 == 0 or len(all_rows) >= total:
                print(f"  第 {page} 页: 累计 {len(all_rows)}/{total}")
            if len(all_rows) >= total or len(rows) < 500:
                break
            page += 1
            time.sleep(random.uniform(1.0, 2.0))
        if all_rows:
            df = pd.DataFrame(all_rows)
            df = df.rename(columns={"f12": "代码", "f14": "名称", "f17": "今开", "f2": "最新价", "f18": "昨收"})
            df = df[["代码", "名称", "今开", "最新价", "昨收"]]
            return df
    except Exception as e:
        print(f"东方财富接口也失败: {e}")

    # 备用：雪球接口（精确数据，无需真实账号）
    print("尝试雪球接口...")
    try:
        session = curl_requests.Session(impersonate="chrome")
        session.get("https://xueqiu.com/", timeout=15)
        # 访问登录接口获取 xq_a_token（无需真实账号）
        session.post("https://xueqiu.com/snowman/login", data={
            "username": "", "password": "", "remember_me": "on",
        }, timeout=15)

        # 第一步：获取全部股票代码
        all_symbols = []
        for market_type in ["sha", "sza"]:
            page = 1
            while True:
                resp = session.get(
                    "https://xueqiu.com/service/v5/stock/screener/quote/list",
                    params={"page": str(page), "size": "90", "order_by": "symbol",
                            "order": "asc", "market": "CN", "type": market_type},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                items = data.get("data", {}).get("list", [])
                if not items:
                    break
                all_symbols.extend([item["symbol"] for item in items])
                total = data.get("data", {}).get("count", 0)
                if len(items) < 90 or page * 90 >= total:
                    break
                page += 1
                time.sleep(random.uniform(0.3, 0.6))

        print(f"  获取到 {len(all_symbols)} 只股票代码，正在获取详细行情...")

        # 第二步：分批获取详细行情（含今开、昨收）
        batch_size = 50
        all_rows = []
        for i in range(0, len(all_symbols), batch_size):
            batch = all_symbols[i:i + batch_size]
            symbol_str = ",".join(batch)
            resp = session.get(
                "https://stock.xueqiu.com/v5/stock/batch/quote.json",
                params={"symbol": symbol_str},
                timeout=30,
            )
            if resp.status_code == 200:
                d = resp.json()
                for item in d["data"]["items"]:
                    q = item.get("quote", {})
                    if q.get("current") and q.get("open") and q.get("last_close"):
                        code = q["symbol"][2:]  # 去掉 SH/SZ 前缀
                        all_rows.append({
                            "代码": code, "名称": q.get("name", ""),
                            "今开": q["open"], "最新价": q["current"],
                            "昨收": q["last_close"],
                        })
            if (i // batch_size) % 10 == 0:
                print(f"  已获取 {len(all_rows)}/{len(all_symbols)} 只")
            time.sleep(random.uniform(0.3, 0.6))

        if all_rows:
            return pd.DataFrame(all_rows)
    except Exception as e:
        print(f"雪球接口也失败: {e}")

    # 最后备用：akshare
    try:
        return ak.stock_zh_a_spot_em()
    except Exception as e:
        print(f"akshare 备用接口也失败: {e}")
        return None

def fetch_zengchi_count(min_count=1):
    """获取近半年董监高增持次数统计，返回 {股票代码: 增持次数}"""
    print("正在获取近半年董监高增减持数据...")

    # 主数据源：雪球接口（curl_cffi 直连）
    try:
        print("  尝试雪球接口...")
        session = curl_requests.Session(impersonate="chrome")
        session.get("https://xueqiu.com/", timeout=15)
        session.post("https://xueqiu.com/snowman/login", data={
            "username": "", "password": "", "remember_me": "on",
        }, timeout=15)

        all_items = []
        page = 1
        while True:
            resp = session.get(
                "https://xueqiu.com/service/v5/stock/f10/cn/skholderchg",
                params={"size": "10000", "page": str(page), "extend": "true"},
                timeout=30,
            )
            if resp.status_code != 200:
                break
            d = resp.json()
            items = d.get("data", {}).get("items", [])
            if not items:
                break
            all_items.extend(items)
            count = d.get("data", {}).get("count", 0)
            if count == 0 or len(all_items) >= count:
                break
            page += 1
            time.sleep(0.3)

        if all_items:
            half_year_ago = datetime.now() - timedelta(days=180)
            zengchi_map = {}
            for item in all_items:
                symbol = item.get("symbol")
                if not symbol:
                    continue
                dt = datetime.fromtimestamp(item["chg_date"] / 1000)
                if dt < half_year_ago:
                    continue
                if item["chg_shares_num"] > 0:  # 增持
                    code = symbol[2:]  # SH600519 -> 600519
                    zengchi_map[code] = zengchi_map.get(code, 0) + 1

            result = {k: v for k, v in zengchi_map.items() if v >= min_count}
            print(f"  [雪球] 近半年增持 >= {min_count} 次的股票: {len(result)} 只")
            return result
    except Exception as e:
        print(f"  雪球接口失败: {e}")

    # 备用数据源：akshare（雪球 akshare 接口）
    try:
        print("  尝试 akshare 接口...")
        df = ak.stock_inner_trade_xq()
        if df.empty:
            print("  akshare 增减持数据为空")
            return {}

        half_year_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        df['变动日期'] = pd.to_datetime(df['变动日期'])
        df_recent = df[df['变动日期'] >= half_year_ago]

        df_zengchi = df_recent[df_recent['变动股数'] > 0].copy()
        df_zengchi['代码'] = df_zengchi['股票代码'].str.extract(r'(\d{6})')
        count_by_code = df_zengchi.groupby('代码').size().reset_index(name='增持次数')
        count_by_code = count_by_code[count_by_code['增持次数'] >= min_count]

        result = dict(zip(count_by_code['代码'], count_by_code['增持次数']))
        print(f"  [akshare] 近半年增持 >= {min_count} 次的股票: {len(result)} 只")
        return result
    except Exception as e:
        print(f"  akshare 接口也失败: {e}")
        return {}

def input_params():
    """让用户交互式输入筛选参数"""
    print("=" * 60)
    print("请设置筛选条件（直接回车使用默认值）")
    print("=" * 60)

    defaults = {
        'open_gap': (-0.03, '允许低开幅度', '今开 > 昨收 × (1 + 此值)'),
        'close_up': (-0.02, '允许收盘跌幅', '现价 > 昨收 × (1 + 此值)'),
        'close_above_open': (-0.03, '允许假阴线幅度', '现价 > 今开 × (1 + 此值)'),
    }

    result = {}
    print()
    for key, (default, label, desc) in defaults.items():
        while True:
            val = input(f"  {label} [{desc}] (默认 {default*100:.1f}%): ").strip()
            if val == '':
                result[key] = default
                break
            try:
                num = float(val)
                # 输入如 -3 表示 -3%，输入如 -0.03 也行
                result[key] = num / 100 if abs(num) > 1 else num
                break
            except ValueError:
                print("    输入无效，请输入数字（如 -3 表示 -3%，或 -0.03）")

    # 增持次数筛选
    print()
    while True:
        val = input(f"  近半年增持最少次数 (默认 1, 输入 0 跳过此条件): ").strip()
        if val == '':
            result['min_zengchi'] = 1
            break
        try:
            num = int(val)
            result['min_zengchi'] = num
            break
        except ValueError:
            print("    输入无效，请输入整数")

    print()
    print("-" * 60)
    print("当前筛选条件：")
    print(f"  1. 今开 > 昨收 × (1 + {result['open_gap']*100:.1f}%)")
    print(f"  2. 现价 > 昨收 × (1 + {result['close_up']*100:.1f}%)")
    print(f"  3. 现价 > 今开 × (1 + {result['close_above_open']*100:.1f}%)")
    if result['min_zengchi'] > 0:
        print(f"  4. 近半年董监高增持 >= {result['min_zengchi']} 次")
    else:
        print(f"  4. 近半年增持筛选: 跳过")
    print("-" * 60)
    return result

def main():
    params = input_params()
    
    # 获取增持数据（在获取行情之前，因为可能较慢）
    zengchi_map = {}
    zengchi_available = False
    if params.get('min_zengchi', 0) > 0:
        zengchi_map = fetch_zengchi_count(params['min_zengchi'])
        zengchi_available = bool(zengchi_map)  # 数据获取成功才启用筛选
        if not zengchi_available:
            print("  [警告] 增持数据获取失败，将跳过增持筛选条件")
    
    # 获取行情数据
    stock_df = fetch_all_stocks_robustly()
    
    if stock_df is None or stock_df.empty:
        print("\n[ERROR] 无法获取数据。最后的建议：")
        print("1. 重启你的路由器，获取新的IP地址")
        print("2. 等待30分钟后重试，可能触发了临时封禁")
        print("3. 如果以上都不行，说明你的IP可能被长时间限制，需要更换网络环境")
        return
    
    print(f"[OK] 成功获取 {len(stock_df)} 只股票的实时数据。")
    
    # 数据清洗与筛选
    stock_df.rename(columns={
        '代码': '股票代码', '名称': '股票名称', '今开': '今日开盘',
        '最新价': '今日收盘', '昨收': '昨日收盘'
    }, inplace=True)
    
    stock_df = stock_df.dropna(subset=['今日开盘', '今日收盘', '昨日收盘'])
    stock_df['今日开盘'] = pd.to_numeric(stock_df['今日开盘'], errors='coerce')
    stock_df['今日收盘'] = pd.to_numeric(stock_df['今日收盘'], errors='coerce')
    stock_df['昨日收盘'] = pd.to_numeric(stock_df['昨日收盘'], errors='coerce')
    stock_df = stock_df.dropna()
    
    print("开始筛选股票...")
    result = []
    
    for idx, row in stock_df.iterrows():
        today_open = row['今日开盘']
        today_close = row['今日收盘']
        yesterday_close = row['昨日收盘']
        code = str(row['股票代码'])
        
        if today_open <= 0 or today_close <= 0 or yesterday_close <= 0:
            continue
        
        cond1 = today_open > yesterday_close * (1 + params['open_gap'])
        cond2 = today_close > yesterday_close * (1 + params['close_up'])
        cond3 = today_close > today_open * (1 + params['close_above_open'])
        
        # 增持筛选（仅当数据获取成功时启用）
        cond4 = True
        zengchi_times = 0
        if zengchi_available:
            zengchi_times = zengchi_map.get(code, 0)
            cond4 = zengchi_times >= params['min_zengchi']
        
        if cond1 and cond2 and cond3 and cond4:
            item = {
                '股票代码': code,
                '股票名称': row['股票名称'],
                '今日开盘': round(today_open, 2),
                '今日收盘': round(today_close, 2),
                '昨日收盘': round(yesterday_close, 2),
                '开盘涨幅%': round((today_open/yesterday_close - 1)*100, 2),
                '收盘涨幅%': round((today_close/yesterday_close - 1)*100, 2),
                '阳线实体%': round((today_close/today_open - 1)*100, 2),
            }
            if zengchi_available:
                item['近半年增持'] = zengchi_times
            result.append(item)
    
    print(f"\n扫描完成！共扫描 {len(stock_df)} 只股票，找到 {len(result)} 只。")
    
    if result:
        df_result = pd.DataFrame(result)
        # 按增持次数降序排列（如果增持数据可用）
        if zengchi_available:
            df_result = df_result.sort_values('近半年增持', ascending=False)
        print("\n====== 筛选结果 ======")
        print(df_result.to_string(index=False))
        filename = f'selected_stocks_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        df_result.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n结果已保存到 {filename}")
    else:
        print("\n[X] 未找到符合条件的股票。")
        print("建议：将 params 中的负数调得更低（如 -0.05）以放宽条件")

if __name__ == "__main__":
    main()