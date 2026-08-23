# -*- coding: utf-8 -*-
"""
البوت الرئيسي: يفحص الرموز دوريًا، يولّد توصيات جديدة، يرسلها كصورة،
ويتابع الأسعار عشان يرسل بطاقة "تحقق الهدف" أو تنبيه وقف خسارة.

التشغيل:
    pip install -r requirements.txt
    export TELEGRAM_BOT_TOKEN="التوكن"
    export TELEGRAM_CHANNEL_ID="@قناتك"
    python bot.py
"""

import asyncio
import os
import time

from telegram import Bot
from telegram.constants import ParseMode

import config
from data_source import build_data_source
from strategy import evaluate
from card_generator import render_entry_card, render_target_hit_card
from signal_tracker import SignalTracker

OUTPUT_DIR = "generated_cards"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def send_entry_recommendation(bot: Bot, rec):
    path = os.path.join(OUTPUT_DIR, f"{rec.symbol}_entry_{int(time.time())}.png")
    render_entry_card(rec, path)
    with open(path, "rb") as f:
        await bot.send_photo(
            chat_id=config.TELEGRAM_CHANNEL_ID,
            photo=f,
            caption=f"🚀 توصية جديدة: {rec.symbol}",
        )


async def send_target_hit(bot: Bot, trade, target_index):
    path = os.path.join(
        OUTPUT_DIR, f"{trade.rec.symbol}_target{target_index}_{int(time.time())}.png"
    )
    render_target_hit_card(trade.rec, target_index, path)
    with open(path, "rb") as f:
        await bot.send_photo(
            chat_id=config.TELEGRAM_CHANNEL_ID,
            photo=f,
            caption=f"✅ {trade.rec.symbol} حقق الهدف {target_index}",
        )


async def send_stop_hit(bot: Bot, trade):
    await bot.send_message(
        chat_id=config.TELEGRAM_CHANNEL_ID,
        text=(
            f"🛑 تنبيه: {trade.rec.symbol} ضرب وقف الخسارة عند "
            f"${trade.rec.stop_loss}.\n\n{config.DISCLAIMER_AR}"
        ),
    )


async def main_loop():
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    data_source = build_data_source(config.WATCHLIST)
    tracker = SignalTracker()

    # نتتبع الرموز اللي عندها صفقة مفتوحة حاليًا عشان ما نكرر نفس التوصية
    active_symbols = set()

    print("البوت شغال... (Ctrl+C للإيقاف)")

    while True:
        for symbol in config.WATCHLIST:
            price = data_source.get_price(symbol)
            history = data_source.get_history(symbol)

            # 1) فحص إشارات دخول جديدة (فقط إذا ما فيه صفقة مفتوحة على نفس الرمز)
            if symbol not in active_symbols:
                rec = evaluate(symbol, history)
                if rec is not None:
                    tracker.add(rec)
                    active_symbols.add(symbol)
                    await send_entry_recommendation(bot, rec)
                    print(f"[+] توصية جديدة: {symbol} عند {rec.entry_price}")

            # 2) فحص الأهداف / وقف الخسارة لكل الصفقات المفتوحة على هذا الرمز
            events = tracker.update_price(symbol, price)
            for event_type, trade, target_index in events:
                if event_type == "target_hit":
                    await send_target_hit(bot, trade, target_index)
                    print(f"[✓] {symbol} حقق الهدف {target_index}")
                elif event_type == "stop_hit":
                    await send_stop_hit(bot, trade)
                    print(f"[×] {symbol} ضرب وقف الخسارة")

                if trade.closed:
                    active_symbols.discard(symbol)

        await asyncio.sleep(config.PRICE_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main_loop())
