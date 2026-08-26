# -*- coding: utf-8 -*-
"""
مولّد بطاقات الصور للتوصيات (بطاقة دخول جديدة + بطاقة تحقيق هدف).
تصميم "فخم": خلفية متدرجة عميقة، إطار ذهبي، توهج خفيف على اسم السهم،
وشارات (pills) مصممة بدل نص عادي.

يحتاج:
    pip install pillow arabic-reshaper python-bidi

ويحتاج خط عربي حقيقي (يدعم النسخ العربي) موضوع في:
    fonts/NotoNaskhArabic-Regular.ttf
    fonts/NotoNaskhArabic-Bold.ttf
تقدر تنزلهم مجانًا من Google Fonts (Noto Naskh Arabic).
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from config import FONT_REGULAR_PATH, FONT_BOLD_PATH, BRAND_NAME, DISCLAIMER_AR, PROFIT_TAKE_NOTE_AR

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _AR_SUPPORT = True
except ImportError:
    _AR_SUPPORT = False


def ar(text: str) -> str:
    """يهيّئ نص عربي للعرض الصحيح داخل صورة (تشكيل الحروف + اتجاه RTL)."""
    if not _AR_SUPPORT:
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


WIDTH = 1080

# لوحة ألوان فخمة: كحلي/بنفسجي عميق مع لمسات ذهبية
BG_TOP = (8, 6, 20)
BG_MID = (24, 12, 42)
BG_BOTTOM = (12, 8, 24)
PANEL_BG = (38, 24, 58)
PANEL_BORDER = (70, 55, 95)
GOLD = (222, 178, 90)
GOLD_SOFT = (170, 140, 90)
ACCENT_GREEN = (70, 205, 130)
ACCENT_RED = (225, 80, 80)
ACCENT_ORANGE = (232, 140, 65)
ACCENT_GOLD = GOLD
TEXT_WHITE = (247, 245, 250)
TEXT_MUTED = (172, 165, 188)

FRAME_MARGIN = 26


def _luxury_bg(width, height):
    """خلفية متدرجة ثلاثية النقاط (كحلي داكن -> بنفسجي عميق -> كحلي داكن)."""
    img = Image.new("RGB", (width, height), BG_TOP)
    draw = ImageDraw.Draw(img)
    mid_point = height * 0.45
    for y in range(height):
        if y <= mid_point:
            t = y / mid_point if mid_point else 0
            r = int(BG_TOP[0] + (BG_MID[0] - BG_TOP[0]) * t)
            g = int(BG_TOP[1] + (BG_MID[1] - BG_TOP[1]) * t)
            b = int(BG_TOP[2] + (BG_MID[2] - BG_TOP[2]) * t)
        else:
            t = (y - mid_point) / (height - mid_point) if height > mid_point else 0
            r = int(BG_MID[0] + (BG_BOTTOM[0] - BG_MID[0]) * t)
            g = int(BG_MID[1] + (BG_BOTTOM[1] - BG_MID[1]) * t)
            b = int(BG_MID[2] + (BG_BOTTOM[2] - BG_MID[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img, draw


def _draw_rtl_text(draw, xy, text, font, fill, anchor="ra"):
    """رسم نص RTL: xy هي نقطة اليمين، والنص يمتد لليسار."""
    draw.text(xy, ar(text), font=font, fill=fill, anchor=anchor)


def _draw_frame(draw, width, height, margin=FRAME_MARGIN, color=GOLD, radius=28, w=3):
    """إطار ذهبي رفيع حول كامل البطاقة."""
    draw.rounded_rectangle(
        [(margin, margin), (width - margin, height - margin)],
        radius=radius, outline=color, width=w,
    )


def _draw_corner_diamonds(draw, width, margin=FRAME_MARGIN, color=GOLD, size=10, offset=22):
    """زخرفة ماسية صغيرة بزوايا البطاقة العلوية."""
    for cx in (margin + offset, width - margin - offset):
        cy = margin + offset
        draw.polygon(
            [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)],
            fill=color,
        )


def _draw_pill(draw, center_x, y, text, font, text_color, border_color, fill_color=None, pad_x=28, pad_y=12):
    """شارة بيضاوية (pill) بنص بالمنتصف - تستخدم للعلامة والنوع (CALL/PUT)."""
    txt = ar(text)
    bbox = draw.textbbox((0, 0), txt, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x0 = center_x - tw // 2 - pad_x
    x1 = center_x + tw // 2 + pad_x
    y0 = y
    y1 = y + th + pad_y * 2
    radius = (y1 - y0) // 2
    if fill_color:
        draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, fill=fill_color, outline=border_color, width=2)
    else:
        draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, outline=border_color, width=2)
    draw.text((center_x, y0 + pad_y - bbox[1]), txt, font=font, fill=text_color, anchor="ma")
    return y1 - y0


def _glow_text(img, draw, xy, text, font, color, anchor="ma", blur_radius=16, glow_alpha=190):
    """يرسم توهج ناعم خلف النص (زي إضاءة نيون خفيفة) ثم النص الحاد فوقه."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.text(xy, ar(text) if _AR_SUPPORT_TEXT_IS_ARABIC(text) else text,
                font=font, fill=color + (glow_alpha,), anchor=anchor)
    overlay = overlay.filter(ImageFilter.GaussianBlur(blur_radius))
    img_rgba = img.convert("RGBA")
    img_rgba.alpha_composite(overlay)
    img.paste(img_rgba.convert("RGB"), (0, 0))
    draw.text(xy, text, font=font, fill=color, anchor=anchor)


