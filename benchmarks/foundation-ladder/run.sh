#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="${1:-/tmp/sens-foundation-ladder}"
SRC="$ROOT/benchmarks/foundation-ladder/foundation_ladder.rs"
BIN="$OUT_DIR/foundation-ladder"
RESULTS="$OUT_DIR/results.tsv"
REPORT="$OUT_DIR/report.md"
RAW="$OUT_DIR/raw.log"

mkdir -p "$OUT_DIR"
: > "$RAW"

rustc -O "$SRC" -o "$BIN"

git_sha="$(git -C "$ROOT" rev-parse HEAD)"
corpus_sha="$(sha256sum "$SRC" | awk '{print $1}')"
binary_sha="$(sha256sum "$BIN" | awk '{print $1}')"
channels_sha="$(sha256sum "$ROOT/channels.scm" | awk '{print $1}')"
cpu="$(grep -m1 '^model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2- | xargs || true)"
rustc_version="$(rustc --version)"
valgrind_version="$(valgrind --version)"
cpu="${cpu:-unknown}"

header=(
  case_id candidate family semantic_depth mode rep i_refs tree_steps
  root_selections bits_consumed generator_apps registry_lookups residue_lookups
  cache_hits cache_misses allocations allocated_bytes object_bytes wire_bits
  compiler_phase machine_insts code_bytes loads stores branches calls spills
  corpus_sha binary_sha git_sha guix_channels_sha cpu valgrind_version
  prepared_bytes peak_prepare_bytes relation_edge_reads observer_fields
  quotient_lookups word_compares checksum
)
(IFS=$'\t'; echo "${header[*]}") > "$RESULTS"

field() {
  local line="$1"
  local key="$2"
  printf '%s\n' "$line" | tr '\t' '\n' | sed -n "s/^${key}=//p"
}

emit_row() {
  local case_id="$1"
  local candidate="$2"
  local size="$3"
  local mode="$4"
  local reps="$5"
  local irefs="$6"
  local line="$7"
  local relation_kind="$8"

  local prepared_bytes peak_prepare_bytes relation_edge_reads observer_fields quotient_lookups word_compares checksum
  prepared_bytes="$(field "$line" prepared_bytes)"
  peak_prepare_bytes="$(field "$line" peak_prepare_bytes)"
  checksum="$(field "$line" checksum)"

  if [[ "$relation_kind" == "prep" ]]; then
    relation_edge_reads="$(field "$line" prep_relation_edge_reads)"
    observer_fields="$(field "$line" prep_observer_fields)"
    quotient_lookups="$(field "$line" prep_quotient_lookups)"
    word_compares="$(field "$line" prep_word_compares)"
  else
    relation_edge_reads="$(field "$line" exec_relation_edge_reads)"
    observer_fields="$(field "$line" exec_observer_fields)"
    quotient_lookups="$(field "$line" exec_quotient_lookups)"
    word_compares="$(field "$line" exec_word_compares)"
  fi

  local row=(
    "$case_id" "$candidate" "foundation-ladder" "" "$mode" "$reps" "$irefs" ""
    "" "" "" "" "" "" "" "" "" "$prepared_bytes" "" ""
    "" "" "" "" "" "" ""
    "$corpus_sha" "$binary_sha" "$git_sha" "$channels_sha" "$cpu" "$valgrind_version"
    "$prepared_bytes" "$peak_prepare_bytes" "$relation_edge_reads" "$observer_fields"
    "$quotient_lookups" "$word_compares" "$checksum"
  )
  (IFS=$'\t'; echo "${row[*]}") >> "$RESULTS"
}

cachegrind_run() {
  local candidate="$1"
  local mode="$2"
  local size="$3"
  local reps="$4"
  local tag="$5"
  local stdout_file="$OUT_DIR/${tag}.out"
  local stderr_file="$OUT_DIR/${tag}.cachegrind.log"
  local cg_file="$OUT_DIR/${tag}.cg"

  valgrind --tool=cachegrind --cachegrind-out-file="$cg_file" \
    "$BIN" --candidate "$candidate" --mode "$mode" --size "$size" --reps "$reps" \
    >"$stdout_file" 2>"$stderr_file"

  cat "$stdout_file" >> "$RAW"
  cat "$stderr_file" >> "$RAW"

  local line irefs
  line="$(grep '^FOUNDATION_RESULT' "$stdout_file")"
  irefs="$(grep -E 'I[[:space:]]+refs:' "$stderr_file" | tail -1 \
    | sed -E 's/.*refs:[[:space:]]+([0-9,]+).*/\1/' | tr -d ',')"
  test -n "$line"
  test -n "$irefs"
  printf '%s\t%s\n' "$irefs" "$line"
}

