def stock_added(item_name: str) -> str:
    return f'"{item_name}" を追加しました'


def stock_updated() -> str:
    return '更新しました'


def stock_deleted() -> str:
    return 'アイテムを削除しました'


def stock_deleted_permanently() -> str:
    return 'アイテムを完全削除しました'


def stock_restored() -> str:
    return 'アイテムを復元しました'


def logged_out() -> str:
    return 'ログアウトしました'


def register_welcome(user_name: str) -> str:
    return f'Hi, {user_name}! Welcome to SALB!'
