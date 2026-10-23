#!/usr/bin/env python3
"""Свідок: один фізичний носій T5M → кілька людських проєкцій (ук / en / sa / LISP).

Доводить модель власника (2026-10-09): пишемо однією проєкцією, кодуємо у
фізичні T5M-байти, декодуємо будь-якою доступною проєкцією. Інваріант —
точність СЛІВ: decode_t5m_bytes(encode_t5m_projection(w)) == w, тож сама
людська проєкція не впливає на виконуваний код.

Фіксований вхід і фіксований хеш байтів — щоб прогін був відтворюваний у CI.
Джерела: lib/surface/semantic-registry.lisp (ук/en/sa), lib/domains/d*.lisp (LISP).
Скрипт нічого не переписує; він лише читає й перевіряє. Fail-closed.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sens_t5_t5m_codec import decode_t5m_bytes, encode_t5m_projection  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Фіксований вхід: виконувані укр-голови (реєстрові символи), зняті з
# scripts/check-encoder-coverage.lisp. Порядок незмінний.
UKR_INPUT = (
    "та визначити перше за-умовою за-умовою як-є перше список як-є як-є "
    "перше сполучити як-є"
)
EXPECTED_T5M_SHA256 = "3117cc3b77dd3108d4d835ddb284cecfcce08545fab0424f2132fd0b28181e38"

ENTRY = re.compile(r"^\s*\(([01]{8})\s+(.*)\)\s*$")
SURFACE = re.compile(r"\(([^\s()]+)\s+(\(\)|[^\s()]+)\)")
DOMAIN = re.compile(
    r"\(ук ([^)]*)\)\s*\(укр ([^)]*)\)\s*\(san ([^)]*)\)\s*"
    r"\(en ([^)]*)\)\s*\(LISP ([^)]*)\)"
)


def _token(raw: str) -> str:
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        return raw[1:-1]
    return raw


def registry_rows() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    text = (ROOT / "lib" / "surface" / "semantic-registry.lisp").read_text(
        encoding="utf-8"
    )
    for line in text.splitlines():
        match = ENTRY.match(line)
        if not match:
            continue
        sid, body = match.groups()
        surfaces: dict[str, str] = {}
        for surface in SURFACE.finditer(body):
            language, raw = surface.groups()
            name = _token(raw)
            if name not in ("()", "—"):
                surfaces[language] = name
        rows[sid] = surfaces
    return rows


def lisp_projection() -> tuple[dict[str, str], dict[str, str]]:
    uk2lisp: dict[str, str] = {}
    en2lisp: dict[str, str] = {}
    for path in sorted((ROOT / "lib" / "domains").glob("d*.lisp")):
        for match in DOMAIN.finditer(path.read_text(encoding="utf-8")):
            uk, _ukr, _san, en, lisp = match.groups()
            if lisp not in ("()", ""):
                uk2lisp.setdefault(uk, lisp)
                en2lisp.setdefault(en, lisp)
    return uk2lisp, en2lisp


def main() -> int:
    rows = registry_rows()
    uk2sid = {s["ук"]: sid for sid, s in rows.items() if "ук" in s}
    symbols = UKR_INPUT.split()
    missing = [s for s in symbols if s not in uk2sid]
    if missing:
        print(f"FAIL: символи відсутні в реєстрі: {missing}")
        return 1

    words = [uk2sid[s] for s in symbols]
    physical = encode_t5m_projection(" ".join(words))
    decoded = decode_t5m_bytes(physical)
    if decoded != words:
        print("FAIL: decode_t5m_bytes(encode_t5m_projection(w)) != w")
        return 1

    digest = hashlib.sha256(physical).hexdigest()
    if digest != EXPECTED_T5M_SHA256:
        print(f"FAIL: T5M sha256 {digest} != {EXPECTED_T5M_SHA256}")
        return 1

    uk2lisp, en2lisp = lisp_projection()

    def render(surface: str) -> str:
        if surface == "LISP":
            return " ".join(
                uk2lisp.get(
                    rows[w].get("ук", ""), en2lisp.get(rows[w].get("en", ""), "?")
                )
                for w in decoded
            )
        return " ".join(rows[w].get(surface, "?") for w in decoded)

    print(f"T5M байти    : {physical.hex()} ({len(physical)} байт)")
    print(f"T5M sha256   : {digest}")
    print(f"decode==words: {decoded == words}")
    for surface in ("ук", "en", "sa", "LISP"):
        print(f"'{surface}'".ljust(13) + ": " + render(surface))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
