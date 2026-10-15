#!/usr/bin/env bash
# Local-only corridor evidence (#5777/#5788). Needs cargo + Zig (pinned) + cc.
#
# Produces ONE JSON receipt with SEPARATE, non-blended statuses:
#   TRANSPORT_VERIFIED  Rust host and the Rust-free C host cross the same Zig ABI
#   RUST_FREE_VERIFIED  the C host link carries no Rust markers
#   SEMANTICS_VERIFIED  NEVER set here -- semantic conformance is a separate
#                       proof (#5788), never inferred from byte parity
#
# Fail-closed: exact clean SHA before AND after all steps is mandatory;
# unknown HEAD, wrong Git root, dirty source, or moving HEAD is BLOCKED.
# A local synthetic --self-test cannot award transport or release admission.
# Any step that exits non-zero also makes the receipt BLOCKED.
#
# Run:  bash scripts/corridor_local_evidence.sh
# Out:  $SENS_CORRIDOR_RECEIPT (default: ./corridor-local-evidence.json)

set -Eeuo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$root"

# Pure predicate shared by live preflight, postflight and synthetic negatives.
# A 40-hex exact source commit and an unchanged full checkout are compulsory.
source_identity_ok() {
  local candidate="$1" top="$2" dirty="$3" expected="$4"
  [[ "$candidate" =~ ^[0-9a-f]{40}$ && "$top" == "$expected" && -z "$dirty" ]]
}

if [[ "${1:-}" == "--self-test" && "$#" -eq 1 ]]; then
  sample="$(printf 'a%.0s' {1..40})"
  source_identity_ok "$sample" /tmp/source '' /tmp/source || exit 1
  for invalid in UNKNOWN abc ABCDEF; do
    if source_identity_ok "$invalid" /tmp/source '' /tmp/source; then
      echo "CORRIDOR_PROVENANCE_SELFTEST_FAIL case=missing_or_short_sha" >&2
      exit 1
    fi
  done
  if source_identity_ok "$sample" /tmp/other '' /tmp/source; then
    echo "CORRIDOR_PROVENANCE_SELFTEST_FAIL case=wrong_repository_root" >&2
    exit 1
  fi
  if source_identity_ok "$sample" /tmp/source ' M src.rs' /tmp/source; then
    echo "CORRIDOR_PROVENANCE_SELFTEST_FAIL case=tracked_mutation" >&2
    exit 1
  fi
  if source_identity_ok "$sample" /tmp/source '?? new.sens' /tmp/source; then
    echo "CORRIDOR_PROVENANCE_SELFTEST_FAIL case=untracked_mutation" >&2
    exit 1
  fi
  echo "CORRIDOR_PROVENANCE_SELFTEST_PASS positives=1 negatives=6 verdict=SOURCE_ONLY semantic_authority=SENS"
  exit 0
fi
if [[ "$#" -ne 0 ]]; then
  echo 'usage: corridor_local_evidence.sh [--self-test]' >&2
  exit 2
fi

read_source_state() {
  source_sha="$(git rev-parse --verify HEAD 2>/dev/null || printf UNKNOWN)"
  source_root="$(git rev-parse --show-toplevel 2>/dev/null || printf UNKNOWN)"
  source_dirty="$(git status --porcelain=v1 --untracked-files=all 2>/dev/null)" || source_dirty='UNAVAILABLE'
}

receipt="${SENS_CORRIDOR_RECEIPT:-$PWD/corridor-local-evidence.json}"
logdir="$(mktemp -d -t corridor-evidence-XXXXXXXX)"
trap 'rm -rf "$logdir"' EXIT

# No successful release receipt may name UNKNOWN, a foreign checkout, or
# bytes that differ from its exact commit. Perform this before any build.
read_source_state
if ! source_identity_ok "$source_sha" "$source_root" "$source_dirty" "$root"; then
  echo 'CORRIDOR_LOCAL_EVIDENCE_BLOCKED phase=source-provenance reason=invalid-sha-root-or-dirty-tree' >&2
  exit 1
fi
sha="$source_sha"
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

# A long cross-host build can itself alter the checkout (or another writer
# can advance HEAD). Such bytes must not receive this SHA's green receipt.
read_source_state
provenance='CLEAN_EXACT_SHA'
if ! source_identity_ok "$source_sha" "$source_root" "$source_dirty" "$root" ||
   [[ "$source_sha" != "$sha" ]]; then
  provenance='BLOCKED_SOURCE_DRIFT'
  overall=1
  echo 'CORRIDOR_LOCAL_EVIDENCE_BLOCKED phase=postflight reason=head-or-working-tree-changed' >&2
fi

python3 - "$receipt" "$sha" "$pinned" "$zig_ver" "$cc_present" "$overall" "$provenance" "$logdir" \
         "${steps[@]}" <<'PY'
import json, pathlib, sys
receipt, sha, pinned, zig_ver, cc_present, overall, provenance, logdir, *steps = sys.argv[1:]
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
    "source_provenance": provenance,
    "source_clean_exact_sha": provenance == "CLEAN_EXACT_SHA",
    "TRANSPORT_VERIFIED": overall == "0" and provenance == "CLEAN_EXACT_SHA",
    "RUST_FREE_VERIFIED": overall == "0" and provenance == "CLEAN_EXACT_SHA",  # tested link marker inspection
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