def _AR_SUPPORT_TEXT_IS_ARABIC(text):
    # النص هنا دايمًا رمز سهم إنجليزي (زي TSLA) فما يحتاج تشكيل عربي
    return False


def _diamond_divider(draw, y, width, margin=60, color=GOLD_SOFT):
    """خط فاصل رفيع مع ماسة صغيرة بالمنتصف - لمسة فخامة بين الأقسام."""
    cx = width // 2
    draw.line([(margin, y), (cx - 24, y)], fill=color, width=2)
    draw.line([(cx + 24, y), (width - margin, y)], fill=color, width=2)
    s = 8
    draw.polygon([(cx, y - s), (cx + s, y), (cx, y + s), (cx - s, y)], fill=GOLD)


def _row_panel(draw, x0, x1, y, height, accent_color=None):
    """خلفية بطاقة صغيرة أنيقة خلف كل صف بيانات، مع شريط لون جانبي اختياري."""
    draw.rounded_rectangle([(x0, y), (x1, y + height)], radius=16, fill=PANEL_BG, outline=PANEL_BORDER, width=1)
    if accent_color:
        draw.rounded_rectangle([(x1 - 8, y + 8), (x1, y + height - 8)], radius=4, fill=accent_color)


def _count_wrapped_lines(draw, text, font, max_width):
    """يحسب كم سطر بيحتاجه نص عربي بعد التلفيف، بدون ما يرسمه فعليًا."""
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
    return len(lines)


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


# ============================================================
#                     بطاقات الأوبشن (المستخدمة فعليًا)
# ============================================================

