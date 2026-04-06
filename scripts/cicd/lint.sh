#!/usr/bin/env bash
# =============================================================================
# lint.sh - Python コードの静的解析
#
# 使い方: ./scripts/lint.sh [対象ディレクトリ]
# デフォルトはカレントディレクトリ
# =============================================================================
set -euo pipefail

TARGET="${1:-.}"

echo "=== ruff によるリント実行 ==="

# ruff がなければインストール
if ! command -v ruff &> /dev/null; then
  echo "ruff をインストール中..."
  pip install --quiet ruff
fi

# ruff.toml があればそれを使う、なければデフォルト設定
if [ -f "ruff.toml" ]; then
  ruff check "$TARGET" --config ruff.toml
else
  ruff check "$TARGET"
fi

echo "=== リント完了（エラーなし） ==="
