"""
AI Signal Engine
Combines technical analysis + fundamental sentiment + news
to generate high-quality BUY/SELL forex signals with
entry, TP, SL, confidence, risk rating and AI explanation.
"""

import os
import asyncio
import anthropic
from typing import Optional
from cachetools import TTLCache

from engines.ta_engine import TAEngine
from engines.currency_engine import CurrencyEngine

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

_signal_cache = TTLCache(maxsize=50, ttl=120)  # 2-min cache

SIGNAL_PROMPT = """You are a quantitative forex analyst generating precise trading signals.

Given the technical analysis data, generate a signal in ONLY valid JSON (no markdown):
{
  "direction": "BUY",
  "entry": 1.0862,
  "tp1": 1.0900,
  "tp2": 1.0940,
  "sl": 1.0830,
  "confidence": 84,
  "risk_level": "LOW",
  "risk_reward": 2.5,
  "reasons": ["Reason 1", "Reason 2", "Reason 3", "Reason 4"],
  "invalidation": "Signal invalid if price closes below 1.0820",
  "timeframe": "H4",
  "expiry_hours": 24
}

risk_level: "LOW" | "MEDIUM" | "HIGH"
confidence: 60–95
tp1 must give at least 1:1 risk/reward, tp2 at least 1:2
reasons: exactly 4 bullet points combining TA + fundamental factors"""


class SignalEngine:

    def __init__(self):
        self.ta = TAEngine()
        self.fx = CurrencyEngine()

    # ── Public ────────────────────────────────────────────────────────────────

    async def generate_signal(self, pair: str, timeframe: str = "H4") -> dict:
        cache_key = f"{pair}_{timeframe}"
        if cache_key in _signal_cache:
            return _signal_cache[cache_key]

        ta_data  = await self.ta.analyze(pair, timeframe)
        strength = await self.fx.get_strength_index()
        signal   = await self._build_signal(pair, timeframe, ta_data, strength)
        _signal_cache[cache_key] = signal
        return signal

    async def generate_all_signals(self, timeframe: str = "H4") -> list:
        pairs = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CHF", "USD/CAD", "XAU/USD", "GBP/JPY"]
        tasks = [self.generate_signal(p, timeframe) for p in pairs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        signals = [r for r in results if not isinstance(r, Exception)]
        # Sort by confidence
        return sorted(signals, key=lambda x: x.get("confidence", 0), reverse=True)

    async def get_top_signals(self, n: int = 5) -> list:
        all_signals = await self.generate_all_signals()
        return all_signals[:n]

    # ── Build Signal ──────────────────────────────────────────────────────────

    async def _build_signal(self, pair: str, timeframe: str, ta: dict, strength: dict) -> dict:
        # Try AI-generated signal first
        try:
            signal = await self._claude_signal(pair, timeframe, ta, strength)
        except Exception as e:
            print(f"Claude signal error for {pair}: {e}")
            signal = self._rule_based_signal(pair, ta)

        signal["pair"] = pair
        signal["timeframe"] = timeframe
        signal["ai_score"] = ta.get("ai_score", 50)
        signal["trend"] = ta.get("trend", {})
        signal["breakouts"] = ta.get("breakouts", [])
        signal["support_levels"] = ta.get("support_levels", [])
        signal["resistance_levels"] = ta.get("resistance_levels", [])
        return signal

    async def _claude_signal(self, pair: str, timeframe: str, ta: dict, strength: dict) -> dict:
        """Use Claude to generate an intelligent signal."""
        import json

        # Build context
        indicators_summary = "\n".join([
            f"- {ind['name']}: {ind['value']} → {ind['signal']}"
            for ind in ta.get("indicators", [])[:8]
        ])

        patterns_summary = ", ".join([
            f"{p['name']} ({p['confidence']}%)"
            for p in ta.get("patterns", [])
        ]) or "No clear patterns"

        smc_summary = "\n".join([
            f"- {s['concept']}: {s['description']}"
            for s in ta.get("smc", [])[:4]
        ])

        base_curr = pair.split("/")[0]
        quote_curr = pair.split("/")[1]
        base_strength = strength.get(base_curr, 50)
        quote_strength = strength.get(quote_curr, 50)

        user_msg = f"""Pair: {pair} | Timeframe: {timeframe}
Current Price: {ta.get('current_price')}
Overall TA Signal: {ta.get('overall_signal')} (Score: {ta.get('ai_score')}/100)
Buy/Sell/Neutral Count: {ta.get('buy_count')}/{ta.get('sell_count')}/{ta.get('neutral_count')}

Key Indicators:
{indicators_summary}

Patterns Detected: {patterns_summary}

Smart Money Concepts:
{smc_summary}

Currency Strength: {base_curr}={base_strength} vs {quote_curr}={quote_strength}
Support: {ta.get('support_levels', [])}
Resistance: {ta.get('resistance_levels', [])}"""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                system=SIGNAL_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            ),
        )

        import re
        text = response.content[0].text.strip()
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)

    def _rule_based_signal(self, pair: str, ta: dict) -> dict:
        """Fallback: rule-based signal from TA data."""
        score = ta.get("ai_score", 50)
        price = ta.get("current_price", 1.0)
        pip = 0.0001 if "JPY" not in pair else 0.01
        if pair == "XAU/USD":
            pip = 0.5

        direction = "BUY" if score >= 55 else "SELL"
        sl_pips  = 30 * pip
        tp1_pips = 35 * pip
        tp2_pips = 70 * pip

        if direction == "BUY":
            entry = price
            tp1   = round(price + tp1_pips, 5)
            tp2   = round(price + tp2_pips, 5)
            sl    = round(price - sl_pips, 5)
        else:
            entry = price
            tp1   = round(price - tp1_pips, 5)
            tp2   = round(price - tp2_pips, 5)
            sl    = round(price + sl_pips, 5)

        conf = min(90, max(60, score + 10))
        risk = "LOW" if conf > 80 else "MEDIUM" if conf > 70 else "HIGH"

        return {
            "direction":   direction,
            "entry":       round(entry, 5),
            "tp1":         tp1,
            "tp2":         tp2,
            "sl":          sl,
            "confidence":  conf,
            "risk_level":  risk,
            "risk_reward": round(tp1_pips / sl_pips, 1),
            "reasons": [
                f"TA Score: {score}/100 favoring {direction}",
                f"Overall signal: {ta.get('overall_signal')}",
                f"{ta.get('buy_count', 0)} buy vs {ta.get('sell_count', 0)} sell indicators",
                "Trend confirmation on current timeframe",
            ],
            "invalidation": f"Signal invalid if price moves against by {round(sl_pips*1.5, 5)}",
            "timeframe":    "H4",
            "expiry_hours": 24,
        }
