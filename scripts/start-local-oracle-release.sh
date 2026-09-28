#!/bin/bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cache_root=${CARGO_TARGET_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/my-lisp-target}
oracle_port=${ORACLE_LOCAL_PORT:-9999}
state_root=${XDG_STATE_HOME:-$HOME/.local/state}/my-lisp
pid_file=$state_root/oracle-local.pid
log_file=$state_root/oracle-local.log
binary=$cache_root/release/my-lisp
cargo_bin=${CARGO_BIN:-cargo}

mkdir -p "$state_root"

if [ -f "$pid_file" ]; then
  old_pid=$(sed -n '1p' "$pid_file")
  if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
    echo "local Oracle already running: pid=$old_pid port=$oracle_port"
    exit 0
  fi
  rm -f "$pid_file"
fi

if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "(^|:)${oracle_port}$"; then
  echo "ERROR: local port already in use: $oracle_port" >&2
  exit 1
fi

if ! command -v "$cargo_bin" >/dev/null 2>&1; then
  echo "ERROR: cargo not found: $cargo_bin" >&2
  exit 1
fi

echo "Building release Oracle into $cache_root ..."
CARGO_TARGET_DIR="$cache_root" "$cargo_bin" build --release -p sens-cli --manifest-path "$project_root/Cargo.toml"
test -x "$binary" || {
  echo "ERROR: release binary missing: $binary" >&2
  exit 1
}

commit=$(git -C "$project_root" rev-parse --short HEAD)
version=$($binary --version)
printf 'commit=%s\nversion=%s\nport=%s\n' "$commit" "$version" "$oracle_port" > "$state_root/oracle-local.meta"

nohup "$binary" --tcp="$oracle_port" --protocol=sexpr >> "$log_file" 2>&1 &
oracle_pid=$!
printf '%s\n' "$oracle_pid" > "$pid_file"

for _ in $(seq 1 20); do
  if printf '%s\n' '(request (id 1) (op contract-version))' \
      | nc -w 1 127.0.0.1 "$oracle_port" > "$state_root/oracle-local.probe" 2>/dev/null; then
    if grep -q '(status ok)' "$state_root/oracle-local.probe"; then
      if printf '%s\n' '(request (id 2) (op eval) (source "(utc-now)"))' \
          | nc -w 1 127.0.0.1 "$oracle_port" > "$state_root/oracle-local-time.probe" 2>/dev/null \
          && grep -q '(status ok)' "$state_root/oracle-local-time.probe" \
          && grep -q '(value (utc ' "$state_root/oracle-local-time.probe"; then
        echo "local Oracle ready: pid=$oracle_pid port=$oracle_port commit=$commit version=$version"
        cat "$state_root/oracle-local.probe"
        cat "$state_root/oracle-local-time.probe"
        exit 0
      fi
    fi
  fi
  sleep 1
done

echo "ERROR: local Oracle did not answer its contract probe" >&2
echo "log: $log_file" >&2
kill "$oracle_pid" 2>/dev/null || true
rm -f "$pid_file"
exit 1
