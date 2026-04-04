# 波段抄底策略选股系统

基于多因子打分的波段抄底策略，包含因子计算、选股引擎、回测框架和胜率分析模块。

## 项目结构

```
wave_bottom_strategy/
├── config/          # 配置模块
├── data/            # 数据模块
├── factors/         # 因子模块（KDJ、MA、成交量、RSI、MACD、布林带）
├── selector/        # 选股模块
├── backtest/        # 回测模块
├── analysis/        # 分析模块
├── utils/           # 工具模块
├── tests/           # 单元测试
└── main.py          # 主入口
```

## 因子权重

| 因子 | 权重 |
|------|------|
| KDJ | 45% |
| 成交量 | 15% |
| 均线 | 15% |
| RSI | 10% |
| MACD | 10% |
| 布林带 | 5% |

## 快速开始

```bash
pip install -r requirements.txt
python wave_bottom_strategy/main.py --mode backtest
```

详见：[技术方案](docs/波段抄底策略_技术方案_v1.0.md)