#!/usr/bin/env python3
"""Generate a modern dark-themed rich menu image for LINE Bot.

Output: scripts/assets/rich_menu_default.png (2500x1686)
Layout: 3 columns x 2 rows
"""

import math
import sys
from PIL import Image, ImageDraw, ImageFont

# --- Layout constants ---
WIDTH, HEIGHT = 2500, 1686
ROW_H = HEIGHT // 2  # 843
COL_W = [833, 833, 834]

# --- Color palette ---
BG = (18, 18, 38)            # #12122e deep dark navy
DIVIDER = (40, 40, 72)       # #282848
ICON_BG = (32, 32, 68)       # #202044 subtle circle behind icon
ICON_COLOR = (255, 255, 255) # white
LABEL_COLOR = (210, 210, 230) # soft white

# --- Sizes ---
ICON_SIZE = 210   # icon drawing area (radius = half)
ICON_BG_R = 148   # radius of circle behind icon
LINE_W = 26       # stroke width for icons
FONT_SIZE = 82

FONT_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"


def cell_centers():
    """Return (cx, cy) center of each of the 6 cells, row-major."""
    cy_list = [ROW_H // 2, ROW_H + ROW_H // 2]
    result = []
    for row in range(2):
        x = 0
        for col in range(3):
            cx = x + COL_W[col] // 2
            result.append((cx, cy_list[row]))
            x += COL_W[col]
    return result


# ---------- Icon drawing helpers ----------

def _rr(draw, x0, y0, x1, y1, r, **kw):
    """Rounded rectangle shorthand."""
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, **kw)


def draw_list_icon(draw, cx, cy, sz, color, lw):
    """Three rounded horizontal bars (hamburger)."""
    half = sz // 2
    cap = lw // 2
    for dy in (-sz // 3, 0, sz // 3):
        _rr(draw, cx - half, cy + dy - lw // 2,
            cx + half, cy + dy + lw // 2, cap, fill=color)


def draw_plus_icon(draw, cx, cy, sz, color, lw):
    """Thin plus / cross."""
    half = sz // 2
    cap = lw // 2
    _rr(draw, cx - half, cy - lw // 2, cx + half, cy + lw // 2, cap, fill=color)
    _rr(draw, cx - lw // 2, cy - half, cx + lw // 2, cy + half, cap, fill=color)


def draw_question_icon(draw, cx, cy, sz, color, lw):
    """Circle outline with '?' inside."""
    r = sz // 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=lw)
    try:
        font = ImageFont.truetype(FONT_PATH, sz - 10)
    except Exception:
        font = ImageFont.load_default()
    draw.text((cx, cy + 6), "?", font=font, fill=color, anchor="mm")


def draw_globe_icon(draw, cx, cy, sz, color, lw):
    """Simple globe: circle + meridian + two latitudes."""
    r = sz // 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=lw)
    # central meridian
    draw.line([cx, cy - r + lw, cx, cy + r - lw], fill=color, width=lw)
    # two latitude arcs (drawn as ellipses, clipped to circle bbox)
    for yo_frac in (-0.35, 0.35):
        yo = int(r * yo_frac)
        # horizontal width at latitude yo
        inner_r = int(math.sqrt(max(0, r ** 2 - yo ** 2))) - lw // 2
        if inner_r > lw:
            # draw as a flat ellipse
            ey = cy + yo
            ew = inner_r
            eh = max(inner_r // 3, lw * 2)
            draw.ellipse(
                [cx - ew, ey - eh // 2, cx + ew, ey + eh // 2],
                outline=color, width=lw,
            )


def draw_link_icon(draw, cx, cy, sz, color, lw):
    """Two overlapping chain-link ovals at 45 degrees."""
    # Simulate by drawing two pill shapes rotated via a temporary image
    link_w = sz * 2 // 3
    link_h = sz // 3
    gap = sz // 5

    def draw_pill(img_layer, ox, oy):
        d = ImageDraw.Draw(img_layer)
        _rr(d, ox - link_w // 2, oy - link_h // 2,
            ox + link_w // 2, oy + link_h // 2,
            link_h // 2, outline=color, width=lw)

    # Upper-left link
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_pill(layer, cx - gap, cy - gap)
    rotated = layer.rotate(-45, center=(cx, cy))

    # Lower-right link
    layer2 = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_pill(layer2, cx + gap, cy + gap)
    rotated2 = layer2.rotate(-45, center=(cx, cy))

    # Composite onto draw's image
    base = draw._image
    base.alpha_composite(rotated)
    base.alpha_composite(rotated2)


def draw_check_icon(draw, cx, cy, sz, color, lw):
    """Circle with checkmark inside."""
    r = sz // 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=lw)
    # Checkmark: short left stroke + long right stroke
    pts = [
        (cx - sz // 4, cy + sz // 16),
        (cx - sz // 10 + 4, cy + sz // 4),
        (cx + sz // 3, cy - sz // 5),
    ]
    draw.line(pts, fill=color, width=lw + 6, joint="curve")


# ---------- Main ----------

CELLS = [
    ("一覧",      draw_list_icon),
    ("登録",      draw_plus_icon),
    ("使い方",    draw_question_icon),
    ("Web一覧",   draw_globe_icon),
    ("連携",      draw_link_icon),
    ("習慣タスク", draw_check_icon),
]


def main(output: str = "scripts/assets/rich_menu_default.png"):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (*BG, 255))
    draw = ImageDraw.Draw(img)

    # Dividers
    draw.rectangle([0, ROW_H - 1, WIDTH, ROW_H + 1], fill=(*DIVIDER, 255))
    x = 0
    for w in COL_W[:-1]:
        x += w
        draw.rectangle([x - 1, 0, x + 1, HEIGHT], fill=(*DIVIDER, 255))

    # Load font
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()

    centers = cell_centers()
    icon_dy = -90   # icon center offset from cell center
    label_dy = 210  # label center offset from cell center

    for (label, draw_fn), (cx, cy) in zip(CELLS, centers):
        icy = cy + icon_dy

        # Icon background circle
        draw.ellipse(
            [cx - ICON_BG_R, icy - ICON_BG_R, cx + ICON_BG_R, icy + ICON_BG_R],
            fill=(*ICON_BG, 255),
        )

        # Icon — link icon needs the composited image; others use draw directly
        if draw_fn is draw_link_icon:
            draw_link_icon(draw, cx, icy, ICON_SIZE, ICON_COLOR, LINE_W)
        else:
            draw_fn(draw, cx, icy, ICON_SIZE, ICON_COLOR, LINE_W)

        # Label
        draw.text((cx, cy + label_dy), label, font=font, fill=(*LABEL_COLOR, 255), anchor="mm")

    # Convert to RGB for PNG output
    final = img.convert("RGB")
    final.save(output)
    print(f"Saved: {output}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "scripts/assets/rich_menu_default.png"
    main(out)
