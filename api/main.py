# -*- coding: utf-8 -*-
"""FastAPI Backend API for Wave Bottom Strategy - Enhanced for Frontend F2-F6"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path
import random
import json
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logger
logger = logging.getLogger('api')
logging.basicConfig(level=logging.INFO)

from wave_bottom_strategy.data.loader import DataLoader
from wave_bottom_strategy.selector.scorer import FactorScorer
from wave_bottom_strategy.backtest.engine import BacktestEngine
from wave_bottom_strategy.analysis.metrics import PerformanceMetrics

app = FastAPI(
    title="Wave Bottom Strategy API",
    description="Backend API for stock selection and backtesting",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
try:
    data_loader = DataLoader()
    factor_scorer = FactorScorer()
except Exception as e:
    print(f"Warning: Failed to initialize components: {e}")
    data_loader = None
    factor_scorer = None


# ==================== Models ====================

class StockInfo(BaseModel):
    code: str
    name: str
    industry: Optional[str] = None
    price: Optional[float] = None
    change: Optional[float] = None


class DailyData(BaseModel):
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class SignalItem(BaseModel):
    ts_code: str
    trade_date: str
    total_score: float
    signal: int
    kdj_j: Optional[float] = None
    volume_ratio: Optional[float] = None


class BacktestRequest(BaseModel):
    start_date: str
    end_date: str
    initial_capital: float = 1000000.0
    max_positions: int = 10
    stock_pool: str = "hs300"
    buy_threshold: int = 70
    sell_threshold: int = 30
    commission_rate: float = 0.0003
    slippage: float = 0.001


class BacktestResult(BaseModel):
    initial: float
    final: float
    total_return: float
    trades: int


class MetricsResult(BaseModel):
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float


class ConfigUpdate(BaseModel):
    factor_weights: Optional[Dict[str, float]] = None
    buy_threshold: Optional[int] = None
    sell_threshold: Optional[int] = None
    data_source: Optional[str] = None
    tdx_path: Optional[str] = None


# Mock data generators
def mock_stock_data(count=20):
    industries = ['银行', '房地产', '电子', '计算机', '医药生物', '食品饮料', '汽车', '通信', '有色金属', '电力设备']
    data = []
    for i in range(count):
        score = random.randint(20, 95)
        data.append({
            "code": f"{random.randint(0, 6)}{str(random.randint(1, 9999)).zfill(4)}",
            "name": f"股票{chr(65 + i % 26)}{i + 1}",
            "industry": random.choice(industries),
            "price": round(random.uniform(5, 100), 2),
            "change": round(random.uniform(-10, 10), 2),
            "score": score,
            "signal": 1 if score >= 70 else (-1 if score <= 30 else 0),
            "kdj_j": round(random.uniform(-20, 100), 1),
            "volume_ratio": round(random.uniform(0.5, 3.0), 2),
            "rsi": round(random.uniform(10, 90), 1),
            "macd_signal": random.choice([1, -1]),
            "trade_date": "2024-04-05"
        })
    return sorted(data, key=lambda x: x['score'], reverse=True)


def mock_kline_data(days=90):
    base_price = 12.0
    data = []
    for i in range(days):
        date = f"2024-{str((i // 30) + 1).zfill(2)}-{str((i % 30) + 1).zfill(2)}"
        open_price = base_price + random.uniform(-1, 1)
        close_price = open_price + random.uniform(-0.5, 0.5)
        low_price = min(open_price, close_price) - random.uniform(0, 0.5)
        high_price = max(open_price, close_price) + random.uniform(0, 0.5)
        volume = random.randint(100000, 2000000)
        data.append({
            "trade_date": date,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })
        base_price = close_price
    return data


def mock_factor_scores():
    return {
        "kdj": {"value": -8.5, "score": 85},
        "volume": {"value": 1.85, "score": 72},
        "ma": {"value": 0.95, "score": 65},
        "rsi": {"value": 28.5, "score": 78},
        "macd": {"value": 0.012, "score": 62},
        "bollinger": {"value": -1.2, "score": 55}
    }


def mock_signal_history(count=20):
    data = []
    for i in range(count):
        score = random.randint(30, 90)
        data.append({
            "trade_date": f"2024-{str(12 - i // 4).zfill(2)}-{str(28 - (i % 4) * 7).zfill(2)}",
            "signal": 1 if score >= 70 else -1,
            "total_score": score,
            "price": round(random.uniform(8, 15), 2),
            "kdj_j": round(random.uniform(-20, 100), 1),
            "volume_ratio": round(random.uniform(0.5, 2.5), 2),
            "rsi": round(random.uniform(20, 80), 1),
            "macd_hist": round(random.uniform(-0.02, 0.04), 4),
            "return_5d": round(random.uniform(-3, 10), 2),
            "return_10d": round(random.uniform(-5, 15), 2)
        })
    return data


# ==================== Dashboard APIs ====================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    return {
        "total_return": 45.8,
        "win_rate": 68.5,
        "max_drawdown": -12.3,
        "sharpe_ratio": 1.85
    }


@app.get("/api/dashboard/equity-curve")
async def get_equity_curve():
    """Get equity curve data"""
    dates = []
    equity = []
    benchmark = []
    
    equity_val = 1.0
    benchmark_val = 1.0
    
    for i in range(250):
        date = f"2024-{str((i // 30) + 1).zfill(2)}-{str((i % 30) + 1).zfill(2)}"
        dates.append(date)
        equity_val *= (1 + random.uniform(-0.015, 0.04))
        benchmark_val *= (1 + random.uniform(-0.01, 0.03))
        equity.append(round((equity_val - 1) * 100, 2))
        benchmark.append(round((benchmark_val - 1) * 100, 2))
    
    return {"dates": dates, "equity": equity, "benchmark": benchmark}


# ==================== Stock APIs ====================

@app.get("/api/stocks")
async def get_stocks(
    market: str = Query(default="hs300"),
    industry: str = Query(default=None),
    keyword: str = Query(default=None),
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    min_score: int = Query(default=0),
    max_score: int = Query(default=100),
    sort_by: str = Query(default="score"),
    sort_order: str = Query(default="desc")
):
    """Get stock list with pagination and filtering"""
    try:
        # 使用真实股票池数据
        if data_loader:
            stock_codes = data_loader.load_stock_pool(market)
            logger.info(f"获取股票池 {market}: {len(stock_codes)} 只股票")
        else:
            stock_codes = [f"{str(i).zfill(6)}" for i in range(1, 101)]
        
        # 生成股票数据（代码使用真实数据，其他使用模拟数据）
        all_stocks = []
        industries = ['银行', '房地产', '电子', '计算机', '医药生物', '食品饮料', '汽车', '通信', '有色金属', '电力设备']
        
        for i, code in enumerate(stock_codes[:200]):  # 限制200只避免响应过大
            score = random.randint(20, 95)
            all_stocks.append({
                "code": code,
                "name": f"股票{code}",  # 可后续对接真实名称
                "industry": random.choice(industries),
                "price": round(random.uniform(5, 100), 2),
                "change": round(random.uniform(-10, 10), 2),
                "score": score,
                "signal": 1 if score >= 70 else (-1 if score <= 30 else 0),
                "kdj_j": round(random.uniform(-20, 100), 1),
                "volume_ratio": round(random.uniform(0.5, 3.0), 2),
                "rsi": round(random.uniform(10, 90), 1),
                "macd_signal": random.choice([1, -1]),
                "trade_date": "2024-04-05"
            })
        
        # Filter by score range
        all_stocks = [s for s in all_stocks if min_score <= s['score'] <= max_score]
        
        # Filter by industry
        if industry:
            all_stocks = [s for s in all_stocks if s['industry'] == industry]
        
        # Filter by keyword
        if keyword:
            all_stocks = [s for s in all_stocks if keyword in s['code'] or keyword in s['name']]
        
        # Sort
        reverse = sort_order == 'desc'
        if sort_by in ['score', 'price', 'change']:
            all_stocks = sorted(all_stocks, key=lambda x: x[sort_by], reverse=reverse)
        
        # Paginate
        total = len(all_stocks)
        start = (page - 1) * page_size
        end = start + page_size
        items = all_stocks[start:end]
        
        return {"items": items, "total": total, "page": page, "page_size": page_size}
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/{code}")
async def get_stock(code: str):
    """Get stock detail"""
    return {
        "code": code,
        "name": "平安银行" if code == "000001" else f"股票_{code}",
        "industry": random.choice(['银行', '电子', '医药生物']),
        "price": round(random.uniform(5, 50), 2),
        "change": round(random.uniform(-5, 5), 2)
    }


@app.get("/api/stocks/{code}/daily")
async def get_daily_data(
    code: str,
    start_date: str = Query(default="20240101"),
    end_date: str = Query(default="20241231")
):
    """Get daily K-line data"""
    try:
        # Try to use real data loader
        if data_loader:
            df = data_loader.load_daily_data(code, start_date, end_date)
            if not df.empty:
                return [
                    DailyData(
                        trade_date=str(row["trade_date"])[:10],
                        open=row["open"],
                        high=row["high"],
                        low=row["low"],
                        close=row["close"],
                        volume=row["volume"]
                    )
                    for _, row in df.iterrows()
                ]
        
        # Return mock data
        return mock_kline_data(90)
        
    except Exception as e:
        # Return mock data on error
        return mock_kline_data(90)


@app.get("/api/stocks/{code}/factors")
async def get_factor_scores(code: str, date: str = Query(default=None)):
    """Get factor scores for a stock"""
    return mock_factor_scores()


@app.get("/api/stocks/{code}/signals")
async def get_stock_signal_history(code: str):
    """Get signal history for a stock"""
    return mock_signal_history(50)


# ==================== Signal APIs ====================

@app.get("/api/signals")
async def get_signals(date: str = Query(default=None)):
    """Get signal list"""
    stocks = mock_stock_data(20)
    signals = []
    for s in stocks:
        if s['signal'] != 0:
            signals.append({
                "code": s['code'],
                "name": s['name'],
                "score": s['score'],
                "signal": "BUY" if s['signal'] == 1 else "SELL",
                "kdj": s['kdj_j'],
                "volume": s['volume_ratio'],
                "price": s['price'],
                "change": s['change']
            })
    return signals


@app.post("/api/select")
async def run_selection(
    date: str = Query(default="20241201"),
    top_n: int = Query(default=10)
):
    """Run stock selection"""
    stocks = mock_stock_data(top_n)
    return [
        SignalItem(ts_code=f"{s['code']}.SZ", trade_date=date, total_score=s['score'], signal=s['signal'])
        for s in stocks
    ]


# ==================== Backtest APIs ====================

@app.post("/api/backtest/run")
async def run_backtest(request: BacktestRequest):
    """Run backtest"""
    try:
        # Try real backtest engine
        if data_loader:
            engine = BacktestEngine(
                initial_capital=request.initial_capital,
                max_positions=request.max_positions
            )
            # For now, return mock result
        
        # Mock result
        total_return = random.uniform(10, 60)
        
        return {
            "metrics": {
                "totalReturn": round(total_return, 2),
                "annualReturn": round(total_return * 1.1, 2),
                "winRate": round(random.uniform(55, 75), 1),
                "sharpeRatio": round(random.uniform(1.0, 2.5), 2),
                "maxDrawdown": round(random.uniform(5, 15), 2),
                "tradeCount": random.randint(50, 200),
                "profitLossRatio": round(random.uniform(1.5, 3.0), 2),
                "benchmarkReturn": round(random.uniform(5, 25), 2)
            },
            "trades": [
                {
                    "trade_date": f"2024-{str(i % 12 + 1).zfill(2)}-{str((i % 28) + 1).zfill(2)}",
                    "code": f"{random.randint(0, 6)}{str(random.randint(1, 9999)).zfill(4)}",
                    "action": "BUY" if i % 2 == 0 else "SELL",
                    "price": round(random.uniform(10, 60), 2),
                    "shares": random.randint(100, 1000) * 100,
                    "amount": random.randint(50000, 200000),
                    "profit": round(random.uniform(-5, 20), 2) if i % 2 == 1 else None,
                    "score": random.randint(60, 90)
                }
                for i in range(30)
            ],
            "equity_curve": []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/history")
async def get_backtest_history():
    """Get backtest history list"""
    return [
        {"id": i, "date": f"2024-{str(i % 12 + 1).zfill(2)}-01", "return": round(random.uniform(10, 50), 2)}
        for i in range(1, 6)
    ]


# ==================== Analysis APIs ====================

@app.get("/api/analysis/layering")
async def get_layering_analysis(
    start_date: str = Query(default="20240101"),
    end_date: str = Query(default="20241231"),
    layers: int = Query(default=5),
    factor: str = Query(default="total_score")
):
    """Get layering analysis"""
    layer_data = []
    for i in range(layers):
        mean_return = random.uniform(0.01, 0.08) * (layers - i)  # Higher layers better
        win_rate = random.uniform(0.45, 0.75) * (layers - i) / layers + 0.4
        layer_data.append({
            "layer": i + 1,
            "mean_return": round(mean_return, 4),
            "win_rate": round(win_rate, 3),
            "stock_count": random.randint(50, 100)
        })
    
    return {
        "layers": layer_data,
        "ic_mean": round(random.uniform(0.02, 0.08), 4),
        "ic_std": round(random.uniform(0.1, 0.2), 4),
        "ic_ir": round(random.uniform(0.1, 0.4), 4)
    }


@app.get("/api/analysis/winrate")
async def get_winrate_analysis(
    start_date: str = Query(default="20240101"),
    end_date: str = Query(default="20241231")
):
    """Get win rate analysis"""
    return {
        "overall_win_rate": round(random.uniform(0.55, 0.75), 3),
        "buy_signal_win_rate": round(random.uniform(0.6, 0.8), 3),
        "sell_signal_accuracy": round(random.uniform(0.5, 0.7), 3),
        "avg_holding_days": round(random.uniform(5, 15), 1),
        "avg_profit_per_trade": round(random.uniform(0.02, 0.08), 4)
    }


# ==================== Config APIs ====================

# Default configuration
default_config = {
    "factor_weights": {
        "kdj": 45,
        "volume": 15,
        "ma": 15,
        "rsi": 10,
        "macd": 10,
        "bollinger": 5
    },
    "buy_threshold": 70,
    "sell_threshold": 30,
    "data_source": "tdx",
    "tdx_path": "E:\\new_tdx"
}


@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return default_config


@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    """Update configuration"""
    global default_config
    
    if config.factor_weights:
        default_config["factor_weights"] = config.factor_weights
    if config.buy_threshold:
        default_config["buy_threshold"] = config.buy_threshold
    if config.sell_threshold:
        default_config["sell_threshold"] = config.sell_threshold
    if config.data_source:
        default_config["data_source"] = config.data_source
    if config.tdx_path:
        default_config["tdx_path"] = config.tdx_path
    
    return {"status": "success", "config": default_config}


@app.post("/api/config/reset")
async def reset_config():
    """Reset to default configuration"""
    global default_config
    default_config = {
        "factor_weights": {
            "kdj": 45,
            "volume": 15,
            "ma": 15,
            "rsi": 10,
            "macd": 10,
            "bollinger": 5
        },
        "buy_threshold": 70,
        "sell_threshold": 30,
        "data_source": "tdx",
        "tdx_path": "E:\\new_tdx"
    }
    return {"status": "success", "config": default_config}


# ==================== Metrics APIs ====================

@app.get("/api/metrics")
async def get_metrics():
    """Get performance metrics"""
    return MetricsResult(
        win_rate=0.685,
        sharpe_ratio=1.85,
        max_drawdown=-0.123
    )


# ==================== Health Check ====================

@app.get("/api/health")
async def health_check():
    """Health check"""
    return {"status": "ok", "service": "wave-bottom-api", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Wave Bottom Strategy API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)