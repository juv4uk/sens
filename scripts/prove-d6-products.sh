#!/usr/bin/env bash
# Один точковий тест: два SENS-закони та негатив асиметрії/нерівних довжин.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
law="tests/semantic/d6-products-zip-unzip-laws.lisp"
bad="tests/semantic/d6-products-zip-unzip-mismatch.lisp"
reproduce="bash scripts/prove-d6-products.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'UNVERIFIED test_id=d6-zip-unzip layer=eval expected=native-executor actual=missing path=%s reproduce=%q\n' "$cli" "$reproduce" >&2
  exit 1
fi
actual="$("$cli" "$law" 2> /tmp/d6-zip-unzip-law-error-$$)" || {
  printf 'REGRESSION test_id=d6-zip-unzip layer=eval expected=(1 1 0) actual=execution-error fixture=%s reproduce=%q\n' "$law" "$reproduce" >&2
  cat /tmp/d6-zip-unzip-law-error-$$ >&2
  rm -f /tmp/d6-zip-unzip-law-error-$$
  exit 1
}
rm -f /tmp/d6-zip-unzip-law-error-$$
if [[ "$actual" != '(1 1 0)' ]]; then
  printf 'REGRESSION test_id=d6-zip-unzip layer=eval expected=(1 1 0) actual=%q first_diff=law-vector fixture=%s reproduce=%q\n' "$actual" "$law" "$reproduce" >&2
  exit 1
fi
if "$cli" "$bad" >/tmp/d6-zip-unzip-negative-$$ 2>&1; then
  printf 'REGRESSION test_id=d6-zip-unzip-negative layer=eval expected=reject-unequal-length actual=accepted fixture=%s reproduce=%q\n' "$bad" "$reproduce" >&2
  rm -f /tmp/d6-zip-unzip-negative-$$
  exit 1
fi
printf 'SENS_D6_ZIP_UNZIP_PASS test_id=d6-zip-unzip expected=(1 1 0) unequal-length=rejected semantic_authority=SENS\n'
sha256sum "$law" "$bad"
rm -f /tmp/d6-zip-unzip-negative-$$
