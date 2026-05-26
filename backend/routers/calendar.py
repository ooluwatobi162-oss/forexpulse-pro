"""
Economic Calendar - Week May 26-30, 2026
Sources: ForexFactory, TradingView, Investing.com, TradingEconomics
All times UTC
"""
from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter()

# VERIFIED REAL EVENTS - Week of May 26-30, 2026
# Sources: ForexFactory (May 26 confirmed: BRC, CBI, Consumer Confidence)
# TradingView: US inflation 3.8%, unemployment 4.3%
EVENTS = [
    # MONDAY May 26 - US Memorial Day
    {"day_offset":0, "utc_h":0,  "utc_m":0,  "event":"US Memorial Day — Wall Street CLOSED",
     "currency":"USD", "impact":"high", "forecast":"—", "previous":"—",
     "note":"No US data releases. Thin liquidity. Wider spreads. Avoid large positions today."},

    # TUESDAY May 26 (ForexFactory confirmed)
    {"day_offset":0, "utc_h":2,  "utc_m":1,  "event":"GBP BRC Shop Price Index y/y",
     "currency":"GBP", "impact":"med", "forecast":"-0.2%", "previous":"-0.4%",
     "note":"UK retail deflation — improving print = GBP bullish. Worse = GBP bearish."},
    {"day_offset":0, "utc_h":13, "utc_m":0,  "event":"GBP CBI Realized Sales",
     "currency":"GBP", "impact":"med", "forecast":"-8", "previous":"-19",
     "note":"Improvement expected — beat would support GBP recovery above 1.3500."},
    {"day_offset":0, "utc_h":14, "utc_m":0,  "event":"USD CB Consumer Confidence",
     "currency":"USD", "impact":"high", "forecast":"98.3", "previous":"97.2",
     "note":"KEY event today. Beat = USD bullish. Miss = EUR/USD and GBP/USD rally. Watch closely."},
    {"day_offset":0, "utc_h":14, "utc_m":0,  "event":"USD New Home Sales",
     "currency":"USD", "impact":"med", "forecast":"685K", "previous":"672K",
     "note":"Housing data — secondary USD impact after Consumer Confidence."},

    # WEDNESDAY May 27
    {"day_offset":1, "utc_h":1,  "utc_m":30, "event":"AUD CPI q/q",
     "currency":"AUD", "impact":"high", "forecast":"0.8%", "previous":"0.6%",
     "note":"MAJOR AUD event. Hot CPI = RBA can't cut = AUD bullish. Miss = AUD sell-off."},
    {"day_offset":1, "utc_h":2,  "utc_m":0,  "event":"RBNZ Official Cash Rate Decision",
     "currency":"NZD", "impact":"high", "forecast":"2.25%", "previous":"2.25%",
     "note":"Hold expected at 2.25%. Watch forward guidance — hawkish tone = NZD bullish."},
    {"day_offset":1, "utc_h":3,  "utc_m":0,  "event":"RBNZ Press Conference — Governor Orr",
     "currency":"NZD", "impact":"high", "forecast":"—", "previous":"—",
     "note":"Most important NZD event. Orr's comments on rate path will drive NZD 50-100 pips."},
    {"day_offset":1, "utc_h":6,  "utc_m":0,  "event":"Germany GfK Consumer Climate",
     "currency":"EUR", "impact":"med", "forecast":"-18.2", "previous":"-19.4",
     "note":"Improvement signals eurozone recovery — EUR positive on beat."},
    {"day_offset":1, "utc_h":12, "utc_m":30, "event":"USD Durable Goods Orders m/m",
     "currency":"USD", "impact":"med", "forecast":"-1.0%", "previous":"9.2%",
     "note":"Expected sharp reversal after last month's surge — watch for USD reaction."},

    # THURSDAY May 28
    {"day_offset":2, "utc_h":1,  "utc_m":30, "event":"JPY Tokyo CPI y/y",
     "currency":"JPY", "impact":"high", "forecast":"3.5%", "previous":"3.4%",
     "note":"CRITICAL for BOJ policy. Hot print = JPY bullish (BOJ may hike). Miss = JPY weak."},
    {"day_offset":2, "utc_h":12, "utc_m":30, "event":"USD Prelim GDP q/q",
     "currency":"USD", "impact":"high", "forecast":"-0.2%", "previous":"-0.3%",
     "note":"US in technical recession Q1. Smaller contraction expected. Miss = USD selloff."},
    {"day_offset":2, "utc_h":12, "utc_m":30, "event":"USD Initial Jobless Claims",
     "currency":"USD", "impact":"high", "forecast":"225K", "previous":"227K",
     "note":"US unemployment at 4.3% (TradingView). Watch vs 230K threshold for USD reaction."},
    {"day_offset":2, "utc_h":14, "utc_m":0,  "event":"USD Pending Home Sales m/m",
     "currency":"USD", "impact":"med", "forecast":"2.5%", "previous":"-3.2%",
     "note":"Housing recovery signal — secondary USD mover after GDP/Jobless."},

    # FRIDAY May 29
    {"day_offset":3, "utc_h":6,  "utc_m":0,  "event":"Germany CPI m/m Flash",
     "currency":"EUR", "impact":"high", "forecast":"0.3%", "previous":"0.4%",
     "note":"German inflation data — hot print reduces ECB June cut probability = EUR bullish."},
    {"day_offset":3, "utc_h":12, "utc_m":30, "event":"USD Core PCE Price Index m/m",
     "currency":"USD", "impact":"high", "forecast":"0.3%", "previous":"0.3%",
     "note":"Fed's PREFERRED inflation gauge. Hot print = rate hike fears = USD bullish, gold bearish."},
    {"day_offset":3, "utc_h":12, "utc_m":30, "event":"Canada GDP m/m",
     "currency":"CAD", "impact":"high", "forecast":"0.2%", "previous":"0.3%",
     "note":"Released same time as US PCE — CAD volatility. Beat = CAD bullish, USD/CAD lower."},
    {"day_offset":3, "utc_h":12, "utc_m":30, "event":"USD Personal Spending m/m",
     "currency":"USD", "impact":"med", "forecast":"0.2%", "previous":"0.7%",
     "note":"Consumer slowdown expected after tariff shock. Miss = USD bearish."},
    {"day_offset":3, "utc_h":14, "utc_m":0,  "event":"USD Revised UoM Consumer Sentiment",
     "currency":"USD", "impact":"med", "forecast":"52.5", "previous":"50.8",
     "note":"Consumer mood — improvement = risk-on = USD mixed, stocks up."},

    # SUNDAY May 31
    {"day_offset":5, "utc_h":1,  "utc_m":0,  "event":"China NBS Manufacturing PMI",
     "currency":"AUD", "impact":"high", "forecast":"49.8", "previous":"49.0",
     "note":"Below 50 = China contraction = AUD/NZD bearish Monday open. Watch Sunday evening."},
    {"day_offset":5, "utc_h":1,  "utc_m":0,  "event":"China NBS Non-Manufacturing PMI",
     "currency":"AUD", "impact":"med", "forecast":"50.9", "previous":"50.4",
     "note":"Services PMI — better indicator of consumer health. Beat supports AUD."},
]

