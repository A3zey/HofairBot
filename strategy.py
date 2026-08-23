# -*- coding: utf-8 -*-
"""
استراتيجية توليد التوصيات.

هذا مثال بسيط وتعليمي (تقاطع متوسطين متحركين + RSI). مو استراتيجية
"مضمونة الربح" - أي استراتيجية آلية بسيطة زي هذي معرضة لإشارات خاطئة
خصوصًا بالأسواق العرضية (sideways). عدّلها أو استبدلها باستراتيجيتك
الخاصة إذا عندك منهجية تداول مختلفة.
"""

from dataclasses import dataclass
from typing import List, Optional

from config import STRATEGY_SETTINGS
from data_source import Candle


@dataclass
class Recommendation:
    symbol: str
    entry_price: float
    stop_loss: float
    targets: List[float]
    momentum_score: int  # 0-100، مقياس تعليمي وليس احتمال إحصائي حقيقي
    reason: str


def _sma(values: List[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _rsi(values: List[float], period: int) -> Optional[float]:
    if len(values) < period + 1:
        return None
    gains, losses = [], []
    for i in range(-period, 0):
        diff = values[i] - values[i - 1]
        if diff >= 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def evaluate(symbol: str, history: List[Candle]) -> Optional[Recommendation]:
    """
    يرجّع توصية إذا توفرت شروط الاستراتيجية، أو None إذا ما فيه إشارة واضحة.
    مهم: رجوع None هو سلوك صحيح ومطلوب - لا تصطنع توصية وهمية لمجرد إنه
    "لازم يطلع شي"، لأن هذا بالضبط اللي يخلي بوتات كثيرة غير موثوقة.
    """
    closes = [c.close for c in history]
    s = STRATEGY_SETTINGS

    fast = _sma(closes, s["fast_ma_period"])
    slow = _sma(closes, s["slow_ma_period"])
    rsi = _rsi(closes, s["rsi_period"])

    if fast is None or slow is None or rsi is None:
        return None

    price = closes[-1]
    bullish_cross = fast > slow
    not_overbought = rsi < s["rsi_overbought"]

    if not (bullish_cross and not_overbought):
        return None  # لا توجد إشارة واضحة حسب الشروط المحددة

    stop_loss = round(price * (1 - s["stop_loss_pct"]), 2)
    targets = [round(price * (1 + pct), 2) for pct in s["target_pcts"]]

    # مقياس زخم تعليمي بسيط بناءً على قوة الفرق بين المتوسطين وموقع RSI
    spread_score = min(50, abs(fast - slow) / price * 1000)
    rsi_score = max(0, min(50, rsi - s["rsi_oversold"]))
    momentum_score = int(min(100, spread_score + rsi_score))

    reason = (
        f"تقاطع صاعد: المتوسط {s['fast_ma_period']} أعلى من {s['slow_ma_period']}، "
        f"RSI عند {rsi:.1f} (غير متشبع شرائيًا)."
    )

    return Recommendation(
        symbol=symbol,
        entry_price=price,
        stop_loss=stop_loss,
        targets=targets,
        momentum_score=momentum_score,
        reason=reason,
    )


def evaluate_bearish(symbol: str, history: List[Candle]) -> Optional[Recommendation]:
    """
    نفس فكرة evaluate() بس بالاتجاه المعاكس (يكتشف فرص هبوط للاستخدام
    مع عقود Put). نفس القاعدة تنطبق: None هو رد صحيح لو ما فيه إشارة.
    """
    closes = [c.close for c in history]
    s = STRATEGY_SETTINGS

    fast = _sma(closes, s["fast_ma_period"])
    slow = _sma(closes, s["slow_ma_period"])
    rsi = _rsi(closes, s["rsi_period"])

    if fast is None or slow is None or rsi is None:
        return None

    price = closes[-1]
    bearish_cross = fast < slow
    not_oversold = rsi > s["rsi_oversold"]

    if not (bearish_cross and not_oversold):
        return None

    stop_loss = round(price * (1 + s["stop_loss_pct"]), 2)  # وقف الخسارة فوق السعر للهبوط
    targets = [round(price * (1 - pct), 2) for pct in s["target_pcts"]]

    spread_score = min(50, abs(fast - slow) / price * 1000)
    rsi_score = max(0, min(50, s["rsi_overbought"] - rsi))
    momentum_score = int(min(100, spread_score + rsi_score))

    reason = (
        f"تقاطع هابط: المتوسط {s['fast_ma_period']} أدنى من {s['slow_ma_period']}، "
        f"RSI عند {rsi:.1f} (غير متشبع بيعيًا)."
    )

    return Recommendation(
        symbol=symbol,
        entry_price=price,
        stop_loss=stop_loss,
        targets=targets,
        momentum_score=momentum_score,
        reason=reason,
    )
