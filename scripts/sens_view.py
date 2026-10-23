#!/usr/bin/env python3
"""T5M spaced-bit VIEW generator/checker (#4694 / #4449).

Three projections of one admitted program (owner directive 2026-10-09):
  path/name.lisp  — canonical Ukrainian human-readable projection (укр surface)
  path/name.sens  — physical T5M machine file (exact words; 5 trits/byte)
  path/name       — generated read-only VIEW: exact bit-words [01]+ separated by
                    exactly one space, one trailing newline. No brackets, names,
                    trit '2', headers, comments, width tags or padding.

This tool owns the .sens <-> view edge and proves the reversible identity:

    decode_T5M(.sens) -> exact-width words -> canonical view(name)
    parse_view(name) -> encode_T5M         -> byte-identical .sens

It reuses the repository codec (sens_t5_t5m_codec.py); it is not a new codec,
parser, domain table or semantic oracle. Fail-closed.

Usage:
  sens_view.py emit  <file.sens> [--out OUT]   # write the view
  sens_view.py check <file.sens>               # verify view == parse(.sens)
  sens_view.py parse <view-file> [--out OUT.sens]  # старий запис заборонено; тільки Zig/T5M
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sens_t5_t5m_codec as C  # noqa: E402


def view_from_words(words: list[str]) -> str:
    """Canonical view: exact words, one space between, one trailing newline."""
    return " ".join(words) + "\n"


def words_from_view(text: str) -> list[str]:
    """Only single-space 0/1 words followed by exactly one newline."""
    if re.fullmatch(r"[01]+(?: [01]+)*\n", text) is None:
        raise C.SensT5Error("non-canonical spaced-bit view")
    words = text[:-1].split(" ")
    C.parse_t5m_words(text)
    return words

def emit(sens_path: pathlib.Path) -> str:
    return view_from_words(C.decode_t5m_bytes(sens_path.read_bytes()))


def check(sens_path: pathlib.Path) -> tuple[bool, str]:
    """Verify both the physical T5M carrier and the existing adjacent view."""
    raw = sens_path.read_bytes()
    words = C.decode_t5m_bytes(raw)
    view = view_from_words(words)
    if words_from_view(view) != words:
        return False, "view->words mismatch"
    if C.encode_t5m_projection(view) != raw:
        return False, "T5M re-encode not byte-identical"
    adjacent = sens_path.with_suffix("")
    if adjacent.is_symlink() or not adjacent.is_file():
        return False, "same-stem view missing or linked"
    if adjacent.read_bytes() != view.encode("ascii"):
        return False, "same-stem view stale or noncanonical"
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
        with out.open("x", encoding="utf-8", newline="\n") as target:
            target.write(view)
        print(f"wrote view {out} ({len(view)} bytes)")
        return 0

    if ns.cmd == "check":
        ok, detail = check(pathlib.Path(ns.sens))
        print(("OK " if ok else "FAIL ") + str(ns.sens) + ("  " + detail if not ok else ""))
        return 0 if ok else 1

    if ns.cmd == "parse":
        # Відновлення слів дозволене як перевірка, але Python більше
        # не карбує фізичний .sens. Фізичну пару створює Zig/T5M,
        # а доказ виконання належить SENS.
        words_from_view(pathlib.Path(ns.view).read_text(encoding="utf-8"))
        print("LEGACY_PYTHON_T5M_PUBLICATION_DISABLED: "
              "use migrate-one-to-sens.py with pinned Zig/T5M", file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
