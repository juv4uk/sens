#!/usr/bin/env python3
"""Manifest-driven migration of S-expression source to current SENS exact-width codes.

Safety rules:
- current coordinates come only from knowledge/d1-d7-foundation.json;
- default is audit/dry-run;
- only executable list-head symbols are rewritten;
- strings, comments, quoted data and package-qualified names are preserved;
- obvious redefinitions of canonical names block rewriting;
- host-language source is never blindly rewritten.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

CALL_DOMAINS = ("D3", "D4", "D5", "D6")
LISP_EXTS = {".lisp", ".lsp", ".cl", ".scm", ".rkt", ".sens"}
SKIP_DIRS = {".git", ".hg", ".svn", "target", "node_modules", ".venv", "venv", "dist", "build", "__pycache__"}

@dataclass(frozen=True)
class Entry:
    domain: str
    width: int
    bits: str
    label: str
    authority: str

@dataclass(frozen=True)
class Hit:
    line: int
    column: int
    label: str
    bits: str
    domain: str

def load_foundation(path: Path):
    raw = path.read_bytes()
    data = json.loads(raw)
    if data.get("status") != "owner-ratified":
        raise SystemExit(f"{path}: foundation is not owner-ratified")
    return data, sha256(raw).hexdigest()

def build_map(data, domains):
    out = {}
    for domain in domains:
        desc = data["domains"][domain]
        width = int(desc["width"])
        authority = str(desc.get("authority", data.get("authority", "unknown")))
        for bits, label in desc["residents"].items():
            if len(bits) != width or set(bits) - {"0", "1"}:
                raise SystemExit(f"{domain}: invalid exact-width word {bits}")
            key = str(label).upper()
            if key in out:
                raise SystemExit(f"duplicate label across selected domains: {key}")
            out[key] = Entry(domain, width, bits, str(label), authority)
    return out

def line_col(text, offset):
    line = text.count("\n", 0, offset) + 1
    last = text.rfind("\n", 0, offset)
    return line, offset + 1 if last < 0 else offset - last

def mask_comments_and_strings(text):
    chars = list(text)
    i = 0
    state = "normal"
    depth = 0
    while i < len(text):
        if state == "string":
            if text[i] == "\\" and i + 1 < len(text):
                chars[i] = chars[i + 1] = " "
                i += 2
            elif text[i] == '"':
                chars[i] = " "
                state = "normal"
                i += 1
            else:
                if text[i] != "\n":
                    chars[i] = " "
                i += 1
            continue
        if state == "line":
            if text[i] == "\n":
                state = "normal"
            else:
                chars[i] = " "
            i += 1
            continue
        if state == "block":
            if text.startswith("#|", i):
                chars[i:i+2] = [" ", " "]
                depth += 1
                i += 2
            elif text.startswith("|#", i):
                chars[i:i+2] = [" ", " "]
                depth -= 1
                i += 2
                if depth == 0:
                    state = "normal"
            else:
                if text[i] != "\n":
                    chars[i] = " "
                i += 1
            continue
        if text[i] == '"':
            chars[i] = " "
            state = "string"
            i += 1
        elif text[i] == ";":
            chars[i] = " "
            state = "line"
            i += 1
        elif text.startswith("#|", i):
            chars[i:i+2] = [" ", " "]
            state = "block"
            depth = 1
            i += 2
        else:
            i += 1
    return "".join(chars)

def shadowing(text, code_map):
    masked = mask_comments_and_strings(text)
    pattern = re.compile(r"(?i)\(\s*(defun|defmacro|defgeneric|defmethod)\s+([^\s()]+)")
    rows = []
    for match in pattern.finditer(masked):
        label = match.group(2).upper()
        if label in code_map:
            line, col = line_col(text, match.start(2))
            rows.append({"line": line, "column": col, "label": label, "kind": match.group(1).upper()})
    return rows

def symbol_char(ch):
    return (not ch.isspace()) and ch not in "()\";',"

def rewrite(text, code_map):
    blocked = shadowing(text, code_map)
    if blocked:
        return text, [], blocked

    frames = []
    out = []
    hits = []
    i = 0
    pending_quote = False

    while i < len(text):
        ch = text[i]
        if ch == '"':
            start = i
            i += 1
            while i < len(text):
                if text[i] == "\\" and i + 1 < len(text):
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            out.append(text[start:i])
            pending_quote = False
            continue
        if ch == ";":
            end = text.find("\n", i)
            if end < 0:
                out.append(text[i:])
                break
            out.append(text[i:end])
            i = end
            continue
        if text.startswith("#|", i):
            start = i
            i += 2
            depth = 1
            while i < len(text) and depth:
                if text.startswith("#|", i):
                    depth += 1
                    i += 2
                elif text.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            out.append(text[start:i])
            continue
        if text.startswith("#'", i):
            out.append("#'")
            i += 2
            pending_quote = True
            continue
        if ch == "'" or ord(ch) == 96:
            out.append(ch)
            i += 1
            pending_quote = True
            continue
        if ch == ",":
            out.append(ch)
            i += 1
            pending_quote = True
            if i < len(text) and text[i] == "@":
                out.append("@")
                i += 1
            continue
        if ch == "(":
            parent_quoted = bool(frames and (frames[-1]["quoted"] or frames[-1]["quote_children"]))
            if frames and frames[-1]["head"]:
                frames[-1]["head"] = False
            frames.append({"quoted": parent_quoted or pending_quote, "head": True, "quote_children": False})
            out.append(ch)
            i += 1
            pending_quote = False
            continue
        if ch == ")":
            if frames:
                frames.pop()
            out.append(ch)
            i += 1
            pending_quote = False
            continue
        if ch.isspace():
            out.append(ch)
            i += 1
            continue

        start = i
        while i < len(text) and symbol_char(text[i]) and ord(text[i]) != 96:
            if text.startswith("#|", i):
                break
            i += 1
        token = text[start:i]
        if not token:
            out.append(text[i])
            i += 1
            continue

        frame = frames[-1] if frames else None
        is_head = bool(frame and frame["head"])
        quoted = pending_quote or bool(frame and (frame["quoted"] or frame["quote_children"]))
        upper = token.upper()
        entry = code_map.get(upper)
        replacement = token
        if is_head and not quoted and entry and ":" not in token:
            replacement = entry.bits
            line, col = line_col(text, start)
            hits.append(Hit(line, col, entry.label, entry.bits, entry.domain))
        out.append(replacement)
        if frame and frame["head"]:
            frame["head"] = False
            if upper == "QUOTE":
                frame["quote_children"] = True
        pending_quote = False

    return "".join(out), hits, blocked

def source_files(root):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in LISP_EXTS:
            yield path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="repository or source tree")
    parser.add_argument("--foundation", type=Path, required=True)
    parser.add_argument("--domains", nargs="+", default=list(CALL_DOMAINS))
    parser.add_argument("--apply", action="store_true", help="rewrite supported source in place")
    parser.add_argument("--mirror", type=Path, help="write converted mirror instead of in-place")
    parser.add_argument("--report", type=Path, default=Path("sens-code-migration-report.json"))
    args = parser.parse_args()

    if args.apply and args.mirror:
        parser.error("--apply and --mirror are mutually exclusive")

    foundation, digest = load_foundation(args.foundation)
    code_map = build_map(foundation, args.domains)
    root = args.root.resolve()
    rows = []
    rewritten_files = 0
    blocked_files = 0
    total_hits = 0

    for path in source_files(root):
        text = path.read_text(encoding="utf-8")
        converted, hits, blocked = rewrite(text, code_map)
        rel = path.relative_to(root)
        status = "clean"
        if blocked:
            status = "blocked"
            blocked_files += 1
        elif hits:
            status = "would-rewrite"
            total_hits += len(hits)
            if args.apply:
                path.write_text(converted, encoding="utf-8")
                status = "rewritten"
                rewritten_files += 1
            elif args.mirror:
                target = args.mirror / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(converted, encoding="utf-8")
                status = "mirrored"
                rewritten_files += 1
        rows.append({
            "path": str(rel),
            "status": status,
            "hits": [asdict(x) for x in hits],
            "blockers": blocked,
        })

    report = {
        "foundation_schema": foundation.get("schema"),
        "foundation_authority": foundation.get("authority"),
        "foundation_date": foundation.get("date"),
        "foundation_sha256": digest,
        "identity_rule": foundation.get("identity_rule"),
        "domains": args.domains,
        "root": str(root),
        "mode": "apply" if args.apply else ("mirror" if args.mirror else "audit"),
        "summary": {
            "files_seen": len(rows),
            "files_written": rewritten_files,
            "files_blocked": blocked_files,
            "rewritable_call_heads": total_hits,
        },
        "files": rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 2 if blocked_files else (1 if total_hits and not (args.apply or args.mirror) else 0)

if __name__ == "__main__":
    raise SystemExit(main())
