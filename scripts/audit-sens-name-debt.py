#!/usr/bin/env python3
"""Find symbolic SENS-name debt in host and source code without rewriting host syntax."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

CODE_EXTS = {
    ".rs", ".c", ".h", ".cc", ".cpp", ".hpp", ".py", ".js", ".mjs", ".ts",
    ".java", ".kt", ".go", ".sh", ".ps1", ".lisp", ".lsp", ".cl", ".scm",
    ".rkt", ".sens", ".yml", ".yaml", ".toml"
}
SKIP_DIRS = {".git", ".hg", ".svn", "target", "node_modules", ".venv", "venv", "dist", "build", "__pycache__"}

def load_map(path, domains):
    raw = path.read_bytes()
    data = json.loads(raw)
    if data.get("status") != "owner-ratified":
        raise SystemExit(f"{path}: foundation is not owner-ratified")
    labels = {}
    for domain in domains:
        desc = data["domains"][domain]
        for bits, label in desc["residents"].items():
            labels[str(label).upper()] = {"domain": domain, "bits": bits}
    return data, sha256(raw).hexdigest(), labels

def files(root):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in CODE_EXTS:
            yield path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("--foundation", type=Path, required=True)
    p.add_argument("--domains", nargs="+", default=["D3", "D4", "D5", "D6"])
    p.add_argument("--report", type=Path, default=Path("sens-name-debt-report.json"))
    p.add_argument("--fail", action="store_true")
    args = p.parse_args()

    foundation, digest, labels = load_map(args.foundation, args.domains)
    names = sorted(labels, key=len, reverse=True)
    pattern = re.compile(
        r"(?i)(?<![A-Za-z0-9_:+*<>/=!?-])(" +
        "|".join(map(re.escape, names)) +
        r")(?![A-Za-z0-9_:+*<>/=!?-])"
    )

    rows = []
    total = 0
    for path in files(args.root.resolve()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        hits = []
        for m in pattern.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            last = text.rfind("\n", 0, m.start())
            col = m.start() + 1 if last < 0 else m.start() - last
            key = m.group(1).upper()
            meta = labels[key]
            hits.append({
                "line": line,
                "column": col,
                "label": key,
                "domain": meta["domain"],
                "bits": meta["bits"],
            })
        if hits:
            rows.append({"path": str(path), "hits": hits})
            total += len(hits)

    report = {
        "foundation_authority": foundation.get("authority"),
        "foundation_sha256": digest,
        "domains": args.domains,
        "root": str(args.root.resolve()),
        "summary": {"files_with_name_debt": len(rows), "symbolic_mentions": total},
        "files": rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 1 if args.fail and total else 0

if __name__ == "__main__":
    raise SystemExit(main())
