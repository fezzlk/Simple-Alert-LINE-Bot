import json
import logging
import re
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

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
                    "item_name":          {"type": "string"},
                    "expiry_date":        {"type": ["string", "null"]},
                    "notify_days_before": {"type": ["integer", "null"], "description": "何日前から通知するか。null = 常に通知、省略や不明もnull。"},
                },
                "required": ["item_name", "expiry_date", "notify_days_before"],
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
            "description": "在庫・タスクを削除する。expiry_dateは完全一致フィルタ（M/D・M月D日・相対日付を今日の日付を基準にYYYY-MM-DDに変換）、exclude_expiry_dateは除外フィルタ（「以外を削除」）。",
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
            "description": "習慣タスクを登録する。頻度はdaily（毎日）、every_other_day（1日おき）、every_two_days（2日おき）、weekly（毎週）、monthly（毎月）から選択。頻度が明示されていない場合はdailyをデフォルトとする。notify_timeはHH:MM形式、不明ならnull。weeklyの場合はnotify_day_of_week（0=月〜6=日）、monthlyの場合はnotify_day_of_month（1〜31）を指定。それ以外はどちらもnull。",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name":           {"type": "string"},
                    "frequency":           {"type": "string", "enum": ["daily", "every_other_day", "every_two_days", "weekly", "monthly"]},
                    "notify_time":         {"type": ["string", "null"]},
                    "notify_day_of_week":  {"type": ["integer", "null"], "description": "週次の場合の曜日（0=月〜6=日）。weekly以外はnull。"},
                    "notify_day_of_month": {"type": ["integer", "null"], "description": "月次の場合の日（1〜31）。monthly以外はnull。"},
                },
                "required": ["item_name", "frequency", "notify_time", "notify_day_of_week", "notify_day_of_month"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_habit_frequency",
            "description": "習慣タスクの頻度を変更する。頻度はdaily/every_other_day/every_two_days/weekly/monthlyから選択。weekly→notify_day_of_week（0〜6）、monthly→notify_day_of_month（1〜31）を指定。",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name":           {"type": "string"},
                    "frequency":           {"type": "string", "enum": ["daily", "every_other_day", "every_two_days", "weekly", "monthly"]},
                    "notify_day_of_week":  {"type": ["integer", "null"]},
                    "notify_day_of_month": {"type": ["integer", "null"]},
                },
                "required": ["task_name", "frequency", "notify_day_of_week", "notify_day_of_month"],
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
            "description": "登録済みアイテムの通知設定を変更する。何日前から通知するかを指定する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name":          {"type": "string"},
                    "notify_days_before": {"type": ["integer", "null"], "description": "何日前から通知するか。null = 常に通知、省略や不明もnull。"},
                },
                "required": ["item_name", "notify_days_before"],
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
    "update_habit_frequency":    "update_habit_frequency",
    "update_notification_setting": "update_notification",
    "update_stock_notify":       "update_stock_notify",
    "update_habit_log":          "update_habit_log",
}


