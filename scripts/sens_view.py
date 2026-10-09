#!/usr/bin/env python3
"""T5 spaced-bit VIEW generator/checker (#4694 / #4449).

Three projections of one admitted program (owner directive 2026-10-09):
  path/name.lisp  — canonical Ukrainian human-readable projection (uk surface)
  path/name.sens  — physical T5 machine file (exact D1-D9 words; 5 trits/byte)
  path/name       — generated read-only VIEW: exact bit-words [01]+ separated by
                    exactly one space, one trailing newline. No brackets, names,
                    trit '2', headers, comments, width tags or padding.

This tool owns the .sens <-> view edge and proves the reversible identity:

    decode_T5(.sens) -> typed exact-width words -> canonical view(name)
    parse_view(name) -> encode_T5          -> byte-identical .sens

It reuses the repository codec (sens_t5_codec.py); it is not a new codec,
parser, domain table or semantic oracle. Fail-closed.

Usage:
  sens_view.py emit  <file.sens> [--out OUT]   # write the view
  sens_view.py check <file.sens>               # verify view == parse(.sens)
  sens_view.py parse <view-file> [--out OUT.sens]
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sens_t5_codec as C  # noqa: E402


def view_from_words(words: list[str]) -> str:
    """Canonical view: exact words, one space between, one trailing newline."""
    return " ".join(words) + "\n"


def words_from_view(text: str) -> list[str]:
    """Parse a canonical view. Reject anything that is not [01]+ tokens."""
    stripped = text[:-1] if text.endswith("\n") else text
    if "\n" in stripped:
        raise C.SensT5Error("view must be a single line")
    if stripped == "":
        raise C.SensT5Error("empty view")
    words = stripped.split(" ")
    for w in words:
        if not C.BITS.fullmatch(w):
            raise C.SensT5Error(f"non-canonical view token: {w!r}")
    return words


def emit(sens_path: pathlib.Path) -> str:
    return view_from_words(C.decode_bytes(sens_path.read_bytes()))


def check(sens_path: pathlib.Path) -> tuple[bool, str]:
    """Verify decode->view->parse->encode is byte-identical to the .sens."""
    raw = sens_path.read_bytes()
    words = C.decode_bytes(raw)
    view = view_from_words(words)
    reparsed = words_from_view(view)
    if reparsed != words:
        return False, "view->words mismatch"
    if C.encode_words(reparsed) != raw:
        return False, "re-encode not byte-identical"
    return True, view


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_emit = sub.add_parser("emit"); p_emit.add_argument("sens"); p_emit.add_argument("--out")
    p_chk = sub.add_parser("check"); p_chk.add_argument("sens")
    p_par = sub.add_parser("parse"); p_par.add_argument("view"); p_par.add_argument("--out")
    ns = ap.parse_args()

    if ns.cmd == "emit":
        view = emit(pathlib.Path(ns.sens))
        out = pathlib.Path(ns.out) if ns.out else pathlib.Path(ns.sens).with_suffix("")
        out.write_text(view, encoding="utf-8")
        print(f"wrote view {out} ({len(view)} bytes)")
        return 0

    if ns.cmd == "check":
        ok, detail = check(pathlib.Path(ns.sens))
        print(("OK " if ok else "FAIL ") + str(ns.sens) + ("  " + detail if not ok else ""))
        return 0 if ok else 1

    if ns.cmd == "parse":
        words = words_from_view(pathlib.Path(ns.view).read_text(encoding="utf-8"))
        data = C.encode_words(words)
        out = pathlib.Path(ns.out) if ns.out else pathlib.Path(ns.view).with_suffix(".sens")
        out.write_bytes(data)
        print(f"wrote .sens {out} ({len(data)} bytes)")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
