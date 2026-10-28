#!/usr/bin/env bash
# CI glue only: time the SAME SENS-owned D5 positive witness through real REPL.
# No host-language implementation of D5, no semantic fallback, no cross-CPU ranking.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/release/sens}"
outdir="${2:-.ci-metrics}"
if [[ ! -x "$cli" ]]; then
  printf 'REPL_BENCH_BLOCKED reason=missing-sens-cli path=%s\n' "$cli" >&2
  exit 1
fi
mkdir -p "$outdir"
outdir="$(cd "$outdir" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT

# The workload is already proven by scripts/prove-repl-semantic-corpus.sh.
# This script measures only time and verifies the emitted existing D1 verdict.
witness=tests/semantic/d5-arithmetic-native-t5m-law.lisp
if [[ ! -f "$witness" || -L "$witness" ]]; then
  printf 'REPL_BENCH_BLOCKED missing-fixture=%s\n' "$witness" >&2
  exit 1
fi

{
  printf 'head_sha\t%s\n' "$(git rev-parse HEAD)"
  printf 'runner_os\t%s\n' "${RUNNER_OS:-unknown}"
  printf 'runner_arch\t%s\n' "${RUNNER_ARCH:-unknown}"
  printf 'machine\t%s\n' "$(uname -a)"
  printf 'rustc\t%s\n' "$(rustc --version)"
  printf 'zig\t%s\n' "$(zig version)"
  printf 'scope\tSENS_REPL_D5_existing_positive_witness\n'
} > "$outdir/environment.tsv"

# Physical energy is optional. Reuse the existing Rust RAPL package meter,
# never derive energy from TDP, CPU power limits, or a cloud VM's clock.
# A real package counter measures the entire package, NOT just this process.
energy_mode=unavailable
energy_reason=not_linux
if [[ "${RUNNER_OS:-}" == Linux ]]; then
  energy_reason=rapl_package_counter_unavailable
  rapl_root="${SENS_RAPL_ROOT:-/sys/class/powercap}"
  zones=0
  for zone in "$rapl_root"/intel-rapl:[0-9]*; do
    [[ -r "$zone/name" && -r "$zone/energy_uj" && -r "$zone/max_energy_range_uj" ]] || continue
    read -r domain < "$zone/name" || continue
    if [[ "$domain" =~ ^package-[0-9]+$ ]]; then
      zones=$((zones + 1))
    fi
  done
  if (( zones == 1 )); then
    # Rust owns the physical sensor and subprocess timing, SENS owns D5 verdicts.
    rustc --edition=2021 -O benchmarks/mechanism/rapl-energy-bench.rs -o "$tmp/sens-rapl-meter"
    energy_mode=rapl
    energy_reason=measured_whole_cpu_package
  elif (( zones > 1 )); then
    energy_reason=multiple_cpu_packages_unresolved
  fi
fi
printf 'energy_mode\t%s\nenergy_reason\t%s\n' "$energy_mode" "$energy_reason" >> "$outdir/environment.tsv"
if [[ "$energy_mode" != rapl ]]; then
  printf 'ENERGY_NOT_MEASURED reason=%s platform=%s/%s\n' "$energy_reason" "${RUNNER_OS:-unknown}" "${RUNNER_ARCH:-unknown}"
fi

