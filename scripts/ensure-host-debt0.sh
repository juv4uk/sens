#!/usr/bin/env bash
# विन्यास: host_debt → 0 before language-stays-in-sens
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
if [[ -f scripts/apply-host-debt0.py ]]; then
  exec python3 scripts/apply-host-debt0.py
fi
exec python3 knowledge/d11/restore/patch-host-debt-live.py
