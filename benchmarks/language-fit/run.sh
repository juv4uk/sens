#!/usr/bin/env bash
# Єдина методика для ручного ci.yml і власного i5-6400 / UbuntuStudio.
set -euo pipefail
cd "$(dirname "$0")/../.."

if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "Потрібен x86_64" >&2
  exit 2
fi
cpu_flags="$(awk '/^flags[[:space:]]*:/ {print; exit}' /proc/cpuinfo)"
for flag in avx2 fma; do
  if [[ ! " $cpu_flags " =~ [[:space:]]$flag[[:space:]] ]]; then
    echo "Немає $flag: Skylake-бенчмарк не запускається" >&2
    exit 2
  fi
done
for compiler in gcc gfortran rustc zig awk; do
  command -v "$compiler" >/dev/null || {
    echo "Бракує інструмента: $compiler" >&2
    exit 2
  }
done
# В репозиторії піновано Zig 0.16.0; іншою версією не імітуємо parity.
if [[ "$(zig version)" != "0.16.0" ]]; then
  echo "Потрібен Zig 0.16.0; виявлено $(zig version)" >&2
  exit 2
fi

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
: > "$scratch/build.tsv"
: > "$scratch/samples.tsv"
# Серійне ядро C та те саме чотирьохланцюжкове AVX2/FMA як у ASM.
variants=(fortran c c-avx2 rust zig asm-scalar asm-avx2)

build_variant() {
  local lang="$1"
  shift
  local start end
  start="$(date +%s%N)"
  "$@"
  end="$(date +%s%N)"
  printf '%s\t%s\t%s\n' "$lang" "$((end-start))" "$(stat -c %s "$scratch/dot-$lang")" >> "$scratch/build.tsv"
}
# Адресні тести машинного ядра, без важкого Cargo workspace.
rustc --edition=2021 --test -C opt-level=2 crates/sens/src/machine_math.rs -o "$scratch/machine-math-tests"
"$scratch/machine-math-tests"

# ОКРЕМИЙ дослід: чи випереджає ASM компілятор Rust для точних
# D24/D48/D96 цілочисельних ядер? Обов'язковий контроль кожного входу.
# Відсутність числової відповідності — помилка, швидкісний програш — ні.
rustc --edition=2021 -C opt-level=3 -C target-cpu=skylake \
  benchmarks/language-fit/exact-integer.rs -o "$scratch/exact-integer"
"$scratch/exact-integer" | tee "$scratch/exact-integer.md"
if [[ -v GITHUB_STEP_SUMMARY && -n "$GITHUB_STEP_SUMMARY" ]]; then
  cat "$scratch/exact-integer.md" >> "$GITHUB_STEP_SUMMARY"
fi

build_variant fortran gfortran -O3 -march=skylake -std=f2008 -Wall benchmarks/language-fit/dot.f90 -o "$scratch/dot-fortran"
build_variant c gcc -O3 -march=skylake -std=c11 -Wall -Wextra benchmarks/language-fit/dot.c -o "$scratch/dot-c"
# Рівний SIMD-конкурент: та сама ширина, FMA і 4 незалежні накопичувачі.
build_variant c-avx2 gcc -O3 -march=skylake -std=c11 -Wall -Wextra -DSENS_C_AVX2 benchmarks/language-fit/dot.c benchmarks/language-fit/dot-c-avx2.c -o "$scratch/dot-c-avx2"
build_variant rust rustc -C opt-level=3 -C target-cpu=skylake -C debuginfo=0 benchmarks/language-fit/dot.rs -o "$scratch/dot-rust"
# Zig 0.16 компілюємо окремо у власний .o; gcc тільки лінкує його
# зі спільним C-драйвером. Це не «zig cc» замість справжнього Zig.
build_zig() {
  zig build-obj benchmarks/language-fit/dot.zig -O ReleaseFast -mcpu skylake -fPIC -femit-bin="$scratch/dot-zig.o"
  gcc -O3 -march=skylake -std=c11 -Wall -Wextra -DSENS_ZIG benchmarks/language-fit/dot.c "$scratch/dot-zig.o" -o "$scratch/dot-zig"
}
build_variant zig build_zig
build_variant asm-scalar gcc -O3 -march=skylake -std=c11 -Wall -Wextra -DSENS_ASM_SCALAR benchmarks/language-fit/dot.c crates/sens/src/machine_math_skylake.S -o "$scratch/dot-asm-scalar"
build_variant asm-avx2 gcc -O3 -march=skylake -std=c11 -Wall -Wextra -DSENS_ASM_AVX2 benchmarks/language-fit/dot.c crates/sens/src/machine_math_skylake.S -o "$scratch/dot-asm-avx2"

