#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
out="${1:-$root/target/d11-families-benchmark}"
mkdir -p "$out"
raw="$out/raw.tsv"
summary="$out/summary.tsv"
rust_bin="$out/d11-families-rust"
zig_bin="$out/d11-families-zig"
: > "$raw"
: > "$summary"

rustc -O --edition=2021 "$root/benchmarks/native/d11_families.rs" -o "$rust_bin"
zig build-exe -O ReleaseFast -lc "$root/benchmarks/native/d11_families.zig" -femit-bin="$zig_bin"

D11_FAMILIES_PREFLIGHT_ONLY=1 "$rust_bin" >> "$raw" 2>&1
D11_FAMILIES_PREFLIGHT_ONLY=1 "$zig_bin" >> "$raw" 2>&1
grep -Fq 'D11_FAMILIES_PREFLIGHT impl=rust filtered=4 assoc_value=20 distinct=4 counts=4,1,1,1 checksum=9 allocations=0' "$raw"
grep -Fq 'D11_FAMILIES_PREFLIGHT impl=zig filtered=4 assoc_value=20 distinct=4 counts=4,1,1,1 checksum=9 allocations=0' "$raw"

# Alternate process order per sample (Rust→Zig, then Zig→Rust) to reduce run-order bias.
for ((sample=0; sample<15; sample++)); do
  if (( sample % 2 == 0 )); then
    D11_FAMILIES_SAMPLE="$sample" "$rust_bin" >> "$raw" 2>&1
    D11_FAMILIES_SAMPLE="$sample" "$zig_bin" >> "$raw" 2>&1
  else
    D11_FAMILIES_SAMPLE="$sample" "$zig_bin" >> "$raw" 2>&1
    D11_FAMILIES_SAMPLE="$sample" "$rust_bin" >> "$raw" 2>&1
  fi
done

test "$(grep -c '^D11_FAMILIES_SAMPLE ' "$raw")" -eq 30
test "$(grep -c '^D11_FAMILIES_SAMPLE impl=rust ' "$raw")" -eq 15
test "$(grep -c '^D11_FAMILIES_SAMPLE impl=zig ' "$raw")" -eq 15
# Every sample must have the same checksum, a unique index, and the expected AB/BA process order.
awk '
  /^D11_FAMILIES_SAMPLE / {
    impl_value=""; sample_value=""; checksum_value=""; allocations_value="";
    for (i=1; i<=NF; i++) {
      split($i, pair, "=");
      if (pair[1] == "impl") impl_value=pair[2];
      if (pair[1] == "sample") sample_value=pair[2];
      if (pair[1] == "checksum") checksum_value=pair[2];
      if (pair[1] == "allocations") allocations_value=pair[2];
    }
    sample_index=int(rows/2);
    if (sample_value != sample_index || checksum_value != "9" || allocations_value != "0") exit 1;
    if (sample_index % 2 == 0) expected_impl=(rows % 2 == 0 ? "rust" : "zig");
    else expected_impl=(rows % 2 == 0 ? "zig" : "rust");
    if (impl_value != expected_impl) exit 1;
    key=impl_value SUBSEP sample_value;
    if (seen[key]++) exit 1;
    rows++;
  }
  END {
    if (rows != 30) exit 1;
    for (i=0; i<15; i++) {
      if (!seen["rust" SUBSEP i] || !seen["zig" SUBSEP i]) exit 1;
    }
  }
' "$raw"

for impl in rust zig; do
  values="$(awk -v impl="$impl" '
    /^D11_FAMILIES_SAMPLE / {
      impl_value=""; ns_value="";
      for (i=1; i<=NF; i++) {
        split($i, pair, "=");
        if (pair[1] == "impl") impl_value=pair[2];
        if (pair[1] == "ns_per_round") ns_value=pair[2];
      }
      if (impl_value == impl) print ns_value;
    }' "$raw" | sort -n)"
  p50="$(printf '%s\n' "$values" | sed -n '8p')"
  p90="$(printf '%s\n' "$values" | sed -n '14p')"
  reps="$(awk -v impl="$impl" '
    /^D11_FAMILIES_SAMPLE / {
      impl_value=""; reps_value="";
      for (i=1; i<=NF; i++) {
        split($i, pair, "=");
        if (pair[1] == "impl") impl_value=pair[2];
        if (pair[1] == "reps") reps_value=pair[2];
      }
      if (impl_value == impl) print reps_value;
    }' "$raw" | sort -n)"
  reps_min="$(printf '%s\n' "$reps" | sed -n '1p')"
  reps_max="$(printf '%s\n' "$reps" | sed -n '15p')"
  test -n "$p50" && test -n "$p90" && test -n "$reps_min" && test -n "$reps_max"
  printf 'D11_FAMILIES_SUMMARY impl=%s samples=15 p50_ns_per_round=%s p90_ns_per_round=%s reps_min=%s reps_max=%s preflight=EXACT allocations=0 alternating=YES\n' \
    "$impl" "$p50" "$p90" "$reps_min" "$reps_max" | tee -a "$summary"
done

echo "D11_FAMILIES_METHOD same_workload=YES same_timed_boundary=YES reusable_fixed_buffers=YES timed_allocations=0 samples=15 target_sample_ns=2000000 alternating_process_order=YES semantic_oracle=NOT_USED" | tee -a "$summary"
cat "$raw"
