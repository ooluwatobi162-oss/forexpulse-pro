"""
Currency Engine - Updated with current market prices May 2026
"""

import os
import time
import random
from cachetools import TTLCache

TWELVE_KEY = os.getenv("TWELVE_DATA_KEY", "")

PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "AUD/USD", "USD/CAD", "NZD/USD", "EUR/GBP",
    "EUR/JPY", "GBP/JPY", "USD/MXN", "XAU/USD",
]

CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "NZD", "CHF"]

# ✅ UPDATED TO CURRENT MARKET PRICES - May 2026
BASE_PRICES = {
    "EUR/USD": 1.1320,
    "GBP/USD": 1.3450,
    "USD/JPY": 159.15,
    "USD/CHF": 0.8980,
    "AUD/USD": 0.6480,
    "USD/CAD": 1.3820,
    "NZD/USD": 0.5920,
    "EUR/GBP": 0.8410,
    "EUR/JPY": 180.15,
    "GBP/JPY": 214.05,
    "USD/MXN": 19.350,
    "XAU/USD": 3285.00,
}

_price_cache    = TTLCache(maxsize=50, ttl=3)
_strength_cache = TTLCache(maxsize=10, ttl=10)

_sim_prices = dict(BASE_PRICES)


def _simulate_prices() -> dict:
    global _sim_prices
    result = {}
    for pair, base in BASE_PRICES.items():
        old = _sim_prices.get(pair, base)
        factor = 0.0008 if pair == "XAU/USD" else 0.0003 if "JPY" in pair else 0.0002
        new = old * (1 + (random.random() - 0.5) * factor)
        _sim_prices[pair] = new
        decimals = 3 if "JPY" in pair else 2 if pair == "XAU/USD" else 5
        change = new - base
        result[pair] = {
            "price":      round(new, decimals),
            "change":     round(change, decimals),
            "change_pct": round((change / base) * 100, 3),
            "source":     "simulation",
            "ts":         int(time.time()),
        }
    return result


async def _fetch_twelve_data() -> dict:
    import httpx
    symbols = ",".join(p.replace("/", "") for p in PAIRS)
    url = (
        f"https://api.twelvedata.com/price?symbol={symbols}"
        f"&apikey={TWELVE_KEY}"
    )
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(url)
        r.raise_for_status()
        raw = r.json()

    result = {}
    for pair in PAIRS:
        sym = pair.replace("/", "")
        if sym in raw and "price" in raw[sym]:
            price = float(raw[sym]["price"])
            base  = BASE_PRICES.get(pair, price)
            change = price - base
            decimals = 3 if "JPY" in pair else 2 if pair == "XAU/USD" else 5
            result[pair] = {
                "price":      round(price, decimals),
                "change":     round(change, decimals),
                "change_pct": round((change / base) * 100, 3),
                "source":     "TwelveData",
                "ts":         int(time.time()),
            }

    # If TwelveData returned empty or partial, fill missing with simulation
    sim = _simulate_prices()
    for pair in PAIRS:
        if pair not in result:
            result[pair] = sim[pair]

    return result


class CurrencyEngine:
    def __init__(self):
        pass

    async def get_live_prices(self) -> dict:
        if "prices" in _price_cache:
            return _price_cache["prices"]

        if TWELVE_KEY:
            try:
                prices = await _fetch_twelve_data()
            except Exception as e:
                print(f"TwelveData error: {e} — using simulation")
                prices = _simulate_prices()
        else:
            prices = _simulate_prices()

        _price_cache["prices"] = prices
        return prices

    async def get_pair_price(self, pair: str):
        prices = await self.get_live_prices()
        normalized = pair.upper().replace("-", "/")
        return prices.get(normalized)

    async def get_strength_index(self) -> dict:
        if "strength" in _strength_cache:
            return _strength_cache["strength"]
        prices = await self.get_live_prices()
        strength = self._calculate_strength(prices)
        _strength_cache["strength"] = strength
        return strength

    async def get_top_movers(self, n: int = 5) -> list:
        prices = await self.get_live_prices()
        movers = sorted(
            [{"pair": k, **v} for k, v in prices.items()],
            key=lambda x: abs(x.get("change_pct", 0)),
            reverse=True,
        )
        return movers[:n]

    def _calculate_strength(self, prices: dict) -> dict:
        scores = {c: 50.0 for c in CURRENCIES}
        pair_weights = {
            "EUR/USD": ("EUR", "USD", 1.0),
            "GBP/USD": ("GBP", "USD", 1.0),
            "USD/JPY": ("USD", "JPY", 1.0),
            "USD/CHF": ("USD", "CHF", 0.8),
            "AUD/USD": ("AUD", "USD", 0.9),
            "USD/CAD": ("USD", "CAD", 0.9),
            "NZD/USD": ("NZD", "USD", 0.8),
            "EUR/GBP": ("EUR", "GBP", 0.7),
            "EUR/JPY": ("EUR", "JPY", 0.7),
            "GBP/JPY": ("GBP", "JPY", 0.7),
        }
        for pair, (base_curr, quote_curr, weight) in pair_weights.items():
            if pair in prices:
                pct = prices[pair].get("change_pct", 0)
                if base_curr in scores:
                    scores[base_curr] += pct * weight * 2
                if quote_curr in scores:
                    scores[quote_curr] -= pct * weight * 2

        mn, mx = min(scores.values()), max(scores.values())
        spread = mx - mn if mx != mn else 1
        normalized = {
            k: round(20 + ((v - mn) / spread) * 60, 1)
            for k, v in scores.items()
        }
        return dict(sorted(normalized.items(), key=lambda x: -x[1]))
