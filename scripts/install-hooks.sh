#!/usr/bin/env bash
# Запустити один раз на клон: активує версіоновані Git hooks.
# Інсталятор не переписує source-файли й не запускає міграційні скрипти.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
git config core.hooksPath githooks
chmod +x githooks/pre-commit githooks/pre-push githooks/commit-msg scripts/check-bilingual-docs 2>/dev/null || true
echo "Готово: core.hooksPath -> githooks; джерела залишено без змін"
