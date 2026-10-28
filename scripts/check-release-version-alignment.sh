#!/usr/bin/env bash
# Перевіряє механічну відповідність версії пакунків та активного installer.
set -euo pipefail
cd "$(dirname "$0")/.."

expected="${1:-$(sed -n '/^\[package\]/,/^\[/s/^version = "\([^"]*\)".*/\1/p' crates/sens-cli/Cargo.toml | head -n 1)}"
tag="s${expected}"
crates=(sens sens-cli sens-host sens-literate sens-lsp sens-semantic sens-wasm)

if [[ ! "$expected" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  printf 'RELEASE_VERSION_ALIGNMENT invalid-version=%s\n' "$expected" >&2
  exit 1
fi

for crate in "${crates[@]}"; do
  manifest="crates/${crate}/Cargo.toml"
  actual="$(sed -n '/^\[package\]/,/^\[/s/^version = "\([^"]*\)".*/\1/p' "$manifest" | head -n 1)"
  if [[ "$actual" != "$expected" ]]; then
    printf 'RELEASE_VERSION_ALIGNMENT crate=%s expected=%s actual=%s\n' "$crate" "$expected" "${actual:-missing}" >&2
    exit 1
  fi

  if ! awk -v wanted="$crate" -v expected="$expected" '
    function finish() {
      if (inside && name == wanted) {
        count++
        if (version != expected || external) bad = 1
      }
    }
    /^\[\[package\]\]$/ { finish(); inside = 1; name = ""; version = ""; external = 0; next }
    /^\[/ { finish(); inside = 0; next }
    inside && /^name = "/ { name = $0; sub(/^name = "/, "", name); sub(/"$/, "", name) }
    inside && /^version = "/ { version = $0; sub(/^version = "/, "", version); sub(/"$/, "", version) }
    inside && /^source = "/ { external = 1 }
    END { finish(); if (count != 1 || bad) exit 1 }
  ' Cargo.lock; then
    printf 'RELEASE_VERSION_ALIGNMENT lock-package=%s expected=one-local-%s\n' "$crate" "$expected" >&2
    exit 1
  fi
done

guix_version="$(sed -n 's/^[[:space:]]*(version "\([^"]*\)").*/\1/p' guix.scm | head -n 1)"
if [[ "$guix_version" != "$expected" ]]; then
  printf 'RELEASE_VERSION_ALIGNMENT guix.scm expected=%s actual=%s\n' "$expected" "${guix_version:-missing}" >&2
  exit 1
fi

for required in \
  "sens-cli_${expected}_linux_amd64" \
  "sens-cli_${expected}_macos_arm64" \
  "sens-cli_${expected}_macos_x64" \
  "releases/download/${tag}/" \
  "sens ${expected}"; do
  if ! grep -Fq "$required" packaging/install.sh; then
    printf 'RELEASE_VERSION_ALIGNMENT installer-missing=%s\n' "$required" >&2
    exit 1
  fi
done

printf 'RELEASE_VERSION_ALIGNMENT=PASS version=%s tag=%s crates=%s\n' "$expected" "$tag" "${#crates[@]}"
