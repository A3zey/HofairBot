# -*- coding: utf-8 -*-
"""
يختار عقد Call أو Put مناسب بناءً على:
  1) إشارة اتجاه (صعود -> Call، هبوط -> Put) من strategy.py
  2) سعر دخول (premium) بين OPTIONS_ENTRY_PREMIUM_MIN و OPTIONS_ENTRY_PREMIUM_MAX
  3) من بين العقود اللي تحقق الشرط، يختار الأقرب لسعر السهم الحالي (الأكثر سيولة عادة)

مهم: لو ما فيه أي عقد يحقق نطاق السعر المطلوب، يرجّع None ولا يخترع
عقد غير مناسب فقط عشان "يطلع شي".
"""

from dataclasses import dataclass
from typing import List, Optional

import config
from options_source import get_nearest_expiration, get_option_chain


@dataclass
class OptionRecommendation:
    symbol: str
    option_type: str        # "CALL" أو "PUT"
    strike: float
    expiration: str
    contract_symbol: str
    entry_premium: float
    stop_loss_premium: float
    targets: List[float]
    momentum_score: int
    reason: str


def pick_option_contract(
    symbol: str,
    direction: str,               # "bullish" -> Call, "bearish" -> Put
    current_stock_price: float,
    momentum_score: int,
    reason: str,
) -> Optional[OptionRecommendation]:
    right = "call" if direction == "bullish" else "put"
    option_type = "CALL" if direction == "bullish" else "PUT"

    expiration = get_nearest_expiration(symbol)
    chain = get_option_chain(symbol, expiration, right)

    candidates = [
        c
        for c in chain
        if config.OPTIONS_ENTRY_PREMIUM_MIN <= c.premium <= config.OPTIONS_ENTRY_PREMIUM_MAX
    ]

    if not candidates:
        return None  # ما فيه عقد ضمن النطاق المطلوب حاليًا - سلوك متوقع وصحيح

    # من بين المرشحين، نفضّل الأقرب لسعر السهم الحالي (أعلى سيولة غالبًا)
    best = min(candidates, key=lambda c: abs(c.strike - current_stock_price))

    stop_loss_premium = round(best.premium * (1 - config.OPTIONS_STOP_LOSS_PCT), 2)
    targets = [round(best.premium * (1 + p), 2) for p in config.OPTIONS_TARGET_PCTS]

    return OptionRecommendation(
        symbol=symbol,
        option_type=option_type,
        strike=best.strike,
        expiration=expiration,
        contract_symbol=best.contract_symbol,
        entry_premium=best.premium,
        stop_loss_premium=stop_loss_premium,
        targets=targets,
        momentum_score=momentum_score,
        reason=reason,
    )
