#!/usr/bin/env python3
"""Draw a one-page broadsheet of Thursday 26 November 2026 world news.

Regenerate the broadsheet PNG. The submitted entrypoint is main.py, which
copies the committed entry.png. This script writes a deterministic PNG to /output/entry.png (and, when that
directory is missing, to entry.png beside this file). It uses only files in
this repository. Two runs must emit identical bytes.
"""
from __future__ import annotations

import io
import os
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "fonts"
SIZE = 1024

# Cream broadsheet, dark ink, a single crimson accent.
PAPER = (244, 237, 223)
INK = (26, 24, 21)
NAVY = (24, 38, 62)
CRIMSON = (150, 32, 32)
RULE = (120, 48, 42)
GOLD = (168, 128, 58)
CHIP = (252, 248, 238)
LEAD = (250, 245, 232)
MUTED = (92, 86, 78)
LINE = (196, 184, 164)
OFFICIAL = (18, 108, 74)
REPORTED = (28, 78, 138)
CLAIM = (148, 72, 22)
ONGOING = (120, 88, 18)
WHITE = (255, 252, 246)
MAP_SEA = (214, 226, 230)
MAP_LAND = (196, 184, 158)
MAP_EDGE = (120, 108, 90)
PIN = (150, 32, 32)


def _font(name: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONTS / name), size=size)
    if weight is not None:
        try:
            axes = font.get_variation_axes()
            values = []
            for axis in axes:
                axis_name = axis.get("name") or axis.get("tag") or ""
                if "wght" in str(axis_name).lower() or "weight" in str(axis_name).lower():
                    values.append(float(weight))
                else:
                    default = axis.get("default")
                    values.append(float(default if default is not None else axis.get("minimum", 0)))
            if values:
                font.set_variation_by_axes(values)
        except Exception:
            pass
    return font


class Fonts:
    def __init__(self) -> None:
        self.date = _font("PlayfairDisplaySC-Black.ttf", 52)
        self.date_sm = _font("PlayfairDisplaySC-Black.ttf", 44)
        self.mast = _font("Oswald-VariableFont_wght.ttf", 13, 600)
        self.kicker = _font("PTSerif-BoldItalic.ttf", 17)
        self.anton_lg = _font("Anton-Regular.ttf", 44)
        self.anton_md = _font("Anton-Regular.ttf", 36)
        self.anton_sm = _font("Anton-Regular.ttf", 28)
        self.anton_xl = _font("Anton-Regular.ttf", 52)
        self.oswald_b = _font("Oswald-VariableFont_wght.ttf", 13, 650)
        self.oswald_m = _font("Oswald-VariableFont_wght.ttf", 11, 500)
        self.oswald_s = _font("Oswald-VariableFont_wght.ttf", 10, 500)
        self.sans = _font("PTSans-Regular.ttf", 11)
        self.sans_b = _font("PTSans-Bold.ttf", 11)
        self.sans_i = _font("PTSans-Italic.ttf", 11)
        self.sans10 = _font("PTSans-Regular.ttf", 10)
        self.sans10b = _font("PTSans-Bold.ttf", 10)
        self.sans10i = _font("PTSans-Italic.ttf", 10)
        self.sans9 = _font("PTSans-Regular.ttf", 9)
        self.sans9b = _font("PTSans-Bold.ttf", 9)
        self.sans9i = _font("PTSans-Italic.ttf", 9)
        self.sans8 = _font("PTSans-Regular.ttf", 8)
        self.sans8b = _font("PTSans-Bold.ttf", 8)
        self.sans8i = _font("PTSans-Italic.ttf", 8)
        self.head = _font("PTSans-Bold.ttf", 16)
        self.head14 = _font("PTSans-Bold.ttf", 14)
        self.head13 = _font("PTSans-Bold.ttf", 13)
        self.lead_sub = _font("PTSans-Regular.ttf", 11)
        self.serif_b = _font("PTSerif-Bold.ttf", 12)
        self.tag = _font("PTSans-Bold.ttf", 8)


F: Fonts  # filled in main


def text_w(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> float:
    return float(draw.textlength(text, font=font))


def wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: float) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    cur = words[0]
    for word in words[1:]:
        trial = f"{cur} {word}"
        if text_w(draw, trial, font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, font, fill, max_w, leading) -> int:
    lines = wrap(draw, text, font, max_w)
    for i, line in enumerate(lines):
        draw.text((x, y + i * leading), line, font=font, fill=fill)
    return y + len(lines) * leading


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def tag_chip(draw, x, y, label, color):
    font = F.tag
    w = text_w(draw, label, font) + 8
    h = 11
    rounded(draw, (x, y, x + w, y + h), 2, color)
    draw.text((x + 4, y - 1), label, font=font, fill=WHITE)
    return w


