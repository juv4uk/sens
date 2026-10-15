#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: manual native D3 controls, using the existing SENS
# self-verdicts and exact physical T5. No new automatic CI workflow.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=retired-d3-laws layer=eval reason=executor-missing path=%s reproduce=%q\n' \
    "$cli" 'cargo build --locked -p sens-cli --bin sens' >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf 'NATIVE_SENS_EXECUTOR path=%s version=%s sha256=' "$cli" "$("$cli" --version)"
sha256sum "$cli"
# Physical .sens authorship is Zig only; the helper validates D1 mutation position.
python3 scripts/prepare_h2_zig_t5.py d3 "$tmp"
for kind in cond eq; do
  id="retired-d3-${kind}"
  pos="tests/semantic/${id}-law.bits"
  neg="tests/semantic/${id}-mutant.bits"
  printf 'NATIVE_SENS_INPUT id=%s reproduce=%q\n' "$id" "bash scripts/prove-retired-d3-laws.sh $cli"
  sha256sum "$pos" "$neg" "$tmp/$kind-law.sens" "$tmp/$kind-mutant.sens"
  expected="$tmp/$kind.expected"
  actual="$tmp/$kind.actual"
  printf '1\n' > "$expected"
  if ! "$cli" "$tmp/$kind-law.sens" > "$actual" 2> "$tmp/$kind-law.stderr"; then
    printf 'REGRESSION test_id=%s layer=eval expected=D1:1 actual=execution-error fixture=%s first_diff=unknown\n' "$id" "$pos" >&2
    cat "$tmp/$kind-law.stderr" >&2
    sha256sum "$expected" "$actual" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_VERDICT id=%s expected_sha256=' "$id"
  sha256sum "$expected"
  printf 'NATIVE_SENS_VERDICT id=%s actual_sha256=' "$id"
  sha256sum "$actual"
  if ! cmp -s "$expected" "$actual"; then
    printf 'REGRESSION test_id=%s layer=eval expected=D1:1 actual=wrong-verdict fixture=%s first_diff=0\n' "$id" "$pos" >&2
    exit 1
  fi
  if "$cli" "$tmp/$kind-mutant.sens" > "$tmp/$kind-mutant.actual" 2> "$tmp/$kind-mutant.stderr"; then
    printf 'REGRESSION test_id=%s-mutant layer=eval expected=D1-noncallable actual=accepted fixture=%s first_diff=mutated-D1\n' "$id" "$neg" >&2
    sha256sum "$tmp/$kind-mutant.actual" >&2
    exit 1
  fi
  if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$tmp/$kind-mutant.stderr"; then
    printf 'UNINFORMATIVE-NEGATIVE test_id=%s-mutant layer=eval expected=D1-noncallable actual=unclassified-error fixture=%s\n' "$id" "$neg" >&2
    cat "$tmp/$kind-mutant.stderr" >&2
    sha256sum "$tmp/$kind-mutant.stderr" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_NEGATIVE id=%s-mutant expected=D1-noncallable stderr_sha256=' "$id"
  sha256sum "$tmp/$kind-mutant.stderr"
  printf 'NATIVE_SENS_PASS id=%s semantic_authority=binary-SENS mutant=D1-noncallable\n' "$id"
done
