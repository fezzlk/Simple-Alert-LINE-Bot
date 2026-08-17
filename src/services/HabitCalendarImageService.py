import os
from datetime import date, timedelta
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

# ImageFont.load_default() はPIL組み込みのビットマップフォントでCJKグリフを一切含まない
# （日本語のタスク名・見出しが豆腐/空白になる）。そのため日本語対応TrueTypeフォントを優先し、
# 見つからない場合のみ load_default() にフォールバックする。
#
# 本番・開発コンテナでは Dockerfile / Dockerfile.dev で `fonts-noto-cjk`（Debian パッケージ）を
# apt-get install しており、以下のパスに実体が存在する
# （Debian bookworm/trixie で確認済み: https://packages.debian.org/bookworm/fonts-noto-cjk ）。
# ローカルの venv 等、フォント未インストールの環境ではフォールバックにより
# render_habit_calendar_image() 自体は動作し続ける（ユニットテストはPNGが生成されることのみ検証し、
# 実フォントの存在を前提にしない）。
_CJK_FONT_PATH_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
_HEADER_FONT_SIZE = 20
_BODY_FONT_SIZE = 16


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _CJK_FONT_PATH_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


# HabitTaskLog.result に格納される値（HandleHabitTaskResponseUseCase 参照）:
#   "done" / "not_done" / "other"。ログが無い日は None として扱う。
_RESULT_COLORS = {
    "done": (33, 136, 56),       # green
    "not_done": (200, 40, 40),   # red
}
_DEFAULT_COLOR = (140, 140, 140)  # gray: "other" またはログ無し

_RESULT_MARKS = {
    "done": "OK",
    "not_done": "NG",
}
_DEFAULT_MARK = "?"

IMAGE_WIDTH = 700
_ROW_HEIGHT = 40
_HEADER_HEIGHT = 60
_LABEL_WIDTH = 180
_MARGIN = 20
_BACKGROUND_COLOR = (255, 255, 255)
_TEXT_COLOR = (30, 30, 30)
_HEADER_TEXT_COLOR = (80, 80, 80)
_GRID_COLOR = (220, 220, 220)


def build_week_dates(week_start: date) -> list[date]:
    """week_start を起点とした7日分の日付リスト（古い順）を返す。"""
    return [week_start + timedelta(days=offset) for offset in range(7)]


def render_habit_calendar_image(task_rows: list[dict], week_dates: list[date]) -> bytes:
    """習慣タスクの週次実績カレンダーをPNGバイト列として描画する。

    task_rows: [{"task_name": str, "results": {"YYYY-MM-DD": "done"|"not_done"|"other"|None}}]
    week_dates: 表示対象の日付リスト（7件、古い順）
    """
    header_font = _load_font(_HEADER_FONT_SIZE)
    body_font = _load_font(_BODY_FONT_SIZE)
    row_count = max(len(task_rows), 1)
    height = _HEADER_HEIGHT + _ROW_HEIGHT * row_count + _MARGIN

    image = Image.new("RGB", (IMAGE_WIDTH, height), color=_BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    draw.text((_MARGIN, 12), "今週の習慣タスク実績", fill=_TEXT_COLOR, font=header_font)

    col_width = (IMAGE_WIDTH - _LABEL_WIDTH - _MARGIN * 2) // 7
    for col, day in enumerate(week_dates):
        x = _LABEL_WIDTH + _MARGIN + col * col_width
        draw.text((x, _HEADER_HEIGHT - 22), day.strftime("%m/%d"), fill=_HEADER_TEXT_COLOR, font=body_font)

    if not task_rows:
        draw.text((_MARGIN, _HEADER_HEIGHT + 10), "実施中の習慣タスクはありません", fill=_TEXT_COLOR, font=body_font)

    for row, task in enumerate(task_rows):
        y = _HEADER_HEIGHT + row * _ROW_HEIGHT
        draw.line([(_MARGIN, y), (IMAGE_WIDTH - _MARGIN, y)], fill=_GRID_COLOR, width=1)
        task_name = task["task_name"] or ""
        draw.text((_MARGIN, y + 12), task_name[:18], fill=_TEXT_COLOR, font=body_font)

        for col, day in enumerate(week_dates):
            x = _LABEL_WIDTH + _MARGIN + col * col_width
            result: str | None = task["results"].get(day.strftime("%Y-%m-%d"))
            color = _RESULT_COLORS.get(result, _DEFAULT_COLOR)
            mark = _RESULT_MARKS.get(result, _DEFAULT_MARK)
            draw.ellipse(
                [x, y + 6, x + 26, y + 32],
                outline=color,
                width=2,
            )
            draw.text((x + 8, y + 12), mark, fill=color, font=body_font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
