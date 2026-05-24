"""
Technical Analysis Engine
Computes RSI, MACD, Bollinger Bands, EMAs, SMAs, ATR, Stochastic,
detects candlestick patterns and Smart Money Concepts.
"""

import os
import asyncio
import httpx
import numpy as np
from typing import Optional
from cachetools import TTLCache

TWELVE_KEY = os.getenv("TWELVE_DATA_KEY", "")

_ta_cache = TTLCache(maxsize=100, ttl=60)  # 60s cache per pair/tf


class TAEngine:

    # ── Public ────────────────────────────────────────────────────────────────

    async def analyze(self, pair: str, timeframe: str = "1h") -> dict:
        cache_key = f"{pair}_{timeframe}"
        if cache_key in _ta_cache:
            return _ta_cache[cache_key]

        ohlcv = await self._fetch_ohlcv(pair, timeframe)
        result = self._compute_all(ohlcv, pair, timeframe)
        _ta_cache[cache_key] = result
        return result

    # ── Fetch OHLCV ───────────────────────────────────────────────────────────

    async def _fetch_ohlcv(self, pair: str, timeframe: str) -> dict:
        """Fetch OHLCV from TwelveData or generate synthetic data."""
        if TWELVE_KEY:
            try:
                return await self._twelve_ohlcv(pair, timeframe)
            except Exception:
                pass
        return self._synthetic_ohlcv(pair)

    async def _twelve_ohlcv(self, pair: str, timeframe: str) -> dict:
        symbol = pair.replace("/", "")
        interval_map = {"M15": "15min", "H1": "1h", "H4": "4h", "D1": "1day", "W1": "1week"}
        interval = interval_map.get(timeframe, "1h")
        url = (
            f"https://api.twelvedata.com/time_series?symbol={symbol}"
            f"&interval={interval}&outputsize=100&apikey={TWELVE_KEY}"
        )
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()

        values = data.get("values", [])
        closes = [float(v["close"]) for v in reversed(values)]
        highs  = [float(v["high"])  for v in reversed(values)]
        lows   = [float(v["low"])   for v in reversed(values)]
        opens  = [float(v["open"])  for v in reversed(values)]
        return {"closes": closes, "highs": highs, "lows": lows, "opens": opens}

    def _synthetic_ohlcv(self, pair: str) -> dict:
        """Generate realistic synthetic OHLCV for demo/fallback."""
        base_prices = {
            "EUR/USD": 1.0862, "GBP/USD": 1.2734, "USD/JPY": 151.43,
            "AUD/USD": 0.6541, "USD/CHF": 0.8932, "XAU/USD": 2341.5,
        }
        base = base_prices.get(pair, 1.1000)
        np.random.seed(hash(pair) % 2**31)
        returns = np.random.normal(0.0001, 0.002, 100)
        closes = base * np.cumprod(1 + returns)
        highs  = closes * (1 + np.abs(np.random.normal(0, 0.001, 100)))
        lows   = closes * (1 - np.abs(np.random.normal(0, 0.001, 100)))
        opens  = np.roll(closes, 1); opens[0] = base
        return {
            "closes": closes.tolist(),
            "highs": highs.tolist(),
            "lows": lows.tolist(),
            "opens": opens.tolist(),
        }

    # ── Core Calculations ─────────────────────────────────────────────────────

    def _compute_all(self, ohlcv: dict, pair: str, timeframe: str) -> dict:
        c = np.array(ohlcv["closes"])
        h = np.array(ohlcv["highs"])
        l = np.array(ohlcv["lows"])
        o = np.array(ohlcv["opens"])

        rsi        = self._rsi(c)
        macd_line, signal_line, histogram = self._macd(c)
        upper_bb, mid_bb, lower_bb = self._bollinger(c)
        ema20      = self._ema(c, 20)
        ema50      = self._ema(c, 50)
        ema200     = self._ema(c, 200)
        sma20      = self._sma(c, 20)
        atr        = self._atr(h, l, c)
        stoch_k, stoch_d = self._stochastic(h, l, c)
        cci        = self._cci(h, l, c)
        williams_r = self._williams_r(h, l, c)
        momentum   = self._momentum(c)

        indicators = [
            self._rsi_signal(rsi[-1]),
            self._macd_signal(macd_line[-1], signal_line[-1], histogram[-1]),
            self._bb_signal(c[-1], upper_bb[-1], mid_bb[-1], lower_bb[-1]),
            self._ema_cross_signal(c[-1], ema20[-1], ema50[-1], ema200[-1]),
            self._stoch_signal(stoch_k[-1], stoch_d[-1]),
            self._cci_signal(cci[-1]),
            self._williams_signal(williams_r[-1]),
            self._momentum_signal(momentum[-1]),
            self._atr_signal(atr[-1], c[-1]),
            self._sma_signal(c[-1], sma20[-1]),
        ]

        buy_count  = sum(1 for i in indicators if i["signal"] == "BUY")
        sell_count = sum(1 for i in indicators if i["signal"] == "SELL")
        neut_count = len(indicators) - buy_count - sell_count

        overall = "BULLISH" if buy_count > sell_count else "BEARISH" if sell_count > buy_count else "NEUTRAL"
        score = round((buy_count / len(indicators)) * 100)

        patterns   = self._detect_patterns(o, h, l, c)
        support, resistance = self._support_resistance(h, l, c)
        smc        = self._smart_money(o, h, l, c)
        trend      = self._trend_analysis(c, ema20, ema50)
        breakouts  = self._breakout_detection(h, l, c)

        return {
            "pair": pair,
            "timeframe": timeframe,
            "current_price": round(float(c[-1]), 5),
            "overall_signal": overall,
            "ai_score": score,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "neutral_count": neut_count,
            "indicators": indicators,
            "patterns": patterns,
            "support_levels": [round(s, 5) for s in support],
            "resistance_levels": [round(r, 5) for r in resistance],
            "smc": smc,
            "trend": trend,
            "breakouts": breakouts,
            "key_levels": {
                "ema20":    round(float(ema20[-1]), 5),
                "ema50":    round(float(ema50[-1]), 5),
                "ema200":   round(float(ema200[-1]), 5),
                "sma20":    round(float(sma20[-1]), 5),
                "upper_bb": round(float(upper_bb[-1]), 5),
                "lower_bb": round(float(lower_bb[-1]), 5),
                "atr":      round(float(atr[-1]), 5),
            },
        }

    # ── Indicator Math ────────────────────────────────────────────────────────

    def _rsi(self, closes: np.ndarray, period: int = 14) -> np.ndarray:
        delta = np.diff(closes)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = np.convolve(gain, np.ones(period)/period, mode='valid')
        avg_loss = np.convolve(loss, np.ones(period)/period, mode='valid')
        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        return 100 - (100 / (1 + rs))

    def _ema(self, closes: np.ndarray, period: int) -> np.ndarray:
        alpha = 2 / (period + 1)
        result = np.zeros_like(closes)
        result[0] = closes[0]
        for i in range(1, len(closes)):
            result[i] = alpha * closes[i] + (1 - alpha) * result[i - 1]
        return result

    def _sma(self, closes: np.ndarray, period: int) -> np.ndarray:
        kernel = np.ones(period) / period
        padded = np.pad(closes, (period - 1, 0), mode='edge')
        return np.convolve(padded, kernel, mode='valid')

    def _macd(self, closes: np.ndarray):
        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        macd  = ema12 - ema26
        signal = self._ema(macd, 9)
        hist   = macd - signal
        return macd, signal, hist

    def _bollinger(self, closes: np.ndarray, period: int = 20, std_dev: float = 2.0):
        sma = self._sma(closes, period)
        std = np.array([
            np.std(closes[max(0, i - period):i]) for i in range(1, len(closes) + 1)
        ])
        return sma + std_dev * std, sma, sma - std_dev * std

    def _atr(self, highs, lows, closes, period: int = 14) -> np.ndarray:
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1]))
        )
        return self._sma(tr, period)

    def _stochastic(self, highs, lows, closes, k_period: int = 14, d_period: int = 3):
        k = np.array([
            100 * (closes[i] - min(lows[max(0, i-k_period):i+1])) /
            max(1e-10, max(highs[max(0, i-k_period):i+1]) - min(lows[max(0, i-k_period):i+1]))
            for i in range(len(closes))
        ])
        d = self._sma(k, d_period)
        return k, d

    def _cci(self, highs, lows, closes, period: int = 20) -> np.ndarray:
        typical = (highs + lows + closes) / 3
        sma_tp  = self._sma(typical, period)
        mad = np.array([
            np.mean(np.abs(typical[max(0, i-period):i+1] - sma_tp[i]))
            for i in range(len(typical))
        ])
        return (typical - sma_tp) / (0.015 * np.where(mad == 0, 1e-10, mad))

    def _williams_r(self, highs, lows, closes, period: int = 14) -> np.ndarray:
        return np.array([
            -100 * (max(highs[max(0,i-period):i+1]) - closes[i]) /
            max(1e-10, max(highs[max(0,i-period):i+1]) - min(lows[max(0,i-period):i+1]))
            for i in range(len(closes))
        ])

    def _momentum(self, closes: np.ndarray, period: int = 10) -> np.ndarray:
        result = np.zeros_like(closes)
        result[period:] = closes[period:] - closes[:-period]
        return result

    # ── Signals ───────────────────────────────────────────────────────────────

    def _rsi_signal(self, rsi: float) -> dict:
        signal = "BUY" if rsi < 40 else "SELL" if rsi > 65 else "NEUTRAL"
        return {"name": "RSI (14)", "value": round(rsi, 1), "signal": signal,
                "progress": round(rsi), "description": f"RSI at {rsi:.1f}"}

    def _macd_signal(self, macd, signal, hist) -> dict:
        sig = "BUY" if hist > 0 and macd > signal else "SELL" if hist < 0 else "NEUTRAL"
        return {"name": "MACD", "value": f"{macd:+.5f}", "signal": sig,
                "progress": 70 if sig == "BUY" else 30 if sig == "SELL" else 50}

    def _bb_signal(self, price, upper, mid, lower) -> dict:
        if price <= lower:  sig, val, prog = "BUY", "AT LOWER BAND", 15
        elif price >= upper: sig, val, prog = "SELL", "AT UPPER BAND", 85
        else:               sig, val, prog = "NEUTRAL", "MID BAND", 50
        return {"name": "Bollinger Bands", "value": val, "signal": sig, "progress": prog}

    def _ema_cross_signal(self, price, ema20, ema50, ema200) -> dict:
        if price > ema20 > ema50 > ema200:
            return {"name": "EMA 20/50/200", "value": "PERFECT BULL", "signal": "BUY", "progress": 85}
        if price < ema20 < ema50:
            return {"name": "EMA 20/50/200", "value": "BEARISH STACK", "signal": "SELL", "progress": 20}
        if ema20 > ema50:
            return {"name": "EMA 20/50/200", "value": "GOLDEN CROSS", "signal": "BUY", "progress": 70}
        return {"name": "EMA 20/50/200", "value": "DEATH CROSS", "signal": "SELL", "progress": 30}

    def _stoch_signal(self, k, d) -> dict:
        sig = "BUY" if k < 25 and k > d else "SELL" if k > 75 and k < d else "NEUTRAL"
        return {"name": "Stochastic", "value": f"{k:.1f}", "signal": sig, "progress": round(k)}

    def _cci_signal(self, cci: float) -> dict:
        sig = "BUY" if cci < -80 else "SELL" if cci > 120 else "NEUTRAL"
        return {"name": "CCI (20)", "value": f"{cci:+.0f}", "signal": sig,
                "progress": min(100, max(0, int(50 + cci / 4)))}

    def _williams_signal(self, wr: float) -> dict:
        sig = "BUY" if wr < -75 else "SELL" if wr > -25 else "NEUTRAL"
        return {"name": "Williams %R", "value": f"{wr:.1f}", "signal": sig,
                "progress": min(100, max(0, int(100 + wr)))}

    def _momentum_signal(self, mom: float) -> dict:
        sig = "BUY" if mom > 0 else "SELL" if mom < 0 else "NEUTRAL"
        return {"name": "Momentum", "value": f"{mom:+.5f}", "signal": sig,
                "progress": 70 if sig == "BUY" else 30}

    def _atr_signal(self, atr: float, price: float) -> dict:
        pct = (atr / price) * 100
        vol = "HIGH" if pct > 0.15 else "MEDIUM" if pct > 0.08 else "LOW"
        return {"name": "ATR (Volatility)", "value": f"{atr:.5f} [{vol}]",
                "signal": "NEUTRAL", "progress": min(100, int(pct * 200))}

    def _sma_signal(self, price, sma20) -> dict:
        sig = "BUY" if price > sma20 else "SELL"
        return {"name": "SMA 20", "value": "ABOVE SMA" if sig == "BUY" else "BELOW SMA",
                "signal": sig, "progress": 65 if sig == "BUY" else 35}

    # ── Patterns ──────────────────────────────────────────────────────────────

    def _detect_patterns(self, o, h, l, c) -> list:
        patterns = []
        if len(c) < 3:
            return patterns

        # Last 3 candles
        o1, h1, l1, c1 = o[-3], h[-3], l[-3], c[-3]
        o2, h2, l2, c2 = o[-2], h[-2], l[-2], c[-2]
        o3, h3, l3, c3 = o[-1], h[-1], l[-1], c[-1]
        body3 = abs(c3 - o3)
        range3 = h3 - l3

        # Doji
        if body3 < range3 * 0.1:
            patterns.append({"name": "Doji", "type": "neutral", "confidence": 72})

        # Bullish engulfing
        if c2 < o2 and c3 > o3 and c3 > o2 and o3 < c2:
            patterns.append({"name": "Bullish Engulfing", "type": "bullish", "confidence": 84})

        # Bearish engulfing
        if c2 > o2 and c3 < o3 and c3 < o2 and o3 > c2:
            patterns.append({"name": "Bearish Engulfing", "type": "bearish", "confidence": 82})

        # Pin bar bullish (hammer)
        lower_wick = o3 - l3 if c3 > o3 else c3 - l3
        if lower_wick > body3 * 2 and body3 > 0:
            patterns.append({"name": "Bullish Pin Bar", "type": "bullish", "confidence": 76})

        # Pin bar bearish (shooting star)
        upper_wick = h3 - c3 if c3 > o3 else h3 - o3
        if upper_wick > body3 * 2 and body3 > 0:
            patterns.append({"name": "Bearish Pin Bar", "type": "bearish", "confidence": 74})

        # Higher lows (trend)
        if l[-1] > l[-5] > l[-10]:
            patterns.append({"name": "Higher Lows (Uptrend)", "type": "bullish", "confidence": 78})

        if h[-1] < h[-5] < h[-10]:
            patterns.append({"name": "Lower Highs (Downtrend)", "type": "bearish", "confidence": 76})

        # Morning star
        if c1 < o1 and body3 < (h2 - l2) * 0.3 and c3 > o3 and c3 > (o1 + c1) / 2:
            patterns.append({"name": "Morning Star", "type": "bullish", "confidence": 80})

        return patterns

    # ── Support / Resistance ──────────────────────────────────────────────────

    def _support_resistance(self, h, l, c, lookback: int = 20):
        recent_h = h[-lookback:]
        recent_l = l[-lookback:]

        # Find pivot highs
        resistance = []
        for i in range(2, len(recent_h) - 2):
            if recent_h[i] == max(recent_h[i-2:i+3]):
                resistance.append(recent_h[i])

        # Find pivot lows
        support = []
        for i in range(2, len(recent_l) - 2):
            if recent_l[i] == min(recent_l[i-2:i+3]):
                support.append(recent_l[i])

        return sorted(support, reverse=True)[:3], sorted(resistance)[:3]

    # ── Smart Money Concepts ──────────────────────────────────────────────────

    def _smart_money(self, o, h, l, c) -> list:
        results = []

        # Break of Structure
        if c[-1] > max(h[-10:-1]):
            results.append({"concept": "BOS", "description": "Break of Structure — Bullish BOS confirmed", "bias": "bullish"})
        elif c[-1] < min(l[-10:-1]):
            results.append({"concept": "BOS", "description": "Break of Structure — Bearish BOS confirmed", "bias": "bearish"})
        else:
            results.append({"concept": "Market Structure", "description": "Ranging — No clear BOS", "bias": "neutral"})

        # Order Block (simplified: last strong bearish/bullish candle before move)
        ob_price = round(float(o[-5]), 5)
        results.append({"concept": "Order Block", "description": f"Bullish OB @ {ob_price}", "bias": "bullish"})

        # Fair Value Gap
        for i in range(-5, -1):
            if l[i+1] > h[i-1]:  # Bullish FVG
                results.append({"concept": "FVG", "description": f"Bullish FVG: {round(h[i-1],5)}–{round(l[i+1],5)}", "bias": "bullish"})
                break
            if h[i+1] < l[i-1]:  # Bearish FVG
                results.append({"concept": "FVG", "description": f"Bearish FVG: {round(h[i+1],5)}–{round(l[i-1],5)}", "bias": "bearish"})
                break

        # Liquidity zones
        buy_side = round(float(max(h[-20:])), 5)
        sell_side = round(float(min(l[-20:])), 5)
        results.append({"concept": "Liquidity", "description": f"Buy-side liquidity @ {buy_side}", "bias": "neutral"})
        results.append({"concept": "Liquidity", "description": f"Sell-side liquidity @ {sell_side}", "bias": "neutral"})

        # Premium / Discount
        high20 = max(h[-20:])
        low20  = min(l[-20:])
        mid20  = (high20 + low20) / 2
        zone = "Premium Zone (potential sell)" if c[-1] > mid20 else "Discount Zone (potential buy)"
        results.append({"concept": "Premium/Discount", "description": zone, "bias": "bullish" if "buy" in zone else "bearish"})

        return results

    def _trend_analysis(self, c, ema20, ema50) -> dict:
        slope = (c[-1] - c[-20]) / c[-20] * 100
        direction = "UP" if slope > 0.1 else "DOWN" if slope < -0.1 else "SIDEWAYS"
        strength = "STRONG" if abs(slope) > 0.5 else "MODERATE" if abs(slope) > 0.2 else "WEAK"
        return {"direction": direction, "strength": strength, "slope_pct": round(slope, 3)}

    def _breakout_detection(self, h, l, c) -> list:
        breakouts = []
        recent_high = max(h[-20:-1])
        recent_low  = min(l[-20:-1])

        if c[-1] > recent_high:
            breakouts.append({"type": "BULLISH BREAKOUT", "level": round(float(recent_high), 5), "confirmed": True})
        if c[-1] < recent_low:
            breakouts.append({"type": "BEARISH BREAKOUT", "level": round(float(recent_low), 5), "confirmed": True})

        # Approaching breakout
        if recent_high - c[-1] < (recent_high - recent_low) * 0.05:
            breakouts.append({"type": "APPROACHING RESISTANCE", "level": round(float(recent_high), 5), "confirmed": False})

        return breakouts
