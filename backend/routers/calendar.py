"""routers/calendar.py - REAL Economic Calendar Week May 25-31, 2026"""
from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter()

# SOURCE: LiteFinance + ForexFactory + Investing.com - Week May 25-31, 2026
# All times in UTC
EVENTS = [
    # MONDAY May 25 - US Memorial Day, Catholic Whit Monday
    {"event": "US Memorial Day — Wall Street CLOSED", "currency": "USD", "impact": "high",
     "forecast": "—", "previous": "—", "day": "Mon May 25", "utc_hour": 0, "utc_min": 0,
     "note": "Thin liquidity expected. False breakouts possible. Avoid large positions."},

    # TUESDAY May 26
    {"event": "US CB Consumer Confidence", "currency": "USD", "impact": "high",
     "forecast": "98.3", "previous": "97.2", "day": "Tue May 26", "utc_hour": 14, "utc_min": 0,
     "note": "Beat = USD bullish. Miss = USD bearish. Key USD mover this week."},
    {"event": "US New Home Sales", "currency": "USD", "impact": "med",
     "forecast": "685K", "previous": "672K", "day": "Tue May 26", "utc_hour": 14, "utc_min": 0,
     "note": "Housing data — secondary USD impact."},
    {"event": "Fed Governor Cook Speech", "currency": "USD", "impact": "med",
     "forecast": "—", "previous": "—", "day": "Tue May 26", "utc_hour": 17, "utc_min": 0,
     "note": "Watch for rate hike/cut signals amid Iran-driven inflation fears."},

    # WEDNESDAY May 27
    {"event": "Australia CPI q/q", "currency": "AUD", "impact": "high",
     "forecast": "0.8%", "previous": "0.6%", "day": "Wed May 27", "utc_hour": 1, "utc_min": 30,
     "note": "Hot print = AUD bullish, delays RBA cuts. Miss = AUD bearish."},
    {"event": "RBNZ Official Cash Rate Decision", "currency": "NZD", "impact": "high",
     "forecast": "2.25%", "previous": "2.25%", "day": "Wed May 27", "utc_hour": 2, "utc_min": 0,
     "note": "Hold expected. Focus on hawkish tone and updated forecasts for NZD direction."},
    {"event": "RBNZ Press Conference", "currency": "NZD", "impact": "high",
     "forecast": "—", "previous": "—", "day": "Wed May 27", "utc_hour": 3, "utc_min": 0,
     "note": "Governor Orr comments on future rate path will drive NZD volatility."},
    {"event": "Germany GfK Consumer Climate", "currency": "EUR", "impact": "med",
     "forecast": "-18.2", "previous": "-19.4", "day": "Wed May 27", "utc_hour": 6, "utc_min": 0,
     "note": "Improvement = EUR positive. Still negative = EUR capped."},

    # THURSDAY May 28
    {"event": "US Prelim GDP q/q", "currency": "USD", "impact": "high",
     "forecast": "-0.2%", "previous": "-0.3%", "day": "Thu May 28", "utc_hour": 12, "utc_min": 30,
     "note": "GDP revision — smaller contraction expected. Beat = USD bullish. Miss = USD selloff."},
    {"event": "US Initial Jobless Claims", "currency": "USD", "impact": "high",
     "forecast": "225K", "previous": "227K", "day": "Thu May 28", "utc_hour": 12, "utc_min": 30,
     "note": "Tight labor market supports Fed hawkishness. Watch vs 230K threshold."},
    {"event": "Japan Tokyo CPI y/y", "currency": "JPY", "impact": "high",
     "forecast": "2.9%", "previous": "2.8%", "day": "Thu May 28", "utc_hour": 23, "utc_min": 30,
     "note": "Rising CPI may force BOJ to act — JPY bullish on hot print."},
    {"event": "New Zealand Government Budget Release", "currency": "NZD", "impact": "med",
     "forecast": "—", "previous": "—", "day": "Thu May 28", "utc_hour": 2, "utc_min": 0,
     "note": "Fiscal policy details may impact NZD sentiment."},

    # FRIDAY May 29
    {"event": "US Core PCE Price Index m/m", "currency": "USD", "impact": "high",
     "forecast": "0.3%", "previous": "0.3%", "day": "Fri May 29", "utc_hour": 12, "utc_min": 30,
     "note": "Fed's preferred inflation gauge. Hot print = rate hike fears, USD bullish, gold bearish."},
    {"event": "Canada GDP m/m", "currency": "CAD", "impact": "high",
     "forecast": "0.2%", "previous": "0.3%", "day": "Fri May 29", "utc_hour": 12, "utc_min": 30,
     "note": "Strong print = CAD bullish. Released same time as US PCE — expect volatility."},
    {"event": "Germany CPI m/m Flash", "currency": "EUR", "impact": "high",
     "forecast": "0.3%", "previous": "0.4%", "day": "Fri May 29", "utc_hour": 12, "utc_min": 0,
     "note": "Hot CPI reduces ECB June cut probability — EUR bullish on beat."},
    {"event": "US Personal Spending m/m", "currency": "USD", "impact": "med",
     "forecast": "0.2%", "previous": "0.7%", "day": "Fri May 29", "utc_hour": 12, "utc_min": 30,
     "note": "Consumer spending slowdown expected after tariff shock."},

    # SUNDAY May 31
    {"event": "China NBS Manufacturing PMI", "currency": "AUD", "impact": "high",
     "forecast": "49.8", "previous": "49.0", "day": "Sun May 31", "utc_hour": 1, "utc_min": 0,
     "note": "Below 50 = contraction = AUD/NZD bearish. Watch for China demand signal."},
]

AI_TIPS = {
    "high": "High impact — widen stops, reduce position size before this release.",
    "med": "Moderate impact — standard risk management applies.",
}

@router.get("")
async def get_calendar():
    now = datetime.utcnow()
    result = []
    for ev in EVENTS:
        # Calculate event datetime this week
        days_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
        day_abbr = ev["day"].split()[0]
        # Find next occurrence of this weekday
        current_weekday = now.weekday()
        target_weekday = days_map.get(day_abbr, 0)
        days_ahead = target_weekday - current_weekday
        if days_ahead < 0:
            days_ahead += 7
        event_date = now.replace(hour=ev["utc_hour"], minute=ev["utc_min"], second=0, microsecond=0) + timedelta(days=days_ahead)
        diff = int((event_date - now).total_seconds())
        if diff < -3600:  # more than 1 hour past
            diff += 7 * 86400
        hours = max(0, diff) // 3600
        minutes = (max(0, diff) % 3600) // 60
        if diff < 0:
            countdown = "Released"
        elif hours > 0:
            countdown = f"{hours}h {minutes}m"
        else:
            countdown = f"{minutes}m"
        result.append({
            "time": f"{ev['utc_hour']:02d}:{ev['utc_min']:02d} UTC",
            "event": ev["event"],
            "currency": ev["currency"],
            "impact": ev["impact"],
            "forecast": ev["forecast"],
            "previous": ev["previous"],
            "countdown": countdown,
            "seconds_until": diff,
            "date": ev["day"],
            "ai_prediction": ev.get("note", AI_TIPS.get(ev["impact"], "")),
        })
    return sorted(result, key=lambda x: x["seconds_until"])

@router.get("/upcoming")
async def get_upcoming(n: int = 5):
    all_events = await get_calendar()
    return [e for e in all_events if e["countdown"] != "Released"][:n]