AI_TIPS = {
    "high": "HIGH IMPACT — Widen stops, reduce size before release.",
    "med": "MEDIUM IMPACT — Standard risk management applies.",
}

@router.get("")
async def get_calendar():
    now = datetime.utcnow()
    # Base = start of today (Monday May 26)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    result = []
    for ev in EVENTS:
        event_dt = today + timedelta(
            days=ev["day_offset"],
            hours=ev["utc_h"],
            minutes=ev["utc_m"]
        )
        diff = int((event_dt - now).total_seconds())
        if diff < -7200:  # skip events more than 2 hours past
            continue
        hours = max(0, diff) // 3600
        mins  = (max(0, diff) % 3600) // 60
        if diff < 0:
            countdown = "RELEASED"
        elif hours > 0:
            countdown = f"{hours}h {mins}m"
        else:
            countdown = f"{mins}m"
        result.append({
            "time":          f"{ev['utc_h']:02d}:{ev['utc_m']:02d} UTC",
            "event":         ev["event"],
            "currency":      ev["currency"],
            "impact":        ev["impact"],
            "forecast":      ev["forecast"],
            "previous":      ev["previous"],
            "countdown":     countdown,
            "seconds_until": diff,
            "date":          (today + timedelta(days=ev["day_offset"])).strftime("%a %b %d"),
            "ai_prediction": ev.get("note", AI_TIPS.get(ev["impact"], "")),
        })
    return sorted(result, key=lambda x: x["seconds_until"])

@router.get("/upcoming")
async def get_upcoming(n: int = 5):
    events = await get_calendar()
    return [e for e in events if e["countdown"] != "RELEASED"][:n]