single_p50='' single_p90='' batch_p50='' batch_p90=''
single_e50='' single_e90='' batch_e50='' batch_e90=''
single_jload='' batch_jload=''
for workload in single-load batch-10-loads; do
  request="$tmp/$workload.input"
  : > "$request"
  loads=1
  if [[ "$workload" == batch-10-loads ]]; then loads=10; fi
  for ((n=1; n<=loads; n++)); do
    printf ':завантажити %s\n' "$witness" >> "$request"
  done

  samples="$outdir/$workload.tsv"
  printf 'sample\telapsed_seconds\n' > "$samples"
  if [[ "$energy_mode" == rapl ]]; then
    energy_samples="$outdir/$workload-energy.tsv"
    printf 'sample\tenergy_j\tjoules_per_declared_load\n' > "$energy_samples"
  fi

  for iteration in {1..11}; do
    if [[ "$energy_mode" == rapl ]]; then
      # One meter invocation brackets exactly this SENS execution.
      if ! "$tmp/sens-rapl-meter" --operations "$loads" -- "$cli" --surface=укр < "$request" \
        > "$tmp/meter.out" 2> "$tmp/meter.err"; then
        printf 'REPL_ENERGY_FAIL workload=%s sample=%s sensor_or_child_failed\n' "$workload" "$iteration" >&2
        cat "$tmp/meter.err" >&2
        exit 1
      fi
      # Separate the Rust mechanism's physical observations from the REPL
      # transcript before checking the positive SENS witness.
      grep -vE '^RUST_RAPL_(PACKAGE|NORMALIZED) ' "$tmp/meter.out" > "$tmp/reply.out" || true
      grep -v '^RAPL_NOTE ' "$tmp/meter.err" > "$tmp/reply.err" || true
      package="$(grep '^RUST_RAPL_PACKAGE ' "$tmp/meter.out")"
      normalized="$(grep '^RUST_RAPL_NORMALIZED ' "$tmp/meter.out")"
      [[ "$(grep -c '^RUST_RAPL_PACKAGE ' "$tmp/meter.out")" -eq 1 ]] || { echo 'RAPL_INVALID_PACKAGE_OBSERVATION' >&2; exit 1; }
      elapsed='' joules='' joules_load=''
      for item in $package; do
        case "$item" in
          elapsed_s=*) elapsed="${item#*=}" ;;
          energy_j=*) joules="${item#*=}" ;;
        esac
      done
      for item in $normalized; do
        case "$item" in
          joules_per_declared_operation=*) joules_load="${item#*=}" ;;
        esac
      done
      for number in "$elapsed" "$joules" "$joules_load"; do
        [[ "$number" =~ ^[0-9]+([.][0-9]+)?$ ]] || { echo "RAPL_INVALID_MEASUREMENT $number" >&2; exit 1; }
      done
      printf '%s\t%s\t%s\n' "$iteration" "$joules" "$joules_load" >> "$energy_samples"
      printf '%s\n%s\n' "$package" "$normalized" >> "$outdir/rapl-observations.log"
    else
      TIMEFORMAT='%3R'
      if ! elapsed="$( { time "$cli" --surface=укр < "$request" > "$tmp/reply.out" 2> "$tmp/reply.err"; } 2>&1 )"; then
        printf 'REPL_BENCH_FAIL workload=%s sample=%s reason=executor\n' "$workload" "$iteration" >&2
        cat "$tmp/reply.err" >&2
        exit 1
      fi
      elapsed="$(printf '%s\n' "$elapsed" | tr -d '\r' | tail -n 1)"
      [[ "$elapsed" =~ ^[0-9]+([.][0-9]+)?$ ]] || { echo "REPL_BENCH_FAIL invalid-time=$elapsed" >&2; exit 1; }
    fi

    if [[ -s "$tmp/reply.err" ]] || grep -Eq 'Помилка (REPL/T5M|завантаження|виконання)' "$tmp/reply.out"; then
      printf 'REPL_BENCH_FAIL workload=%s sample=%s reason=unexpected-SENS-error\n' "$workload" "$iteration" >&2
      cat "$tmp/reply.err" "$tmp/reply.out" >&2
      exit 1
    fi
    if ! awk -v marker="Завантажено: $witness" '
      { sub(/\r$/, "", $0); sub(/[ \t]+$/, "", $0) }
      index($0, marker) { found=1; last=""; next }
      found && NF { last=$0 }
      END { exit !(found && (last=="ТАК" || last=="sens[укр]> ТАК")) }
    ' "$tmp/reply.out"; then
      printf 'REPL_BENCH_FAIL workload=%s sample=%s reason=wrong-SENS-D1\n' "$workload" "$iteration" >&2
      cat "$tmp/reply.out" >&2
      exit 1
    fi
    printf '%s\t%s\n' "$iteration" "$elapsed" >> "$samples"
  done

  p50="$(tail -n +2 "$samples" | cut -f2 | sort -n | sed -n '6p')"
  p90="$(tail -n +2 "$samples" | cut -f2 | sort -n | sed -n '10p')"
  printf 'SENS_REPL_BENCH workload=%s samples=11 p50_s=%s p90_s=%s target=D5 platform=%s/%s sha=%s\n' \
    "$workload" "$p50" "$p90" "${RUNNER_OS:-unknown}" "${RUNNER_ARCH:-unknown}" "$(git rev-parse HEAD)"
  if [[ "$workload" == single-load ]]; then
    single_p50="$p50"
    single_p90="$p90"
  else
    batch_p50="$p50"
    batch_p90="$p90"
  fi
  if [[ "$energy_mode" == rapl ]]; then
    e50="$(tail -n +2 "$energy_samples" | cut -f2 | sort -n | sed -n '6p')"
    e90="$(tail -n +2 "$energy_samples" | cut -f2 | sort -n | sed -n '10p')"
    jload="$(tail -n +2 "$energy_samples" | cut -f3 | sort -n | sed -n '6p')"
    printf 'SENS_REPL_PACKAGE_ENERGY workload=%s samples=11 p50_j=%s p90_j=%s p50_j_per_declared_load=%s source=Linux_RAPL scope=whole_package_not_process\n' \
      "$workload" "$e50" "$e90" "$jload"
    if [[ "$workload" == single-load ]]; then
      single_e50="$e50"
      single_e90="$e90"
      single_jload="$jload"
    else
      batch_e50="$e50"
      batch_e90="$e90"
      batch_jload="$jload"
    fi
  fi
