#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
guard="$repo_root/scripts/domain-paradigm-one-way-guard.sh"

fail() {
  echo "domain-paradigm-one-way self-test: $*" >&2
  exit 1
}

[[ -x "$guard" || -f "$guard" ]] || fail "missing guard"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
repo="$tmp/repo"
mkdir -p "$repo/crates/sens/src" "$repo/crates/sens/examples" "$repo/crates/sens/tests"
cd "$repo"

git init -q
git config user.name paradigm-one-way-self-test
git config user.email paradigm-one-way-self-test@example.invalid

cat > crates/sens/src/source_words.rs <<'EOF'
pub struct BinarySourceWord;
pub fn exact_width() -> usize { 3 }
EOF
cat > crates/sens/src/compat.rs <<'EOF'
pub struct Sid8;
pub fn compatibility_only(_: Sid8) {}
EOF

git add -A
git commit -qm baseline
base=$(git rev-parse HEAD)

run_guard_expect_green() {
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
  grep -Fq "PARADIGM-ONE-WAY: PASS" "$tmp/$name.log" || {
    cat "$tmp/$name.log" >&2
    fail "$name did not emit PASS"
  }
  git reset --hard -q "$base"
}

run_guard_expect_red() {
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
  grep -Fq "PARADIGM-ONE-WAY violation" "$tmp/$name.log" || {
    cat "$tmp/$name.log" >&2
    fail "$name failed for the wrong reason"
  }
  git reset --hard -q "$base"
}

green_exact_growth() {
  cat >> crates/sens/src/source_words.rs <<'EOF'

pub fn another_exact_width_path() -> usize { 4 }
EOF
}

green_compat_growth() {
  cat >> crates/sens/src/compat.rs <<'EOF'

pub fn another_compatibility_path(_: Sid8) {}
EOF
}

green_historical_comment() {
  cat >> crates/sens/src/source_words.rs <<'EOF'

// Historical Function8 mapping is intentionally outside this layer.
EOF
}

red_legacy_import() {
  cat >> crates/sens/src/source_words.rs <<'EOF'

use crate::Sid8;
EOF
}

red_mixed_new_file() {
  cat > crates/sens/src/new_exact_path.rs <<'EOF'
use crate::{PackedBitstream, Sens8};

pub fn bad_mix(_: &PackedBitstream, _: Sens8) {}
EOF
}

green_explicit_legacy_registry_boundary() {
  cat >> crates/sens/src/source_words.rs <<'EOF'

fn compatibility_probe() {
    let _ = crate::legacy_registry::lookup(crate::sens!(00000001));
}
EOF
}

green_quarantined_legacy_module() {
  cat > crates/sens/src/legacy_registry.rs <<'EOF'
use crate::{CoreDomainIdentity, Sens8};

fn compatibility_only(_: CoreDomainIdentity, _: Sens8) {}
EOF
}


green_exact_example() {
  mkdir -p crates/sens/examples
  cat > crates/sens/examples/exact.rs <<'EOF'
use sens::PackedBitstream;

fn observe(_: &PackedBitstream) {}
fn main() {}
EOF
}

green_compat_example() {
  mkdir -p crates/sens/examples
  cat > crates/sens/examples/compat.rs <<'EOF'
use sens::Sid8;

fn compatibility_only(_: Sid8) {}
fn main() {}
EOF
}

red_exact_example_legacy() {
  mkdir -p crates/sens/examples
  cat > crates/sens/examples/exact_bad.rs <<'EOF'
use sens::{Function8, PackedBitstream};

fn bad(_: &PackedBitstream, _: Function8) {}
fn main() {}
EOF
}

red_exact_test_legacy() {
  mkdir -p crates/sens/tests
  cat > crates/sens/tests/exact_bad.rs <<'EOF'
use sens::{BinarySourceWord, Sid8};

#[test]
fn bad(_: BinarySourceWord, _: Sid8) {}
EOF
}

green_byte_scatter_comment() {
  cat >> crates/sens/src/source_words.rs <<'EOF'

// Historical TAG_DOMAIN_IDENTITY byte framing is migration debt, not authority.
EOF
}

red_domain_tag_growth() {
  cat >> crates/sens/src/source_words.rs <<'EOF'

const TAG_DOMAIN_IDENTITY: u8 = 0x59;
EOF
}

red_width_byte_growth() {
  cat >> crates/sens/src/source_words.rs <<'EOF'

fn bad_domain_width_byte(out: &mut Vec<u8>, identity: CoreDomainIdentity) {
    out.push(identity.width() as u8);
}
EOF
}

red_payload_byte_growth() {
  cat >> crates/sens/src/source_words.rs <<'EOF'

fn bad_domain_payload_byte(out: &mut Vec<u8>, identity: CoreDomainIdentity) {
    out.push(identity.packed_bits());
}
EOF
}

run_guard_expect_green exact-width-growth green_exact_growth
run_guard_expect_green compatibility-growth green_compat_growth
run_guard_expect_green historical-comment green_historical_comment
run_guard_expect_green exact-example green_exact_example
run_guard_expect_green compat-example green_compat_example
run_guard_expect_green explicit-legacy-registry-boundary green_explicit_legacy_registry_boundary
run_guard_expect_green quarantined-legacy-module green_quarantined_legacy_module
run_guard_expect_red legacy-import red_legacy_import
run_guard_expect_red mixed-new-file red_mixed_new_file
run_guard_expect_red exact-example-legacy red_exact_example_legacy
run_guard_expect_red exact-test-legacy red_exact_test_legacy
run_guard_expect_green byte-scatter-comment green_byte_scatter_comment
run_guard_expect_red domain-tag-growth red_domain_tag_growth
run_guard_expect_red width-byte-growth red_width_byte_growth
run_guard_expect_red payload-byte-growth red_payload_byte_growth

echo "domain-paradigm-one-way self-test: PASS"
