# 波段抄底策略选股系统

基于6因子打分的波段抄底策略，包含因子计算、选股引擎、回测框架和胜率分析模块。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行回测
python wave_bottom_strategy/main.py --mode backtest

# 选股
python wave_bottom_strategy/main.py --mode select --date today

# 分析
python wave_bottom_strategy/main.py --mode analysis --sensitivity
```

## 项目结构

```
wave_bottom_strategy/
├── config/          # 配置模块
│   ├── settings.py          # 全局配置
│   └── factor_params.py     # 因子参数
├── data/            # 数据模块
│   ├── loader.py            # AKShare数据加载
│   ├── processor.py         # 数据预处理
│   └── cache.py             # Parquet缓存
├── factors/         # 因子模块
│   ├── kdj.py               # KDJ因子 (45%)
│   ├── ma.py                # 均线因子 (15%)
│   ├── volume.py            # 成交量因子 (15%)
│   ├── rsi.py               # RSI因子 (10%)
│   ├── macd.py              # MACD因子 (10%)
│   └── bollinger.py         # 布林带因子 (5%)
├── selector/        # 选股模块
│   ├── engine.py            # 选股引擎
│   ├── scorer.py            # 因子打分
│   ├── filter.py            # 股票过滤
│   └── signal.py            # 信号生成
├── backtest/        # 回测模块
│   ├── engine.py            # 回测引擎
│   ├── portfolio.py         # 组合管理
│   ├── matcher.py           # 订单撮合
│   └── benchmark.py         # 基准对比
├── analysis/        # 分析模块
│   ├── metrics.py           # 绩效指标
│   ├── layering.py          # 分层分析
│   ├── sensitivity.py       # 敏感性分析
│   └── reporter.py          # 报告生成
├── utils/           # 工具模块
│   ├── logger.py            # 日志
│   ├── calendar.py          # 交易日历
│   └── helpers.py           # 工具函数
├── tests/           # 单元测试
└── main.py          # 主入口
```

## 因子权重

| 因子 | 权重 | 说明 |
|------|------|------|
| KDJ | 45% | 抄底核心指标，超卖信号 |
| 成交量 | 15% | 量比、缩量天数 |
| 均线 | 15% | MA5/20/60偏离度 |
| RSI | 10% | 相对强弱指标 |
| MACD | 10% | 趋势转折确认 |
| 布林带 | 5% | 价格通道位置 |

## 抄底信号

买入条件：
- 综合得分 >= 70分
- KDJ J值 < 20（超卖）

卖出条件：
- 止损：-5%
- 止盈：+15%
- 最大持仓天数：5天

## 回测参数

```bash
python main.py --mode backtest \
  --start 2020-01-01 \
  --end 2025-12-31 \
  --capital 1000000 \
  --max-positions 10 \
  --min-score 70 \
  --stop-loss -0.05 \
  --take-profit 0.15 \
  --hold-days 5
```

## 数据源

- 行情数据：AKShare（免费，无需token）
- 股票池：沪深300成分股
- 复权方式：前复权

## 开发进度

| 里程碑 | 状态 | 说明 |
|--------|------|------|
| M0 项目初始化 | ✅ | 项目骨架、配置 |
| M1 数据层 | ✅ | AKShare加载、预处理 |
| M2 因子层 | ✅ | 6因子计算 |
| M3 选股引擎 | ✅ | 多因子打分、信号生成 |
| M4 回测框架 | ✅ | 组合管理、基准对比 |
| M5 胜率分析 | ✅ | 绩效指标、分层分析 |
| M6 联调优化 | ✅ | 端到端测试、文档 |

## 文档

- [技术方案](docs/波段抄底策略_技术方案_v1.0.md)

---

*量化开发经理 (KkTTM7)*