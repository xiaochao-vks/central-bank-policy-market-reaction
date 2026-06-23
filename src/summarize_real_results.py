import argparse
from pathlib import Path

import pandas as pd


def pct(value: float) -> str:
    if pd.isna(value):
        return "NA"
    return f"{value * 100:.2f}%"


def main() -> None:
    parser = argparse.ArgumentParser(description="生成真实数据事件研究结果摘要")
    parser.add_argument("--input", type=Path, default=Path("real_output"))
    parser.add_argument("--out", type=Path, default=Path("real_output/真实数据结果摘要.md"))
    args = parser.parse_args()

    by_asset = pd.read_csv(args.input / "summary_by_asset.csv")
    by_type = pd.read_csv(args.input / "summary_by_event_type.csv")

    lines = [
        "# 真实数据结果摘要",
        "",
        "数据来源：东方财富公开日 K 线接口。",
        "",
        "## 按资产汇总",
        "",
    ]

    for _, row in by_asset.sort_values(["asset", "window"]).iterrows():
        lines.append(
            f"- {row['asset']} 在 `{row['window']}` 窗口的平均累计收益为 "
            f"**{pct(row['mean'])}**，中位数为 **{pct(row['median'])}**，样本数 {int(row['count'])}。"
        )

    lines.extend(["", "## 按事件类型汇总", ""])
    for _, row in by_type.sort_values(["asset", "event_type", "window"]).iterrows():
        lines.append(
            f"- {row['asset']} / {row['event_type']} / `{row['window']}`：平均累计收益 **{pct(row['cum_return'])}**。"
        )

    lines.extend(
        [
            "",
            "## 答辩可用结论模板",
            "",
            "基于真实指数日频数据，央行宽松政策发布日附近的市场反应可以从事件日窗口、事件后窗口和全窗口三个角度解释。"
            "如果权益指数在 `[0,+1]` 或 `[-5,+5]` 窗口收益为正，可说明市场对宽松政策存在短期正向反应；"
            "如果不同指数差异较大，则说明政策冲击会受到风险偏好、板块结构和同期市场环境影响。",
            "",
            "## 注意事项",
            "",
            "- 东方财富公开接口可能存在临时限流，若抓取失败，稍后重跑本脚本即可。",
            "- 若某个指数缺失，不影响其他指数的事件研究结果。",
            "- 结果应结合事件日期、窗口设置和同期新闻解释，不能简单等同于因果关系。",
        ]
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved summary to {args.out}")


if __name__ == "__main__":
    main()
