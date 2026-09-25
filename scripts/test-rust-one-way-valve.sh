#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
guard="$repo_root/scripts/rust-one-way-valve.sh"
workflow="$repo_root/.github/workflows/ci.yml"

fail() {
  echo "rust-growth-policy self-test: $*" >&2
  exit 1
}

[[ -f "$guard" ]] || fail "missing scripts/rust-one-way-valve.sh"
grep -Fq 'bash scripts/rust-one-way-valve.sh "$BASE_SHA" "$HEAD_SHA"' "$workflow" \
  || fail "CI does not invoke the Rust growth policy check"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
repo="$tmp/repo"
mkdir -p "$repo"
cd "$repo"

git init -q
git config user.name rust-growth-self-test
git config user.email rust-growth-self-test@example.invalid
mkdir -p src lib
cat > src/existing.rs <<'EOF'
fn keep() {}
EOF
cat > lib/core.lisp <<'EOF'
(quote baseline)
EOF

git add -A
git commit -qm baseline
base=$(git rev-parse HEAD)

run_green() {
  local name="$1"
  git add -A
  git commit -qm "$name"
  local head
  head=$(git rev-parse HEAD)
  local log="$tmp/$name.log"
  bash "$guard" "$base" "$head" >"$log" 2>&1 || {
    cat "$log" >&2
    fail "$name unexpectedly failed"
  }
  grep -Fq 'RUST-GROWTH-ALLOWED' "$log" || {
    cat "$log" >&2
    fail "$name did not emit the allowed verdict"
  }
  base="$head"
}

# GREEN: executable Rust may grow.
printf '\nfn added_behavior() {}\n' >> src/existing.rs
run_green rust-existing-file-growth

# GREEN: new Rust source files may be created.
cat > src/new.rs <<'EOF'
pub fn substrate_transport() {}
EOF
run_green rust-new-file

# GREEN: comments/documentation in Rust may grow.
printf '\n// substrate instrumentation is allowed\n' >> src/new.rs
run_green rust-comment-growth

# GREEN: local Rust semantics may grow too. #1347 forbids only feeding
# implementation semantics back into Lisp language authority.
cat > src/local_semantics.rs <<'EOF'
pub enum LocalMeaning { Car, Cons }
pub const LOCAL_SID_MEANING: &[(u8, LocalMeaning)] = &[
    (0b00000101, LocalMeaning::Car),
    (0b00000100, LocalMeaning::Cons),
];
EOF
run_green rust-local-semantic-table

# GREEN: non-Rust changes remain valid too.
printf '(quote non-rust-change)\n' >> lib/core.lisp
run_green non-rust-change

echo "rust-growth-policy self-test: PASS"