def masthead(draw: ImageDraw.ImageDraw):
    draw.rectangle((0, 0, SIZE, 22), fill=NAVY)
    draw.text((14, 3), "THE WORLD IN ONE PAGE", font=F.mast, fill=WHITE)
    right = "28 STORIES  ·  8 REGIONS  ·  EVERY ITEM DATED THURSDAY 26 NOVEMBER 2026"
    rw = text_w(draw, right, F.mast)
    draw.text((SIZE - 14 - rw, 3), right, font=F.mast, fill=(230, 220, 200))
    draw.rectangle((0, 22, SIZE, 26), fill=CRIMSON)


def date_block(draw: ImageDraw.ImageDraw):
    y = 30
    title = "Thursday 26 November 2026"
    # Shrink slightly if needed to keep side margins.
    font = F.date
    tw = text_w(draw, title, font)
    if tw > SIZE - 24:
        font = F.date_sm
        tw = text_w(draw, title, font)
    draw.text(((SIZE - tw) / 2, y), title, font=font, fill=INK)
    kicker = (
        "Coalition downs two missiles over Riyadh  ·  "
        "Asia stocks rebound as US markets shut  ·  "
        "Bank of Korea lifts rate to 3.25%"
    )
    kw = text_w(draw, kicker, F.kicker)
    draw.text(((SIZE - kw) / 2, 86), kicker, font=F.kicker, fill=CRIMSON)
    draw.line((14, 108, SIZE - 14, 108), fill=RULE, width=1)
    return 112


CHIPS = [
    ("2", "MISSILES", "downed over Riyadh", "OFFICIAL"),
    ("2", "DRONES", "Eastern Province", "OFFICIAL"),
    ("+1.19%", "HANG SENG", "close 22,226.88", "OFFICIAL"),
    ("+0.86%", "NIKKEI", "close 57,499", "OFFICIAL"),
    ("3.25%", "BOK RATE", "highest since Oct 2024", "OFFICIAL"),
    ("8", "KILLED", "Gaza, overnight", "REPORTED"),
    ("SHUT", "US MARKETS", "Thanksgiving Day", "OFFICIAL"),
]

TAG_COLOR = {
    "OFFICIAL": OFFICIAL,
    "REPORTED": REPORTED,
    "CLAIM": CLAIM,
    "ONGOING": ONGOING,
}


def chips_row(draw, y):
    n = len(CHIPS)
    gap = 5
    x0 = 14
    x1 = SIZE - 14
    width = (x1 - x0 - gap * (n - 1)) / n
    h = 52
    foot = 17
    for i, (big, label, sub, tag) in enumerate(CHIPS):
        x = x0 + i * (width + gap)
        rounded(draw, (x, y, x + width, y + h), 4, CHIP, LINE, 1)
        draw.rectangle((x, y, x + 3, y + h), fill=CRIMSON)
        # Reserved footer for the two label lines; the figure stays above it.
        if len(big) >= 6:
            font = _font("Anton-Regular.ttf", 20)
        elif len(big) >= 4:
            font = _font("Anton-Regular.ttf", 24)
        else:
            font = _font("Anton-Regular.ttf", 26)
        # Anchor the figure to the top of the chip so it cannot enter the footer.
        draw.text((x + 7, y - 1), big, font=font, fill=INK)
        lab_y = y + h - foot
        draw.line((x + 6, lab_y - 1, x + width - 4, lab_y - 1), fill=LINE, width=1)
        draw.text((x + 7, lab_y), label, font=F.sans8b, fill=CRIMSON)
        draw.text((x + 7, lab_y + 8), sub, font=F.sans8, fill=MUTED)
    return y + h + 5


def timeline(draw, y):
    band = 36
    draw.rectangle((14, y, SIZE - 14, y + band), fill=(236, 228, 212))
    draw.text((18, y + 12), "THURSDAY IN UTC", font=F.sans8b, fill=NAVY)
    events = [
        ("~00-04", "Riyadh intercepts"),
        ("03:21", "Trump-Rutte text"),
        ("05:00", "ASX close"),
        ("06:00", "Nikkei close"),
        ("08:00", "Hang Seng close"),
        ("12:00", "Tube strike"),
        ("all day", "US markets shut"),
    ]
    x = 128
    rail_y = y + 16
    draw.line((x, rail_y, SIZE - 22, rail_y), fill=NAVY, width=1)
    n = len(events)
    # Keep the last label inside the right margin.
    left, right = x + 18, SIZE - 70
    for i, (t, label) in enumerate(events):
        px = left + i * ((right - left) / (n - 1))
        draw.ellipse((px - 2, rail_y - 2, px + 2, rail_y + 2), fill=CRIMSON)
        tw = text_w(draw, t, F.sans8b)
        draw.text((px - tw / 2, y + 3), t, font=F.sans8b, fill=INK)
        lw = text_w(draw, label, F.sans8)
        draw.text((px - lw / 2, y + 22), label, font=F.sans8, fill=MUTED)
    return y + band + 4


