#!/usr/bin/env bash
# सूत्रधार: host_debt → 0 before language-stays-in-sens
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
exec python3 knowledge/d11/restore/patch-host-debt-live.py
