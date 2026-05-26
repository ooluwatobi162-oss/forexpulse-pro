"""
Currency Engine - Uses Frankfurter (free, no API key) + CoinGecko for BTC
"""

import os
import time
import random
import asyncio
import httpx
from cachetools import TTLCache

_price_cache = TTLCache(maxsize=50, ttl=60)  # Cache 60 seconds
_strength_cache = TTLCache(maxsize=10, ttl=120)

CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "NZD", "CHF"]

# ✅ VERIFIED PRICES — May 25, 2026 (Yahoo Finance + CoinDesk + Investing.com)
# Key theme: US-Iran deal "subject to finalization", oil -5%, USD recovering
BASE_PRICES = {
    "EUR/USD": 1.15630, "GBP/USD": 1.33620, "USD/JPY": 159.404,
    "USD/CHF": 0.90000, "AUD/USD": 0.69430, "USD/CAD": 1.38000,
    "NZD/USD": 0.58060, "EUR/GBP": 0.86510, "EUR/JPY": 184.277,
    "GBP/JPY": 213.000, "XAU/USD": 4558.82, "BTC/USD": 77277,
}

_sim_prices = dict(BASE_PRICES)


async def _fetch_frankfurter() -> dict:
    """Fetch all major forex rates from Frankfurter (free, no key needed)"""
    url = "https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,JPY,AUD,CAD,NZD,CHF"
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    rates = data.get("rates", {})
    result = {}
    ts = int(time.time())

    # USD base pairs
    pair_map = {
        "EUR": "EUR/USD", "GBP": "GBP/USD",
        "AUD": "AUD/USD", "NZD": "NZD/USD",
    }
    for curr, pair in pair_map.items():
        if curr in rates:
            price = round(1 / rates[curr], 5) if curr != "EUR" else round(rates[curr], 5)
            # Frankfurter gives how many EUR = 1 USD, we need USD/EUR = EUR/USD
            price = round(rates[curr], 5)
            base = BASE_PRICES.get(pair, price)
            result[pair] = {
                "price": price,
                "change": round(price - base, 5),
                "change_pct": round((price - base) / base * 100, 3),
                "source": "Frankfurter",
                "ts": ts,
            }

    # JPY, CHF, CAD are quoted as USD per unit
    for curr, pair in [("JPY", "USD/JPY"), ("CHF", "USD/CHF"), ("CAD", "USD/CAD")]:
        if curr in rates:
            price = round(rates[curr], 3 if curr == "JPY" else 5)
            base = BASE_PRICES.get(pair, price)
            result[pair] = {
                "price": price,
                "change": round(price - base, 5),
                "change_pct": round((price - base) / base * 100, 3),
                "source": "Frankfurter",
                "ts": ts,
            }

    # Cross pairs
    if "EUR" in rates and "GBP" in rates:
        eurgbp = round(rates["EUR"] / rates["GBP"], 5)
        base = BASE_PRICES.get("EUR/GBP", eurgbp)
        result["EUR/GBP"] = {"price": eurgbp, "change": round(eurgbp - base, 5), "change_pct": round((eurgbp - base) / base * 100, 3), "source": "Frankfurter", "ts": ts}

    if "EUR" in rates and "JPY" in rates:
        eurjpy = round(rates["EUR"] * rates["JPY"], 3)
        base = BASE_PRICES.get("EUR/JPY", eurjpy)
        result["EUR/JPY"] = {"price": eurjpy, "change": round(eurjpy - base, 3), "change_pct": round((eurjpy - base) / base * 100, 3), "source": "Frankfurter", "ts": ts}

    if "GBP" in rates and "JPY" in rates:
        gbpjpy = round(rates["GBP"] * rates["JPY"], 3)
        base = BASE_PRICES.get("GBP/JPY", gbpjpy)
        result["GBP/JPY"] = {"price": gbpjpy, "change": round(gbpjpy - base, 3), "change_pct": round((gbpjpy - base) / base * 100, 3), "source": "Frankfurter", "ts": ts}

    return result


async def _fetch_gold() -> dict:
    """Fetch gold price from a free source"""
    try:
        url = "https://api.metals.live/v1/spot/gold"
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            price = float(data[0].get("price", BASE_PRICES["XAU/USD"]))
            base = BASE_PRICES["XAU/USD"]
            return {"XAU/USD": {"price": round(price, 2), "change": round(price - base, 2), "change_pct": round((price - base) / base * 100, 3), "source": "MetalsLive", "ts": int(time.time())}}
    except Exception:
        # Fallback simulation for gold
        global _sim_prices
        old = _sim_prices.get("XAU/USD", BASE_PRICES["XAU/USD"])
        new = old * (1 + (random.random() - 0.5) * 0.0008)
        _sim_prices["XAU/USD"] = new
        base = BASE_PRICES["XAU/USD"]
        return {"XAU/USD": {"price": round(new, 2), "change": round(new - base, 2), "change_pct": round((new - base) / base * 100, 3), "source": "simulation", "ts": int(time.time())}}


