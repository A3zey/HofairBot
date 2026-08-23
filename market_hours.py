# -*- coding: utf-8 -*-
"""
يتحقق إذا كان سوق الأسهم الأمريكي مفتوح حاليًا حسب توقيت نيويورك،
ويوقف البوت تلقائيًا خارج ساعات التداول وبعطلة نهاية الأسبوع.

ملاحظة: هذا لا يأخذ بعين الاعتبار العطلات الرسمية الأمريكية (زي عيد
الشكر أو رأس السنة) لأنها تحتاج تقويم خاص يتغير كل سنة. إذا تبي دقة
أكبر لاحقًا، نقدر نضيف قائمة بالعطلات الرسمية.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from config import (
    MARKET_TIMEZONE,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MINUTE,
)


def is_market_open(now: datetime = None) -> bool:
    tz = ZoneInfo(MARKET_TIMEZONE)
    now = now.astimezone(tz) if now else datetime.now(tz)

    # الاثنين = 0 ... الأحد = 6. السبت والأحد = عطلة
    if now.weekday() >= 5:
        return False

    open_time = now.replace(
        hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0
    )
    close_time = now.replace(
        hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0
    )
    return open_time <= now <= close_time


def market_status_text() -> str:
    """نص عربي مختصر لحالة السوق الحالية، يفيد بالسجلات (logs)."""
    tz = ZoneInfo(MARKET_TIMEZONE)
    now = datetime.now(tz)
    if is_market_open(now):
        return f"السوق مفتوح الآن ({now.strftime('%H:%M')} بتوقيت نيويورك)"
    return f"السوق مغلق حاليًا ({now.strftime('%A %H:%M')} بتوقيت نيويورك)"
