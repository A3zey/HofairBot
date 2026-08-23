# -*- coding: utf-8 -*-
"""
مولّد بطاقات الصور للتوصيات (بطاقة دخول جديدة + بطاقة تحقيق هدف).

يحتاج:
    pip install pillow arabic-reshaper python-bidi

ويحتاج خط عربي حقيقي (يدعم النسخ العربي) موضوع في:
    fonts/NotoNaskhArabic-Regular.ttf
    fonts/NotoNaskhArabic-Bold.ttf
تقدر تنزلهم مجانًا من Google Fonts (Noto Naskh Arabic).
"""

from PIL import Image, ImageDraw, ImageFont

from config import FONT_REGULAR_PATH, FONT_BOLD_PATH, BRAND_NAME, DISCLAIMER_AR

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _AR_SUPPORT = True
except ImportError:
    _AR_SUPPORT = False


def ar(text: str) -> str:
    """يهيّئ نص عربي للعرض الصحيح داخل صورة (تشكيل الحروف + اتجاه RTL)."""
    if not _AR_SUPPORT:
        # بدون المكتبات، النص بيرسم لكن الحروف بتكون منفصلة وغير متصلة بصريًا
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        # خط احتياطي إذا الخط العربي غير موجود بعد (النص العربي وقتها ما يرسم صح)
        return ImageFont.load_default()


WIDTH = 1080
BG_TOP = (18, 10, 30)
BG_BOTTOM = (35, 15, 55)
ACCENT_GREEN = (60, 200, 120)
ACCENT_RED = (220, 70, 70)
ACCENT_ORANGE = (230, 130, 60)
ACCENT_GOLD = (230, 180, 70)
TEXT_WHITE = (245, 245, 245)
TEXT_MUTED = (170, 165, 180)


