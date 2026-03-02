import json
import re
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional

from src import config
from src.services.LineIntentRulebook import (
    HELP_ALIASES,
    LIST_DISPLAY_ALIASES,
    LOGIN_ALIASES,
    WEB_LINK_ALIASES,
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "register_stock",
            "description": "在庫・タスク・締切付き作業を登録する。expiry_dateは相対日付（今日/明日/明後日）を具体的なYYYY-MM-DDに変換。",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name":      {"type": "string"},
                    "expiry_date":    {"type": ["string", "null"]},
                    "notify_enabled": {"type": "boolean"},
                },
                "required": ["item_name", "expiry_date", "notify_enabled"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_stock_expiry",
            "description": "登録済みアイテムの期限を変更する。expiry_dateは相対日付を変換。",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name":   {"type": "string"},
                    "expiry_date": {"type": "string"},
                },
                "required": ["item_name", "expiry_date"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_stock",
            "description": "在庫・タスクを削除する。expiry_dateは完全一致フィルタ、exclude_expiry_dateは除外フィルタ（「以外を削除」）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name":           {"type": "string"},
                    "expiry_date":         {"type": ["string", "null"]},
                    "exclude_expiry_date": {"type": ["string", "null"]},
                },
                "required": ["item_name", "expiry_date", "exclude_expiry_date"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "register_habit_task",
            "description": "毎日・毎週の習慣タスクを登録する。notify_timeはHH:MM形式、不明ならnull。",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name":   {"type": "string"},
                    "frequency":   {"type": "string", "enum": ["daily", "weekly"]},
                    "notify_time": {"type": ["string", "null"]},
                },
                "required": ["item_name", "frequency", "notify_time"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_habit_task",
            "description": "習慣タスクを停止（論理削除）する。",
            "parameters": {
                "type": "object",
                "properties": {"task_name": {"type": "string"}},
                "required": ["task_name"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_habit_notify_time",
            "description": "習慣タスクの通知時刻を変更する。notify_timeはHH:MM形式。",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name":   {"type": "string"},
                    "notify_time": {"type": "string"},
                },
                "required": ["task_name", "notify_time"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_notification_setting",
            "description": "在庫期限通知スケジュールのON/OFFまたは時刻を変更する。変更しない項目はnull。",
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled":     {"type": ["boolean", "null"]},
                    "notify_time": {"type": ["string", "null"]},
                },
                "required": ["enabled", "notify_time"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_stock_notify",
            "description": "登録済みアイテムの通知設定（notify_enabled）を変更する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name":      {"type": "string"},
                    "notify_enabled": {"type": "boolean"},
                },
                "required": ["item_name", "notify_enabled"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_habit_log",
            "description": "習慣タスクの実績を修正する。scheduled_dateはYYYY-MM-DD（今日/昨日を変換）。resultはdone/not_done/other。",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name":      {"type": "string"},
                    "scheduled_date": {"type": "string"},
                    "result":         {"type": "string", "enum": ["done", "not_done", "other"]},
                    "note":           {"type": ["string", "null"]},
                },
                "required": ["task_name", "scheduled_date", "result", "note"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
]

FUNCTION_TO_INTENT = {
    "register_stock":            "register",
    "update_stock_expiry":       "update",
    "delete_stock":              "delete",
    "register_habit_task":       "register_habit",
    "delete_habit_task":         "delete_habit",
    "update_habit_notify_time":  "update_habit_notify_time",
    "update_notification_setting": "update_notification",
    "update_stock_notify":       "update_stock_notify",
    "update_habit_log":          "update_habit_log",
}


class LineIntentParserService:
    def parse(self, message: str) -> Dict[str, Any]:
        text = (message or "").strip()
        if not text:
            return self._none_result()
        lower = text.lower()

        # Tier-1A: エイリアス完全一致
        if any(a in text for a in HELP_ALIASES):
            return {**self._none_result(), "intent": "help"}
        if any(a in text for a in LIST_DISPLAY_ALIASES):
            return {**self._none_result(), "intent": "list"}
        if any(a in lower for a in WEB_LINK_ALIASES):
            return {**self._none_result(), "intent": "web"}
        if any(a in lower for a in LOGIN_ALIASES):
            return {**self._none_result(), "intent": "login"}

        # Tier-1B: セキュリティフィルタ
        if re.search(r"(ignore|system prompt|開発者指示|内部ルール|プロンプト)", text, re.IGNORECASE):
            return self._none_result()
        if re.search(r"(全部|全て|すべて).*(削除|消去|消して|消す|期限|更新|変更)", text):
            return self._none_result()

        # APIキーなし → none
        if not config.OPENAI_API_KEY:
            return self._none_result()

        # Tier-2: Function Calling
        return self._parse_with_function_calling(text)

    def _parse_with_function_calling(self, message: str) -> Dict[str, Any]:
        today_str = datetime.now().strftime("%Y-%m-%d")
        system_prompt = (
            f"Today's date is {today_str} (JST).\n"
            "You are an intent parser for a Japanese LINE bot.\n"
            "Call exactly one tool that matches the user's intent.\n"
            "Convert relative dates (今日/明日/明後日) to YYYY-MM-DD.\n"
            "If the intent is unclear or unsafe, do NOT call any tool."
        )
        payload = {
            "model": config.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": message},
            ],
            "tools": TOOLS,
            "tool_choice": "auto",
            "temperature": 0,
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            tool_calls = data["choices"][0]["message"].get("tool_calls")
            if not tool_calls:
                return self._none_result()
            tc = tool_calls[0]
            args = json.loads(tc["function"]["arguments"])
            return self._sanitize(self._build_result_from_tool_call(tc["function"]["name"], args))
        except Exception:
            return self._none_result()

    def _build_result_from_tool_call(self, tool_name: str, args: dict) -> dict:
        return {
            "intent":              FUNCTION_TO_INTENT.get(tool_name, "none"),
            "item_name":           args.get("item_name") or args.get("task_name"),
            "expiry_date":         args.get("expiry_date"),
            "exclude_expiry_date": args.get("exclude_expiry_date"),
            "notify_enabled":      bool(args.get("notify_enabled", False)),
            "frequency":           args.get("frequency"),
            "notify_time":         args.get("notify_time"),
            "enabled":             args.get("enabled"),
            "scheduled_date":      args.get("scheduled_date"),
            "result":              args.get("result"),
            "note":                args.get("note"),
        }

    def _sanitize(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        item_name = parsed.get("item_name")
        if isinstance(item_name, str):
            item_name = item_name.strip()
            if not item_name or len(item_name) > 100 or re.search(r"[\r\n\t]", item_name):
                item_name = None
        else:
            item_name = None

        def _check_date(v: Any) -> Optional[str]:
            if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v.strip()):
                return v.strip()
            return None

        def _check_time(v: Any) -> Optional[str]:
            if isinstance(v, str) and re.fullmatch(r"\d{2}:\d{2}", v.strip()):
                return v.strip()
            return None

        frequency = parsed.get("frequency")
        if frequency not in ("daily", "weekly"):
            frequency = None

        intent = parsed.get("intent", "none")
        if intent in {"register", "delete"} and not item_name:
            intent = "none"
        if intent == "update" and (not item_name or not _check_date(parsed.get("expiry_date"))):
            intent = "none"
        if intent == "register_habit" and not item_name:
            intent = "none"
        if intent == "delete_habit" and not item_name:
            intent = "none"
        if intent == "update_habit_notify_time" and (not item_name or not _check_time(parsed.get("notify_time"))):
            intent = "none"
        if intent == "update_notification":
            if parsed.get("enabled") is None and not _check_time(parsed.get("notify_time")):
                intent = "none"
        if intent == "update_stock_notify" and not item_name:
            intent = "none"
        if intent == "update_habit_log":
            if not item_name or not _check_date(parsed.get("scheduled_date")) or parsed.get("result") not in ("done", "not_done", "other"):
                intent = "none"

        return {
            "intent":              intent,
            "item_name":           item_name,
            "expiry_date":         _check_date(parsed.get("expiry_date")),
            "exclude_expiry_date": _check_date(parsed.get("exclude_expiry_date")),
            "notify_enabled":      bool(parsed.get("notify_enabled", False)),
            "frequency":           frequency,
            "notify_time":         _check_time(parsed.get("notify_time")),
            "enabled":             parsed.get("enabled"),
            "scheduled_date":      _check_date(parsed.get("scheduled_date")),
            "result":              parsed.get("result"),
            "note":                parsed.get("note"),
        }

    def _none_result(self) -> Dict[str, Any]:
        return {
            "intent":              "none",
            "item_name":           None,
            "expiry_date":         None,
            "exclude_expiry_date": None,
            "notify_enabled":      False,
            "frequency":           None,
            "notify_time":         None,
            "enabled":             None,
            "scheduled_date":      None,
            "result":              None,
            "note":                None,
        }