def render_option_entry_card(rec, out_path: str):
    """بطاقة توصية دخول أوبشن (Call/Put) - تصميم فخم."""
    WORK_HEIGHT = 2200
    img, draw = _luxury_bg(WIDTH, WORK_HEIGHT)

    title_font = _font(FONT_BOLD_PATH, 46)
    symbol_font = _font(FONT_BOLD_PATH, 92)
    tag_font = _font(FONT_BOLD_PATH, 32)
    label_font = _font(FONT_REGULAR_PATH, 32)
    value_font = _font(FONT_BOLD_PATH, 44)
    small_font = _font(FONT_REGULAR_PATH, 26)
    brand_font = _font(FONT_BOLD_PATH, 30)

    margin = 60
    inner_x0, inner_x1 = FRAME_MARGIN + 20, WIDTH - FRAME_MARGIN - 20

    # ---- الترويسة: شارة العلامة + العنوان ----
    _draw_pill(draw, WIDTH // 2, 56, BRAND_NAME, brand_font, GOLD, GOLD, fill_color=(30, 20, 15))
    _draw_rtl_text(draw, (WIDTH // 2, 150), "", label_font, TEXT_MUTED, anchor="ma")  # spacer no-op
    draw.text((WIDTH // 2, 160), ar("توصية أوبشن جديدة"), font=title_font, fill=TEXT_WHITE, anchor="ma")

    _diamond_divider(draw, 232, WIDTH, margin=margin)

    # ---- اسم السهم بتأثير توهج + شارة النوع ----
    _glow_text(img, draw, (WIDTH // 2, 268), rec.symbol, symbol_font, GOLD, anchor="ma", blur_radius=18)

    tag_color = ACCENT_GREEN if rec.option_type == "CALL" else ACCENT_ORANGE
    tag_fill = (18, 40, 30) if rec.option_type == "CALL" else (42, 28, 16)
    _draw_pill(draw, WIDTH // 2, 420, rec.option_type, tag_font, tag_color, tag_color, fill_color=tag_fill)

    y = 520
    row_h = 92
    panel_h = 68

    def row(label, value, value_color=TEXT_WHITE, accent=None):
        nonlocal y
        _row_panel(draw, inner_x0, inner_x1, y, panel_h, accent_color=accent)
        text_y = y + panel_h // 2
        _draw_rtl_text(draw, (inner_x1 - 26, text_y), label, label_font, TEXT_MUTED, anchor="rm")
        draw.text((inner_x0 + 26, text_y), str(value), font=value_font, fill=value_color, anchor="lm")
        y += row_h

    row("السترايك (Strike)", f"${rec.strike}", TEXT_WHITE)
    row("تاريخ الانتهاء", rec.expiration, TEXT_WHITE)
    row("سعر الدخول (Premium)", f"${rec.entry_premium}", GOLD, accent=GOLD)
    row("وقف الخسارة", f"${rec.stop_loss_premium}", ACCENT_RED, accent=ACCENT_RED)

    for i, t in enumerate(rec.targets, start=1):
        row(f"الهدف {i}", f"${t}", ACCENT_GREEN, accent=ACCENT_GREEN)

    row("قوة الزخم", f"{rec.momentum_score}/100", GOLD, accent=GOLD)

    # ---- السبب ----
    y += 20
    _diamond_divider(draw, y, WIDTH, margin=margin)
    y += 36
    _draw_rtl_text(draw, (WIDTH - margin, y), "السبب:", label_font, TEXT_MUTED)
    y += 46
    _wrap_rtl_paragraph(
        draw, rec.reason, small_font, TEXT_WHITE,
        right=WIDTH - margin, top=y, max_width=WIDTH - 2 * margin, line_height=36,
    )
    reason_lines = max(1, _count_wrapped_lines(draw, rec.reason, small_font, WIDTH - 2 * margin))
    y += reason_lines * 36 + 30

    # ---- التنويه القانوني ----
    draw.line([(margin, y), (WIDTH - margin, y)], fill=PANEL_BORDER, width=2)
    y += 22
    disclaimer_text = (
        DISCLAIMER_AR + " تداول الأوبشن أخطر بكثير من تداول الأسهم العادية "
        "بسبب سرعة تحرك السعر واحتمال فقدان كامل قيمة العقد."
    )
    _wrap_rtl_paragraph(
        draw, disclaimer_text, small_font, TEXT_MUTED,
        right=WIDTH - margin, top=y, max_width=WIDTH - 2 * margin, line_height=38,
    )
    disclaimer_lines = max(1, _count_wrapped_lines(draw, disclaimer_text, small_font, WIDTH - 2 * margin))
    y += disclaimer_lines * 38 + 26

    # ---- نصيحة القناعة بالربح ----
    _wrap_rtl_paragraph(
        draw, PROFIT_TAKE_NOTE_AR, small_font, GOLD,
        right=WIDTH - margin, top=y, max_width=WIDTH - 2 * margin, line_height=38,
    )
    note_lines = max(1, _count_wrapped_lines(draw, PROFIT_TAKE_NOTE_AR, small_font, WIDTH - 2 * margin))
    y += note_lines * 38 + 50

    final_height = min(y, WORK_HEIGHT)
    _draw_frame(draw, WIDTH, final_height)
    _draw_corner_diamonds(draw, WIDTH)

    final_img = img.crop((0, 0, WIDTH, final_height))
    final_img.save(out_path)
    return out_path


def render_option_target_hit_card(rec, target_index: int, out_path: str):
    """بطاقة إشعار بتحقق هدف على عقد أوبشن مفتوح - تصميم فخم."""
    height = 1000
    img, draw = _luxury_bg(WIDTH, height)

    brand_font = _font(FONT_BOLD_PATH, 30)
    title_font = _font(FONT_BOLD_PATH, 56)
    symbol_font = _font(FONT_BOLD_PATH, 78)
    label_font = _font(FONT_REGULAR_PATH, 32)
    value_font = _font(FONT_BOLD_PATH, 46)

    margin = 60
    inner_x0, inner_x1 = FRAME_MARGIN + 20, WIDTH - FRAME_MARGIN - 20

    _draw_pill(draw, WIDTH // 2, 50, BRAND_NAME, brand_font, GOLD, GOLD, fill_color=(30, 20, 15))
    draw.text((WIDTH // 2, 150), ar("✅ تم تحقيق الهدف"), font=title_font, fill=ACCENT_GREEN, anchor="ma")

    _diamond_divider(draw, 222, WIDTH, margin=margin)

    _glow_text(img, draw, (WIDTH // 2, 250), rec.symbol, symbol_font, TEXT_WHITE, anchor="ma", blur_radius=14)
    draw.text((WIDTH // 2, 350), ar(f"{rec.option_type} • Strike ${rec.strike} • {rec.expiration}"),
               font=label_font, fill=TEXT_MUTED, anchor="ma")

    y = 440
    row_h = 100
    panel_h = 76
    target_premium = rec.targets[target_index - 1]
    gain_pct = round((target_premium / rec.entry_premium - 1) * 100, 2)

    def row(label, value, color=TEXT_WHITE, accent=None):
        nonlocal y
        _row_panel(draw, inner_x0, inner_x1, y, panel_h, accent_color=accent)
        text_y = y + panel_h // 2
        _draw_rtl_text(draw, (inner_x1 - 26, text_y), label, label_font, TEXT_MUTED, anchor="rm")
        draw.text((inner_x0 + 26, text_y), str(value), font=value_font, fill=color, anchor="lm")
        y += row_h

    row("سعر الدخول (Premium)", f"${rec.entry_premium}")
    row(f"الهدف {target_index} المحقق", f"${target_premium}", ACCENT_GREEN, accent=ACCENT_GREEN)
    row("نسبة الربح من الدخول", f"+{gain_pct}%", ACCENT_GREEN, accent=ACCENT_GREEN)

    y += 20
    _draw_frame(draw, WIDTH, y)
    _draw_corner_diamonds(draw, WIDTH)

    final_img = img.crop((0, 0, WIDTH, y))
    final_img.save(out_path)
    return out_path


# ============================================================
#     بطاقات الأسهم العادية (احتياط - غير مستخدمة بوضع الأوبشن الحالي)
# ============================================================

def render_entry_card(rec, out_path: str):
    """بطاقة توصية دخول جديدة (سهم عادي)."""
    height = 1350
    img, draw = _luxury_bg(WIDTH, height)

    title_font = _font(FONT_BOLD_PATH, 54)
    symbol_font = _font(FONT_BOLD_PATH, 80)
    label_font = _font(FONT_REGULAR_PATH, 36)
    value_font = _font(FONT_BOLD_PATH, 46)
    small_font = _font(FONT_REGULAR_PATH, 28)
    brand_font = _font(FONT_BOLD_PATH, 34)

    margin = 60

    _draw_rtl_text(draw, (WIDTH - margin, 40), BRAND_NAME, brand_font, GOLD)
    _draw_rtl_text(draw, (WIDTH - margin, 110), "توصية جديدة", title_font, TEXT_WHITE)
    _glow_text(img, draw, (WIDTH // 2, 220), rec.symbol, symbol_font, GOLD, anchor="ma", blur_radius=16)

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

    row("قوة الزخم", f"{rec.momentum_score}/100", GOLD)

    y += 20
    _draw_rtl_text(draw, (WIDTH - margin, y), "السبب:", label_font, TEXT_MUTED)
    y += 50
    _draw_rtl_text(draw, (WIDTH - margin, y), rec.reason, small_font, TEXT_WHITE)

    disclaimer_y = height - 220
    draw.line([(margin, disclaimer_y - 20), (WIDTH - margin, disclaimer_y - 20)],
              fill=PANEL_BORDER, width=2)
    _wrap_rtl_paragraph(draw, DISCLAIMER_AR, small_font, TEXT_MUTED,
                         right=WIDTH - margin, top=disclaimer_y, max_width=WIDTH - 2 * margin)

    _draw_frame(draw, WIDTH, height)
    img.save(out_path)
    return out_path


def render_target_hit_card(rec, target_index: int, out_path: str):
    """بطاقة إشعار بتحقق هدف من أهداف توصية سابقة (سهم عادي)."""
    height = 900
    img, draw = _luxury_bg(WIDTH, height)

    brand_font = _font(FONT_BOLD_PATH, 34)
    title_font = _font(FONT_BOLD_PATH, 60)
    symbol_font = _font(FONT_BOLD_PATH, 70)
    label_font = _font(FONT_REGULAR_PATH, 36)
    value_font = _font(FONT_BOLD_PATH, 50)

    margin = 60
    _draw_rtl_text(draw, (WIDTH - margin, 40), BRAND_NAME, brand_font, GOLD)
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

    _draw_frame(draw, WIDTH, height)
    img.save(out_path)
    return out_path
