#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: physical T5 and native SENS judge four exact D4
# lambda substrate laws; a single bit flips the first D3 EQ condition.
# This is NOT evidence that the entire named meta-evaluator is self-hosted.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -gt 1 ]]; then
  echo 'usage: bash scripts/prove-meta-eval-mutual-d4.sh [path-to-native-sens]' >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
id=meta-eval-mutual-d4
law=tests/semantic/meta-eval-mutual-d4-law.bits
mutant=tests/semantic/meta-eval-mutual-d4-mutant.bits
reproduce="bash scripts/prove-meta-eval-mutual-d4.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=eval actual=missing-executor path=%s reproduce=%q\n' "$id" "$cli" "$reproduce" >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
python3 - "$law" "$mutant" "$tmp" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "scripts")
from sens_t5_t5m_codec import parse_words, encode_projection, decode_bytes

law_path, mutant_path, directory = map(Path, sys.argv[1:])
lines = law_path.read_text(encoding="ascii").splitlines()
if len(lines) != 4 or any(not line.strip() for line in lines):
    raise SystemExit("T5_TRANSPORT_RED: expected exactly four D4 lambda self-verdict forms")
all_words = [parse_words(line) for line in lines]
bad = parse_words(mutant_path.read_text(encoding="ascii"))
good = all_words[0]
if len(good) != len(bad):
    raise SystemExit("T5_TRANSPORT_RED: mutant changed D2 framing")
differences = [(i, a, b) for i, (a, b) in enumerate(zip(good, bad)) if a != b]
if differences != [(41, "1", "0")]:
    raise SystemExit(f"T5_TRANSPORT_RED: expected only one D1 change in first argument, got {differences!r}")
# Framing check only: the mutated bit must be the D1 datum under D3 QUOTE.
if good[39:43] != ["001", "00", "1", "01"] or bad[39:43] != ["001", "00", "0", "01"]:
    raise SystemExit("T5_TRANSPORT_RED: changed a word outside the quoted D1 argument")
for index, words in enumerate(all_words, 1):
    physical = encode_projection(" ".join(words))
    if decode_bytes(physical) != words:
        raise SystemExit(f"T5_TRANSPORT_RED: width loss at form={index}")
    (directory / f"positive-{index}.sens").write_bytes(physical)
    print(f"META_D4_T5_PROJECTION form={index} words={len(words)} bits={sum(map(len,words))} bytes={len(physical)} semantic_pass=NOT_INFERRED")
physical = encode_projection(" ".join(bad))
if decode_bytes(physical) != bad:
    raise SystemExit("T5_TRANSPORT_RED: mutant width loss")
(directory / "mutant.sens").write_bytes(physical)
print(f"META_D4_T5_MUTANT changed_word=41 before=D1:1 after=D1:0 bytes={len(physical)} semantic_pass=NOT_INFERRED")
PY

printf 'NATIVE_SENS_EXECUTOR test_id=%s path=%s version=%s\n' "$id" "$cli" "$("$cli" --version)"
printf 'NATIVE_SENS_REPLAY test_id=%s reproduce=%q\n' "$id" "$reproduce"
sha256sum "$cli" "$law" "$mutant" "$tmp"/positive-{1,2,3,4}.sens "$tmp/mutant.sens"
printf '1\n' > "$tmp/expected"
for index in 1 2 3 4; do
  input="$tmp/positive-$index.sens"
  if ! "$cli" "$input" > "$tmp/actual" 2> "$tmp/stderr"; then
    printf 'REGRESSION test_id=%s form=%s layer=eval fixture=%s expected=D1:1 actual=execution-error first_diff=unknown reproduce=%q\n' "$id" "$index" "$input" "$reproduce" >&2
    cat "$tmp/stderr" >&2
    sha256sum "$tmp/expected" "$tmp/actual" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_DIGESTS test_id=%s form=%s expected_sha256=' "$id" "$index"
  sha256sum "$tmp/expected"
  printf 'NATIVE_SENS_DIGESTS test_id=%s form=%s actual_sha256=' "$id" "$index"
  sha256sum "$tmp/actual"
  if ! cmp -s "$tmp/expected" "$tmp/actual"; then
    printf 'REGRESSION test_id=%s form=%s layer=eval fixture=%s expected=D1:1 actual=wrong-verdict first_diff=0 reproduce=%q\n' "$id" "$index" "$input" "$reproduce" >&2
    exit 1
  fi
done

if "$cli" "$tmp/mutant.sens" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  printf 'REGRESSION test_id=%s-mutant layer=eval expected=D1-noncallable actual=accepted first_diff=D1:1-to-0 reproduce=%q\n' "$id" "$reproduce" >&2
  sha256sum "$tmp/mutant.out" >&2
  exit 1
fi
if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$tmp/mutant.err"; then
  printf 'UNINFORMATIVE-NEGATIVE test_id=%s-mutant layer=eval expected=D1-noncallable actual=unrelated-failure first_diff=unknown reproduce=%q\n' "$id" "$reproduce" >&2
  cat "$tmp/mutant.err" >&2
  sha256sum "$tmp/mutant.err" >&2
  exit 1
fi
printf 'NATIVE_SENS_NEGATIVE test_id=%s-mutant outcome=D1-noncallable stderr_sha256=' "$id"
sha256sum "$tmp/mutant.err"
printf 'NATIVE_SENS_PASS test_id=%s positive_forms=4 mutant=D1-noncallable semantic_authority=binary-SENS\n' "$id"
