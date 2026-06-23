# 央行货币政策发布日的市场反应

本项目使用事件研究法分析央行宽松货币政策发布日前后，股票市场与债券市场的短期反应。研究对象包括沪深300和中证全债，事件类型包括降准、LPR 下调、公开市场操作利率下调和组合政策。

## 核心结论

- 沪深300在 `[0,+1]` 发布日窗口的平均累计收益为 **0.22%**，在 `[-5,+5]` 完整窗口的平均累计收益为 **2.36%**。
- 中证全债在 `[0,+1]` 发布日窗口的平均累计收益为 **0.12%**，在 `[-5,+5]` 完整窗口的平均累计收益为 **0.60%**。
- 组合政策对沪深300的短期冲击最明显，`[0,+1]` 平均累计收益为 **1.94%**，`[-5,+5]` 平均累计收益为 **5.55%**。
- 结果说明政策发布日附近存在可观察的短期市场反应；权益市场反应更强但分化更大，债券市场反应更平滑。

## 项目结构

```text
.
├── dashboard/
│   └── app.py                         # Streamlit 可视化看板
├── data/
│   ├── policy_events.csv              # 货币政策事件表
│   ├── real_market_data.csv           # 真实日频市场价格序列
│   ├── real_event_window_returns.csv  # 事件窗口收益明细
│   ├── real_summary_by_asset.csv      # 按资产汇总结果
│   └── real_summary_by_event_type.csv # 按事件类型汇总结果
├── real_output/
│   ├── event_window_returns.csv
│   ├── summary_by_asset.csv
│   ├── summary_by_event_type.csv
│   └── 真实数据结果摘要.md
├── src/
│   ├── event_study.py                 # 事件研究核心脚本
│   ├── fetch_eastmoney_data.py        # 行情抓取脚本
│   ├── build_real_market_data.py      # Dashboard 价格序列构建
│   └── summarize_real_results.py      # 结果摘要生成
├── requirements.txt
└── README.md
```

## 运行方法

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

重新计算事件窗口结果：

```powershell
python src/event_study.py --events data/policy_events.csv --market data/real_market_data.csv --out real_output
python src/summarize_real_results.py --input real_output --out real_output/真实数据结果摘要.md
```

启动 Dashboard：

```powershell
streamlit run dashboard/app.py
```

## 在线部署

可以通过 Streamlit Community Cloud 部署本项目 Dashboard：

[打开 Streamlit 部署页](https://share.streamlit.io/deploy?repository=xiaochao-vks%2Fcentral-bank-policy-market-reaction&branch=main&mainModule=streamlit_app.py&subdomain=central-bank-policy-market-reaction)

部署配置：

- Repository: `xiaochao-vks/central-bank-policy-market-reaction`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Custom subdomain: `central-bank-policy-market-reaction`

部署完成后的访问地址建议设置为：

```text
https://central-bank-policy-market-reaction.streamlit.app/
```

## 方法说明

项目采用四类事件窗口：

- `pre_5_to_1`：事件前窗口 `[-5,-1]`
- `event_0_to_1`：发布日窗口 `[0,+1]`
- `post_1_to_5`：事件后窗口 `[+1,+5]`
- `full_minus5_to_plus5`：完整窗口 `[-5,+5]`

窗口累计收益计算方式：

```text
窗口累计收益 = 窗口结束日收盘价 / 窗口起始日收盘价 - 1
```

## 数据说明

政策事件来自公开公告整理；沪深300日频价格来自公开行情接口；中证全债序列用于补全课程项目中的债券指数走势，并在 `source` 字段中标注来源。项目结论基于事件窗口内的平均累计收益，属于短期市场反应描述，不直接等同于严格因果关系。
