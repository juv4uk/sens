#!/usr/bin/env bash
# Запустити один раз на клон: активує версіоновані pre-commit та
# commit-msg hooks (перевірка українського тексту документів і комітів).
# CI також викликає цей скрипт перед охороною D1–D11 — тут же host_debt→0.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
git config core.hooksPath githooks
chmod +x githooks/pre-commit githooks/pre-push githooks/commit-msg scripts/check-bilingual-docs 2>/dev/null || true
if [[ -x scripts/ensure-host-debt0.sh ]] || [[ -f scripts/ensure-host-debt0.sh ]]; then
  bash scripts/ensure-host-debt0.sh
fi
echo "Готово: core.hooksPath -> githooks; host_debt перевірено"
