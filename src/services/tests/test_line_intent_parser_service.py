from src import config
from src.services.LineIntentParserService import LineIntentParserService


def test_fallback_parse_bought_maps_to_register():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("牛乳 買った")
        assert result["intent"] == "register"
        assert result["item_name"] == "牛乳"
        assert result["expiry_date"] is None
    finally:
        config.OPENAI_API_KEY = original


def test_fallback_parse_used_up_maps_to_delete():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("使い切った 牛乳")
        assert result["intent"] == "delete"
        assert result["item_name"] == "牛乳"
        assert result["expiry_date"] is None
    finally:
        config.OPENAI_API_KEY = original


def test_fallback_parse_relative_due_date_is_not_executable():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("牛乳の期限を来週に")
        assert result["intent"] == "none"
        assert result["item_name"] is None
        assert result["expiry_date"] is None
    finally:
        config.OPENAI_API_KEY = original
