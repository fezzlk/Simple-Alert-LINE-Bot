from src import config
from datetime import datetime
import pytest
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


def test_fallback_parse_bought_with_particle_maps_to_register():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("卵を買った")
        assert result["intent"] == "register"
        assert result["item_name"] == "卵"
        assert result["expiry_date"] is None
    finally:
        config.OPENAI_API_KEY = original


def test_fallback_parse_bought_colloquial_maps_to_register():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("牛乳買っといた")
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


def test_fallback_parse_consumed_maps_to_delete():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("牛乳 消費した")
        assert result["intent"] == "delete"
        assert result["item_name"] == "牛乳"
        assert result["expiry_date"] is None
    finally:
        config.OPENAI_API_KEY = original


@pytest.mark.parametrize(
    "text,expected_name",
    [
        ("牛乳もうない", "牛乳"),
        ("卵なくなった", "卵"),
        ("納豆は処分した", "納豆"),
    ],
)
def test_fallback_parse_more_delete_variants(text, expected_name):
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse(text)
        assert result["intent"] == "delete"
        assert result["item_name"] == expected_name
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


def test_fallback_parse_bulk_delete_is_not_executable():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("全部削除して")
        assert result["intent"] == "none"
        assert result["item_name"] is None
        assert result["expiry_date"] is None
    finally:
        config.OPENAI_API_KEY = original


def test_fallback_parse_bulk_update_is_not_executable():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("全部期限を今日にして")
        assert result["intent"] == "none"
        assert result["item_name"] is None
        assert result["expiry_date"] is None
    finally:
        config.OPENAI_API_KEY = original


def test_fallback_parse_until_phrase_maps_to_register_with_date():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("確定申告は3/15まで")
        assert result["intent"] == "register"
        assert result["item_name"] == "確定申告"
        assert result["expiry_date"] == f"{datetime.now().year:04d}-03-15"
    finally:
        config.OPENAI_API_KEY = original


@pytest.mark.parametrize(
    "text",
    [
        "確定申告は3月15日まで",
        "確定申告 3/15〆",
        "確定申告 期限3/15",
        "確定申告 締切 3/15",
        "確定申告 期限を3/15まで",
        "ライブチケット購入 3/15まで",
        "新幹線チケット購入は3/15まで",
    ],
)
def test_fallback_parse_month_day_variants_map_to_register_with_date(text):
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse(text)
        assert result["intent"] == "register"
        assert result["item_name"] == "確定申告"
        assert result["expiry_date"] == f"{datetime.now().year:04d}-03-15"
    finally:
        config.OPENAI_API_KEY = original


@pytest.mark.parametrize(
    "text",
    [
        "更新 牛乳 2026-03-20",
        "牛乳の期限を2026-03-20にして",
    ],
)
def test_fallback_parse_update_iso_variants(text):
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse(text)
        assert result["intent"] == "update"
        assert result["item_name"] == "牛乳"
        assert result["expiry_date"] == "2026-03-20"
    finally:
        config.OPENAI_API_KEY = original


def test_fallback_parse_update_month_day_variant():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("牛乳の期限を3/20に変更")
        assert result["intent"] == "update"
        assert result["item_name"] == "牛乳"
        assert result["expiry_date"] == f"{datetime.now().year:04d}-03-20"
    finally:
        config.OPENAI_API_KEY = original


def test_fallback_parse_until_eat_phrase_maps_to_register_with_date():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("りんご 3/2までに食べる")
        assert result["intent"] == "register"
        assert result["item_name"] == "りんご"
        assert result["expiry_date"] == f"{datetime.now().year:04d}-03-02"
    finally:
        config.OPENAI_API_KEY = original


def test_fallback_parse_until_task_phrase_maps_to_register_with_date():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("税務署提出書類 3/10までにやる")
        assert result["intent"] == "register"
        assert result["item_name"] == "税務署提出書類"
        assert result["expiry_date"] == f"{datetime.now().year:04d}-03-10"
    finally:
        config.OPENAI_API_KEY = original


def test_fallback_parse_update_non_food_task_month_day_variant():
    original = config.OPENAI_API_KEY
    config.OPENAI_API_KEY = ""
    try:
        service = LineIntentParserService()
        result = service.parse("ライブチケット購入の期限を3/22にして")
        assert result["intent"] == "update"
        assert result["item_name"] == "ライブチケット購入"
        assert result["expiry_date"] == f"{datetime.now().year:04d}-03-22"
    finally:
        config.OPENAI_API_KEY = original
