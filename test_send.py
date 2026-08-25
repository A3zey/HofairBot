# -*- coding: utf-8 -*-
"""
سكريبت اختبار: يرسل توصية أوبشن وهمية فورًا لقناتك على تلقرام،
عشان تتأكد من شكل البطاقة (التصميم، الخط العربي، التنويهات) بدون
انتظار إشارة حقيقية من السوق.

التشغيل (من نفس بيئة البوت، محليًا أو عبر Railway):
    python test_send.py
"""

import asyncio
import os
import time

from telegram import Bot

import config
from options_strategy import OptionRecommendation
from card_generator import render_option_entry_card

OUTPUT_DIR = "generated_cards"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def send_test():
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

    # توصية وهمية بس عشان الاختبار - مو من السوق الفعلي
    rec = OptionRecommendation(
        symbol="TSLA",
        option_type="CALL",
        strike=250.0,
        expiration="2026-09-04",
        contract_symbol="TSLA260904C00250000",
        entry_premium=1.30,
        stop_loss_premium=round(1.30 * (1 - config.OPTIONS_STOP_LOSS_PCT), 2),
        targets=[round(1.30 * (1 + p), 2) for p in config.OPTIONS_TARGET_PCTS],
        momentum_score=62,
        reason="هذي توصية تجريبية للاختبار فقط - مو إشارة حقيقية من السوق.",
    )

    path = os.path.join(OUTPUT_DIR, f"test_{int(time.time())}.png")
    render_option_entry_card(rec, path)

    with open(path, "rb") as f:
        await bot.send_photo(
            chat_id=config.TELEGRAM_CHANNEL_ID,
            photo=f,
            caption="🧪 هذي رسالة اختبار فقط - للتأكد من شكل البطاقة",
        )

    print("تم إرسال رسالة الاختبار بنجاح!")


if __name__ == "__main__":
    asyncio.run(send_test())
