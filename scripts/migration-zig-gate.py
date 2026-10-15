#!/usr/bin/env python3
"""Fail-closed preparation gate: migration scripts ↔ Zig physical codec.

Thin entry: full implementation in _migration_zig_gate_body.py so the GO path
ships the sterile-corridor gate without a truncated placeholder on tip.
"""
from pathlib import Path
import runpy

body = Path(__file__).resolve().with_name("_migration_zig_gate_body.py")
runpy.run_path(str(body), run_name="__main__")