REGIONS = [
    ("N. AMERICA", "2"),
    ("LATIN AM.", "1"),
    ("EUROPE", "4"),
    ("MIDDLE EAST", "4"),
    ("S. ASIA", "1"),
    ("EAST ASIA", "6"),
    ("SE ASIA", "2"),
    ("OCEANIA", "2"),
]


def region_row(draw, y):
    draw.text((14, y + 1), "REGIONS WITH THURSDAY ITEMS", font=F.sans8b, fill=MUTED)
    x = 188
    for name, n in REGIONS:
        label = f"{name}  {n}"
        w = text_w(draw, label, F.sans8b) + 10
        rounded(draw, (x, y, x + w, y + 13), 2, NAVY)
        draw.text((x + 5, y + 1), label, font=F.sans8b, fill=WHITE)
        x += w + 4
    return y + 18


def lead_panel(draw, box, num, place, beat, huge, headline, deck, source, tag, extra=None):
    x0, y0, x1, y1 = box
    rounded(draw, box, 4, LEAD, LINE, 1)
    draw.rectangle((x0, y0, x0 + 4, y1), fill=CRIMSON)
    # number badge
    badge = f"{num}"
    draw.ellipse((x0 + 10, y0 + 6, x0 + 26, y0 + 22), fill=NAVY)
    tw = text_w(draw, badge, F.sans9b)
    draw.text((x0 + 18 - tw / 2, y0 + 7), badge, font=F.sans9b, fill=WHITE)
    loc = f"{place}  ·  {beat}"
    draw.text((x0 + 30, y0 + 7), loc, font=F.oswald_s, fill=MUTED)
    tw = tag_chip(draw, x1 - 8 - text_w(draw, tag, F.tag) - 8, y0 + 8, tag, TAG_COLOR[tag])
    # huge word
    font = F.anton_lg if len(huge) < 18 else F.anton_md
    if len(huge) > 22:
        font = F.anton_sm
    draw.text((x0 + 10, y0 + 22), huge, font=font, fill=INK)
    # measure huge height
    bbox = draw.textbbox((x0 + 10, y0 + 22), huge, font=font)
    y = bbox[3] + 2
    y = draw_wrapped(draw, x0 + 10, y, headline, F.head13, INK, x1 - x0 - 20, 15)
    y = draw_wrapped(draw, x0 + 10, y + 2, deck, F.sans10, INK, x1 - x0 - 20, 12)
    if extra:
        y = extra(draw, x0, y, x1)
    draw.text((x0 + 10, y1 - 14), source, font=F.sans8i, fill=MUTED)


def mini_bars(draw, x0, y, x1, values):
    """Tiny bar chart of official Asia closes. values: list of (label, pct, color)."""
    # baseline 0; scale to max abs 1.4
    max_v = 1.4
    bw = 18
    gap = 6
    h = 28
    base = y + 16
    total = len(values) * (bw + gap) - gap
    sx = x0 + 10
    for i, (label, pct, color) in enumerate(values):
        x = sx + i * (bw + gap)
        bh = int(abs(pct) / max_v * 14)
        if pct >= 0:
            draw.rectangle((x, base - bh, x + bw, base), fill=color)
        else:
            draw.rectangle((x, base, x + bw, base + bh), fill=color)
        draw.text((x, base + 1), label, font=F.sans8, fill=MUTED)
        draw.text((x, base - bh - 10), f"{pct:+.2f}", font=F.sans8b, fill=INK)
    draw.line((sx, base, sx + total, base), fill=LINE, width=1)
    return y + h + 2