class LineIntentParserService:
    # ゼロ幅・不可視 Unicode 文字（フィルタバイパス対策）
    _INVISIBLE_RE = re.compile(
        "[\u200b\u200c\u200d\u200e\u200f"   # ZWS, ZWNJ, ZWJ, LRM, RLM
        "\u2060\u2061\u2062\u2063\u2064"     # word joiner, function application, etc.
        "\ufeff\ufffe"                        # BOM, non-character
        "\u00ad"                              # soft hyphen
        "\u034f"                              # combining grapheme joiner
        "\u061c"                              # Arabic letter mark
        "\u115f\u1160"                        # Hangul filler
        "\u17b4\u17b5"                        # Khmer vowel inherent
        "\u180e"                              # Mongolian vowel separator
        "\u2000-\u200a"                       # various spaces
        "\u202a-\u202e"                       # bidi controls
        "\u2066-\u2069"                       # bidi isolates
        "\ufff9-\ufffb"                       # interlinear annotations
        "]"
    )

    # ASCII ホモグリフ（キリル文字・ギリシャ文字で英字に見える文字）→ ASCII
    _HOMOGLYPH_MAP = str.maketrans({
        "\u0410": "A", "\u0430": "a",  # Cyrillic А/а
        "\u0412": "B", "\u0432": "b",  # Cyrillic В/в (looks like B)
        "\u0421": "C", "\u0441": "c",  # Cyrillic С/с
        "\u0415": "E", "\u0435": "e",  # Cyrillic Е/е
        "\u041d": "H", "\u043d": "h",  # Cyrillic Н/н
        "\u041a": "K", "\u043a": "k",  # Cyrillic К/к
        "\u041c": "M", "\u043c": "m",  # Cyrillic М/м
        "\u041e": "O", "\u043e": "o",  # Cyrillic О/о
        "\u0420": "P", "\u0440": "p",  # Cyrillic Р/р
        "\u0422": "T", "\u0442": "t",  # Cyrillic Т/т
        "\u0425": "X", "\u0445": "x",  # Cyrillic Х/х
        "\u0423": "Y", "\u0443": "y",  # Cyrillic У/у
        "\u0392": "B",                  # Greek Β
        "\u03b2": "b",                  # Greek β (approximation)
        "\u0395": "E", "\u03b5": "e",  # Greek Ε/ε
        "\u0397": "H", "\u03b7": "h",  # Greek Η/η
        "\u039a": "K", "\u03ba": "k",  # Greek Κ/κ
        "\u039c": "M",                  # Greek Μ
        "\u039d": "N",                  # Greek Ν
        "\u039f": "O", "\u03bf": "o",  # Greek Ο/ο
        "\u03a1": "P", "\u03c1": "p",  # Greek Ρ/ρ
        "\u03a4": "T", "\u03c4": "t",  # Greek Τ/τ
        "\u03a7": "X", "\u03c7": "x",  # Greek Χ/χ
        "\u0405": "S", "\u0455": "s",  # Cyrillic Ѕ/ѕ
        "\u0406": "I", "\u0456": "i",  # Cyrillic І/і
        "\u0408": "J", "\u0458": "j",  # Cyrillic Ј/ј
    })

    @classmethod
    def _normalize(cls, text: str) -> str:
        """全角英数字・記号を半角に正規化し、不可視文字・ホモグリフを除去する。"""
        # ゼロ幅・不可視文字を除去
        text = cls._INVISIBLE_RE.sub("", text)
        # ホモグリフを ASCII に正規化
        text = text.translate(cls._HOMOGLYPH_MAP)
        # 全角英数字・記号 (！〜) → 半角
        result = []
        for ch in text:
            cp = ord(ch)
            if 0xFF01 <= cp <= 0xFF5E:
                result.append(chr(cp - 0xFEE0))
            else:
                result.append(ch)
        return "".join(result)

    # アイテム名インジェクション検出パターン（英語 + 日本語 + 構造攻撃）
    _ITEM_INJECTION_RE = re.compile(
        r"("
        # 英語キーワード
        r"ignore|system|prompt|instruction|role|assistant|forget|disregard"
        r"|override|pretend|act\s+as|you\s+are|new\s+instructions|bypass"
        r"|jailbreak|do\s+not|don'?t|reveal|secret|password|admin"
        # 日本語キーワード
        r"|指示を?無視|無視して|プロンプト|内部ルール|開発者指示"
        r"|システムプロンプト|ロールを|ルールを|命令を|忘れて|新しい指示"
        r"|ふりをして|なりきって|設定を?変更|制約を?解除|制限を?解除"
        r"|あなたは今から|以下の指示|以下は新しい"
        # 構造攻撃（ロールタグ・デリミタ偽装）
        r"|\[system\]|\[user\]|\[assistant\]|<\|system\|>|<\|user\|>"
        r"|```|---\n|===\n"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def _sanitize_item_names(cls, names: list) -> list:
        """既存アイテム名リストをサニタイズ（インジェクション対策）。"""
        sanitized = []
        for name in names:
            if not isinstance(name, str):
                continue
            # 不可視文字・ホモグリフを正規化してからチェック
            clean = cls._INVISIBLE_RE.sub("", name)
            clean = clean.translate(cls._HOMOGLYPH_MAP)
            clean = re.sub(r"[\r\n\t]", "", clean).strip()
            # 長すぎるものは切り捨て
            if not clean or len(clean) > 50:
                continue
            # デリミタインジェクション対策: 括弧・カンマ・引用符を含むものを除外
            if re.search(r"[\[\]{}()\",;\\]", clean):
                continue
            # prompt injection 的なパターンを除外
            if cls._ITEM_INJECTION_RE.search(clean):
                continue
            sanitized.append(clean)
        # 最大30件に制限
        return sanitized[:30]

    def parse(self, message: str, existing_items: Optional[list] = None, openai_api_key: str = None) -> Dict[str, Any]:
        text = self._normalize((message or "").strip())
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

        # Tier-1B: メッセージ長制限（過剰に長い入力は拒否）
        if len(text) > 500:
            return self._none_result()

        # Tier-1B: セキュリティフィルタ
        if re.search(
            r"(ignore|system\s*prompt|forget\s+(all|previous|your)|disregard"
            r"|override|pretend|act\s+as|you\s+are\s+now|new\s+instructions"
            r"|jailbreak|bypass|do\s+anything\s+now|DAN"
            r"|開発者指示|内部ルール|プロンプト|指示を?無視|無視して"
            r"|忘れて|新しい指示|ふりをして|なりきって|制約を?解除|制限を?解除"
            r"|あなたは今から|以下の指示|以下は新しい|設定を?変更して"
            r"|\[system\]|\[INST\]|<\|system\|>)",
            text, re.IGNORECASE,
        ):
            return self._none_result()
        if re.search(r"(全部|全て|すべて).*(削除|消去|消して|消す|期限|更新|変更)", text):
            return self._none_result()

        # Resolve API key: per-user key takes priority over global config
        api_key = openai_api_key or config.OPENAI_API_KEY

        # APIキーなし → none
        if not api_key:
            return self._none_result()

        # Tier-2: Function Calling
        safe_items = self._sanitize_item_names(existing_items or [])
        return self._parse_with_function_calling(text, safe_items, api_key=api_key)

    def _parse_with_function_calling(self, message: str, existing_items: list = None, api_key: str = None) -> Dict[str, Any]:
        today_str = datetime.now().strftime("%Y-%m-%d")
        system_prompt = (
            f"Today's date is {today_str} (JST).\n"
            "You are an intent parser for a Japanese LINE bot.\n"
            "Call exactly one tool that matches the user's intent.\n"
            "Convert all date expressions to YYYY-MM-DD format:\n"
            "  - Relative: 今日/明日/明後日/昨日\n"
            "  - M/D or M月D日 format: use the most recent occurrence (past or future based on context)\n"
            "  - When M/D is in the past (e.g. 2/27 and today is 3/4), interpret as the same year unless context implies otherwise\n"
            "If the intent is unclear or unsafe, do NOT call any tool."
        )
        if existing_items:
            items_str = ", ".join(existing_items)
            system_prompt += (
                f"\n\nThe user's registered items/tasks are: [{items_str}].\n"
                "When the user mentions an item, match it to one of these names if possible. "
                "Use the exact registered name as item_name/task_name."
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
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            tool_calls = data["choices"][0]["message"].get("tool_calls")
            if not tool_calls:
                logger.warning("OpenAI returned no tool_calls for message: %s | response: %s", message, json.dumps(data, ensure_ascii=False))
                return self._none_result()
            tc = tool_calls[0]
            args = json.loads(tc["function"]["arguments"])
            logger.info("OpenAI tool_call: %s args=%s for message: %s", tc["function"]["name"], json.dumps(args, ensure_ascii=False), message)
            return self._sanitize(self._build_result_from_tool_call(tc["function"]["name"], args))
        except Exception as e:
            logger.exception("OpenAI API call failed for message: %s", message)
            return self._none_result()

    def _build_result_from_tool_call(self, tool_name: str, args: dict) -> dict:
        return {
            "intent":              FUNCTION_TO_INTENT.get(tool_name, "none"),
            "item_name":           args.get("item_name") or args.get("task_name"),
            "expiry_date":         args.get("expiry_date"),
            "exclude_expiry_date": args.get("exclude_expiry_date"),
            "notify_days_before":  args.get("notify_days_before"),
            "frequency":           args.get("frequency"),
            "notify_time":         args.get("notify_time"),
            "notify_day_of_week":  args.get("notify_day_of_week"),
            "notify_day_of_month": args.get("notify_day_of_month"),
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
        if frequency not in ("daily", "every_other_day", "every_two_days", "weekly", "monthly"):
            frequency = None

        dow = parsed.get("notify_day_of_week")
        notify_day_of_week = dow if isinstance(dow, int) and 0 <= dow <= 6 else None

        dom = parsed.get("notify_day_of_month")
        notify_day_of_month = dom if isinstance(dom, int) and 1 <= dom <= 31 else None

        intent = parsed.get("intent", "none")
        if intent in {"register", "delete"} and not item_name:
            intent = "none"
        if intent == "update" and (not item_name or not _check_date(parsed.get("expiry_date"))):
            intent = "none"
        if intent == "register_habit" and not item_name:
            intent = "none"
        if intent == "register_habit" and frequency == "weekly" and notify_day_of_week is None:
            intent = "none"
        if intent == "register_habit" and frequency == "monthly" and notify_day_of_month is None:
            intent = "none"
        if intent == "delete_habit" and not item_name:
            intent = "none"
        if intent == "update_habit_notify_time" and (not item_name or not _check_time(parsed.get("notify_time"))):
            intent = "none"
        if intent == "update_habit_frequency" and not item_name:
            intent = "none"
        if intent == "update_habit_frequency" and frequency == "weekly" and notify_day_of_week is None:
            intent = "none"
        if intent == "update_habit_frequency" and frequency == "monthly" and notify_day_of_month is None:
            intent = "none"
        if intent == "update_notification":
            if parsed.get("enabled") is None and not _check_time(parsed.get("notify_time")):
                intent = "none"
        if intent == "update_stock_notify" and not item_name:
            intent = "none"
        if intent == "update_habit_log":
            if not item_name or not _check_date(parsed.get("scheduled_date")) or parsed.get("result") not in ("done", "not_done", "other"):
                intent = "none"

        ndb = parsed.get("notify_days_before")
        if isinstance(ndb, int) and ndb >= 0:
            notify_days_before = ndb
        else:
            notify_days_before = None

        # note フィールドのサニタイズ（LLM出力をそのまま信頼しない）
        note = parsed.get("note")
        if isinstance(note, str):
            note = re.sub(r"[\r\n\t]", " ", note).strip()
            if len(note) > 200:
                note = note[:200]
            if not note:
                note = None
        else:
            note = None

        return {
            "intent":              intent,
            "item_name":           item_name,
            "expiry_date":         _check_date(parsed.get("expiry_date")),
            "exclude_expiry_date": _check_date(parsed.get("exclude_expiry_date")),
            "notify_days_before":  notify_days_before,
            "frequency":           frequency,
            "notify_time":         _check_time(parsed.get("notify_time")),
            "notify_day_of_week":  notify_day_of_week,
            "notify_day_of_month": notify_day_of_month,
            "enabled":             parsed.get("enabled"),
            "scheduled_date":      _check_date(parsed.get("scheduled_date")),
            "result":              parsed.get("result"),
            "note":                note,
        }

    def _none_result(self) -> Dict[str, Any]:
        return {
            "intent":              "none",
            "item_name":           None,
            "expiry_date":         None,
            "exclude_expiry_date": None,
            "notify_days_before":  None,
            "frequency":           None,
            "notify_time":         None,
            "notify_day_of_week":  None,
            "notify_day_of_month": None,
            "enabled":             None,
            "scheduled_date":      None,
            "result":              None,
            "note":                None,
        }
