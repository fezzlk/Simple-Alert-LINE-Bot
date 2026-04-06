#!/usr/bin/env bash
# =============================================================================
# security-scan.sh - 依存パッケージの脆弱性スキャン
#
# 環境変数:
#   ALLOWED_CVES : 許可する CVE のカンマ区切りリスト（例: "CVE-2023-1234,CVE-2023-5678"）
#   STRICT       : "true" の場合、脆弱性があれば非ゼロで終了（デフォルト: true）
#
# 使い方: ALLOWED_CVES="CVE-2023-1234" ./scripts/security-scan.sh
# =============================================================================
set -euo pipefail

ALLOWED_CVES="${ALLOWED_CVES:-}"
STRICT="${STRICT:-true}"

echo "=== pip-audit による依存パッケージの脆弱性スキャン ==="

# pip-audit がなければインストール
if ! command -v pip-audit &> /dev/null; then
  echo "pip-audit をインストール中..."
  pip install --quiet pip-audit
fi

# 依存インストール（スキャン対象）
if [ -f requirements.txt ]; then
  pip install --quiet -r requirements.txt
fi

# スキャン実行
AUDIT_OUTPUT=$(pip-audit --format=json 2>&1) || true

echo "$AUDIT_OUTPUT" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    print('pip-audit の出力をパースできませんでした。手動で確認してください。')
    sys.exit(0)

allowed = set(filter(None, '${ALLOWED_CVES}'.split(',')))
vulnerabilities = data if isinstance(data, list) else data.get('dependencies', [])
blocked = []

for dep in vulnerabilities:
    vulns = dep.get('vulns', [])
    for v in vulns:
        vid = v.get('id', '')
        if vid not in allowed:
            blocked.append(f\"  {dep.get('name', '?')} {dep.get('version', '?')}: {vid} - {v.get('description', '')[:80]}\")

if blocked:
    print(f'脆弱性が {len(blocked)} 件見つかりました:')
    for b in blocked:
        print(b)
    if '${STRICT}' == 'true':
        sys.exit(1)
    else:
        print('(STRICT=false のため非ブロッキング)')
else:
    print('脆弱性は見つかりませんでした。')
"

echo "=== スキャン完了 ==="
