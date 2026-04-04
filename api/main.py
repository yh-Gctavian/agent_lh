# -*- coding: utf-8 -*-
"""FastAPI Backend API for Wave Bottom Strategy"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
data_loader = DataLoader()
factor_scorer = FactorScorer()


# ==================== Models ====================

class StockInfo(BaseModel):
    code: str
    name: str
    industry: Optional[str] = None


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


class BacktestRequest(BaseModel):
    start_date: str
    end_date: str
    initial_capital: float = 1000000.0
    max_positions: int = 10


class BacktestResult(BaseModel):
    initial: float
    final: float
    total_return: float
    trades: int


class MetricsResult(BaseModel):
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float


# ==================== Data APIs ====================

@app.get("/api/stocks", response_model=List[StockInfo])
async def get_stocks():
    """Get stock list"""
    try:
        codes = data_loader.load_stock_pool("hs300")
        return [StockInfo(code=c, name="") for c in codes[:50]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/{code}", response_model=StockInfo)
async def get_stock(code: str):
    """Get stock detail"""
    return StockInfo(code=code, name="")


@app.get("/api/stocks/{code}/daily", response_model=List[DailyData])
async def get_daily_data(
    code: str,
    start_date: str = Query(default="20240101"),
    end_date: str = Query(default="20241231")
):
    """Get daily K-line data"""
    try:
        df = data_loader.load_daily_data(code, start_date, end_date)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Selection APIs ====================

@app.post("/api/select", response_model=List[SignalItem])
async def run_selection(
    date: str = Query(default="20241201"),
    top_n: int = Query(default=10)
):
    """Run stock selection"""
    try:
        # Mock result for demo
        return [
            SignalItem(ts_code="000001.SZ", trade_date=date, total_score=85.0, signal=1),
            SignalItem(ts_code="000002.SZ", trade_date=date, total_score=78.0, signal=1),
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals", response_model=List[SignalItem])
async def get_signals():
    """Get signal list"""
    return [
        SignalItem(ts_code="000001.SZ", trade_date="20241201", total_score=85.0, signal=1),
    ]


@app.get("/api/signals/today", response_model=List[SignalItem])
async def get_today_signals():
    """Get today signals"""
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    return [
        SignalItem(ts_code="000001.SZ", trade_date=today, total_score=85.0, signal=1),
    ]


# ==================== Backtest APIs ====================

@app.post("/api/backtest", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest):
    """Run backtest"""
    try:
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            max_positions=request.max_positions
        )
        result = engine.run(request.start_date, request.end_date)
        
        return BacktestResult(
            initial=result.get("initial", 0),
            final=result.get("final", 0),
            total_return=(result.get("final", 0) - result.get("initial", 0)) / result.get("initial", 1),
            trades=result.get("trades", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/{backtest_id}/result")
async def get_backtest_result(backtest_id: int):
    """Get backtest result"""
    return {"backtest_id": backtest_id, "status": "completed"}


@app.get("/api/backtest/{backtest_id}/report")
async def get_backtest_report(backtest_id: int):
    """Get backtest report"""
    return {"backtest_id": backtest_id, "report_url": f"/reports/{backtest_id}.md"}


# ==================== Analysis APIs ====================

@app.get("/api/metrics", response_model=MetricsResult)
async def get_metrics():
    """Get performance metrics"""
    return MetricsResult(
        win_rate=0.65,
        sharpe_ratio=1.8,
        max_drawdown=-0.15
    )


@app.get("/api/analysis/layering")
async def get_layering_analysis():
    """Get layering analysis"""
    return {
        "layers": [
            {"layer": 1, "mean_return": 0.05, "win_rate": 0.70},
            {"layer": 2, "mean_return": 0.03, "win_rate": 0.60},
            {"layer": 3, "mean_return": 0.01, "win_rate": 0.50},
        ]
    }


# ==================== Health Check ====================

@app.get("/api/health")
async def health_check():
    """Health check"""
    return {"status": "ok", "service": "wave-bottom-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)