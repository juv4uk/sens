#!/usr/bin/env python3
"""Check the current D7 keyboard/v2 source without calling historical UPC7.

The retired text7_projection_generated.rs is provenance only; the runtime
uses crates/sens/src/d7_keyboard.rs and knowledge/d7-keyboard-v2-ratified.json.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "knowledge/d7-keyboard-v2-ratified.json"
RUNTIME = ROOT / "crates/sens/src/lib.rs"
LEGACY = ROOT / "crates/sens/src/text7_projection_generated.rs"


def check() -> None:
    data = json.loads(CURRENT.read_text(encoding="utf-8"))
    if (data.get("schema"), data.get("status"), data.get("width"),
            data.get("capacity"), data.get("occupancy")) != (
            "sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128):
        raise ValueError("current 128/128 D7 authority mismatch")
    expected = [f"{i:07b}" for i in range(128)]
    if [row["bits"] for row in data["table"]] != expected:
        raise ValueError("current D7 coordinate drift")
    rust = RUNTIME.read_text(encoding="utf-8")
    if "mod text7_projection_generated;" in rust:
        raise ValueError("historical phonetic donor reconnected to active Rust")
    if "pub mod d7_keyboard;" not in rust:
        raise ValueError("current D7 keyboard runtime missing")
    # Legacy generated data may survive in the repository solely as an archive.
    # Its contents are never executed, imported, or regenerated here.
    print("D7 CURRENT: PASS — current 128/128 runtime; old donor unlinked")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.parse_args()
    check()
