"""routers/calendar.py"""
from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter()

EVENTS = [
    {"time": "14:30", "event": "US Core CPI m/m", "currency": "USD", "impact": "high", "forecast": "0.3%", "previous": "0.4%", "description": "Consumer Price Index measures change in the price of goods and services from the perspective of the consumer."},
    {"time": "15:00", "event": "ISM Manufacturing PMI", "currency": "USD", "impact": "medium", "forecast": "49.5", "previous": "49.2", "description": "Purchasing Managers Index - a leading economic indicator"},
    {"time": "16:00", "event": "Fed Bowman Speech", "currency": "USD", "impact": "high", "forecast": "—", "previous": "—", "description": "Federal Reserve Board Governor speech may signal future policy"},
    {"time": "18:00", "event": "ECB Lane Speech", "currency": "EUR", "impact": "medium", "forecast": "—", "previous": "—", "description": "ECB Chief Economist speech - watch for rate cut signals"},
    {"time": "20:00", "event": "FOMC Meeting Minutes", "currency": "USD", "impact": "high", "forecast": "—", "previous": "—", "description": "Detailed record of the FOMC's most recent meeting"},
    {"time": "02:30", "event": "China Caixin Manufacturing PMI", "currency": "AUD", "impact": "medium", "forecast": "51.0", "previous": "51.4", "description": "Private sector survey of China manufacturing - impacts AUD/NZD"},
    {"time": "09:30", "event": "UK GDP m/m", "currency": "GBP", "impact": "high", "forecast": "0.1%", "previous": "-0.1%", "description": "Gross Domestic Product measures the value of all goods and services produced in the UK"},
    {"time": "10:00", "event": "Eurozone CPI Flash", "currency": "EUR", "impact": "high", "forecast": "2.4%", "previous": "2.6%", "description": "Flash estimate of consumer price inflation in the Eurozone"},
    {"time": "12:30", "event": "US Jobless Claims", "currency": "USD", "impact": "medium", "forecast": "212K", "previous": "208K", "description": "Number of individuals filing for unemployment benefits"},
    {"time": "13:30", "event": "BOC Interest Rate Decision", "currency": "CAD", "impact": "high", "forecast": "5.00%", "previous": "5.00%", "description": "Bank of Canada sets target for overnight lending rate"},
]

@router.get("")
async def get_calendar():
    now = datetime.utcnow()
    result = []
    for i, ev in enumerate(EVENTS):
        h, m = map(int, ev["time"].split(":"))
        event_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if event_time < now:
            event_time += timedelta(days=1)
        diff = int((event_time - now).total_seconds())
        hours = diff // 3600
        minutes = (diff % 3600) // 60
        countdown = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        result.append({**ev, "countdown": countdown, "seconds_until": diff})

    return sorted(result, key=lambda x: x["seconds_until"])

@router.get("/upcoming")
async def get_upcoming(n: int = 5):
    all_events = await get_calendar()
    return all_events[:n]