# Незалежний аналітичний контроль: кожна зміна a[k]
# впливає рівно на (2048-k) наступних скалярних добутків.
expected="$(awk 'BEGIN {
  n=65536; rounds=2048; base=0; correction=0
  for(i=0;i<n;i++){
    a=(i%97+1)*0.001; b=(i%89+1)*0.002
    base+=a*b
    if(i<rounds) correction+=(rounds-i)*1e-9*b
  }
  printf "%.16e", rounds*base+correction
}')"
verify() {
  local lang="$1" value="$2"
  if [[ ! "$value" =~ ^[+-]?[0-9]+([.][0-9]+)?[Ee][+-]?[0-9]+$ ]]; then
    echo "INVALID_RESULT $lang $value" >&2
    exit 1
  fi
  if ! awk -v got="$value" -v want="$expected" 'BEGIN {
    diff=got-want; if(diff<0)diff=-diff
    scale=want; if(scale<0)scale=-scale
    exit(diff <= 1e-10*(scale+1) ? 0 : 1)
  }'; then
    echo "RESULT_MISMATCH $lang got=$value expected=$expected" >&2
    exit 1
  fi
}

# Попередній запуск кожного ядра — і прогрів, і перевірка точності.
for lang in "${variants[@]}"; do
  value="$("$scratch/dot-$lang" | tr -d '[:space:]')"
  verify "$lang" "$value"
done

# П'ять чергувань семи реалізацій; порядок змінюється між повторами.
for round in 0 1 2 3 4; do
  for position in 0 1 2 3 4 5 6; do
    index="$(((round+position)%7))"
    lang="${variants[index]}"
    started="$(date +%s%N)"
    value="$("$scratch/dot-$lang" | tr -d '[:space:]')"
    ended="$(date +%s%N)"
    verify "$lang" "$value"
    printf '%s\t%s\t%s\n' "$lang" "$round" "$((ended-started))" >> "$scratch/samples.tsv"
  done
done

{
  echo '## Intel Skylake: Fortran / C / C AVX2/FMA / Rust / Zig / ASM SSE2 / ASM AVX2/FMA'
  echo
  echo "- Git SHA: $(git rev-parse HEAD 2>/dev/null || echo НЕВІДОМО)"
  echo "- CPU: $(awk -F: '/model name/ {sub(/^[[:space:]]+/, "", $2); print $2; exit}' /proc/cpuinfo)"
  echo "- ISA: AVX2 і FMA наявні"
  echo "- gcc: $(gcc --version | head -1)"
  echo "- gfortran: $(gfortran --version | head -1)"
  echo "- rustc: $(rustc --version)"
  echo "- zig: $(zig version)"
  echo "- Контрольна сума: $expected"
  echo "- Робота: 65536 елементів, 2048 добутків, 5 чергованих повторів"
  echo "- Метрика: медіана часу цілого процесу (не окремої інструкції)"
  echo
  echo '| Реалізація | Медіана, мс | Компіляція, мс | Бінарник, байт |'
  echo '|---|---:|---:|---:|'
  # В анотації використовуємо ті самі значення, що й у таблиці.
  brief_times=()
  for lang in "${variants[@]}"; do
    median_ns="$(awk -F '\t' -v lang="$lang" '$1==lang {print $3}' "$scratch/samples.tsv" | sort -n | sed -n '3p')"
    build_ns="$(awk -F '\t' -v lang="$lang" '$1==lang {print $2}' "$scratch/build.tsv")"
    binary_bytes="$(awk -F '\t' -v lang="$lang" '$1==lang {print $3}' "$scratch/build.tsv")"

    median_ms="$(awk -v ns="$median_ns" 'BEGIN {printf "%.3f", ns/1000000}')"
    build_ms="$(awk -v ns="$build_ns" 'BEGIN {printf "%.3f", ns/1000000}')"
    printf '| %s | %s | %s | %s |\n' "$lang" "$median_ms" "$build_ms" "$binary_bytes"
    brief_times+=("$lang=${median_ms}ms")
  done

  # GitHub Actions: коротка анотація, повна таблиця нижче в Summary.
  # stderr не потрапляє до Markdown-таблиці; анотація лише після parity PASS.
  if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    cpu_brief="$(awk -F: '/model name/ {sub(/^[[:space:]]+/, "", $2); print $2; exit}' /proc/cpuinfo)"
    cpu_brief="${cpu_brief//%/%25}"
    printf -v compact '%s; ' "${brief_times[@]}"
    printf '::notice title=SENS Skylake — 7 реалізацій::CPU=%s; %sточність=PASS; медіани 5 запусків цілого процесу; дослід\n' "$cpu_brief" "$compact" >&2
  fi
  echo
  echo 'Це дослідницький вимір; результати GitHub-hosted CPU не є результатами i5-6400.'
  echo 'AVX2/FMA може змінювати порядок додавання f64; застосовано числовий допуск.'
  echo 'Скалярні й векторні реалізації — різні класи; ASM AVX2 порівнюємо насамперед з C AVX2/FMA.'
} | tee "$scratch/result.md"

if [[ -v GITHUB_STEP_SUMMARY && -n "$GITHUB_STEP_SUMMARY" ]]; then
  cat "$scratch/result.md" >> "$GITHUB_STEP_SUMMARY"
fi
