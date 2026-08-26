# -*- coding: utf-8 -*-
"""
مصدر بيانات الأوبشن (خيارات) عبر Yahoo Finance (مكتبة yfinance).

⚠️ ملاحظة مهمة: هذا مصدر مجاني لكنه غير رسمي (Yahoo ما يوفر API رسمي
مدعوم للأوبشن). ممكن يتعطل أو يتغير شكل البيانات بدون تنبيه مسبق. مناسب
للتجربة والتعلم، لكن لو اعتمدت عليه بشكل جدي لقناة فيها متابعين كثار،
يفضّل الانتقال لمصدر مدفوع وموثوق أكثر (مثل Tradier أو Polygon.io).
"""

import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

import yfinance as yf

import config


def _safe_float(value, default: float = 0.0) -> float:
    """يحوّل القيمة لرقم عشري بأمان، ويرجّع default لو كانت NaN أو غير صالحة."""
    try:
        v = float(value)
        if math.isnan(v):
            return default
        return v
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    return int(_safe_float(value, default))


@dataclass
class OptionContract:
    strike: float
    premium: float          # منتصف bid/ask إذا متوفر، وإلا آخر سعر تداول
    contract_symbol: str    # الرمز الرسمي للعقد (OCC symbol)
    volume: int


def get_nearest_expiration(symbol: str) -> str:
    """
    يرجّع أقرب تاريخ انتهاء متاح فعليًا لهذا السهم (صيغة YYYY-MM-DD)،
    بشرط إنه يبعد عن اليوم بمقدار OPTIONS_MIN_DAYS_TO_EXPIRATION على الأقل
    (عشان نتجنب عقود "نفس اليوم" 0DTE الخطرة جدًا إذا كان الإعداد أكبر من صفر).
    """
    ticker = yf.Ticker(symbol)
    expirations = ticker.options
    if not expirations:
        raise RuntimeError(f"لا توجد عقود أوبشن متاحة حاليًا لـ {symbol}")

    today = date.today()
    min_days = config.OPTIONS_MIN_DAYS_TO_EXPIRATION

    for exp_str in expirations:
        exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        days_away = (exp_date - today).days
        if days_away >= min_days:
            return exp_str

    raise RuntimeError(
        f"ما فيه عقود أوبشن لـ {symbol} تبعد {min_days} يوم أو أكثر عن اليوم حاليًا"
    )


def get_option_chain(symbol: str, expiration: str, right: str) -> List[OptionContract]:
    """
    يرجّع كل عقود Call أو Put المتاحة لهذا التاريخ مع أسعارها.
    right: "call" أو "put"
    """
    ticker = yf.Ticker(symbol)
    chain = ticker.option_chain(expiration)
    df = chain.calls if right == "call" else chain.puts

    contracts = []
    for _, row in df.iterrows():
        bid = _safe_float(row.get("bid", 0))
        ask = _safe_float(row.get("ask", 0))
        last = _safe_float(row.get("lastPrice", 0))

        if bid > 0 and ask > 0:
            premium = round((bid + ask) / 2, 2)
        else:
            premium = round(last, 2)

        if premium <= 0:
            continue  # نتجاهل عقود بدون سعر موثوق

        contracts.append(
            OptionContract(
                strike=_safe_float(row.get("strike")),
                premium=premium,
                contract_symbol=str(row.get("contractSymbol", "")),
                volume=_safe_int(row.get("volume", 0)),
            )
        )
    return contracts


def get_call_chain(symbol: str, expiration: str) -> List[OptionContract]:
    """للتوافق مع الكود القديم - نفس get_option_chain(..., right='call')."""
    return get_option_chain(symbol, expiration, "call")


def get_contract_premium(contract_symbol: str) -> float:
    """يجيب آخر سعر متداول لعقد أوبشن محدد بالرمز الرسمي (OCC symbol)."""
    ticker = yf.Ticker(contract_symbol)
    hist = ticker.history(period="1d")
    if hist.empty:
        raise RuntimeError(f"تعذر جلب سعر العقد {contract_symbol} حاليًا")
    return round(float(hist["Close"].iloc[-1]), 2)
