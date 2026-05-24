"""routers/calendar.py - Dynamic economic calendar"""
from fastapi import APIRouter
from datetime import datetime, timedelta
import asyncio
import httpx
import os

router = APIRouter()

FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")

EVENTS_TEMPLATE = [
    {"event": "Fed Chair Powell Speech", "currency": "USD", "impact": "high", "forecast": "—", "previous": "—", "hour_offset": 2},
    {"event": "US Core CPI m/m", "currency": "USD", "impact": "high", "forecast": "0.3%", "previous": "0.4%", "hour_offset": 4},
    {"event": "ECB Interest Rate Decision", "currency": "EUR", "impact": "high", "forecast": "3.40%", "previous": "3.65%", "hour_offset": 6},
    {"event": "UK GDP m/m", "currency": "GBP", "impact": "high", "forecast": "0.1%", "previous": "-0.1%", "hour_offset": 8},
    {"event": "US Jobless Claims", "currency": "USD", "impact": "med", "forecast": "210K", "previous": "208K", "hour_offset": 10},
    {"event": "BOJ Interest Rate Decision", "currency": "JPY", "impact": "high", "forecast": "0.50%", "previous": "0.50%", "hour_offset": 12},
    {"event": "Canada Employment Change", "currency": "CAD", "impact": "high", "forecast": "25K", "previous": "32K", "hour_offset": 14},
    {"event": "Australia RBA Meeting Minutes", "currency": "AUD", "impact": "med", "forecast": "—", "previous": "—", "hour_offset": 16},
    {"event": "US FOMC Meeting Minutes", "currency": "USD", "impact": "high", "forecast": "—", "previous": "—", "hour_offset": 18},
    {"event": "NZ RBNZ Rate Decision", "currency": "NZD", "impact": "high", "forecast": "3.50%", "previous": "3.75%", "hour_offset": 20},
    {"event": "Eurozone CPI Flash Estimate", "currency": "EUR", "impact": "high", "forecast": "2.3%", "previous": "2.4%", "hour_offset": 22},
    {"event": "Swiss SNB Policy Rate", "currency": "CHF", "impact": "high", "forecast": "0.00%", "previous": "0.25%", "hour_offset": 24},
    {"event": "US Non-Farm Payrolls", "currency": "USD", "impact": "high", "forecast": "185K", "previous": "177K", "hour_offset": 26},
    {"event": "BOE Governor Bailey Speech", "currency": "GBP", "impact": "med", "forecast": "—", "previous": "—", "hour_offset": 28},
    {"event": "China Caixin Manufacturing PMI", "currency": "AUD", "impact": "med", "forecast": "51.2", "previous": "51.0", "hour_offset": 30},
]

AI_PREDICTIONS = {
    "high": "High volatility expected. Widen stops and reduce position size before release.",
    "med": "Moderate market reaction likely. Standard risk management applies.",
    "low": "Minimal impact expected unless data significantly misses forecast.",
}

@router.get("")
async def get_calendar():
    now = datetime.utcnow()
    result = []
    for ev in EVENTS_TEMPLATE:
        event_time = now + timedelta(hours=ev["hour_offset"])
        diff = int((event_time - now).total_seconds())
        hours = diff // 3600
        minutes = (diff % 3600) // 60
        countdown = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        result.append({
            "time": event_time.strftime("%H:%M"),
            "event": ev["event"],
            "currency": ev["currency"],
            "impact": ev["impact"],
            "forecast": ev["forecast"],
            "previous": ev["previous"],
            "countdown": countdown,
            "seconds_until": diff,
            "ai_prediction": AI_PREDICTIONS.get(ev["impact"], ""),
            "date": event_time.strftime("%b %d"),
        })
    return sorted(result, key=lambda x: x["seconds_until"])

@router.get("/upcoming")
async def get_upcoming(n: int = 5):
    all_events = await get_calendar()
    return all_events[:n]
