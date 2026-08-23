# -*- coding: utf-8 -*-
"""
يتابع التوصيات المفتوحة، ويكتشف:
  - متى يتحقق هدف (يرجّع حدث target_hit)
  - متى يُضرب وقف الخسارة (يرجّع حدث stop_hit)
تصميم بسيط في الذاكرة - لو تبي استمرارية بعد إعادة تشغيل البوت،
حط هذي البيانات في قاعدة بيانات (SQLite مثلًا) بدل القائمة بالذاكرة.
"""

from dataclasses import dataclass, field
from typing import List

from strategy import Recommendation


@dataclass
class OpenTrade:
    rec: Recommendation
    hit_targets: List[int] = field(default_factory=list)  # فهارس الأهداف المتحققة (1-based)
    stopped_out: bool = False
    closed: bool = False


class SignalTracker:
    def __init__(self):
        self.open_trades: List[OpenTrade] = []

    def add(self, rec: Recommendation):
        self.open_trades.append(OpenTrade(rec=rec))

    def update_price(self, symbol: str, price: float):
        """
        يفحص كل الصفقات المفتوحة لهذا الرمز مقابل السعر الجديد.
        يرجّع قائمة أحداث: [("target_hit", trade, target_index), ("stop_hit", trade, None), ...]
        """
        events = []
        for trade in self.open_trades:
            if trade.closed or trade.rec.symbol != symbol:
                continue

            # وقف الخسارة له أولوية إذا انضرب
            if not trade.stopped_out and price <= trade.rec.stop_loss:
                trade.stopped_out = True
                trade.closed = True
                events.append(("stop_hit", trade, None))
                continue

            for i, target in enumerate(trade.rec.targets, start=1):
                if i not in trade.hit_targets and price >= target:
                    trade.hit_targets.append(i)
                    events.append(("target_hit", trade, i))
                    if i == len(trade.rec.targets):
                        trade.closed = True  # آخر هدف يقفل الصفقة

        return events