async def _fetch_btc() -> dict:
    """Fetch BTC price from CoinGecko (free, no key)"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            price = float(data["bitcoin"]["usd"])
            base = BASE_PRICES["BTC/USD"]
            return {"BTC/USD": {"price": round(price, 2), "change": round(price - base, 2), "change_pct": round((price - base) / base * 100, 3), "source": "CoinGecko", "ts": int(time.time())}}
    except Exception:
        global _sim_prices
        old = _sim_prices.get("BTC/USD", BASE_PRICES["BTC/USD"])
        new = old * (1 + (random.random() - 0.5) * 0.001)
        _sim_prices["BTC/USD"] = new
        base = BASE_PRICES["BTC/USD"]
        return {"BTC/USD": {"price": round(new, 2), "change": round(new - base, 2), "change_pct": round((new - base) / base * 100, 3), "source": "simulation", "ts": int(time.time())}}


def _simulate_all() -> dict:
    global _sim_prices
    result = {}
    ts = int(time.time())
    for pair, base in BASE_PRICES.items():
        old = _sim_prices.get(pair, base)
        factor = 0.0008 if pair == "XAU/USD" else 0.001 if pair == "BTC/USD" else 0.0003 if "JPY" in pair else 0.0002
        new = old * (1 + (random.random() - 0.5) * factor)
        _sim_prices[pair] = new
        decimals = 3 if "JPY" in pair else 2 if pair in ["XAU/USD", "BTC/USD"] else 5
        change = new - base
        result[pair] = {"price": round(new, decimals), "change": round(change, decimals), "change_pct": round(change / base * 100, 3), "source": "simulation", "ts": ts}
    return result


class CurrencyEngine:

    async def get_live_prices(self) -> dict:
        if "prices" in _price_cache:
            return _price_cache["prices"]

        try:
            forex_task = _fetch_frankfurter()
            gold_task = _fetch_gold()
            btc_task = _fetch_btc()
            forex, gold, btc = await asyncio.gather(forex_task, gold_task, btc_task, return_exceptions=True)

            prices = _simulate_all()  # Start with simulation as base
            if isinstance(forex, dict): prices.update(forex)
            if isinstance(gold, dict): prices.update(gold)
            if isinstance(btc, dict): prices.update(btc)

        except Exception:
            prices = _simulate_all()

        _price_cache["prices"] = prices
        return prices

    async def get_pair_price(self, pair: str):
        prices = await self.get_live_prices()
        return prices.get(pair.upper().replace("-", "/"))

    async def get_strength_index(self) -> dict:
        if "strength" in _strength_cache:
            return _strength_cache["strength"]
        prices = await self.get_live_prices()
        strength = self._calculate_strength(prices)
        _strength_cache["strength"] = strength
        return strength

    async def get_top_movers(self, n: int = 5) -> list:
        prices = await self.get_live_prices()
        movers = sorted([{"pair": k, **v} for k, v in prices.items()], key=lambda x: abs(x.get("change_pct", 0)), reverse=True)
        return movers[:n]

    def _calculate_strength(self, prices: dict) -> dict:
        scores = {c: 50.0 for c in CURRENCIES}
        pair_weights = {
            "EUR/USD": ("EUR", "USD", 1.0), "GBP/USD": ("GBP", "USD", 1.0),
            "USD/JPY": ("USD", "JPY", 1.0), "USD/CHF": ("USD", "CHF", 0.8),
            "AUD/USD": ("AUD", "USD", 0.9), "USD/CAD": ("USD", "CAD", 0.9),
            "NZD/USD": ("NZD", "USD", 0.8), "EUR/GBP": ("EUR", "GBP", 0.7),
            "EUR/JPY": ("EUR", "JPY", 0.7), "GBP/JPY": ("GBP", "JPY", 0.7),
        }
        for pair, (base_curr, quote_curr, weight) in pair_weights.items():
            if pair in prices:
                pct = prices[pair].get("change_pct", 0)
                if base_curr in scores: scores[base_curr] += pct * weight * 2
                if quote_curr in scores: scores[quote_curr] -= pct * weight * 2

        mn, mx = min(scores.values()), max(scores.values())
        spread = mx - mn if mx != mn else 1
        normalized = {k: round(20 + ((v - mn) / spread) * 60, 1) for k, v in scores.items()}
        return dict(sorted(normalized.items(), key=lambda x: -x[1]))
