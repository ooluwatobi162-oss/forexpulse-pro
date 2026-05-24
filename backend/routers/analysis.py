"""routers/analysis.py"""
from fastapi import APIRouter, Query
from engines.ta_engine import TAEngine

router = APIRouter()
engine = TAEngine()

@router.get("/{pair}")
async def get_technical_analysis(pair: str, timeframe: str = Query("H1")):
    normalized = pair.replace("-", "/").upper()
    return await engine.analyze(normalized, timeframe)
