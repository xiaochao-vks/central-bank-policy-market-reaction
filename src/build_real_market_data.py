import json
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


TENCENT_SERIES = {
    "沪深300": "sh000300",
}


def fetch_tencent_daily(asset: str, symbol: str, start: str, end: str) -> pd.DataFrame:
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        f"?param={symbol},day,{start},{end},1000,qfq"
    )
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))

    node = payload["data"][symbol]
    rows = node.get("qfqday") or node.get("day") or []
    data = []
    for row in rows:
        data.append(
            {
                "date": row[0],
                "asset": asset,
                "open": float(row[1]),
                "close": float(row[2]),
                "high": float(row[3]),
                "low": float(row[4]),
                "volume": float(row[5]),
                "source": "Tencent qfq daily kline",
            }
        )
    return pd.DataFrame(data)


def load_archived_bond_series() -> pd.DataFrame:
    archive_path = ROOT / "data" / "archive_sample_market_data.csv"
    if not archive_path.exists():
        return pd.DataFrame()
    data = pd.read_csv(archive_path, parse_dates=["date"])
    data = data[data["asset"] == "中证全债"].copy()
    if data.empty:
        return data
    data["date"] = data["date"].dt.strftime("%Y-%m-%d")
    data["open"] = data["close"]
    data["high"] = data["close"]
    data["low"] = data["close"]
    data["volume"] = None
    data["source"] = "Archived course bond index series"
    return data[["date", "asset", "open", "close", "high", "low", "volume", "source"]]


def main() -> None:
    frames = []
    for asset, symbol in TENCENT_SERIES.items():
        print(f"Fetching {asset} from Tencent...")
        try:
            frame = fetch_tencent_daily(asset, symbol, "2023-01-01", "2025-05-31")
        except Exception as exc:
            print(f"Skipped {asset}: {exc}")
            continue
        if not frame.empty:
            frames.append(frame)

    bond = load_archived_bond_series()
    if not bond.empty:
        frames.append(bond)
        print("Loaded archived 中证全债 series for dashboard continuity.")

    if not frames:
        raise RuntimeError("No market series available.")

    result = pd.concat(frames, ignore_index=True).sort_values(["asset", "date"])
    out = ROOT / "data" / "real_market_data.csv"
    result.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"Saved {len(result)} rows to {out}")


if __name__ == "__main__":
    main()
