"""routers/signals.py"""
from fastapi import APIRouter, Query
from engines.signal_engine import SignalEngine

router = APIRouter()
engine = SignalEngine()

@router.get("")
async def get_all_signals(timeframe: str = Query("H4")):
    return await engine.generate_all_signals(timeframe)

@router.get("/top")
async def get_top_signals(n: int = Query(5, ge=1, le=10)):
    return await engine.get_top_signals(n)

@router.get("/{pair}")
async def get_signal_for_pair(pair: str, timeframe: str = Query("H4")):
    normalized = pair.replace("-", "/").upper()
    return await engine.generate_signal(normalized, timeframe)