def leads(draw, y):
    gap = 6
    x0 = 14
    x1 = SIZE - 14
    w = (x1 - x0 - 2 * gap) / 3
    h = 162
    boxes = [(x0 + i * (w + gap), y, x0 + i * (w + gap) + w, y + h) for i in range(3)]

    lead_panel(
        draw, boxes[0], "1", "RIYADH / EASTERN PROVINCE", "WAR",
        "2 MISSILES INTERCEPTED",
        "Coalition says it also downed 2 drones.",
        "Air defences destroyed two Houthi ballistic missiles headed for Riyadh, then two drones over the Eastern Province, the coalition said. No casualty details were given. Wednesday’s Ras Tanura claims and a Jazan port projectile are in the DATE CHECK.",
        "AA · Al Arabiya · The National  ·  coalition statement",
        "OFFICIAL",
    )
    def bars(d, x0, y, x1):
        return mini_bars(d, x0, y, x1, [
            ("HSI", 1.19, OFFICIAL),
            ("NKY", 0.86, OFFICIAL),
            ("ASX", 0.82, OFFICIAL),
            ("KOS", 0.29, REPORTED),
            ("SH", 0.01, MUTED),
        ])
    lead_panel(
        draw, boxes[1], "2", "ASIA / BRUSSELS / WASHINGTON", "TRADE & MARKETS",
        "ASIA STOCKS REBOUND",
        "US cash markets are shut for Thanksgiving.",
        "A day after Washington proposed tariffs on 14 partners, Hang Seng closed +1.19%, Nikkei +0.86%, ASX 200 +0.82%. Singapore was “very disappointed”; the EU “firmly rejects” the premise. The proposal itself is Wednesday news — see DATE CHECK.",
        "Exchanges / Yahoo · CNA/METI · ABC/EU  ·  proposal: Reuters 25 Nov",
        "OFFICIAL",
        extra=None,  # bars may not fit; put percents in the huge line already
    )
    lead_panel(
        draw, boxes[2], "3", "SEOUL", "ECONOMY",
        "BOK LIFTS RATE TO 3.25%",
        "Highest since October 2024; two members dissented.",
        "The central bank raised the base rate 25 basis points after an October pause, citing stronger growth and inflation still above target. It lifted its 2026 growth view to 3.9% and 2027 to 4.1%. Two members voted to hold at 3.00%.",
        "Bank of Korea · Yonhap, 26 Nov 11:13 KST",
        "OFFICIAL",
    )
    return y + h + 8


CARDS = [
    dict(n="4", place="GAZA", beat="CONFLICT",
         head="Israeli strikes kill 8 overnight, hospitals say",
         deck="Officials at Shifa and Al-Aqsa Martyrs hospitals told AP that three Israeli strikes overnight into Thursday killed eight Palestinians.",
         src="AP, Thursday Mid-East round-up", tag="REPORTED"),
    dict(n="5", place="WEST OF DUBAI", beat="SHIPPING",
         head="Tanker reports projectile explosion; crew safe",
         deck="UKMTO said early Thursday a master reported an unknown projectile explosion. Time: 21:30 UTC 25 Nov — already Thursday in the Gulf. No damage or pollution.",
         src="UKMTO · Anadolu · AP", tag="OFFICIAL"),
    dict(n="6", place="LONDON", beat="LABOUR",
         head="Tube strike: no Piccadilly or Circle service",
         deck="RMT drivers began a 24-hour strike from noon. TfL: Waterloo & City closed from midday; reduced services late morning; no Tube after 21:00. Talks at Acas failed on Tuesday.",
         src="Guardian · TfL · Independent", tag="OFFICIAL"),
    dict(n="7", place="SINGAPORE", beat="TRADE",
         head="METI ‘very disappointed’ at proposed US tariffs",
         deck="USTR on Wednesday proposed a 20% potential rate, net of existing duties, or 10% if a deal is reached. METI disagrees with the excess-capacity findings and will comment in the consultation.",
         src="CNA, METI statement, 26 Nov 11:37 SST", tag="OFFICIAL"),
    dict(n="8", place="BOGOTÁ", beat="DIPLOMACY",
         head="Colombia will not continue BRICS accession",
         deck="The foreign ministry said it will not go on with steps to join BRICS and the New Development Bank, reversing a Petro-era process. Confirmed Wednesday night — already Thursday UTC.",
         src="Cancillería via El País · Infobae", tag="OFFICIAL"),
    dict(n="9", place="PALM BEACH", beat="DIPLOMACY",
         head="Trump and Rutte: Russia should not expand the war",
         deck="A joint statement after a closed Wednesday-evening Mar-a-Lago meeting was issued at 03:21 UTC Thursday and posted by NATO dated 26 Nov. They also discussed Iran and defence spending.",
         src="NATO · White House · RTÉ", tag="OFFICIAL"),
    dict(n="10", place="LONDON / EU", beat="POLICY",
         head="UK due to publish EU food-trade texts and bill",
         deck="Legal texts of last week’s SPS and emissions deals, plus a cost-cutting bill, were scheduled for Thursday. The SPS pact would scrap most post-Brexit food checks from March 2028.",
         src="Telegraph · Independent · BBC via Telegraph", tag="REPORTED"),
    dict(n="11", place="SE ASIA", beat="TECH",
         head="FT: Nvidia halts AI server shipments to four countries",
         deck="The FT reported Nvidia told partners to stop shipping AI servers to Malaysia, Singapore, Thailand and Indonesia as US export controls tightened. Not officially confirmed here.",
         src="FT via Reuters, CNA, Guardian, Nikkei", tag="REPORTED"),
    dict(n="12", place="SANAA", beat="WAR",
         head="Explosion rocks Yemen’s capital, live blog says",
         deck="Al Jazeera reported an explosion in Sanaa after recent air strikes near the international airport, as the coalition announced the Riyadh intercepts.",
         src="Al Jazeera live blog, 26 Nov", tag="REPORTED"),
    dict(n="13", place="SYDNEY", beat="MARKETS",
         head="ASX 200 closes +0.82%; TVSN goes into liquidation",
         deck="The benchmark finished at 8,763.8, led by materials and energy. ABC also reported that TVSN, the TV shopping channel, entered liquidation after no buyer was found.",
         src="ABC News live, 26 Nov, ASX close", tag="REPORTED"),
]


