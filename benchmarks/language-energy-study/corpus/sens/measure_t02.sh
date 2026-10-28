#!/usr/bin/env bash
# ENERGY-02 / #6287: actual SENS T02 process, not a host-language imitation.
set -euo pipefail
cd "$(dirname "$0")/../../../.."
cli="$PWD/target/debug/sens"
out="$PWD/t02-sens-observation"
if (( $# >= 1 )); then cli="$1"; fi
if (( $# >= 2 )); then out="$2"; fi
[[ -x "$cli" ]] || { echo "SENS_T02_BLOCKED missing_binary=$cli" >&2; exit 2; }
fixture="benchmarks/language-energy-study/corpus/sens/t02_rationals.lisp"
[[ -f "$fixture" ]] || { echo "SENS_T02_BLOCKED missing_fixture" >&2; exit 2; }
mkdir -p "$out"
out="$(cd "$out" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
{
  printf 'source_sha\t%s\n' "$(git rev-parse HEAD)"
  printf 'fixture_sha256\t%s\n' "$(sha256sum "$fixture" | cut -d' ' -f1)"
  printf 'runtime\t%s\n' "$("$cli" --version 2>&1 | head -n 1)"
  printf 'rustc\t%s\n' "$(rustc --version)"
  printf 'zig\t%s\n' "$(zig version)"
  printf 'os\t%s\n' "$(uname -a)"
  printf 'cpu\t%s\n' "$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-)"
  printf 'boundary\t/usr/bin/time wraps one SENS CLI process, excludes build/mint/reference\n'
  printf 'phase\tprocess-cold, no warmup; debug unless user supplied another binary\n'
  printf 'energy_status\tENERGY_NOT_MEASURED\n'
  printf 'scope\tEXPLORATORY_NOT_ADMITTED\n'
} > "$out/environment.tsv"
cp "$fixture" "$tmp/verify.lisp"
sed 's/^(гармонійна-сума число-двадцять)$/\(гармонійна-сума число-чотириста\)/' "$fixture" > "$tmp/measure.lisp"
if cmp -s "$tmp/verify.lisp" "$tmp/measure.lisp"; then
  echo "SENS_T02_BLOCKED measure_source_not_generated" >&2; exit 2
fi
for mode in verify measure; do
  "$cli" --t5m-mint "$tmp/$mode.lisp" "$tmp/$mode.sens"
  printf 'minted_%s_sha256\t%s\n' "$mode" "$(sha256sum "$tmp/$mode.sens" | cut -d' ' -f1)" >> "$out/environment.tsv"
  printf 'minted_%s_bytes\t%s\n' "$mode" "$(wc -c < "$tmp/$mode.sens")" >> "$out/environment.tsv"
done
# Run the actual native source once outside timing and persist COMPLETE stderr.
# The shared parity wrapper truncates stderr to 120 characters by design.
if ! timeout 30s "$cli" "$tmp/verify.sens" > "$out/verify-stdout.txt" 2> "$out/verify-stderr.txt"; then
  echo 'SENS_T02_NATIVE_VERIFY_RED full_native_stderr:' >&2
  tail -c 3000 "$out/verify-stderr.txt" >&2
  exit 2
fi
# Independent cross-language output parity, not SENS semantic authority.
python3 benchmarks/language-energy-study/parity_check.py \
  --task T02-exact-rationals --run "$cli $tmp/verify.sens"
printf 'mode\trepetition\twall_seconds\tpeak_rss_kib\toutput_parity\n' > "$out/raw.tsv"
for mode in verify measure; do
  if [[ "$mode" == verify ]]; then n=20; else n=400; fi
  expected="$(python3 - "$n" <<'PY'
from fractions import Fraction
import sys
n = int(sys.argv[1])
print(sum((Fraction(1, k) for k in range(1, n + 1)), Fraction(0)))
PY
)"
  for repeat in 1 2 3; do
    if ! timeout 30s /usr/bin/time -f '%e	%M' -o "$tmp/time.tsv" \
      "$cli" "$tmp/$mode.sens" > "$tmp/actual.out" 2> "$tmp/actual.err"; then
      echo "SENS_T02_BLOCKED mode=$mode repeat=$repeat reason=execution_or_timeout" >&2
      cat "$tmp/actual.err" >&2
      exit 2
    fi
    actual="$(cat "$tmp/actual.out")"
    [[ "$(grep -cve '^$' "$tmp/actual.out")" -eq 1 ]] || { echo "SENS_T02_BLOCKED unexpected_stdout_lines" >&2; exit 2; }
    if [[ "$actual" != "$expected" ]]; then
      echo "SENS_T02_PARITY_FAILED mode=$mode repeat=$repeat expected=$expected actual=$actual" >&2
      exit 2
    fi
    IFS=$'\t' read -r wall rss < "$tmp/time.tsv"
    [[ "$wall" =~ ^[0-9]+(\.[0-9]+)?$ && "$rss" =~ ^[0-9]+$ && "$rss" -gt 0 ]] || {
      echo "SENS_T02_BLOCKED invalid_physical_time_rss" >&2; exit 2;
    }
    printf '%s\t%s\t%s\t%s\tPARITY_OK\n' "$mode" "$repeat" "$wall" "$rss" >> "$out/raw.tsv"
    echo "SENS_T02_PHYSICAL mode=$mode sample=$repeat seconds=$wall rss_kib=$rss parity=OK"
  done
done
echo "SENS_T02_EXPLORATORY_COMPLETE source=$(git rev-parse HEAD) raw=$out/raw.tsv energy=ENERGY_NOT_MEASURED"
