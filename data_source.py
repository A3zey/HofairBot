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

from config import DATA_SOURCE_MODE

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
    هيكل جاهز للربط بـ API حقيقي. عبّي التنفيذ حسب مزوّد البيانات اللي تختاره.
    """

    def __init__(self, symbols):
        self.symbols = symbols
        # TODO: هيّئ اتصال API هنا (session, api_key, إلخ)
        raise NotImplementedError(
            "لازم تربط RealDataSource بمزوّد بيانات حقيقي قبل استخدام الوضع real. "
            "شوف الأمثلة في تعليقات أعلى الملف."
        )

    def get_price(self, symbol: str) -> float:
        raise NotImplementedError

    def get_history(self, symbol: str) -> List[Candle]:
        raise NotImplementedError


def build_data_source(symbols):
    if DATA_SOURCE_MODE == "mock":
        return MockDataSource(symbols)
    elif DATA_SOURCE_MODE == "real":
        return RealDataSource(symbols)
    else:
        raise ValueError(f"وضع بيانات غير معروف: {DATA_SOURCE_MODE}")