def _gradient_bg(width, height):
    img = Image.new("RGB", (width, height), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / height
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img, draw


def _draw_rtl_text(draw, xy, text, font, fill, anchor="ra"):
    """رسم نص RTL: xy هي نقطة اليمين، والنص يمتد لليسار."""
    draw.text(xy, ar(text), font=font, fill=fill, anchor=anchor)


def render_entry_card(rec, out_path: str):
    """
    بطاقة توصية دخول جديدة.
    rec: كائن Recommendation من strategy.py
    """
    height = 1350
    img, draw = _gradient_bg(WIDTH, height)

    title_font = _font(FONT_BOLD_PATH, 54)
    symbol_font = _font(FONT_BOLD_PATH, 80)
    label_font = _font(FONT_REGULAR_PATH, 36)
    value_font = _font(FONT_BOLD_PATH, 46)
    small_font = _font(FONT_REGULAR_PATH, 28)
    brand_font = _font(FONT_BOLD_PATH, 34)

    margin = 60

    # ترويسة العلامة
    _draw_rtl_text(draw, (WIDTH - margin, 40), BRAND_NAME, brand_font, ACCENT_GOLD)

    # عنوان
    _draw_rtl_text(draw, (WIDTH - margin, 110), "توصية جديدة", title_font, TEXT_WHITE)

    # رمز السهم
    draw.text((WIDTH // 2, 220), rec.symbol, font=symbol_font, fill=ACCENT_GOLD, anchor="ma")

    y = 340
    row_h = 100

    def row(label, value, value_color=TEXT_WHITE):
        nonlocal y
        _draw_rtl_text(draw, (WIDTH - margin, y), label, label_font, TEXT_MUTED)
        draw.text((margin, y), str(value), font=value_font, fill=value_color, anchor="la")
        y += row_h

    row("سعر الدخول", f"${rec.entry_price}", TEXT_WHITE)
    row("وقف الخسارة", f"${rec.stop_loss}", ACCENT_RED)

    for i, t in enumerate(rec.targets, start=1):
        row(f"الهدف {i}", f"${t}", ACCENT_GREEN)

    row("قوة الزخم", f"{rec.momentum_score}/100", ACCENT_GOLD)

    # سبب التوصية
    y += 20
    _draw_rtl_text(draw, (WIDTH - margin, y), "السبب:", label_font, TEXT_MUTED)
    y += 50
    _draw_rtl_text(draw, (WIDTH - margin, y), rec.reason, small_font, TEXT_WHITE)

    # التنويه في الأسفل
    disclaimer_y = height - 220
    draw.line([(margin, disclaimer_y - 20), (WIDTH - margin, disclaimer_y - 20)],
              fill=(80, 75, 95), width=2)
    _wrap_rtl_paragraph(draw, DISCLAIMER_AR, small_font, TEXT_MUTED,
                         right=WIDTH - margin, top=disclaimer_y, max_width=WIDTH - 2 * margin)

    img.save(out_path)
    return out_path


def render_target_hit_card(rec, target_index: int, out_path: str):
    """بطاقة إشعار بتحقق هدف من أهداف توصية سابقة."""
    height = 900
    img, draw = _gradient_bg(WIDTH, height)

    brand_font = _font(FONT_BOLD_PATH, 34)
    title_font = _font(FONT_BOLD_PATH, 60)
    symbol_font = _font(FONT_BOLD_PATH, 70)
    label_font = _font(FONT_REGULAR_PATH, 36)
    value_font = _font(FONT_BOLD_PATH, 50)

    margin = 60
    _draw_rtl_text(draw, (WIDTH - margin, 40), BRAND_NAME, brand_font, ACCENT_GOLD)
    _draw_rtl_text(draw, (WIDTH - margin, 120), "✅ تم تحقيق الهدف", title_font, ACCENT_GREEN)

    draw.text((WIDTH // 2, 260), rec.symbol, font=symbol_font, fill=TEXT_WHITE, anchor="ma")

    y = 420
    target_price = rec.targets[target_index - 1]
    gain_pct = round((target_price / rec.entry_price - 1) * 100, 2)

    def row(label, value, color=TEXT_WHITE):
        nonlocal y
        _draw_rtl_text(draw, (WIDTH - margin, y), label, label_font, TEXT_MUTED)
        draw.text((margin, y), str(value), font=value_font, fill=color, anchor="la")
        y += 100

    row("سعر الدخول", f"${rec.entry_price}")
    row(f"الهدف {target_index} المحقق", f"${target_price}", ACCENT_GREEN)
    row("نسبة الربح من الدخول", f"+{gain_pct}%", ACCENT_GREEN)

    img.save(out_path)
    return out_path


def render_option_entry_card(rec, out_path: str):
    """بطاقة توصية دخول أوبشن (Call) جديدة."""
    height = 1400
    img, draw = _gradient_bg(WIDTH, height)

    title_font = _font(FONT_BOLD_PATH, 54)
    symbol_font = _font(FONT_BOLD_PATH, 76)
    tag_font = _font(FONT_BOLD_PATH, 34)
    label_font = _font(FONT_REGULAR_PATH, 34)
    value_font = _font(FONT_BOLD_PATH, 44)
    small_font = _font(FONT_REGULAR_PATH, 28)
    brand_font = _font(FONT_BOLD_PATH, 34)

    margin = 60

    _draw_rtl_text(draw, (WIDTH - margin, 40), BRAND_NAME, brand_font, ACCENT_GOLD)
    _draw_rtl_text(draw, (WIDTH - margin, 110), "توصية أوبشن جديدة", title_font, TEXT_WHITE)

    draw.text((WIDTH // 2, 210), f"{rec.symbol}", font=symbol_font, fill=ACCENT_GOLD, anchor="ma")
    tag_color = ACCENT_GREEN if rec.option_type == "CALL" else ACCENT_ORANGE
    draw.text((WIDTH // 2, 300), rec.option_type, font=tag_font, fill=tag_color, anchor="ma")

    y = 400
    row_h = 95

    def row(label, value, value_color=TEXT_WHITE):
        nonlocal y
        _draw_rtl_text(draw, (WIDTH - margin, y), label, label_font, TEXT_MUTED)
        draw.text((margin, y), str(value), font=value_font, fill=value_color, anchor="la")
        y += row_h

    row("السترايك (Strike)", f"${rec.strike}", TEXT_WHITE)
    row("تاريخ الانتهاء", rec.expiration, TEXT_WHITE)
    row("سعر الدخول (Premium)", f"${rec.entry_premium}", ACCENT_GOLD)
    row("وقف الخسارة", f"${rec.stop_loss_premium}", ACCENT_RED)

    for i, t in enumerate(rec.targets, start=1):
        row(f"الهدف {i}", f"${t}", ACCENT_GREEN)

    row("قوة الزخم", f"{rec.momentum_score}/100", ACCENT_GOLD)

    y += 15
    _draw_rtl_text(draw, (WIDTH - margin, y), "السبب:", label_font, TEXT_MUTED)
    y += 48
    _draw_rtl_text(draw, (WIDTH - margin, y), rec.reason, small_font, TEXT_WHITE)

    disclaimer_y = height - 240
    draw.line([(margin, disclaimer_y - 20), (WIDTH - margin, disclaimer_y - 20)],
              fill=(80, 75, 95), width=2)
    _wrap_rtl_paragraph(
        draw,
        DISCLAIMER_AR + " تداول الأوبشن أخطر بكثير من تداول الأسهم العادية "
        "بسبب سرعة تحرك السعر واحتمال فقدان كامل قيمة العقد.",
        small_font, TEXT_MUTED,
        right=WIDTH - margin, top=disclaimer_y, max_width=WIDTH - 2 * margin,
    )

    img.save(out_path)
    return out_path


def render_option_target_hit_card(rec, target_index: int, out_path: str):
    """بطاقة إشعار بتحقق هدف على عقد أوبشن مفتوح."""
    height = 950
    img, draw = _gradient_bg(WIDTH, height)

    brand_font = _font(FONT_BOLD_PATH, 34)
    title_font = _font(FONT_BOLD_PATH, 58)
    symbol_font = _font(FONT_BOLD_PATH, 66)
    label_font = _font(FONT_REGULAR_PATH, 34)
    value_font = _font(FONT_BOLD_PATH, 48)

    margin = 60
    _draw_rtl_text(draw, (WIDTH - margin, 40), BRAND_NAME, brand_font, ACCENT_GOLD)
    _draw_rtl_text(draw, (WIDTH - margin, 120), "✅ تم تحقيق الهدف", title_font, ACCENT_GREEN)

    draw.text((WIDTH // 2, 250), rec.symbol, font=symbol_font, fill=TEXT_WHITE, anchor="ma")
    draw.text((WIDTH // 2, 330), f"{rec.option_type} • Strike ${rec.strike} • {rec.expiration}",
               font=label_font, fill=TEXT_MUTED, anchor="ma")

    y = 440
    target_premium = rec.targets[target_index - 1]
    gain_pct = round((target_premium / rec.entry_premium - 1) * 100, 2)

    def row(label, value, color=TEXT_WHITE):
        nonlocal y
        _draw_rtl_text(draw, (WIDTH - margin, y), label, label_font, TEXT_MUTED)
        draw.text((margin, y), str(value), font=value_font, fill=color, anchor="la")
        y += 100

    row("سعر الدخول (Premium)", f"${rec.entry_premium}")
    row(f"الهدف {target_index} المحقق", f"${target_premium}", ACCENT_GREEN)
    row("نسبة الربح من الدخول", f"+{gain_pct}%", ACCENT_GREEN)

    img.save(out_path)
    return out_path


def _wrap_rtl_paragraph(draw, text, font, fill, right, top, max_width, line_height=38):
    """تلفيف فقرة عربية على عدة أسطر مع محاذاة لليمين."""
    words = text.split(" ")
    lines, current = [], ""
    for w in words:
        trial = (current + " " + w).strip()
        bbox = draw.textbbox((0, 0), ar(trial), font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)

    y = top
    for line in lines:
        draw.text((right, y), ar(line), font=font, fill=fill, anchor="ra")
        y += line_height
