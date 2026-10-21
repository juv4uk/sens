#!/usr/bin/env bash
# Запустити один раз на клон: активує версіоновані pre-commit та
# commit-msg hooks (перевірка українського тексту документів і комітів).
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
git config core.hooksPath githooks
chmod +x githooks/pre-commit githooks/pre-push githooks/commit-msg scripts/check-bilingual-docs
echo "Готово: core.hooksPath -> githooks (pre-commit, pre-push і commit-msg активовані)"
