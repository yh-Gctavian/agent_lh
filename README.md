# 波段抄底策略选股系统

基于多因子打分的波段抄底策略，包含因子计算、选股引擎、回测框架和胜率分析模块。

## 项目结构

```
wave_bottom_strategy/
├── config/          # 配置模块
├── data/            # 数据模块（AKShare）
├── factors/         # 6因子模块
├── selector/        # 选股模块
├── backtest/        # 回测模块
├── analysis/        # 分析模块
├── utils/           # 工具模块
├── tests/           # 单元测试
└── main.py          # 主入口
```

## 因子权重

| 因子 | 权重 | 说明 |
|------|------|------|
| KDJ | 45% | 核心抄底指标 |
| 成交量 | 15% | 量比/缩量判断 |
| 均线 | 15% | 均线偏离度 |
| RSI | 10% | 超卖确认 |
| MACD | 10% | 趋势转折 |
| 布林带 | 5% | 价格通道 |

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行回测
python -m wave_bottom_strategy.main --mode backtest --start 2020-01-01 --end 2025-12-31

# 运行选股
python -m wave_bottom_strategy.main --mode select --start 2025-04-01
```

## 开发进度

| 阶段 | 状态 |
|------|------|
| M0 项目初始化 | ✅ |
| M1 数据层 | ✅ |
| M2 因子层 | ✅ |
| M3 选股引擎 | ✅ |
| M4 回测框架 | ✅ |
| M5 胜率分析 | ✅ |

## 技术方案

详见：[docs/波段抄底策略_技术方案_v1.0.md](docs/波段抄底策略_技术方案_v1.0.md)

## 依赖

- Python 3.10+
- pandas, numpy
- akshare (数据源)
- talib (技术指标，可选)

---

*量化开发经理 (KkTTM7)*