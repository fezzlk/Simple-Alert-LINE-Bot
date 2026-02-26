import argparse
import os
import sys

from linebot.models import (
    MessageAction,
    RichMenu,
    RichMenuArea,
    RichMenuBounds,
    RichMenuSize,
    URIAction,
)

from src import config
from src.line_bot_api import line_bot_api


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Create and set LINE rich menu for Simple-Alert-LINE-Bot."
    )
    parser.add_argument(
        "--image-path",
        default="scripts/assets/rich_menu_default.png",
        help="Path to rich menu image (PNG/JPEG, 2500x1686).",
    )
    parser.add_argument(
        "--name",
        default="simple-alert-main-menu",
        help="LINE rich menu name.",
    )
    parser.add_argument(
        "--chat-bar-text",
        default="メニュー",
        help="Text displayed on chat bar.",
    )
    parser.add_argument(
        "--skip-set-default",
        action="store_true",
        help="Skip set_default_rich_menu call.",
    )
    return parser.parse_args()


def _build_rich_menu(name: str, chat_bar_text: str, server_url: str) -> RichMenu:
    base_url = server_url.rstrip("/")
    stock_url = f"{base_url}/stock?openExternalBrowser=1"
    habit_url = f"{base_url}/habit?openExternalBrowser=1"

    # 2500x1686 split into 3 columns x 2 rows
    # col widths: 833, 833, 834 / row heights: 843, 843
    areas = [
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
            action=MessageAction(label="一覧", text="一覧"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=833, y=0, width=833, height=843),
            action=MessageAction(label="登録", text="登録"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=1666, y=0, width=834, height=843),
            action=MessageAction(label="使い方", text="使い方"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=843, width=833, height=843),
            action=URIAction(label="Web一覧", uri=stock_url),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=833, y=843, width=833, height=843),
            action=MessageAction(label="連携", text="アカウント連携"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=1666, y=843, width=834, height=843),
            action=URIAction(label="習慣タスク", uri=habit_url),
        ),
    ]

    return RichMenu(
        size=RichMenuSize(width=2500, height=1686),
        selected=True,
        name=name,
        chat_bar_text=chat_bar_text,
        areas=areas,
    )


def main() -> int:
    args = _parse_args()

    if not config.LINEBOT_CHANNEL_ACCESS_TOKEN:
        print("LINEBOT_CHANNEL_ACCESS_TOKEN is not set.")
        return 1
    if not config.SERVER_URL:
        print("SERVER_URL is not set.")
        return 1
    if not os.path.exists(args.image_path):
        print(f"Image file not found: {args.image_path}")
        return 1

    rich_menu = _build_rich_menu(
        name=args.name,
        chat_bar_text=args.chat_bar_text,
        server_url=config.SERVER_URL,
    )
    rich_menu_id = line_bot_api.create_rich_menu(rich_menu)
    print(f"Created rich menu: {rich_menu_id}")

    content_type = "image/png"
    if args.image_path.lower().endswith(".jpg") or args.image_path.lower().endswith(".jpeg"):
        content_type = "image/jpeg"

    with open(args.image_path, "rb") as fp:
        line_bot_api.set_rich_menu_image(
            rich_menu_id=rich_menu_id,
            content_type=content_type,
            content=fp,
        )
    print(f"Uploaded image: {args.image_path}")

    if not args.skip_set_default:
        line_bot_api.set_default_rich_menu(rich_menu_id)
        print(f"Set default rich menu: {rich_menu_id}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
