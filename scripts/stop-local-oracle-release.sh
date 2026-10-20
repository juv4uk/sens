#!/bin/bash
set -euo pipefail

state_root=${XDG_STATE_HOME:-$HOME/.local/state}/sens
pid_file=$state_root/oracle-local.pid
oracle_port=${ORACLE_LOCAL_PORT:-9999}

if [ -f "$pid_file" ]; then
  pid=$(sed -n '1p' "$pid_file")
  case "$pid" in
    ''|*[!0-9]*) echo "ERROR: invalid pid file: $pid_file" >&2; exit 1 ;;
  esac
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    echo "stopped local Oracle pid=$pid"
    rm -f "$pid_file"
    exit 0
  fi
  echo "local Oracle pid=$pid is already absent; checking listener"
  rm -f "$pid_file"
fi

# Recover a manually started/orphaned Oracle only when its executable and
# command line prove that it owns the requested local port.
candidate=$(ss -ltnpH "sport = :$oracle_port" 2>/dev/null \
  | sed -n 's/.*pid=\([0-9][0-9]*\),.*/\1/p' | head -1 || true)
if [ -n "$candidate" ] && [ -r "/proc/$candidate/cmdline" ]; then
  exe=$(readlink -f "/proc/$candidate/exe" 2>/dev/null || true)
  cmdline=$(tr '\0' ' ' < "/proc/$candidate/cmdline" 2>/dev/null || true)
  case "$exe:$cmdline" in
    */sens:*" --tcp=$oracle_port"*)
      kill "$candidate"
      echo "stopped orphaned local Oracle pid=$candidate port=$oracle_port"
      exit 0
      ;;
  esac
fi
echo "local Oracle is not recorded as running; no verified process to stop"
