#!/usr/bin/env bash
# #4449 read-only canonical triplet gate; NO generation, NO source rewriting.
#
# 'uk render exited zero' never certifies semantic or byte parity. A PASS
# requires committed same-stem Ukrainian source, T5, and view, all checked
# by the existing bounded source->T5->view + reverse Ukrainian validator.
# Unsupported historical/English/binder fixtures explicitly BLOCK (not skip).
#
# Usage:
#   scripts/check-triple-projection.sh
#   scripts/check-triple-projection.sh --fixture tests/fixtures/migration-d1-cond-cohort/branch.lisp
#   scripts/check-triple-projection.sh --root /tmp/fixture --fixture branch.lisp
set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK_ROOT="$SCRIPT_ROOT"
FIXTURES=()
if [ "$#" -eq 0 ]; then
  FIXTURES=(
    tests/fixtures/core1-third-domain-canary/third.lisp
    tests/fixtures/migration-d1-cond-cohort/branch.lisp
    tests/fixtures/migration-d4-selector-cohort/caar.lisp
    tests/fixtures/migration-multiform-cohort/two-forms.lisp
  )
else
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --fixture)
        if [ "$#" -lt 2 ]; then echo "BLOCKED: --fixture needs a path" >&2; exit 2; fi
        FIXTURES+=("$2"); shift 2 ;;
      --root)
        if [ "$#" -lt 2 ]; then echo "BLOCKED: --root needs a path" >&2; exit 2; fi
        CHECK_ROOT="$2"; shift 2 ;;
      *)
        echo "BLOCKED: unsupported argument $1" >&2; exit 2 ;;
    esac
  done
  if [ "${#FIXTURES[@]}" -eq 0 ]; then
    echo "BLOCKED: no explicit fixtures to verify" >&2
    exit 2
  fi
fi

if [ ! -d "$CHECK_ROOT" ]; then
  echo "BLOCKED: source root missing: $CHECK_ROOT" >&2
  exit 2
fi

fail=0
n=0
for relative in "${FIXTURES[@]}"; do
  # Only relative, ordinary .lisp paths; no traversal or symlink escape.
  case "/$relative/" in
    *"/../"*|*"/./"*|*'//'*) echo "BLOCKED: unsafe path $relative" >&2; fail=1; continue ;;
  esac
  if [[ "$relative" = /* || "$relative" = -* || "$relative" = *'\'* ||
        "$relative" != *.lisp || "$relative" = ./* ]]; then
    echo "BLOCKED: invalid fixture path $relative" >&2
    fail=1
    continue
  fi
  source="$CHECK_ROOT/$relative"
  physical="${source%.lisp}.sens"
  view="${source%.lisp}"
  n=$((n+1))
  # Open these ACTUAL committed files: no temporary generated stand-ins.
  if proof="$(python3 "$SCRIPT_ROOT/scripts/verify_uk_t5_triplet.py" \
      --lisp "$source" --sens "$physical" --view "$view" 2>&1)"; then
    printf 'PASS %-64s uk=T5=view (bounded); release=NOT_ADMITTED\n' "$relative"
  else
    echo "BLOCKED: $relative: $proof" >&2
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "checked $n fixture(s); result=BLOCKED (no semantic/release admission)"
  exit 2
fi
echo "checked $n fixture(s); result=PASS (bounded source/physical/view ONLY)"
