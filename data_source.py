# -*- coding: utf-8 -*-
"""
مصدر بيانات الأسعار.

الوضع الحالي: mock (بيانات وهمية) للتجربة والتطوير بدون الحاجة لاشتراك API.
لما تكون جاهز تربطه ببيانات حقيقية، فعّل الوضع "real" وعبّي المفتاح تحت.

مصادر مقترحة لبيانات حقيقية (تحتاج تسجيل حساب مجاني عندهم بنفسك):
  - Alpha Vantage      (https://www.alphavantage.co)
  - Twelve Data        (https://twelvedata.com)
  - Finnhub            (https://finnhub.io)
  - يوروبيان: يمكن أيضًا yfinance (مجاني بدون مفتاح، لكن غير رسمي وقد ينقطع)
"""

import random
import time
from dataclasses import dataclass, field
from typing import List

import requests

from config import DATA_SOURCE_MODE, TWELVE_DATA_API_KEY

TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"

# ============ نموذج بيانات موحّد ============

@dataclass
class Candle:
    timestamp: float
    close: float


@dataclass
class SymbolState:
    symbol: str
    last_price: float
    history: List[Candle] = field(default_factory=list)


# ============ محرّك البيانات الوهمية ============

class MockDataSource:
    """
    يولّد أسعار عشوائية منطقية (مشية عشوائية بسيطة) عشان تقدر تختبر
    شكل التوصيات وصور البطاقات وتتبع الأهداف بدون ما تحتاج API حقيقي.
    """

    def __init__(self, symbols):
        self._states = {}
        for sym in symbols:
            start_price = round(random.uniform(50, 400), 2)
            state = SymbolState(symbol=sym, last_price=start_price)
            # نولّد تاريخ أولي كافي لحساب المتوسطات المتحركة و RSI
            price = start_price
            now = time.time()
            for i in range(60):
                price = max(1.0, price * (1 + random.uniform(-0.01, 0.01)))
                state.history.append(Candle(timestamp=now - (60 - i) * 60, close=round(price, 2)))
            state.last_price = state.history[-1].close
            self._states[sym] = state

    def get_price(self, symbol: str) -> float:
        state = self._states[symbol]
        # حركة سعرية عشوائية بسيطة (مشية عشوائية bounded)
        change_pct = random.uniform(-0.015, 0.015)
        new_price = max(0.5, state.last_price * (1 + change_pct))
        new_price = round(new_price, 2)
        state.last_price = new_price
        state.history.append(Candle(timestamp=time.time(), close=new_price))
        # نحتفظ بآخر 200 شمعة بس
        state.history = state.history[-200:]
        return new_price

    def get_history(self, symbol: str) -> List[Candle]:
        return self._states[symbol].history


class RealDataSource:
    """
    يجيب بيانات أسعار حقيقية من Twelve Data (twelvedata.com).
    يحتاج مفتاح API مجاني تسجّله بحسابك على موقعهم، وتحطه بمتغير بيئة
    اسمه TWELVE_DATA_API_KEY.
    """

    def __init__(self, symbols):
        if not TWELVE_DATA_API_KEY:
            raise ValueError(
                "مفتاح TWELVE_DATA_API_KEY غير موجود. سجّل حساب مجاني على "
                "twelvedata.com واحصل على مفتاح، وحطه بمتغيرات البيئة."
            )
        self.symbols = symbols
        self._history_cache = {sym: self._fetch_history(sym) for sym in symbols}

    def _fetch_history(self, symbol: str, outputsize: int = 60) -> List[Candle]:
        resp = requests.get(
            f"{TWELVE_DATA_BASE_URL}/time_series",
            params={
                "symbol": symbol,
                "interval": "1min",
                "outputsize": outputsize,
                "apikey": TWELVE_DATA_API_KEY,
            },
            timeout=15,
        )
        data = resp.json()
        if "values" not in data:
            raise RuntimeError(
                f"خطأ من مزوّد البيانات لرمز {symbol}: {data.get('message', data)}"
            )
        # يرجع الأحدث أولًا، نعكسه عشان يصير الأقدم أولًا (ترتيب زمني صحيح)
        raw_values = list(reversed(data["values"]))
        candles = []
        for v in raw_values:
            candles.append(Candle(timestamp=time.time(), close=float(v["close"])))
        return candles

    def get_price(self, symbol: str) -> float:
        resp = requests.get(
            f"{TWELVE_DATA_BASE_URL}/price",
            params={"symbol": symbol, "apikey": TWELVE_DATA_API_KEY},
            timeout=15,
        )
        data = resp.json()
        if "price" not in data:
            raise RuntimeError(
                f"خطأ من مزوّد البيانات لرمز {symbol}: {data.get('message', data)}"
            )
        price = float(data["price"])

        hist = self._history_cache.setdefault(symbol, [])
        hist.append(Candle(timestamp=time.time(), close=price))
        self._history_cache[symbol] = hist[-200:]
        return price

    def get_history(self, symbol: str) -> List[Candle]:
        return self._history_cache.get(symbol, [])


def build_data_source(symbols):
    if DATA_SOURCE_MODE == "mock":
        return MockDataSource(symbols)
    elif DATA_SOURCE_MODE == "real":
        return RealDataSource(symbols)
    else:
        raise ValueError(f"وضع بيانات غير معروف: {DATA_SOURCE_MODE}")
