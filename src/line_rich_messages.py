from linebot.models import FlexSendMessage


def add_stock_web_link_button(line_response_service, server_url: str) -> None:
    if not server_url:
        line_response_service.add_message("web URL が未設定です。")
        return

    base_url = server_url.rstrip("/")
    stock_url = f"{base_url}/stock?openExternalBrowser=1"
    image_url = f"{base_url}/static/images/list_icon.png"

    if not hasattr(line_response_service, "buttons"):
        line_response_service.add_message(f"webで一覧を確認する→ {stock_url}")
        return

    line_response_service.buttons.append(
        FlexSendMessage(
            alt_text="webで一覧を確認",
            contents={
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": image_url,
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "cover",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "一覧をWebで確認",
                            "weight": "bold",
                            "size": "lg",
                            "wrap": True,
                        },
                        {
                            "type": "text",
                            "text": "ボタンからアイテム一覧を開けます。",
                            "size": "sm",
                            "color": "#666666",
                            "wrap": True,
                        },
                    ],
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "action": {
                                "type": "uri",
                                "label": "一覧を開く",
                                "uri": stock_url,
                            },
                        }
                    ],
                },
            },
        )
    )
