"""routers/ai_chat.py — AI Analyst Chat powered by Claude"""
import os
import asyncio
import anthropic
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

SYSTEM_PROMPT = """You are ForexPulse Pro's elite AI analyst — an institutional-grade forex intelligence system with deep knowledge of:
- Macroeconomic fundamentals (interest rates, inflation, GDP, employment)
- Technical analysis (RSI, MACD, Bollinger Bands, EMA, SMC, ICT concepts)
- Currency correlations and intermarket relationships
- Central bank policies (Fed, ECB, BoE, BoJ, RBA, RBNZ, BoC, SNB)
- Price action and candlestick patterns
- Smart Money Concepts (order blocks, FVG, liquidity sweeps, BOS/CHoCH)

Current Market Snapshot:
- EUR/USD: 1.08621 (bearish bias — ECB cut priced in)
- GBP/USD: 1.27340 (mixed — CPI undershoot but BoE hawkish)
- USD/JPY: 151.432 (bullish — JPY weak on GDP contraction)
- XAU/USD: 2341.50 (strong bullish — geopolitical + safe haven)
- DXY: ~104.2 (bullish — Fed hawkishness)
- Currency Strength: USD(72) > CAD(63) > EUR(58) > AUD(51) > CHF(55) > NZD(44) > GBP(45) > JPY(38)

Response style:
- Concise and data-driven
- Include specific price levels when relevant
- Bold the most important insight
- End with a clear directional bias when possible
- Max 200 words per response"""


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.post("")
async def chat(request: ChatRequest):
    messages = []

    # Add conversation history (max last 10 turns)
    for h in request.history[-10:]:
        if h.get("role") in ("user", "assistant"):
            messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": request.message})

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                system=SYSTEM_PROMPT,
                messages=messages,
            ),
        )
        reply = response.content[0].text
        return {"reply": reply, "model": "claude-sonnet-4", "status": "success"}

    except Exception as e:
        # Fallback response
        fallback = _fallback_response(request.message)
        return {"reply": fallback, "model": "fallback", "status": "degraded", "error": str(e)}


def _fallback_response(msg: str) -> str:
    msg_lower = msg.lower()
    if "gold" in msg_lower or "xau" in msg_lower:
        return "Gold at $2,341 — rallying on geopolitical tensions and declining real yields. DXY softness supporting the move. Key resistance: $2,365. Break above targets $2,400."
    if "eur" in msg_lower:
        return "EUR/USD bearish — ECB June cut at 78% probability. USD strength dominant. Bias: SELL rallies toward 1.0880. Support: 1.0790, Resistance: 1.0920."
    if "gbp" in msg_lower:
        return "GBP mixed — BoE hawkish tone but CPI undershoot (2.3%). Below-target inflation limits GBP upside. GBP/JPY BUY offers better opportunity than cable."
    if "strong" in msg_lower or "strength" in msg_lower:
        return "Currency strength today: USD(72) leads on Fed hawkishness. CAD(63) supported by oil. JPY(38) and GBP(45) weakest. Favor USD longs and JPY shorts."
    if "best" in msg_lower or "trade" in msg_lower:
        return "Top opportunities: 1) XAU/USD BUY (91% conf) — momentum + geopolitical. 2) USD/CHF BUY (85% conf) — SNB cut divergence. 3) GBP/JPY BUY (82% conf) — dual weakness."
    return "Market currently showing USD strength across the board. EUR/USD under pressure, gold maintaining safe-haven bid. Watch 14:30 UTC for US data — potential high volatility."