def card(draw, box, item):
    x0, y0, x1, y1 = box
    rounded(draw, box, 3, WHITE, LINE, 1)
    # number
    draw.rectangle((x0, y0, x0 + 16, y0 + 16), fill=NAVY)
    tw = text_w(draw, item["n"], F.sans8b)
    draw.text((x0 + 8 - tw / 2, y0 + 2), item["n"], font=F.sans8b, fill=WHITE)
    draw.text((x0 + 20, y0 + 2), f"{item['place']}  ·  {item['beat']}", font=F.sans8b, fill=MUTED)
    tag = item["tag"]
    tw = text_w(draw, tag, F.tag) + 8
    tag_chip(draw, x1 - 6 - tw, y0 + 3, tag, TAG_COLOR[tag])
    y = draw_wrapped(draw, x0 + 6, y0 + 18, item["head"], F.sans10b, INK, x1 - x0 - 12, 12)
    y = draw_wrapped(draw, x0 + 6, y + 1, item["deck"], F.sans9, INK, x1 - x0 - 12, 11)
    draw.text((x0 + 6, y1 - 12), item["src"], font=F.sans8i, fill=MUTED)


def cards_grid(draw, y):
    x0, x1 = 14, SIZE - 14
    gap = 5
    cols, rows = 5, 2
    w = (x1 - x0 - gap * (cols - 1)) / cols
    h = 126
    for i, item in enumerate(CARDS):
        r, c = divmod(i, cols)
        # wait, 5 cols: i 0-4 row0, 5-9 row1
        r = i // cols
        c = i % cols
        box = (x0 + c * (w + gap), y + r * (h + gap), x0 + c * (w + gap) + w, y + r * (h + gap) + h)
        card(draw, box, item)
    return y + rows * (h + gap) + 2


# Approximate land blobs for a locator map (equirectangular-ish, lon -140..180, lat -50..70).
# Coordinates are rough visual shapes, not a survey map.

def lonlat_to_xy(lon, lat, box):
    x0, y0, x1, y1 = box
    # pad
    lon0, lon1 = -130, 180
    lat0, lat1 = -48, 72
    x = x0 + (lon - lon0) / (lon1 - lon0) * (x1 - x0)
    y = y1 - (lat - lat0) / (lat1 - lat0) * (y1 - y0)
    return x, y


