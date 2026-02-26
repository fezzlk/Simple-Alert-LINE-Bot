from linebot.models import ButtonsTemplate, TemplateSendMessage, URIAction


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
        TemplateSendMessage(
            alt_text="webで一覧を確認",
            template=ButtonsTemplate(
                thumbnail_image_url=image_url,
                title="一覧をWebで確認",
                text="ボタンからアイテム一覧を開けます。",
                actions=[
                    URIAction(label="一覧を開く", uri=stock_url),
                ],
            ),
        )
    )
