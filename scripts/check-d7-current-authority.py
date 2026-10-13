#!/usr/bin/env python3
"""Current D7 owner gate; historical phonetic 126-cell profile is archived, not authority.

Keep the stable script entrypoint used by active CI, but make its checks
delegate to the fail-closed, ratified D7 keyboard/v2 witness.  No assertions
and no automatic reinterpretation of historical D7 bitstreams.
"""
from __future__ import annotations
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "scripts/check-d7-keyboard-v2-table.py"
if not CURRENT.is_file():
    raise SystemExit("D7-CURRENT-AUTHORITY: BLOCKED missing keyboard/v2 gate")
runpy.run_path(str(CURRENT), run_name="__main__")
print("D7-CURRENT-AUTHORITY: PASS keyboard/v2 128/128, legacy v1 not authoritative")
