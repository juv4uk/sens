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
for kind in cond eq; do
  id="retired-d3-${kind}"
  pos="tests/semantic/${id}-law.bits"
  neg="tests/semantic/${id}-mutant.bits"
  python3 - "$kind" "$pos" "$neg" "$tmp" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "scripts")
from sens_t5_codec import parse_words, encode_projection, decode_bytes

kind, pos, neg, target = sys.argv[1:]
good = parse_words(Path(pos).read_text(encoding="ascii"))
bad = parse_words(Path(neg).read_text(encoding="ascii"))
if len(good) != len(bad):
    raise SystemExit("T5_TRANSPORT_RED: exact word count mismatch")
diff = [i for i, (a, b) in enumerate(zip(good, bad)) if a != b]
if diff != [{"cond": 4, "eq": 16}[kind]]:
    raise SystemExit("T5_TRANSPORT_RED: mutated unexpected exact-domain word")
if good[diff[0]] != "0" or bad[diff[0]] != "1":
    raise SystemExit("T5_TRANSPORT_RED: expected exactly one D1 bit change")
for role, words in (("law", good), ("mutant", bad)):
    physical = encode_projection(" ".join(words))
    if decode_bytes(physical) != words:
        raise SystemExit("T5_TRANSPORT_RED: physical round-trip changed exact widths")
    Path(target, f"{kind}-{role}.sens").write_bytes(physical)
print(f"SENS_T5_PHYSICAL id={kind} words={len(good)} width_bits={sum(map(len, good))} mutation=D1:0-to-1 semantic_pass=NOT_INFERRED")
PY
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
