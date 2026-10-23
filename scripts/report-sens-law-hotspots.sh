#!/usr/bin/env bash
# Звіт фаз фізичного Lisp → Zig/T5M → SENS; тільки виміри, не семантичний оракул.
set -euo pipefail
if (( $# != 2 )); then echo 'usage: profile EVIDENCE_DIR REPORT.md' >&2; exit 2; fi
input="$1"; report="$2"
phases="$input/law-stage-timings.tsv"
laws="$input/law-timings.tsv"
mkdir -p "$(dirname "$report")"
if [[ ! -s "$phases" || ! -s "$laws" ]]; then
  printf '## Профіль етапів SENS/Zig\n\nNOT_MEASURED: даних немає.\n' > "$report"
  exit 0
fi
if ! awk -F '\t' 'NR==1 {if (NF!=4||$1!="id"||$2!="stage"||$3!="exit"||$4!="elapsed_us") exit 2; next} NF!=4||$1==""||$2 !~ /^(direct|codec-mint|zig-open|zig-verify|sens-paired|sens-standalone)$/||$3 !~ /^[0-9]+$/||$4 !~ /^[0-9]+$/ {exit 2}' "$phases"; then
 echo '::error::SENS_PHASE_TSV_MALFORMED' >&2; exit 2
fi
if ! awk -F '\t' 'NR==1 {if (NF!=3||$1!="id"||$2!="status"||$3!="wall_ms") exit 2; next} NF!=3||$1==""||($2!="PASS"&&$2!="RED")||$3 !~ /^[0-9]+$/ {exit 2}' "$laws"; then
 echo '::error::SENS_LAW_TIMING_TSV_MALFORMED' >&2; exit 2
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
checked="$(awk 'END{print NR-1}' "$laws")"
passed="$(awk -F '\t' 'NR>1 && $2=="PASS" {n++} END{print n+0}' "$laws")"
red="$(awk -F '\t' 'NR>1 && $2=="RED" {n++} END{print n+0}' "$laws")"
{
 echo '## Фази Lisp → Zig/T5M → SENS — вимірювання RED і PASS'
 printf '\nСвідків: %s, PASS: %s, RED: %s.\n\n' "$checked" "$passed" "$red"
 echo 'Одна проба на етап для кожного різного свідка, з вартістю запуску CLI. p50/p90 нижче — розподіл між свідками одного runner, не оцінка чистого EVAL або прискорення.'
 echo
 echo '| Етап | Проб | Ненульових виходів | p50 мкс | p90 мкс | max мкс |'
 echo '|---|---:|---:|---:|---:|---:|'
} > "$report"
for stage in direct codec-mint zig-open zig-verify sens-paired sens-standalone; do
 awk -F '\t' -v st="$stage" 'NR>1 && $2==st {print $4}' "$phases" | sort -n > "$tmp/sorted"
 count="$(wc -l < "$tmp/sorted" | tr -d '[:space:]')"
 if (( count==0 )); then printf '| %s | 0 | 0 | — | — | — |\n' "$stage" >> "$report"; continue; fi
 p50="$(sed -n "$(((count+1)/2))p" "$tmp/sorted")"
 p90="$(sed -n "$(((9*count+9)/10))p" "$tmp/sorted")"
 high="$(tail -n 1 "$tmp/sorted")"
 failed="$(awk -F '\t' -v st="$stage" 'NR>1 && $2==st && $3!="0"{n++}END{print n+0}' "$phases")"
 printf '| %s | %s | %s | %s | %s | %s |\n' "$stage" "$count" "$failed" "$p50" "$p90" "$high" >> "$report"
 echo "SENS_PHASE_BENCHMARK stage=$stage count=$count failed=$failed p50_us=$p50 p90_us=$p90 max_us=$high scope=mixed-witnesses"
done
{
 echo
 echo 'Найдорожчі 10 окремих етапів (не семантичні вердикти):'
 echo '| Свідок | Етап | Exit | Закон | мкс |'
 echo '|---|---|---:|---|---:|'
} >> "$report"
awk -F '\t' 'NR==FNR{if(FNR>1) state[$1]=$2;next} FNR>1{printf "%s\t%s\t%s\t%s\t%s\n",$4,$1,$2,$3,(($1 in state)?state[$1]:"UNKNOWN")}' "$laws" "$phases" | sort -t "$(printf '\t')" -k1,1nr | sed -n '1,10p' |
while IFS="$(printf '\t')" read -r duration id stage exit_code state; do
 printf '| %s | %s | %s | %s | %s |\n' "$id" "$stage" "$exit_code" "$state" "$duration" >> "$report"
done
printf 'SENS_PHASE_BENCHMARK_SUMMARY checked=%s passed=%s red=%s report=%s\n' "$checked" "$passed" "$red" "$report"
