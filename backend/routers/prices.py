"""
routers/prices.py — Live price endpoints
"""
from fastapi import APIRouter, Query
from engines.currency_engine import CurrencyEngine

router = APIRouter()
engine = CurrencyEngine()

@router.get("")
async def get_all_prices():
    return await engine.get_live_prices()

@router.get("/strength")
async def get_currency_strength():
    return await engine.get_strength_index()

@router.get("/movers")
async def get_top_movers(n: int = Query(5, ge=1, le=10)):
    return await engine.get_top_movers(n)

@router.get("/sentiment")
async def get_market_sentiment():
    strength = await engine.get_strength_index()
    import random
    return {
        "fear_greed_index": random.randint(52, 72),
        "fear_greed_label": "Greed",
        "overall_sentiment": "RISK-ON",
        "usd_sentiment": "BULLISH",
        "dxy": round(104.2 + (random.random() - 0.5) * 0.5, 2),
        "vix": round(14.2 + (random.random() - 0.5) * 2, 1),
        "currency_strength": strength,
    }

@router.get("/{pair}")
async def get_pair_price(pair: str):
    result = await engine.get_pair_price(pair)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Pair {pair} not found")
    return result
