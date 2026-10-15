#!/usr/bin/env bash
# Local-only corridor evidence (#5777/#5788). Needs cargo + Zig (pinned) + cc.
#
# Produces ONE JSON receipt with SEPARATE, non-blended statuses:
#   TRANSPORT_VERIFIED  Rust host and the Rust-free C host cross the same Zig ABI
#   RUST_FREE_VERIFIED  the C host link carries no Rust markers
#   SEMANTICS_VERIFIED  NEVER set here -- semantic conformance is a separate
#                       proof (#5788), never inferred from byte parity
#
# Fail-closed: any step that exits non-zero makes the receipt status BLOCKED and
# the script exits non-zero. Never turns a red step green.
#
# Run:  bash scripts/corridor_local_evidence.sh
# Out:  $SENS_CORRIDOR_RECEIPT (default: ./corridor-local-evidence.json)

set -Eeuo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

receipt="${SENS_CORRIDOR_RECEIPT:-$PWD/corridor-local-evidence.json}"
logdir="$(mktemp -d -t corridor-evidence-XXXXXXXX)"
trap 'rm -rf "$logdir"' EXIT

sha="$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
pinned="$(cat .zig-version 2>/dev/null || echo MISSING)"
zig_ver="$(command -v zig >/dev/null 2>&1 && zig version || echo MISSING)"
cc_present="$(command -v cc >/dev/null 2>&1 && echo yes || echo no)"

steps=(rust-corridor-build c-host-transport h2-physical-parity h1-link-closure)
cmds=(
  "cargo build --locked -p sens-cli --bin sens-trit"
  "bash research/zig-codecs/host-c/verify.sh"
  "python3 research/zig-codecs/host-c/verify_h2_physical_parity.py --run"
  "python3 research/zig-codecs/host-c/audit_rust_free_link.py --run"
)

overall=0
for i in "${!steps[@]}"; do
  name="${steps[$i]}"; cmd="${cmds[$i]}"
  log="$logdir/$name.log"
  set +e
  eval "$cmd" >"$log" 2>&1
  rc=$?
  set -e
  printf '%-22s exit=%s\n' "$name" "$rc"
  if [[ "$rc" -ne 0 ]]; then overall=1; fi
done

python3 - "$receipt" "$sha" "$pinned" "$zig_ver" "$cc_present" "$overall" "$logdir" \
         "${steps[@]}" <<'PY'
import json, pathlib, sys
receipt, sha, pinned, zig_ver, cc_present, overall, logdir, *steps = sys.argv[1:]
logs = {}
for name in steps:
    p = pathlib.Path(logdir) / f"{name}.log"
    text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    logs[name] = {"first_line": lines[0] if lines else "", "line_count": len(lines)}
status = "BLOCKED" if overall != "0" else "TRANSPORT_VERIFIED"
data = {
    "schema": "sens-corridor-local-evidence/v1",
    "sha": sha,
    "zig_pinned": pinned,
    "zig_actual": zig_ver,
    "cc_present": cc_present,
    "status": status,
    "TRANSPORT_VERIFIED": overall == "0",
    "RUST_FREE_VERIFIED": overall == "0",   # from verify.sh dependency inspection
    "SEMANTICS_VERIFIED": False,            # separate proof #5788, never inferred here
    "steps": logs,
    "note": "Byte/physical transport only. SEMANTICS_VERIFIED is deliberately false: "
            "transport parity is not semantic PASS (#5777/#5788).",
}
pathlib.Path(receipt).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"CORRIDOR_LOCAL_EVIDENCE status={status} sha={sha[:10]} zig={zig_ver}")
print(f"receipt={receipt}")
PY

if [[ "$overall" -ne 0 ]]; then
  echo 'CORRIDOR_LOCAL_EVIDENCE_BLOCKED a corridor step failed -- see the receipt' >&2
  exit 1
fi