LAND = [
    # North America (incl. a Florida hook)
    [(-130, 55), (-125, 60), (-105, 62), (-85, 60), (-60, 52), (-65, 45),
     (-74, 45), (-80, 35), (-81, 25), (-80, 25), (-82, 31), (-90, 29),
     (-97, 26), (-110, 31), (-124, 40), (-125, 48), (-130, 55)],
    # South America
    [(-81, 12), (-70, 12), (-60, 8), (-50, 2), (-44, -3), (-35, -7),
     (-40, -20), (-54, -32), (-68, -50), (-76, -45), (-73, -18),
     (-79, -5), (-81, 12)],
    # Britain and Ireland
    [(-10, 51), (-8, 54), (-6, 58), (-4, 57), (-2, 53), (1, 52), (1, 50),
     (-5, 50), (-10, 51)],
    # Europe
    [(-9, 42), (-8, 43), (0, 49), (2, 51), (8, 54), (12, 55), (18, 54),
     (24, 60), (30, 69), (28, 60), (40, 60), (40, 48), (29, 41), (24, 38),
     (15, 38), (10, 41), (3, 43), (-1, 44), (-5, 43), (-9, 37), (-9, 42)],
    # Africa
    [(-17, 28), (-13, 33), (-5, 36), (10, 33), (25, 32), (32, 31),
     (35, 28), (32, 22), (40, 15), (48, 14), (51, 12), (49, 6),
     (43, -11), (39, -16), (32, -28), (29, -30), (18, -35), (15, -28),
     (12, -17), (9, 0), (4, 5), (-5, 5), (-14, 10), (-17, 20), (-17, 28)],
    # Arabia / Levant
    [(32, 31), (36, 34), (38, 30), (44, 24), (48, 29), (54, 27),
     (56, 25), (54, 17), (48, 14), (44, 13), (39, 16), (34, 28), (32, 31)],
    # India / Sri Lanka hint
    [(68, 24), (70, 29), (77, 32), (88, 27), (90, 23), (82, 16),
     (80, 8), (78, 8), (73, 18), (68, 24)],
    # Mainland Asia
    [(40, 48), (50, 48), (60, 45), (70, 40), (80, 42), (95, 44),
     (110, 42), (122, 41), (128, 48), (135, 53), (140, 50),
     (134, 40), (122, 31), (108, 21), (100, 21), (96, 18),
     (88, 22), (80, 28), (70, 28), (60, 36), (48, 40), (40, 48)],
    # Korean peninsula
    [(126, 34), (127, 38), (129.5, 37), (129, 35), (126, 34)],
    # Japan
    [(130, 31), (136, 35), (141, 41), (141, 38), (139, 35), (132, 31), (130, 31)],
    # Mainland SE Asia
    [(97, 20), (100, 14), (104, 11), (109, 12), (109, 6), (104, 6),
     (100, 7), (98, 12), (97, 20)],
    # Sumatra / Borneo / Java hint
    [(95, 5), (104, 5), (108, 1), (118, 3), (119, 0), (116, -3),
     (110, -3), (104, -6), (100, -1), (95, 5)],
    # Australia
    [(114, -22), (126, -13), (136, -12), (146, -16), (153, -25),
     (153, -34), (146, -38), (136, -36), (124, -34), (115, -34), (114, -22)],
    # New Zealand
    [(166, -41), (174, -35), (178, -38), (175, -42), (170, -46), (166, -41)],
]

PINS = [
    (1, 46.7, 24.7, "Riyadh"),
    (2, 114.2, 22.3, "Hong Kong"),
    (3, 126.98, 37.57, "Seoul"),
    (4, 34.45, 31.50, "Gaza"),
    (5, 54.5, 25.2, "Dubai W."),
    (6, -0.13, 51.5, "London"),
    (7, 103.8, 1.3, "Singapore"),
    (8, -74.08, 4.71, "Bogotá"),
    (9, -80.04, 26.72, "Palm Bch"),
    (10, 4.35, 50.85, "Brussels"),
    (11, 101.7, 3.14, "Kuala L."),
    (12, 44.21, 15.35, "Sanaa"),
    (13, 151.21, -33.87, "Sydney"),
]


def draw_map(draw, box):
    x0, y0, x1, y1 = box
    rounded(draw, box, 3, MAP_SEA, LINE, 1)
    draw.text((x0 + 6, y0 + 4), "WHERE IT HAPPENED  ·  pins are story numbers 1–13", font=F.sans8b, fill=NAVY)
    inner = (x0 + 4, y0 + 16, x1 - 4, y1 - 4)
    # land
    for poly in LAND:
        pts = [lonlat_to_xy(lon, lat, inner) for lon, lat in poly]
        if len(pts) >= 3:
            draw.polygon(pts, fill=MAP_LAND, outline=MAP_EDGE)
    # pins
    for n, lon, lat, _name in PINS:
        x, y = lonlat_to_xy(lon, lat, inner)
        r = 6
        draw.ellipse((x - r, y - r, x + r, y + r), fill=CRIMSON, outline=INK)
        label = str(n)
        tw = text_w(draw, label, F.sans8b)
        draw.text((x - tw / 2, y - 5), label, font=F.sans8b, fill=WHITE)


