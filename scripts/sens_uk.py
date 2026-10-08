#!/usr/bin/env python3
"""Research-only Ukrainian renderer for exact physical T5 words (#4449).

This renderer is NOT a Ukrainian↔SENS semantic oracle. Its output is sent
to stdout by default. An explicitly requested --out path must be OUTSIDE
the repository and is created atomically, never overwritten. In particular,
running 'render lib/foo.sens' MUST NEVER write or clobber lib/foo.lisp.

Release-facing triple proof: scripts/verify_uk_t5_triplet.py (bounded grammar).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sens_t5_codec as C  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r"^\s*\(([01]{1,9})\s+\(ук\s+([^)]+)\)", re.MULTILINE)


def load_uk_surfaces() -> dict[str, str]:
    """Exact words -> Ukrainian surface from ratified domain tables only."""
    result: dict[str, str] = {}
    for path in sorted((ROOT / "lib/domains").glob("d*.lisp")):
        for bits, uk in ROW.findall(path.read_text(encoding="utf-8")):
            spelling = uk.strip()
            if not spelling or (bits in result and result[bits] != spelling):
                raise C.SensT5Error(f"ambiguous ratified Ukrainian surface: {bits}")
            result[bits] = spelling
    if not result:
        raise C.SensT5Error("missing ratified Ukrainian surfaces")
    return result


def render_words(words: list[str], surfaces: dict[str, str]) -> str:
    """Print one structurally sound expression; don't certify its semantics.

    Reject malformed D2 separator/close sequences, implicit empty lists and
    multiple roots. D2 dotted-pair syntax is intentionally not admitted here.
    """
    if not words:
        raise C.SensT5Error("empty exact-word program")
    result: list[str] = []
    frames: list[int] = []  # 0: item expected, 1: separator or close expected
    top_item = False

    def begin_item() -> None:
        nonlocal top_item
        if frames:
            if frames[-1] != 0:
                raise C.SensT5Error("missing D2 separator between list items")
            frames[-1] = 1
        else:
            if top_item:
                raise C.SensT5Error("multiple top-level expressions unsupported")
            top_item = True

    for word in words:
        if word == "10":  # D2 open
            if len(frames) >= 256:
                raise C.SensT5Error("D2 nesting exceeds bounded renderer")
            begin_item()
            result.append("(")
            frames.append(0)
        elif word == "01":  # D2 close
            if not frames or frames[-1] != 1:
                raise C.SensT5Error("unbalanced/empty D2 list; use D3 EMPTY")
            frames.pop()
            result.append(")")
        elif word == "00":  # D2 separator
            if not frames or frames[-1] != 1:
                raise C.SensT5Error("misplaced D2 separator")
            frames[-1] = 0
            result.append(" ")
        elif word == "11":  # D2 dot
            raise C.SensT5Error("D2 dotted-pair renderer not proven")
        elif word == "000":
            begin_item()
            result.append("()")
        elif word in surfaces:
            begin_item()
            result.append(surfaces[word])
        else:
            raise C.SensT5Error(f"no ratified Ukrainian surface for word {word!r}")
    if frames:
        raise C.SensT5Error("unterminated D2 list")
    return "".join(result) + "\n"


def _stage_only_new_outside_repo(path: Path, payload: bytes) -> None:
    """Atomic no-clobber external output; never write canonical source .lisp."""
    if not path.is_absolute():
        raise C.SensT5Error("--out must be an absolute staging path outside repository")
    if path.is_relative_to(ROOT) or path.resolve().is_relative_to(ROOT.resolve()):
        raise C.SensT5Error("refusing to write inside SENS repository")
    parent = path.parent
    if not parent.is_dir():
        raise C.SensT5Error("staging parent directory must already exist")
    if path.exists() or path.is_symlink():
        raise C.SensT5Error("output already exists; no overwrite")
    if any(item.is_symlink() for item in (parent, *parent.parents)):
        raise C.SensT5Error("staging symlink ancestor forbidden")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=parent, prefix=".sens-uk-", delete=False) as file:
            temporary = Path(file.name)
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        os.link(temporary, path)
    except FileExistsError as exc:
        raise C.SensT5Error("output already exists; no overwrite") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    renderer = sub.add_parser("render")
    renderer.add_argument("sens")
    renderer.add_argument("--out", type=Path, help="absolute outside-repo staging path; no overwrite")
    renderer_words = sub.add_parser("render-words")
    renderer_words.add_argument("words", nargs="+")
    args = parser.parse_args(argv)
    try:
        surfaces = load_uk_surfaces()
        if args.cmd == "render":
            source = Path(args.sens)
            if source.is_symlink() or not source.is_file():
                raise C.SensT5Error("physical .sens missing or symlink")
            words = C.decode_bytes(source.read_bytes())
            rendered = render_words(words, surfaces)
            if args.out is not None:
                _stage_only_new_outside_repo(args.out, rendered.encode("utf-8"))
        else:
            rendered = render_words(args.words, surfaces)
        sys.stdout.write(rendered)
        return 0
    except (C.SensT5Error, OSError, ValueError) as exc:
        print(f"UK RENDER BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
