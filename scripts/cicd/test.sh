#!/usr/bin/env bash
# =============================================================================
# test.sh - pytest 実行 + カバレッジ閾値チェック
#
# 環境変数:
#   MIN_COVERAGE : 最低カバレッジ率（デフォルト: 60）
#   TEST_DIR     : テスト対象ディレクトリ（デフォルト: src）
#   COV_DIR      : カバレッジ計測対象（デフォルト: src）
#
# 使い方: MIN_COVERAGE=80 ./scripts/test.sh
# =============================================================================
set -euo pipefail

MIN_COVERAGE="${MIN_COVERAGE:-60}"
TEST_DIR="${TEST_DIR:-src}"
COV_DIR="${COV_DIR:-src}"

echo "=== テスト実行（カバレッジ閾値: ${MIN_COVERAGE}%） ==="

# 依存インストール（CI 環境用）
if [ -f requirements.txt ]; then
  pip install --quiet -r requirements.txt
fi
if [ -f requirements.dev.txt ]; then
  pip install --quiet -r requirements.dev.txt
fi

# pytest-cov がなければインストール
pip install --quiet pytest-cov

# テスト実行
python -m pytest "$TEST_DIR" \
  --cov="$COV_DIR" \
  --cov-report=term-missing \
  --cov-fail-under="$MIN_COVERAGE" \
  --tb=short \
  -q

echo "=== テスト完了（カバレッジ ${MIN_COVERAGE}% 以上を確認） ==="
