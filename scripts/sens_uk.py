#!/usr/bin/env python3
"""Third projection of #4449: render exact T5 words as canonical Ukrainian .lisp.

    render_uk(decode_T5(.sens))  ->  canonical Ukrainian human-readable .lisp

The word->surface map is taken from the repository's RATIFIED domain tables
(lib/domains/d1..d9.lisp), never from memory. Structural D2 words render as
brackets/spacing; exact words render as their `ук` surface; unknown words FAIL
CLOSED (we do not invent a surface).

Usage:
  sens_uk.py render <file.sens> [--out OUT.lisp]
  sens_uk.py render-words <w1> <w2> ...
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sens_t5_codec as C  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROW = re.compile(r"^\s*\(([01]{1,9})\s+\(ук\s+([^)]+)\)", re.MULTILINE)


def load_uk_surfaces() -> dict[str, str]:
    """word(bits) -> uk surface, from the ratified domain tables."""
    m: dict[str, str] = {}
    for f in sorted((ROOT / "lib/domains").glob("d*.lisp")):
        for bits, uk in ROW.findall(f.read_text(encoding="utf-8")):
            m.setdefault(bits, uk.strip())
    return m


def render_words(words: list[str], surfaces: dict[str, str]) -> str:
    """Render a flat T5 word stream as canonical Ukrainian .lisp text."""
    out: list[str] = []
    depth = 0
    for w in words:
        if w == "10":                       # D2 open
            out.append("("); depth += 1
        elif w == "01":                     # D2 close
            depth -= 1
            if depth < 0:
                raise C.SensT5Error("unbalanced close")
            out.append(")")
        elif w == "00":                     # D2 separator
            out.append(" ")
        elif w == "000":                    # canonical empty list
            out.append("()")
        elif w in surfaces:                 # exact word -> uk surface
            out.append(surfaces[w])
        else:
            raise C.SensT5Error(f"no ratified uk surface for word {w!r}")
    if depth != 0:
        raise C.SensT5Error("unbalanced open")
    return "".join(out).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render"); r.add_argument("sens"); r.add_argument("--out")
    rw = sub.add_parser("render-words"); rw.add_argument("words", nargs="+")
    ns = ap.parse_args()
    surfaces = load_uk_surfaces()
    if ns.cmd == "render":
        words = C.decode_bytes(pathlib.Path(ns.sens).read_bytes())
        text = render_words(words, surfaces)
        out = pathlib.Path(ns.out) if ns.out else pathlib.Path(ns.sens).with_suffix(".lisp")
        out.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0
    if ns.cmd == "render-words":
        print(render_words(ns.words, surfaces), end="")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
