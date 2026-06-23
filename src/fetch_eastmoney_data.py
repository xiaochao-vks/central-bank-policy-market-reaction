import argparse
import json
import time
from http.client import RemoteDisconnected
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd


EASTMONEY_KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

INDEXES = {
    "沪深300": "1.000300",
    "上证指数": "1.000001",
    "深证成指": "0.399001",
    "创业板指": "0.399006",
    "中证500": "1.000905",
    "中证1000": "1.000852",
    "上证50": "1.000016",
    "科创50": "1.000688",
}


def fetch_index_kline(asset: str, secid: str, start: str, end: str) -> pd.DataFrame:
    params = {
        "secid": secid,
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "1",
        "beg": start,
        "end": end,
        "_": str(int(time.time() * 1000)),
    }
    url = f"{EASTMONEY_KLINE_URL}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "close",
            "Referer": "https://quote.eastmoney.com/",
        },
    )
    last_error = None
    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except (HTTPError, URLError, TimeoutError, RemoteDisconnected) as exc:
            last_error = exc
            time.sleep(attempt * 1.5)
    else:
        raise RuntimeError(f"{asset} fetch failed after retries: {last_error}") from last_error

    klines = payload.get("data", {}).get("klines", [])
    rows = []
    for line in klines:
        parts = line.split(",")
        rows.append(
            {
                "date": parts[0],
                "asset": asset,
                "open": float(parts[1]),
                "close": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "volume": float(parts[5]),
                "amount": float(parts[6]),
                "amplitude_pct": float(parts[7]),
                "change_pct": float(parts[8]),
                "change_amount": float(parts[9]),
                "turnover_pct": float(parts[10]) if parts[10] != "-" else None,
                "source": "Eastmoney push2his kline API",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="抓取东方财富指数日 K 线真实行情数据")
    parser.add_argument("--start", default="20220101")
    parser.add_argument("--end", default="20251231")
    parser.add_argument("--out", type=Path, default=Path("data/real_market_data.csv"))
    args = parser.parse_args()

    frames = []
    for asset, secid in INDEXES.items():
        print(f"Fetching {asset} ({secid})...")
        try:
            frame = fetch_index_kline(asset, secid, args.start, args.end)
        except RuntimeError as exc:
            print(f"Skipped {asset}: {exc}")
            continue
        if frame.empty:
            print(f"Skipped {asset}: empty response")
            continue
        frames.append(frame)
        data = pd.concat(frames, ignore_index=True)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(args.out, index=False, encoding="utf-8-sig")
        print(f"Saved checkpoint with {len(data)} rows to {args.out}")
        time.sleep(0.4)

    if not frames:
        raise RuntimeError("No market data fetched.")

    data = pd.concat(frames, ignore_index=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.out, index=False, encoding="utf-8-sig")
    print(f"Saved {len(data)} rows to {args.out}")


if __name__ == "__main__":
    main()
