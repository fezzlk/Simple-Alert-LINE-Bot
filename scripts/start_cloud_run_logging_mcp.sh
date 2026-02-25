#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_REPO_DIR="${MCP_REPO_DIR:-${SCRIPT_DIR}/../../cloud-run-logging-mcp}"
MCP_IMAGE="${MCP_IMAGE:-cloud-run-logging-mcp:local}"
MCP_KEY_PATH="${MCP_KEY_PATH:-/Users/yusuketakizawa/gcp-service-account-key/simple-alert-line-bot-f15d92527d17.json}"

wait_for_docker() {
  if docker info >/dev/null 2>&1; then
    return 0
  fi

  if [[ "$(uname)" == "Darwin" ]]; then
    open -ga Docker || true
  fi

  local retries=90
  for ((i = 1; i <= retries; i++)); do
    if docker info >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  echo "Docker daemon is not ready." >&2
  return 1
}

ensure_image() {
  if docker image inspect "${MCP_IMAGE}" >/dev/null 2>&1; then
    return 0
  fi
  if [[ ! -d "${MCP_REPO_DIR}" ]]; then
    echo "MCP repo not found: ${MCP_REPO_DIR}" >&2
    return 1
  fi
  docker build -t "${MCP_IMAGE}" "${MCP_REPO_DIR}" >/dev/null
}

ensure_key() {
  if [[ ! -f "${MCP_KEY_PATH}" ]]; then
    echo "Service account key not found: ${MCP_KEY_PATH}" >&2
    return 1
  fi
}

wait_for_docker
ensure_image
ensure_key

exec docker run --rm -i \
  -e GCP_SA_JSON_PATH=/secrets/key.json \
  -v "${MCP_KEY_PATH}:/secrets/key.json:ro" \
  "${MCP_IMAGE}"