done

# Never issue a success notice until BOTH time runs and the SENS-owned
# positive/negative corpus (separate CI step) have finished successfully.
[[ -n "$single_p50" && -n "$single_p90" && -n "$batch_p50" && -n "$batch_p90" ]]
platform="${RUNNER_OS:-unknown}/${RUNNER_ARCH:-unknown}"
head="$(git rev-parse HEAD)"
energy_display="джоулі=НЕ ВИМІРЯНО ($energy_reason)"
if [[ "$energy_mode" == rapl ]]; then
  [[ -n "$single_e50" && -n "$single_e90" && -n "$batch_e50" && -n "$batch_e90" ]]
  energy_display="RAPL package cold p50=${single_e50}J p90=${single_e90}J batch10 p50=${batch_e50}J p90=${batch_e90}J; J/load=${single_jload}/${batch_jload}; includes background"
fi
if [[ "${GITHUB_ACTIONS:-}" == true ]]; then
  printf '::notice title=SENS час + енергія (%s)::D5 | cold 11 p50=%ss p90=%ss | batch10 11 p50=%ss p90=%ss | %s | SHA=%s\n' \
    "$platform" "$single_p50" "$single_p90" "$batch_p50" "$batch_p90" "$energy_display" "${head:0:12}"
fi
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  {
    printf '### SENS REPL · час / енергія · %s\n\n' "$platform"
    printf '| D5 workload | n | p50, с | p90, с | p50, Дж CPU package | p90, Дж |\n'
    printf '|:--|--:|--:|--:|--:|--:|\n'
    if [[ "$energy_mode" == rapl ]]; then
      printf '| 1 завантаження | 11 | %s | %s | %s | %s |\n' "$single_p50" "$single_p90" "$single_e50" "$single_e90"
      printf '| 10 завантажень | 11 | %s | %s | %s | %s |\n' "$batch_p50" "$batch_p90" "$batch_e50" "$batch_e90"
      printf '\nRAPL — **цілий CPU package**, з idle/фоном; не енергія SENS-процесу. '
      printf 'Умовні Дж/заявлене завантаження: %s / %s (холодне / пакетне).\n' "$single_jload" "$batch_jload"
    else
      printf '| 1 завантаження | 11 | %s | %s | не виміряно | не виміряно |\n' "$single_p50" "$single_p90"
      printf '| 10 завантажень | 11 | %s | %s | не виміряно | не виміряно |\n' "$batch_p50" "$batch_p90"
      printf '\nЕнергія: **не виміряно** (%s). Без TDP-оцінок.\n' "$energy_reason"
    fi
    printf '\nSHA: \`%s\`. Дані різних CPU не є нормалізованим рейтингом.\n' "$head"
  } >> "$GITHUB_STEP_SUMMARY"
fi
