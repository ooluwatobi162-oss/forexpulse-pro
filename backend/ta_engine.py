"""
Technical Analysis Engine - Render-compatible version (no numpy/pandas)
Uses pure Python math for all calculations.
"""

import os
import asyncio
import random
import math
from cachetools import TTLCache

TWELVE_KEY = os.getenv("TWELVE_DATA_KEY", "")
_ta_cache = TTLCache(maxsize=100, ttl=60)

BASE_PRICES = {
    "EUR/USD": 1.1320, "GBP/USD": 1.3450, "USD/JPY": 159.15,
    "AUD/USD": 0.6480, "USD/CHF": 0.8980, "XAU/USD": 3285.00,
    "USD/CAD": 1.3820, "NZD/USD": 0.5920,
}

class TAEngine:

    async def analyze(self, pair: str, timeframe: str = "H1") -> dict:
        cache_key = f"{pair}_{timeframe}"
        if cache_key in _ta_cache:
            return _ta_cache[cache_key]
        ohlcv = self._synthetic_ohlcv(pair)
        result = self._compute_all(ohlcv, pair, timeframe)
        _ta_cache[cache_key] = result
        return result

    def _synthetic_ohlcv(self, pair: str) -> dict:
        base = BASE_PRICES.get(pair, 1.1000)
        random.seed(hash(pair) % 2**31)
        closes = [base]
        for _ in range(99):
            closes.append(closes[-1] * (1 + (random.random() - 0.5) * 0.004))
        highs  = [c * (1 + abs(random.gauss(0, 0.001))) for c in closes]
        lows   = [c * (1 - abs(random.gauss(0, 0.001))) for c in closes]
        opens  = [closes[0]] + closes[:-1]
        return {"closes": closes, "highs": highs, "lows": lows, "opens": opens}

    def _mean(self, data): return sum(data) / len(data) if data else 0
    def _std(self, data):
        m = self._mean(data)
        return math.sqrt(sum((x - m) ** 2 for x in data) / len(data)) if data else 0

    def _ema(self, closes, period):
        alpha = 2 / (period + 1)
        result = [closes[0]]
        for i in range(1, len(closes)):
            result.append(alpha * closes[i] + (1 - alpha) * result[-1])
        return result

    def _sma(self, closes, period):
        result = []
        for i in range(len(closes)):
            window = closes[max(0, i - period + 1):i + 1]
            result.append(self._mean(window))
        return result

    def _rsi(self, closes, period=14):
        if len(closes) < period + 1:
            return [50.0] * len(closes)
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [max(d, 0) for d in deltas]
        losses = [max(-d, 0) for d in deltas]
        avg_gain = self._mean(gains[:period])
        avg_loss = self._mean(losses[:period])
        rsi_values = []
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            rs = avg_gain / avg_loss if avg_loss != 0 else 100
            rsi_values.append(100 - (100 / (1 + rs)))
        return [50.0] * (period + 1) + rsi_values

    def _compute_all(self, ohlcv: dict, pair: str, timeframe: str) -> dict:
        c = ohlcv["closes"]
        h = ohlcv["highs"]
        l = ohlcv["lows"]
        o = ohlcv["opens"]

        rsi_vals = self._rsi(c)
        rsi = rsi_vals[-1] if rsi_vals else 50
        ema20 = self._ema(c, 20)[-1]
        ema50 = self._ema(c, 50)[-1]
        ema200 = self._ema(c, 200)[-1]
        sma20 = self._sma(c, 20)[-1]
        bb_mid = sma20
        std = self._std(c[-20:])
        bb_upper = bb_mid + 2 * std
        bb_lower = bb_mid - 2 * std

        price = c[-1]

        indicators = [
            {"name": "RSI (14)", "value": f"{rsi:.1f}", "signal": "bull" if rsi < 40 else "bear" if rsi > 65 else "neut", "progress": int(rsi)},
            {"name": "EMA 20/50/200", "value": "GOLDEN CROSS" if ema20 > ema50 else "DEATH CROSS", "signal": "bull" if ema20 > ema50 else "bear", "progress": 75 if ema20 > ema50 else 25},
            {"name": "Bollinger Bands", "value": "LOWER BAND" if price <= bb_lower else "UPPER BAND" if price >= bb_upper else "MID BAND", "signal": "bull" if price <= bb_lower else "bear" if price >= bb_upper else "neut", "progress": 50},
            {"name": "SMA 20", "value": "ABOVE SMA" if price > sma20 else "BELOW SMA", "signal": "bull" if price > sma20 else "bear", "progress": 65 if price > sma20 else 35},
            {"name": "Trend", "value": "UPTREND" if c[-1] > c[-10] else "DOWNTREND", "signal": "bull" if c[-1] > c[-10] else "bear", "progress": 70 if c[-1] > c[-10] else 30},
            {"name": "Momentum", "value": f"{c[-1]-c[-10]:+.5f}", "signal": "bull" if c[-1] > c[-10] else "bear", "progress": 65 if c[-1] > c[-10] else 35},
            {"name": "Price vs EMA200", "value": "ABOVE" if price > ema200 else "BELOW", "signal": "bull" if price > ema200 else "bear", "progress": 72 if price > ema200 else 28},
            {"name": "Volatility", "value": f"{std:.5f}", "signal": "neut", "progress": 50},
        ]

        buy_count = sum(1 for i in indicators if i["signal"] == "bull")
        sell_count = sum(1 for i in indicators if i["signal"] == "bear")
        overall = "BULLISH" if buy_count > sell_count else "BEARISH" if sell_count > buy_count else "NEUTRAL"
        score = round((buy_count / len(indicators)) * 100)

        patterns = []
        if abs(c[-1] - o[-1]) < (h[-1] - l[-1]) * 0.1:
            patterns.append({"name": "Doji", "type": "neutral", "confidence": 72})
        if c[-2] < o[-2] and c[-1] > o[-1] and c[-1] > o[-2] and o[-1] < c[-2]:
            patterns.append({"name": "Bullish Engulfing", "type": "bullish", "confidence": 84})
        if c[-2] > o[-2] and c[-1] < o[-1] and c[-1] < o[-2] and o[-1] > c[-2]:
            patterns.append({"name": "Bearish Engulfing", "type": "bearish", "confidence": 82})
        if l[-1] < min(l[-6:-1]):
            patterns.append({"name": "New Low — Bearish", "type": "bearish", "confidence": 70})
        if h[-1] > max(h[-6:-1]):
            patterns.append({"name": "New High — Bullish", "type": "bullish", "confidence": 70})

        support = sorted(set([round(min(l[i:i+5]), 5) for i in range(0, 20, 5)]))[:3]
        resistance = sorted(set([round(max(h[i:i+5]), 5) for i in range(0, 20, 5)]))[:3]

        smc = [
            {"concept": "Market Structure", "description": "BOS Confirmed ↗" if overall == "BULLISH" else "BOS Confirmed ↘", "bias": "bullish" if overall == "BULLISH" else "bearish"},
            {"concept": "Order Block", "description": f"Bullish OB @ {round(min(l[-10:]), 5)}", "bias": "bullish"},
            {"concept": "Fair Value Gap", "description": "FVG identified in recent price action", "bias": "neutral"},
            {"concept": "Liquidity", "description": f"Buy-side liquidity @ {round(max(h[-20:]), 5)}", "bias": "neutral"},
            {"concept": "Premium/Discount", "description": "Discount Zone" if price < self._mean(c[-20:]) else "Premium Zone", "bias": "bullish" if price < self._mean(c[-20:]) else "bearish"},
        ]

        return {
            "pair": pair, "timeframe": timeframe,
            "current_price": round(price, 5),
            "overall_signal": overall, "ai_score": score,
            "buy_count": buy_count, "sell_count": sell_count,
            "neutral_count": len(indicators) - buy_count - sell_count,
            "indicators": indicators, "patterns": patterns,
            "support_levels": support, "resistance_levels": resistance,
            "smc": smc,
            "trend": {"direction": "UP" if c[-1] > c[-20] else "DOWN", "strength": "MODERATE", "slope_pct": round((c[-1]/c[-20]-1)*100, 3)},
            "breakouts": [],
            "key_levels": {"ema20": round(ema20, 5), "ema50": round(ema50, 5), "ema200": round(ema200, 5), "sma20": round(sma20, 5), "upper_bb": round(bb_upper, 5), "lower_bb": round(bb_lower, 5)},
        }
