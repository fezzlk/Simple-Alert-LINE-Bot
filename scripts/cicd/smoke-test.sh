#!/usr/bin/env bash
# =============================================================================
# smoke-test.sh - デプロイ後のヘルスチェック
#
# 引数:
#   $1 : サービスの URL（例: https://my-service-xxx.run.app）
#
# 環境変数:
#   HEALTH_PATH : ヘルスチェックパス（デフォルト: /_api/v1/health）
#   MAX_RETRIES : 最大リトライ回数（デフォルト: 5）
#   RETRY_WAIT  : リトライ間隔（秒）（デフォルト: 5）
#
# 使い方: ./scripts/smoke-test.sh https://my-service.run.app
# =============================================================================
set -euo pipefail

SERVICE_URL="${1:-}"
HEALTH_PATH="${HEALTH_PATH:-/_api/v1/health}"
MAX_RETRIES="${MAX_RETRIES:-5}"
RETRY_WAIT="${RETRY_WAIT:-5}"

if [ -z "$SERVICE_URL" ]; then
  echo "エラー: サービス URL を第1引数で指定してください。"
  echo "使い方: $0 https://my-service.run.app"
  exit 1
fi

# 末尾スラッシュを除去
SERVICE_URL="${SERVICE_URL%/}"
ENDPOINT="${SERVICE_URL}${HEALTH_PATH}"

echo "=== スモークテスト: ${ENDPOINT} ==="

for i in $(seq 1 "$MAX_RETRIES"); do
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 10 "$ENDPOINT" || echo "000")

  if [ "$STATUS" = "200" ]; then
    echo "ヘルスチェック成功（試行 ${i}/${MAX_RETRIES}）"
    echo "=== スモークテスト完了 ==="
    exit 0
  fi

  echo "試行 ${i}/${MAX_RETRIES}: HTTP ${STATUS}、${RETRY_WAIT}秒後にリトライ..."
  sleep "$RETRY_WAIT"
done

echo "エラー: ${MAX_RETRIES} 回試行しましたがヘルスチェックに失敗しました。"
exit 1
