#!/usr/bin/env python3
"""Three-pass inventory of legacy Lisp source forms.

Pass order is intentional:
  1. legacy exact 8-bit SID8/SENS8 call heads;
  2. my-lisp surface call heads (lowercase/symbolic spellings) + literal ();
  3. historical Lisp 1 / Lisp 1.5 UPPERCASE call heads.

The authoritative mapping is parsed from:
  contracts/core1-historical-sid-map.lisp

This tool inventories syntax only. It does not rewrite source and does not
assign current D1-D7 semantics.
"""
from __future__ import annotations

import argparse
import collections
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import re
from typing import Iterable

SOURCE_EXTS = {".lisp", ".lsp", ".cl", ".scm", ".rkt", ".sens"}
SKIP_DIRS = {
    ".git", ".hg", ".svn", "target", "node_modules", "vendor",
    ".venv", "venv", "dist", "build", "__pycache__",
}

ROW_RE = re.compile(
    r"^\s*\(row\s+([01]{8})\s+([^\s()]+)\s+([^\s()]+)\s+"
    r"([^\s()]+)\s+([^\s()]+)\s+([^\s()]+)\s*\)",
    re.MULTILINE,
)


@dataclass(frozen=True)
class Mapping:
    sid8: str
    my_lisp: str
    historical: str
    source: str
    fit: str
    status: str


@dataclass(frozen=True)
class Head:
    path: str
    line: int
    column: int
    start: int
    end: int
    token: str
    quoted: bool
    empty_list: bool = False


@dataclass(frozen=True)
class Hit:
    pass_number: int
    representation: str
    path: str
    line: int
    column: int
    token: str
    sid8: str
    my_lisp: str
    historical: str
    historical_source: str
    fit: str
    status: str


def strip_contract_comments(text: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in text.splitlines())


def load_mapping(path: Path) -> tuple[list[Mapping], dict[str, Mapping], dict[str, Mapping], dict[str, list[Mapping]]]:
    source = strip_contract_comments(path.read_text(encoding="utf-8"))
    rows = [
        Mapping(*match.groups())
        for match in ROW_RE.finditer(source)
    ]
    if not rows:
        raise SystemExit(f"{path}: no historical SID rows found")

    by_sid: dict[str, Mapping] = {}
    by_my: dict[str, Mapping] = {}
    by_historical_upper: dict[str, list[Mapping]] = {}

    for row in rows:
        if row.sid8 in by_sid and by_sid[row.sid8] != row:
            raise SystemExit(f"{path}: duplicate SID8 {row.sid8}")
        by_sid[row.sid8] = row

        # One my-lisp spelling may intentionally share a historical mechanism;
        # exact duplicate spellings with different SIDs would be ambiguous.
        old = by_my.get(row.my_lisp)
        if old is not None and old.sid8 != row.sid8:
            raise SystemExit(
                f"{path}: ambiguous my-lisp spelling {row.my_lisp!r}: "
                f"{old.sid8} vs {row.sid8}"
            )
        by_my[row.my_lisp] = row

        # Pass 3 recognizes the UPPERCASE source spelling of every historical
        # Lisp 1/1.5 name. Multiple old SID8 rows may legitimately share one
        # historical spelling (e.g. DEFINE), so preserve all candidates.
        historical_upper = row.historical.upper()
        if any(ch.isalpha() for ch in historical_upper):
            by_historical_upper.setdefault(historical_upper, []).append(row)


    return rows, by_sid, by_my, by_historical_upper


