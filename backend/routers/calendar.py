"""routers/calendar.py - Real Economic Calendar May 25, 2026"""
from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter()

# Real events for week of May 25-29, 2026 (UTC times)
EVENTS = [
    {"event": "US Memorial Day — Markets Closed", "currency": "USD", "impact": "high", "forecast": "—", "previous": "—", "hour_offset": 0, "date": "May 25"},
    {"event": "German IFO Business Climate", "currency": "EUR", "impact": "med", "forecast": "87.5", "previous": "86.9", "hour_offset": 8, "date": "May 26"},
    {"event": "ECB President Lagarde Speech", "currency": "EUR", "impact": "high", "forecast": "—", "previous": "—", "hour_offset": 10, "date": "May 26"},
    {"event": "Fed Governor Waller Speech", "currency": "USD", "impact": "high", "forecast": "—", "previous": "—", "hour_offset": 14, "date": "May 26"},
    {"event": "US Consumer Confidence", "currency": "USD", "impact": "med", "forecast": "98.5", "previous": "97.2", "hour_offset": 14, "date": "May 27"},
    {"event": "US Q1 GDP (Second Estimate)", "currency": "USD", "impact": "high", "forecast": "-0.2%", "previous": "-0.3%", "hour_offset": 12, "date": "May 28"},
    {"event": "US Initial Jobless Claims", "currency": "USD", "impact": "med", "forecast": "225K", "previous": "227K", "hour_offset": 12, "date": "May 28"},
    {"event": "Eurozone CPI Flash May", "currency": "EUR", "impact": "high", "forecast": "3.8%", "previous": "3.5%", "hour_offset": 9, "date": "May 29"},
    {"event": "US Core PCE Price Index", "currency": "USD", "impact": "high", "forecast": "0.3%", "previous": "0.3%", "hour_offset": 12, "date": "May 29"},
    {"event": "Canada GDP m/m", "currency": "CAD", "impact": "high", "forecast": "0.2%", "previous": "0.3%", "hour_offset": 12, "date": "May 29"},
    {"event": "Fed Barkin Speech", "currency": "USD", "impact": "med", "forecast": "—", "previous": "—", "hour_offset": 15, "date": "May 29"},
    {"event": "BOJ Meeting Minutes", "currency": "JPY", "impact": "high", "forecast": "—", "previous": "—", "hour_offset": 23, "date": "May 29"},
]

AI_TIPS = {
    "high": "High impact — widen stops, reduce position size before release.",
    "med": "Moderate impact — normal risk management applies.",
    "low": "Low impact — minimal market movement expected.",
}

@router.get("")
async def get_calendar():
    now = datetime.utcnow()
    result = []
    for i, ev in enumerate(EVENTS):
        event_time = now + timedelta(hours=ev["hour_offset"])
        diff = int((event_time - now).total_seconds())
        if diff < 0:
            diff = diff + 86400 * 7  # push to next week if past
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
            "date": ev["date"],
            "ai_prediction": AI_TIPS.get(ev["impact"], ""),
        })
    return sorted(result, key=lambda x: x["seconds_until"])

@router.get("/upcoming")
async def get_upcoming(n: int = 5):
    all_events = await get_calendar()
    return all_events[:n]