candidates=(
  raw-relation
  observer-computed
  observer-cached
  quotient-class
  exact-word
  packed-binary
)

echo "# parity verification" >> "$RAW"
for size in 32 128 512; do
  "$BIN" --verify --size "$size" | tee -a "$RAW"
done

echo "# native logical sweeps" >> "$RAW"
for size in 32 128 512; do
  for reps in 1 10 100 1000 10000; do
    for candidate in "${candidates[@]}"; do
      line="$("$BIN" --candidate "$candidate" --mode full --size "$size" --reps "$reps")"
      echo "$line" >> "$RAW"
      emit_row "logical-s${size}-n${reps}-${candidate}" "$candidate" "$size" \
        "logical-full" "$reps" "" "$line" "exec"
    done
  done
done

echo "# cachegrind instruction counts" >> "$RAW"
size=128
for candidate in "${candidates[@]}"; do
  prep_record="$(cachegrind_run "$candidate" prepare "$size" 1 "cg-${candidate}-prepare")"
  prep_irefs="${prep_record%%$'\t'*}"
  prep_line="${prep_record#*$'\t'}"
  emit_row "cg-s${size}-prepare-${candidate}" "$candidate" "$size" \
    "prepare" 1 "$prep_irefs" "$prep_line" "prep"

  for reps in 1 2 4 5 10 100 1000 10000; do
    full_record="$(cachegrind_run "$candidate" full "$size" "$reps" "cg-${candidate}-full-${reps}")"
    full_irefs="${full_record%%$'\t'*}"
    full_line="${full_record#*$'\t'}"
    execute_irefs="$((full_irefs - prep_irefs))"

    emit_row "cg-s${size}-full-n${reps}-${candidate}" "$candidate" "$size" \
      "amortized-total" "$reps" "$full_irefs" "$full_line" "exec"
    emit_row "cg-s${size}-exec-n${reps}-${candidate}" "$candidate" "$size" \
      "execute-delta" "$reps" "$execute_irefs" "$full_line" "exec"
  done
done

{
  echo "# Foundation ladder benchmark"
  echo
  echo "Semantic parity is checked exhaustively for graph sizes 32, 128 and 512 before performance evidence is emitted."
  echo
  printf -- '- git: `%s`\n' "$git_sha"
  printf -- '- corpus/source sha256: `%s`\n' "$corpus_sha"
  printf -- '- binary sha256: `%s`\n' "$binary_sha"
  printf -- '- channels.scm sha256: `%s`\n' "$channels_sha"
  printf -- '- toolchain: `%s`\n' "$rustc_version"
  printf -- '- valgrind: `%s`\n' "$valgrind_version"
  printf -- '- cpu: `%s`\n' "$cpu"
  echo
  echo "## Cachegrind execute-delta rows (size 128)"
  echo
  echo "| candidate | repetitions | execute I refs | final prepared bytes | relation reads | observer fields | quotient lookups | word compares |"
  echo "|---|---:|---:|---:|---:|---:|---:|---:|"
  awk -F '\t' '
    NR == 1 {
      for (i = 1; i <= NF; i++) h[$i] = i
      next
    }
    $h["mode"] == "execute-delta" {
      printf "| %s | %s | %s | %s | %s | %s | %s | %s |\n",
        $h["candidate"], $h["rep"], $h["i_refs"], $h["prepared_bytes"],
        $h["relation_edge_reads"], $h["observer_fields"],
        $h["quotient_lookups"], $h["word_compares"]
    }
  ' "$RESULTS"
  echo
  echo "These rows compare mechanisms only after semantic parity. Preparation I refs and amortized-total rows are preserved in results.tsv; no single weighted winner is computed."
} > "$REPORT"

cat "$REPORT"