BRIEFS = [
    "14  Tokyo: Nikkei 225 closed 57,499, up 487 points or 0.86% — official cash close, not a midday print.",
    "15  Seoul: Kospi closed +0.29% at 4,711, a modest gain beside the Hang Seng and Nikkei rebounds.",
    "16  Shanghai Composite finished almost unchanged, +0.01% at 3,476.88.",
    "17  Brussels: Commission spokesperson Olof Gill said the EU “firmly rejects” the idea that it fuels overcapacity and expects Washington to respect last year’s tariff agreement.",
    "18  Tokyo: Japan called the proposed US tariffs “regrettable” and rejected claims of structural excess capacity.",
    "19  United States: cash equity and bond markets were closed all day for Thanksgiving; Friday is a short session.",
    "20  Europe was firmer in morning trade after Wednesday’s drop; futures had pointed to a strong open. Official European closes were not yet in at compile time and are not quoted here.",
    "21  India marked Constitution Day; a CJP rally was due in Nagpur, with actor Prakash Raj expected to join (The Hindu).",
    "22  Consultation on the US tariff proposal: written comments due 5 January 2027, hearings from 25 January; no start date for the duties was given.",
    "23  Bank of Korea dropped “pace” from its guidance and now refers to the “timing” of further increases; October CPI was 2.8%, still above the 2% target.",
    "24  Further RMT Tube strike dates include 17 and 19 December and early January 2027 (Guardian / TfL).",
    "25  Gold futures were firmer in Thursday dealing, around $3,593–3,598; Bitcoin was slightly higher early in an incomplete UTC day.",
    "26  Oil quotes were mixed by contract and time after Wednesday’s jump on Saudi-site risk; no single Thursday settle is treated as official here.",
    "27  Australian dollar +0.3% at 66.42 US cents in ABC’s late-session snapshot; private capex printed +12.2% vs 4.4% expected (Newsquawk).",
    "28  No casualty or damage details were given for the Thursday Riyadh and Eastern Province intercepts (coalition / AA).",
]


DATECHECK = [
    "Wed 25: USTR proposed new tariffs on 14 partners (Reuters). Max potential rates were described as 20–40%, to be capped under deals; The Hindu cited India 25% and Vietnam 35%. Thursday covers the reaction, not the announcement.",
    "Wed 25: Shenzhou-24 launched and docked with Tiangong; Pakistani astronaut Muhammad Zeeshan Ali flew with Tang Hongbo and Wu Yi (Xinhua).",
    "Wed 25: Cairo ring-road tanker fire, at least 31 dead, about 21 hurt (Egypt health ministry, Thursday wraps).",
    "Wed 25: West Java mine — 9 found dead, 17 missing (Xinhua, local authorities).",
    "Wed 25: Houthis claimed a Ras Tanura refinery attack (smoke on satellite images; coalition said it downed 4 drones, did not confirm a hit). A projectile hit Jazan port, minor damage, no civilian injuries. A Jeddah claim was unconfirmed.",
    "Tue 24: PIF tower in Riyadh struck, 11 wounded — second hit in a week (Saudi Civil Defence). FCC SpaceX “Starmind” radio-link authorisation. NY signed a 5-year AI-chatbot-toy ban.",
    "Wed 25 late: Trump–Rutte met at Mar-a-Lago (the Thursday item is the statement, issued 03:21 UTC 26 Nov). Russia struck a Kyiv shopping centre; 7 injured. A Hamas security official and family were killed in Gaza City. Iraq agreed a 1 Dec Baghdad–Erbil dialogue. El-Sisi met Maersk’s CEO on Suez traffic.",
    "Wed 25: Lagos ports groundbreaking; Sudan rejected Ethiopia’s offer to host peace talks; Brazil approved tighter credit-card limits effective 2027; KCNA said Kim Jong Un inspected nuclear sites (event dated 25 Nov).",
    "Mon 23: Andy Taylor of Duran Duran died at 65 (band / AP) — Thursday UK briefings recorded the mourning, not a Thursday death. Upcoming, not today: US short session Fri 27 Nov; Huang-related congressional meetings 1 and 3 Dec.",
]