def line_col(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    last = text.rfind("\n", 0, offset)
    return line, offset + 1 if last < 0 else offset - last


def scan_heads(path: str, text: str) -> list[Head]:
    """Return executable list heads, excluding strings/comments/quoted data."""
    heads: list[Head] = []
    frames: list[dict[str, object]] = []
    i = 0
    pending_quote = False
    block_depth = 0

    def current_quoted() -> bool:
        return bool(frames and frames[-1]["quoted"])

    while i < len(text):
        ch = text[i]

        if block_depth:
            if text.startswith("#|", i):
                block_depth += 1
                i += 2
            elif text.startswith("|#", i):
                block_depth -= 1
                i += 2
            else:
                i += 1
            continue

        if ch == ";":
            end = text.find("\n", i)
            i = len(text) if end < 0 else end + 1
            continue

        if text.startswith("#|", i):
            block_depth = 1
            i += 2
            continue

        if ch == '"':
            i += 1
            while i < len(text):
                if text[i] == "\\" and i + 1 < len(text):
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            pending_quote = False
            # A string can syntactically occupy a list-head position, but it is
            # never one of the three source notations we inventory.
            if frames and frames[-1]["need_head"]:
                frames[-1]["need_head"] = False
            continue

        if text.startswith("#'", i):
            pending_quote = True
            i += 2
            continue
        if ch in ("'", "`"):
            pending_quote = True
            i += 1
            continue
        if ch == ",":
            pending_quote = True
            i += 2 if i + 1 < len(text) and text[i + 1] == "@" else 1
            continue

        if ch == "(":
            quoted = current_quoted() or pending_quote
            frames.append({
                "quoted": quoted,
                "need_head": True,
                "open_offset": i,
            })
            pending_quote = False
            i += 1
            continue

        if ch == ")":
            if frames:
                frame = frames.pop()
                if frame["need_head"] and not frame["quoted"]:
                    open_offset = int(frame["open_offset"])
                    line, col = line_col(text, open_offset)
                    heads.append(
                        Head(path, line, col, open_offset, i + 1, "()", False, True)
                    )
            pending_quote = False
            i += 1
            continue

        if ch.isspace():
            i += 1
            continue

        start = i
        while i < len(text):
            if text[i].isspace() or text[i] in "()\";',":
                break
            if text.startswith("#|", i):
                break
            i += 1
        token = text[start:i]
        if not token:
            i += 1
            continue

        if frames and frames[-1]["need_head"]:
            frame = frames[-1]
            if not frame["quoted"]:
                line, col = line_col(text, start)
                heads.append(Head(path, line, col, start, i, token, False))
            frame["need_head"] = False

        pending_quote = False

    return heads


def classify_three_passes(
    heads: Iterable[Head],
    by_sid: dict[str, Mapping],
    by_my: dict[str, Mapping],
    by_historical_upper: dict[str, list[Mapping]],
) -> list[Hit]:
    heads = list(heads)
    claimed: set[tuple[str, int, int]] = set()
    hits: list[Hit] = []

    def key(head: Head) -> tuple[str, int, int]:
        return (head.path, head.start, head.end)

    def add(
        pass_number: int,
        representation: str,
        head: Head,
        rows: Mapping | list[Mapping] | None,
    ) -> None:
        claimed.add(key(head))
        if rows is None:
            candidates: list[Mapping] = []
        elif isinstance(rows, list):
            candidates = rows
        else:
            candidates = [rows]

        def joined(field: str) -> str:
            values = []
            for row in candidates:
                value = str(getattr(row, field))
                if value not in values:
                    values.append(value)
            return "|".join(values)

        hits.append(
            Hit(
                pass_number=pass_number,
                representation=representation,
                path=head.path,
                line=head.line,
                column=head.column,
                token=head.token,
                sid8=joined("sid8") if candidates else (head.token if pass_number == 1 else ""),
                my_lisp=joined("my_lisp"),
                historical=joined("historical"),
                historical_source=joined("source"),
                fit=joined("fit"),
                status=joined("status") if candidates else "unmapped",
            )
        )


    # PASS 1 — every exact legacy 8-bit executable head. A historical
    # contract row enriches the hit, but absence from the contract never hides
    # the legacy form.
    for head in heads:
        if head.empty_list:
            continue
        if re.fullmatch(r"[01]{8}", head.token):
            add(1, "sid8-sens8", head, by_sid.get(head.token))

    # PASS 2 — our my-lisp notation. Reserve known historical UPPERCASE names
    # for pass 3, and leave already-binary exact-width heads alone. Everything
    # else in executable head position is a my-lisp surface, including
    # user-defined functions and symbolic names. Literal () is its own case.
    empty_row = by_my.get("empty-list")
    historical_upper_tokens = set(by_historical_upper)
    for head in heads:
        if key(head) in claimed:
            continue
        if head.empty_list:
            add(2, "my-lisp-empty-list", head, empty_row)
            continue
        if re.fullmatch(r"[01]{1,8}", head.token):
            continue
        if head.token in historical_upper_tokens:
            continue
        add(2, "my-lisp", head, by_my.get(head.token))

    # PASS 3 — historical Lisp 1 / Lisp 1.5 spelling, UPPERCASE only.
    for head in heads:
        if key(head) in claimed or head.empty_list:
            continue
        row = by_historical_upper.get(head.token)
        if row is not None:
            add(3, "lisp1-1.5-uppercase", head, row)

    return sorted(hits, key=lambda hit: (hit.path, hit.line, hit.column, hit.pass_number))


def source_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SOURCE_EXTS:
            yield path


def scan_tree(root: Path, contract: Path) -> tuple[list[Hit], dict[str, int]]:
    _, by_sid, by_my, by_historical = load_mapping(contract)
    all_hits: list[Hit] = []
    files_seen = 0

    for path in source_files(root):
        files_seen += 1
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root).as_posix()
        heads = scan_heads(rel, text)
        all_hits.extend(classify_three_passes(heads, by_sid, by_my, by_historical))

    counts = collections.Counter(hit.representation for hit in all_hits)
    summary = {
        "files_seen": files_seen,
        "hits_total": len(all_hits),
        "pass1_sid8_sens8": counts["sid8-sens8"],
        "pass2_my_lisp": counts["my-lisp"] + counts["my-lisp-empty-list"],
        "pass2_my_lisp_empty_list": counts["my-lisp-empty-list"],
        "pass3_lisp1_1_5_uppercase": counts["lisp1-1.5-uppercase"],
    }
    return all_hits, summary


def write_tsv(path: Path, hits: list[Hit]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "pass_number", "representation", "path", "line", "column", "token",
        "sid8", "my_lisp", "historical", "historical_source", "fit", "status",
    ]
    lines = ["\t".join(columns)]
    for hit in hits:
        row = asdict(hit)
        lines.append("\t".join(str(row[name]).replace("\t", " ") for name in columns))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("contracts/core1-historical-sid-map.lisp"),
    )
    parser.add_argument("--json", type=Path)
    parser.add_argument("--tsv", type=Path)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    contract = args.contract.resolve()
    hits, summary = scan_tree(root, contract)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {"summary": summary, "hits": [asdict(hit) for hit in hits]},
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
    if args.tsv:
        write_tsv(args.tsv, hits)

    print(json.dumps(summary, ensure_ascii=False))
    if not args.summary_only:
        for hit in hits:
            print(
                f"P{hit.pass_number}\t{hit.representation}\t"
                f"{hit.path}:{hit.line}:{hit.column}\t{hit.token}\t"
                f"sid8={hit.sid8}\tmy={hit.my_lisp}\thist={hit.historical}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
