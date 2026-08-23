# -*- coding: utf-8 -*-
"""
البوت الرئيسي: يفحص الأسهم بحثًا عن إشارة صعود (Call) أو هبوط (Put)،
ولما يلقى إشارة يختار عقد أسبوعي سعره (premium) بين
OPTIONS_ENTRY_PREMIUM_MIN و OPTIONS_ENTRY_PREMIUM_MAX، يرسله كتوصية،
ويتابع سعر العقد نفسه لإرسال تحديثات الأهداف / وقف الخسارة.

التشغيل:
    pip install -r requirements.txt
    export TELEGRAM_BOT_TOKEN="التوكن"
    export TELEGRAM_CHANNEL_ID="@قناتك"
    export TWELVE_DATA_API_KEY="مفتاح Twelve Data"
    python bot.py
"""

import asyncio
import os
import time

from telegram import Bot

import config
from data_source import build_data_source
from strategy import evaluate, evaluate_bearish
from options_strategy import pick_option_contract
from options_source import get_contract_premium
from card_generator import render_option_entry_card, render_option_target_hit_card
from signal_tracker import OptionTracker
from market_hours import is_market_open, market_status_text

OUTPUT_DIR = "generated_cards"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def send_option_entry(bot: Bot, rec):
    path = os.path.join(
        OUTPUT_DIR, f"{rec.symbol}_{rec.option_type}_entry_{int(time.time())}.png"
    )
    render_option_entry_card(rec, path)
    with open(path, "rb") as f:
        await bot.send_photo(
            chat_id=config.TELEGRAM_CHANNEL_ID,
            photo=f,
            caption=f"🚀 توصية {rec.option_type} جديدة: {rec.symbol} ${rec.strike}",
        )


async def send_option_target_hit(bot: Bot, trade, target_index):
    path = os.path.join(
        OUTPUT_DIR,
        f"{trade.rec.symbol}_{trade.rec.option_type}_target{target_index}_{int(time.time())}.png",
    )
    render_option_target_hit_card(trade.rec, target_index, path)
    with open(path, "rb") as f:
        await bot.send_photo(
            chat_id=config.TELEGRAM_CHANNEL_ID,
            photo=f,
            caption=(
                f"✅ {trade.rec.symbol} {trade.rec.option_type} ${trade.rec.strike} "
                f"حقق الهدف {target_index}"
            ),
        )


async def send_option_stop_hit(bot: Bot, trade):
    await bot.send_message(
        chat_id=config.TELEGRAM_CHANNEL_ID,
        text=(
            f"🛑 تنبيه: {trade.rec.symbol} {trade.rec.option_type} ${trade.rec.strike} "
            f"({trade.rec.expiration}) ضرب وقف الخسارة عند ${trade.rec.stop_loss_premium}.\n\n"
            f"{config.DISCLAIMER_AR}"
        ),
    )


async def check_and_open_position(bot: Bot, tracker, symbol, stock_price, history):
    """يفحص إشارتي الصعود والهبوط، ويفتح صفقة أوبشن مناسبة لو لقى إشارة."""

    for direction, signal_fn in (("bullish", evaluate), ("bearish", evaluate_bearish)):
        stock_signal = signal_fn(symbol, history)
        if stock_signal is None:
            continue

        try:
            option_rec = pick_option_contract(
                symbol=symbol,
                direction=direction,
                current_stock_price=stock_price,
                momentum_score=stock_signal.momentum_score,
                reason=stock_signal.reason,
            )
        except Exception as e:
            print(f"[!] تعذر جلب بيانات أوبشن {symbol} ({direction}): {e}")
            continue

        if option_rec is not None:
            tracker.add(option_rec)
            await send_option_entry(bot, option_rec)
            print(
                f"[+] توصية {option_rec.option_type}: {symbol} ${option_rec.strike} "
                f"عند ${option_rec.entry_premium}"
            )
        else:
            print(
                f"[i] {symbol}: فيه إشارة {direction} بس ما فيه عقد "
                f"بنطاق السعر ${config.OPTIONS_ENTRY_PREMIUM_MIN}-"
                f"${config.OPTIONS_ENTRY_PREMIUM_MAX} حاليًا"
            )
        return  # لا نفتح أكثر من صفقة على نفس الرمز بنفس اللحظة


async def main_loop():
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    data_source = build_data_source(config.WATCHLIST)
    tracker = OptionTracker()

    print("البوت شغال (وضع الأوبشن - Call وPut)... (Ctrl+C للإيقاف)")
    market_was_open = None

    while True:
        market_open_now = is_market_open()

        if market_open_now != market_was_open:
            print(market_status_text())
            market_was_open = market_open_now

        if not market_open_now:
            await asyncio.sleep(config.MARKET_CLOSED_CHECK_INTERVAL_SECONDS)
            continue

        for symbol in config.WATCHLIST:
            stock_price = data_source.get_price(symbol)
            history = data_source.get_history(symbol)

            # 1) إذا ما فيه صفقة أوبشن مفتوحة على هذا الرمز، نفحص إشارات جديدة
            if not tracker.has_open(symbol):
                await check_and_open_position(bot, tracker, symbol, stock_price, history)

            # 2) تحديث سعر العقود المفتوحة على هذا الرمز
            for trade in list(tracker.open_trades):
                if trade.closed or trade.rec.symbol != symbol:
                    continue
                try:
                    premium = get_contract_premium(trade.rec.contract_symbol)
                except Exception as e:
                    print(f"[!] تعذر تحديث سعر عقد {trade.rec.contract_symbol}: {e}")
                    continue

                events = tracker.update_premium(trade, premium)
                for event_type, t, idx in events:
                    if event_type == "target_hit":
                        await send_option_target_hit(bot, t, idx)
                        print(f"[✓] {symbol} حقق الهدف {idx}")
                    elif event_type == "stop_hit":
                        await send_option_stop_hit(bot, t)
                        print(f"[×] {symbol} ضرب وقف الخسارة")

        await asyncio.sleep(config.PRICE_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main_loop())