def bottom(draw, y):
    x0, x1 = 14, SIZE - 14
    foot = 1008
    gap = 6
    mid = x0 + int((x1 - x0) * 0.38)
    # map
    draw_map(draw, (x0, y, mid - 4, y + 168))
    # also column
    ax0, ay0, ax1, ay1 = mid + 2, y, x1, y + 168
    rounded(draw, (ax0, ay0, ax1, ay1), 3, WHITE, LINE, 1)
    draw.rectangle((ax0, ay0, ax1, ay0 + 14), fill=NAVY)
    draw.text((ax0 + 6, ay0 + 1), "ALSO ON THURSDAY  —  BRIEFS 14–28", font=F.sans8b, fill=WHITE)
    yy = ay0 + 16
    for line in BRIEFS:
        if yy > ay1 - 10:
            break
        yy = draw_wrapped(draw, ax0 + 5, yy, line, F.sans8, INK, ax1 - ax0 - 10, 9)
    # date check
    dy = y + 174
    rounded(draw, (x0, dy, x1, foot - 22), 3, (238, 230, 214), LINE, 1)
    draw.rectangle((x0, dy, x0 + 70, dy + 14), fill=CRIMSON)
    draw.text((x0 + 6, dy + 1), "DATE CHECK", font=F.sans8b, fill=WHITE)
    draw.text((x0 + 76, dy + 1), "LEFT OUT — NOT THURSDAY 26 NOVEMBER 2026 NEWS  ·  adjacent-day events deliberately omitted from the leads", font=F.sans8b, fill=CRIMSON)
    yy = dy + 16
    for line in DATECHECK:
        if yy > foot - 36:
            break
        yy = draw_wrapped(draw, x0 + 6, yy, line, F.sans8, INK, x1 - x0 - 12, 9)
    # legend + compile
    ly = foot - 20
    draw.rectangle((0, ly, SIZE, SIZE), fill=NAVY)
    legend = "HOW SURE   OFFICIAL = on the record    REPORTED = wires / outlets    CLAIM = one side, unverified    ONGOING = still developing"
    draw.text((14, ly + 2), legend, font=F.sans8b, fill=WHITE)
    compile_line = (
        "Compiled about 16:30 Hong Kong time (08:30 UTC) Thu 26 Nov 2026, after Asia closes, during the European morning. "
        "The UTC day was still open in the Americas. US cash markets were closed for Thanksgiving. "
        "Typeset and drawn in code; sources are on the image."
    )
    draw.text((14, ly + 11), compile_line, font=F.sans8, fill=(220, 210, 190))


def render() -> Image.Image:
    global F
    F = Fonts()
    img = Image.new("RGB", (SIZE, SIZE), PAPER)
    draw = ImageDraw.Draw(img)
    masthead(draw)
    y = date_block(draw)
    y = chips_row(draw, y)
    y = timeline(draw, y)
    y = region_row(draw, y)
    y = leads(draw, y)
    y = cards_grid(draw, y)
    bottom(draw, y)
    # outer rule
    draw.rectangle((0, 0, SIZE - 1, SIZE - 1), outline=(60, 50, 40), width=1)
    return img


def png_bytes(img: Image.Image) -> bytes:
    """Write a deterministic PNG: no text chunks, fixed compression, RGB."""
    rgb = img.convert("RGB")
    # Encode manually via Pillow then strip optional time-ish behaviour.
    buf = io.BytesIO()
    # Pillow may add tEXt; use a clean encoder.
    rgb.save(buf, format="PNG", optimize=True, compress_level=9, pnginfo=PngImagePlugin.PngInfo())
    data = buf.getvalue()
    # Re-chunk, dropping any tEXt/tIME/iTXt/zTXt, rebuild IDAT with fixed zlib if needed.
    return _sanitize_png(data)


def _sanitize_png(data: bytes) -> bytes:
    sig, rest = data[:8], data[8:]
    assert sig == b"\x89PNG\r\n\x1a\n"
    chunks = []
    i = 0
    while i + 8 <= len(rest):
        length = int.from_bytes(rest[i:i + 4], "big")
        typ = rest[i + 4:i + 8]
        raw = rest[i + 8:i + 8 + length]
        crc = rest[i + 8 + length:i + 12 + length]
        i += 12 + length
        if typ in {b"tEXt", b"zTXt", b"iTXt", b"tIME"}:
            continue
        chunks.append((typ, raw))
        if typ == b"IEND":
            break
    out = bytearray(sig)
    for typ, raw in chunks:
        out += len(raw).to_bytes(4, "big")
        out += typ + raw
        out += zlib.crc32(typ + raw).to_bytes(4, "big")
    return bytes(out)


def output_path() -> Path:
    out_dir = Path("/output")
    if out_dir.is_dir() or os.environ.get("MAKEFUN_OUTPUT") == "1":
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / "entry.png"
    return ROOT / "entry.png"


def main() -> None:
    img = render()
    data = png_bytes(img)
    dest = output_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    # Also keep a copy beside the program when writing to /output, for the repo.
    local = ROOT / "entry.png"
    if dest.resolve() != local.resolve():
        local.write_bytes(data)


if __name__ == "__main__":
    main()
