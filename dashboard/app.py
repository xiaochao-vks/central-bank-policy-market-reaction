from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
REAL_MARKET_PATH = ROOT / "data" / "real_market_data.csv"
REAL_OUTPUT = ROOT / "real_output"


def pct_frame(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    result = frame.copy()
    for col in cols:
        if col in result.columns:
            result[col] = result[col].map(lambda x: f"{x * 100:.2f}%" if pd.notna(x) else "")
    return result


st.set_page_config(page_title="央行政策事件研究", layout="wide")
st.title("央行货币政策发布日的市场反应")

events = pd.read_csv(ROOT / "data" / "policy_events.csv")
event_windows = pd.read_csv(REAL_OUTPUT / "event_window_returns.csv")
summary_by_asset = pd.read_csv(REAL_OUTPUT / "summary_by_asset.csv")
summary_by_event_type = pd.read_csv(REAL_OUTPUT / "summary_by_event_type.csv")
market = pd.read_csv(REAL_MARKET_PATH, parse_dates=["date"]) if REAL_MARKET_PATH.exists() else pd.DataFrame()

asset_options = sorted(event_windows["asset"].unique())
event_type_options = sorted(events["event_type"].unique())

asset = st.sidebar.selectbox("选择资产", asset_options)
event_type = st.sidebar.multiselect(
    "选择事件类型",
    event_type_options,
    default=event_type_options,
)

st.caption("事件研究结果来自 real_output；走势页读取 data/real_market_data.csv。")

filtered_events = events[events["event_type"].isin(event_type)]
filtered_windows = event_windows[
    (event_windows["asset"] == asset) & (event_windows["event_type"].isin(event_type))
]
filtered_type = summary_by_event_type[
    (summary_by_event_type["asset"] == asset) & (summary_by_event_type["event_type"].isin(event_type))
]

tab_price, tab_summary, tab_events = st.tabs(["走势与事件", "真实结果汇总", "事件明细"])

with tab_price:
    if market.empty or asset not in set(market["asset"].unique()):
        st.warning("未检测到当前资产的逐日价格序列，请先运行 `python src/build_real_market_data.py`。")
    else:
        filtered_market = market[market["asset"] == asset].sort_values("date")
        source_text = "、".join(sorted(filtered_market["source"].dropna().unique()))
        st.caption(f"当前价格序列来源：{source_text}")

        fig = px.line(
            filtered_market,
            x="date",
            y="close",
            title=f"{asset} 逐日价格走势与央行政策事件",
            labels={"date": "日期", "close": "收盘价"},
        )
        for _, row in filtered_events.iterrows():
            fig.add_vline(x=row["event_date"], line_width=1, line_dash="dash", line_color="#CC3333")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("当前资产窗口收益摘要")
        asset_summary = summary_by_asset[summary_by_asset["asset"] == asset]
        st.dataframe(pct_frame(asset_summary, ["mean", "median"]), use_container_width=True)

with tab_summary:
    st.subheader("按资产汇总")
    asset_summary = summary_by_asset[summary_by_asset["asset"] == asset]
    st.dataframe(pct_frame(asset_summary, ["mean", "median"]), use_container_width=True)

    st.subheader("按事件类型和窗口汇总")
    st.dataframe(pct_frame(filtered_type, ["cum_return"]), use_container_width=True)

    chart_data = filtered_type[filtered_type["window"] == "event_0_to_1"].copy()
    if not chart_data.empty:
        chart_data["return_pct"] = chart_data["cum_return"] * 100
        fig_bar = px.bar(
            chart_data,
            x="event_type",
            y="return_pct",
            color="event_type",
            title=f"{asset} 不同政策类型的发布日窗口 [0,+1] 平均累计收益",
            labels={"event_type": "事件类型", "return_pct": "累计收益(%)"},
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with tab_events:
    st.subheader("政策事件表")
    st.dataframe(filtered_events, use_container_width=True)

    st.subheader("逐事件窗口收益")
    st.dataframe(pct_frame(filtered_windows, ["cum_return"]), use_container_width=True)
