#!/usr/bin/env python3
"""Guard: the sterile Zig corridor is the ONLY path to a published .sens (#5777/#5779).

Owner rule (2026-10-15): the Rust/Python<->SENS link crosses ONLY the sterile Zig
corridor. There are no other paths. If there were, contamination would reach the
SENS machine. So a physical .sens may be published ONLY after the pinned Zig
transport has certified the bytes; there is no silent Python fallback.

This is a STRUCTURAL, fail-closed checker (it does not run Zig):
M1  scripts/migrate-t5-batch.py imports the corridor bridge `zig_codec_bridge`.
M2  it builds the pinned transport (`zig_codec_bridge.build_transport`).
M3  it certifies the candidate bytes through Zig (`zig_codec_bridge.verify_t5`).
M4  publishing (`--write`) REQUIRES `--zig-codec` and fails closed without it --
    the gate `if args.write and not args.zig_codec` must be present.
M5  the Zig certification precedes the publish staging: `verify_t5(` appears
    before the first `staged.append(` in the source.
M6  scripts/zig_codec_bridge.py fails closed: it pins the compiler (0.16.0),
    raises ZigCodecError, refuses to overwrite the built binary, and rejects a
    non-attested binary.

Exit 0 = MIGRATION_ZIG_ONLY_PATH_OK; exit 1 = MIGRATION_ZIG_ONLY_PATH_BLOCKED.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BATCH = "scripts/migrate-t5-batch.py"
BRIDGE = "scripts/zig_codec_bridge.py"


def check(root: Path) -> list[str]:
    problems: list[str] = []
    batch_path = root / BATCH
    bridge_path = root / BRIDGE
    if not batch_path.is_file():
        return [f"missing {BATCH}"]
    if not bridge_path.is_file():
        return [f"missing {BRIDGE}"]
    batch = batch_path.read_text(encoding="utf-8")
    bridge = bridge_path.read_text(encoding="utf-8")

    # M1 -- the migration driver uses the corridor bridge.
    if "import zig_codec_bridge" not in batch:
        problems.append("M1: migrate-t5-batch.py does not import zig_codec_bridge "
                        "(no sterile Zig corridor on the migration path)")

    # M2 -- it builds the pinned transport.
    if "zig_codec_bridge.build_transport(" not in batch:
        problems.append("M2: migrate-t5-batch.py does not call "
                        "zig_codec_bridge.build_transport (no pinned Zig transport)")

    # M3 -- it certifies the candidate bytes through Zig.
    if "zig_codec_bridge.verify_t5(" not in batch:
        problems.append("M3: migrate-t5-batch.py does not call "
                        "zig_codec_bridge.verify_t5 (bytes are never certified by Zig)")

    # M4 -- publishing requires the corridor, fail-closed.
    if "if args.write and not args.zig_codec" not in batch:
        problems.append("M4: --write does not require --zig-codec; a physical .sens "
                        "could be published WITHOUT the sterile Zig corridor")

    # M5 -- the Zig certification precedes the publish staging.
    verify_at = batch.find("zig_codec_bridge.verify_t5(")
    staged_at = batch.find("staged.append(")
    if verify_at == -1 or staged_at == -1:
        problems.append("M5: cannot order Zig certification before publish staging "
                        "(verify_t5 or staged.append missing)")
    elif verify_at > staged_at:
        problems.append("M5: publish staging (staged.append) precedes the Zig "
                        "certification (verify_t5); a file could be staged uncertified")

    # M6 -- the bridge itself fails closed.
    if "ZigCodecError" not in bridge:
        problems.append("M6: zig_codec_bridge.py has no fail-closed ZigCodecError")
    if '"0.16.0"' not in bridge or "PIN_DRIFT" not in bridge:
        problems.append("M6: zig_codec_bridge.py does not pin the compiler (0.16.0)")
    if "ZIG_CODEC_OUTPUT_EXISTS" not in bridge:
        problems.append("M6: zig_codec_bridge.py does not refuse to overwrite the binary")
    if "UNATTESTED_BINARY" not in bridge:
        problems.append("M6: zig_codec_bridge.py does not reject a non-attested binary")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except OSError as exc:
        print(f"MIGRATION_ZIG_ONLY_PATH_BLOCKED: {exc}", flush=True)
        return 1
    if problems:
        print("MIGRATION_ZIG_ONLY_PATH_BLOCKED:", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print("MIGRATION_ZIG_ONLY_PATH_OK the sterile Zig corridor is the only path to "
          "a published .sens (build + certify + --write gate + fail-closed bridge)",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
