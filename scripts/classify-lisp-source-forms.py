#!/usr/bin/env python3
"""Inventory real SENS source generations before canonical migration.

History-derived pass order:
  1. legacy exact 8-bit SID8/Sens8 executable heads;
  2. known my-lisp / admitted surface executable heads;
  3. historical Lisp I / Lisp 1.5 UPPERCASE executable heads.

Already-current D3-D6 exact-width heads are reported separately.  Unknown
user/dynamic call heads are also separate and are NEVER mislabeled as my-lisp
builtins.  Literal () is structural-empty inventory, not a function head.

This is an inventory/resolution tool; it does not rewrite source.
"""
from __future__ import annotations

import argparse
import collections
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sens_source_resolver import Resolution, SourceResolver, build_resolver

SOURCE_EXTS = {".lisp", ".lsp", ".cl", ".scm", ".rkt", ".sens"}
SKIP_DIRS = {
    ".git", ".hg", ".svn", "target", "node_modules", "vendor",
    ".venv", "venv", "dist", "build", "__pycache__",
}


@dataclass(frozen=True)
class Head:
    path: str
    line: int
    column: int
    start: int
    end: int
    token: str
    empty_list: bool = False


@dataclass(frozen=True)
class Hit:
    pass_number: int
    representation: str
    path: str
    line: int
    column: int
    token: str
    current_domain: str
    current_bits: str
    current_label: str
    legacy_sid8: str
    my_lisp: str
    historical: str
    resolution: str
    evidence: str


def line_col(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    last = text.rfind("\n", 0, offset)
    return line, offset + 1 if last < 0 else offset - last


def scan_heads(path: str, text: str) -> list[Head]:
    """Lexically find list heads while excluding quoted/comment/string data.

    This scanner intentionally does not call unknown heads "my-lisp".  Semantic
    special-form container cleanup happens later; unknown heads are blockers /
    dynamic evidence, never static function identity.
    """
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
                    heads.append(Head(path, line, col, open_offset, i + 1, "()", True))
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


def _hit(head: Head, resolution: Resolution) -> Hit:
    current = resolution.current
    return Hit(
        pass_number=resolution.pass_number,
        representation=resolution.kind,
        path=head.path,
        line=head.line,
        column=head.column,
        token=head.token,
        current_domain=current.domain if current else "",
        current_bits=current.bits if current else "",
        current_label=current.label if current else "",
        legacy_sid8=resolution.legacy_sid8 or "",
        my_lisp=resolution.my_lisp or "",
        historical=resolution.historical or "",
        resolution=(
            "resolved"
            if resolution.resolved
            else "ambiguous"
            if resolution.ambiguous
            else "legacy-unmapped"
            if resolution.legacy_unmapped
            else "unresolved"
        ),
        evidence=";".join(resolution.evidence),
    )


def classify_heads(
    heads: list[Head],
    resolver: SourceResolver,
) -> tuple[list[Hit], list[Hit], list[Head], list[Head]]:
    """Return (three_pass_hits, current_exact, dynamic_heads, empty_lists)."""
    three_pass: list[Hit] = []
    current: list[Hit] = []
    dynamic: list[Head] = []
    empty: list[Head] = []

    for head in heads:
        if head.empty_list:
            empty.append(head)
            continue
        resolution = resolver.resolve_head(head.token)
        if resolution.pass_number in (1, 2, 3):
            three_pass.append(_hit(head, resolution))
        elif resolution.kind == "current-exact":
            current.append(_hit(head, resolution))
        else:
            dynamic.append(head)

    return three_pass, current, dynamic, empty


def source_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SOURCE_EXTS:
            yield path


def scan_tree(
    root: Path,
    resolver: SourceResolver,
) -> tuple[list[Hit], list[Hit], list[Head], list[Head], dict[str, int]]:
    historical: list[Hit] = []
    current: list[Hit] = []
    dynamic: list[Head] = []
    empty: list[Head] = []
    files_seen = 0

    for path in source_files(root):
        files_seen += 1
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root).as_posix()
        groups = classify_heads(scan_heads(rel, text), resolver)
        historical.extend(groups[0])
        current.extend(groups[1])
        dynamic.extend(groups[2])
        empty.extend(groups[3])

    counts = collections.Counter(hit.pass_number for hit in historical)
    summary = {
        "files_seen": files_seen,
        "three_pass_hits": len(historical),
        "pass1_sid8_sens8": counts[1],
        "pass2_my_lisp_surface": counts[2],
        "pass3_lisp1_1_5_uppercase": counts[3],
        "current_exact_heads": len(current),
        "dynamic_or_unresolved_heads": len(dynamic),
        "structural_empty_lists": len(empty),
        "resolved_to_current": sum(hit.resolution == "resolved" for hit in historical),
        "historical_unresolved_or_ambiguous": sum(
            hit.resolution != "resolved" for hit in historical
        ),
    }
    return historical, current, dynamic, empty, summary


def write_tsv(path: Path, hits: list[Hit]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(Hit.__dataclass_fields__)
    lines = ["\t".join(columns)]
    for hit in hits:
        row = asdict(hit)
        lines.append("\t".join(str(row[name]).replace("\t", " ") for name in columns))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument(
        "--historical-map",
        type=Path,
        default=Path("contracts/core1-historical-sid-map.lisp"),
    )
    parser.add_argument(
        "--foundation",
        type=Path,
        default=Path("knowledge/d1-d7-foundation.json"),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("lib/surface/semantic-registry.lisp"),
    )
    parser.add_argument(
        "--domain-surfaces",
        type=Path,
        nargs="*",
        default=[Path(f"lib/domains/d{width}.lisp") for width in range(1, 7)],
    )
    parser.add_argument("--json", type=Path)
    parser.add_argument("--tsv", type=Path)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    resolver = build_resolver(
        historical_map=args.historical_map.resolve(),
        foundation=args.foundation.resolve(),
        registry=args.registry.resolve(),
        domain_surfaces=[p.resolve() for p in args.domain_surfaces],
    )
    result = scan_tree(args.root.resolve(), resolver)
    historical, current, dynamic, empty, summary = result

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "summary": summary,
                    "three_pass_hits": [asdict(hit) for hit in historical],
                    "current_exact_heads": [asdict(hit) for hit in current],
                    "dynamic_or_unresolved_heads": [asdict(head) for head in dynamic],
                    "structural_empty_lists": [asdict(head) for head in empty],
                },
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
    if args.tsv:
        write_tsv(args.tsv, historical)

    print(json.dumps(summary, ensure_ascii=False))
    if not args.summary_only:
        for hit in historical:
            current_text = (
                f"{hit.current_domain}:{hit.current_bits}:{hit.current_label}"
                if hit.current_bits else "UNRESOLVED"
            )
            print(
                f"P{hit.pass_number}\t{hit.representation}\t"
                f"{hit.path}:{hit.line}:{hit.column}\t{hit.token}\t"
                f"=> {current_text}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
