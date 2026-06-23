import argparse
from pathlib import Path

import pandas as pd


WINDOWS = {
    "pre_5_to_1": (-5, -1),
    "event_0_to_1": (0, 1),
    "post_1_to_5": (1, 5),
    "full_minus5_to_plus5": (-5, 5),
}


def load_inputs(events_path: Path, market_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = pd.read_csv(events_path, parse_dates=["event_date"])
    market = pd.read_csv(market_path, parse_dates=["date"])
    market = market.sort_values(["asset", "date"]).reset_index(drop=True)
    market["daily_return"] = market.groupby("asset")["close"].pct_change()
    return events, market


def nearest_trading_index(dates: pd.Series, event_date: pd.Timestamp) -> int:
    on_or_after = dates[dates >= event_date]
    if len(on_or_after) == 0:
        return len(dates) - 1
    return int(on_or_after.index[0])


def cumulative_return(frame: pd.DataFrame, start_idx: int, end_idx: int) -> float | None:
    start_idx = max(0, start_idx)
    end_idx = min(len(frame) - 1, end_idx)
    if start_idx >= end_idx:
        return None
    start_price = frame.iloc[start_idx]["close"]
    end_price = frame.iloc[end_idx]["close"]
    return end_price / start_price - 1


def build_event_windows(events: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, event in events.iterrows():
        for asset, asset_frame in market.groupby("asset", sort=False):
            asset_frame = asset_frame.sort_values("date").reset_index(drop=True)
            event_idx = nearest_trading_index(asset_frame["date"], event["event_date"])
            trading_date = asset_frame.iloc[event_idx]["date"]
            for window_name, (left, right) in WINDOWS.items():
                ret = cumulative_return(asset_frame, event_idx + left, event_idx + right)
                rows.append(
                    {
                        "event_date": event["event_date"].date().isoformat(),
                        "trading_date": trading_date.date().isoformat(),
                        "event_name": event["event_name"],
                        "event_type": event["event_type"],
                        "direction": event["direction"],
                        "asset": asset,
                        "window": window_name,
                        "cum_return": ret,
                    }
                )
    return pd.DataFrame(rows)


def write_outputs(event_windows: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    event_windows.to_csv(out_dir / "event_window_returns.csv", index=False, encoding="utf-8-sig")

    summary_by_event_type = (
        event_windows.groupby(["event_type", "asset", "window"], as_index=False)["cum_return"]
        .mean()
        .sort_values(["asset", "event_type", "window"])
    )
    summary_by_event_type.to_csv(out_dir / "summary_by_event_type.csv", index=False, encoding="utf-8-sig")

    summary_by_asset = (
        event_windows.groupby(["asset", "window"], as_index=False)["cum_return"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    summary_by_asset.to_csv(out_dir / "summary_by_asset.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="央行货币政策发布日市场反应事件研究")
    parser.add_argument("--events", type=Path, default=Path("data/policy_events.csv"))
    parser.add_argument("--market", type=Path, default=Path("data/real_market_data.csv"))
    parser.add_argument("--out", type=Path, default=Path("real_output"))
    args = parser.parse_args()

    events, market = load_inputs(args.events, args.market)
    event_windows = build_event_windows(events, market)
    write_outputs(event_windows, args.out)
    print(f"分析完成，共生成 {len(event_windows)} 条事件-资产-窗口记录。输出目录：{args.out}")


if __name__ == "__main__":
    main()
