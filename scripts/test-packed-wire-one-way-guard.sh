#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
guard="$repo_root/scripts/packed-wire-one-way-guard.sh"

fail() {
  echo "packed-wire-one-way self-test: $*" >&2
  exit 1
}

[[ -f "$guard" ]] || fail "missing guard"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
repo="$tmp/repo"
mkdir -p "$repo/crates/sens/src"
cd "$repo"

git init -q
git config user.name packed-wire-self-test
git config user.email packed-wire-self-test@example.invalid

cat > crates/sens/src/source_packing.rs <<'EOF'
pub fn exact_payload_bits(widths: &[usize]) -> usize {
    widths.iter().sum()
}
EOF

cat > crates/sens/src/syntax.rs <<'EOF'
pub fn legacy_cache_only() -> u8 { 7 }
EOF

git add -A
git commit -qm baseline
base=$(git rev-parse HEAD)

run_green() {
  local name="$1"
  shift
  "$@"
  git add -A
  git commit -qm "$name"
  local head
  head=$(git rev-parse HEAD)
  if ! bash "$guard" "$base" "$head" >"$tmp/$name.log" 2>&1; then
    cat "$tmp/$name.log" >&2
    fail "$name unexpectedly failed"
  fi
  grep -Fq "PACKED-WIRE-ONE-WAY: PASS" "$tmp/$name.log" || fail "$name did not emit PASS"
  git reset --hard -q "$base"
}

run_red() {
  local name="$1"
  shift
  "$@"
  git add -A
  git commit -qm "$name"
  local head
  head=$(git rev-parse HEAD)
  if bash "$guard" "$base" "$head" >"$tmp/$name.log" 2>&1; then
    cat "$tmp/$name.log" >&2
    fail "$name unexpectedly passed"
  fi
  grep -Fq "PACKED-WIRE-ONE-WAY violation" "$tmp/$name.log" || {
    cat "$tmp/$name.log" >&2
    fail "$name failed for wrong reason"
  }
  git reset --hard -q "$base"
}

green_dense_bits() {
  cat >> crates/sens/src/source_packing.rs <<'EOF'

pub fn byte_len_for_payload(bits: usize) -> usize {
    bits.div_ceil(8)
}
EOF
}

green_comment_only() {
  cat >> crates/sens/src/syntax.rs <<'EOF'

// Historical TAG_DOMAIN_IDENTITY is debt to remove from canonical wire.
EOF
}

red_domain_tag() {
  cat >> crates/sens/src/syntax.rs <<'EOF'

const TAG_DOMAIN_IDENTITY: u8 = 0x59;
EOF
}

red_width_byte() {
  cat >> crates/sens/src/syntax.rs <<'EOF'

fn bad(out: &mut Vec<u8>, identity: Identity) {
    out.push(identity.width() as u8);
}
EOF
}

red_payload_byte() {
  cat >> crates/sens/src/syntax.rs <<'EOF'

fn bad2(out: &mut Vec<u8>, identity: Identity) {
    out.push(identity.packed_bits());
}
EOF
}

run_green dense-bits green_dense_bits
run_green historical-comment green_comment_only
run_red domain-tag red_domain_tag
run_red width-byte red_width_byte
run_red payload-byte red_payload_byte

echo "packed-wire-one-way self-test: PASS"
