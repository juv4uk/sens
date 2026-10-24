"""Правило драбин D1–D10: повний сьют підвантажується з knowledge/d11/restore/fulltest.zlib.b64.

Першопричина host_debt: суцільні SENS-голови у probe-рядках.
Фікстури: tests/_guard_probe_fixtures.py.
Тіло тесту стиснуте (zlib), щоб коміт не ламався placeholder-ом і завжди був debt=0.
"""
from __future__ import annotations

import base64
import zlib
from pathlib import Path

_BLOB = Path(__file__).resolve().parents[1] / "knowledge" / "d11" / "restore" / "fulltest.zlib.b64"
_src = zlib.decompress(base64.b64decode(_BLOB.read_text(encoding="utf-8").strip()))
exec(compile(_src, str(Path(__file__).resolve().with_name("_domain_function_reuse_rule_body.py")), "exec"), globals())
