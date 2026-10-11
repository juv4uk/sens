#!/usr/bin/env python3
"""Read-only census of every tracked Lisp original for historical SID8 retirement.

This is a triage tool, not a semantic equivalence oracle or source rewriter.
Archives, test fixtures, record tables and research remain in their source
form. No old W8 code is assumed to equal a ratified D8 code by shared bits.
"""
from __future__ import annotations
from collections import Counter
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MAPPER = ROOT / "knowledge/sens8-current-coverage-v1.json"
READER = ROOT / "scripts/check_d3_legacy_logic.py"
BITS8 = re.compile(r"[01]{8}\Z")
QUOTE_HEADS = {"00000001", "001", "QUOTE", "quote", "як-є"}
LEGACY_DEFINE = {"00001001", "00001011"}


def d3_reader():
    spec = importlib.util.spec_from_file_location("_sid8_corpus_d3_reader", READER)
    if spec is None or spec.loader is None:
        raise ValueError("canonical D3 scanner unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def authority():
    data = json.loads(MAPPER.read_text(encoding="utf-8"))
    rows = data.get("rows")
    if data.get("status") != "AUDIT-COMPLETE" or len(rows or []) != 256:
        raise ValueError("not the complete audited old-word ledger")
    result = {r["legacy_code"]: r for r in rows}
    if len(result) != 256 or any(not BITS8.fullmatch(x) for x in result):
        raise ValueError("not one unique row per old 8-bit identity")
    return result


def scope(path):
    # Existing carrier/registry payloads are records, not executable W8 heads.
    # Machine index rows are generated; CPU profiles are frozen provenance.
    if path == "lib/machine/intel-core-i5-6400.lisp":
        return "PRESERVE_HISTORICAL"
    if path in {
        "mylisp-cml-export.lisp",
        "lib/function-table-mechanisms.lisp",
        "lib/machine/encoding/admitted-iclass-index.lisp",
    }:
        return "CONTRACT_OR_DATA_REVIEW"
    if (path.startswith(("research/", "docs/archive/", "knowledge/archive/",
                         "knowledge/d10-source-snapshots/",
                         "benchmarks/sens-surface/results/"))):
        return "PRESERVE_HISTORICAL"
    if path.startswith(("tests/", "fixtures/", "evidence/")):
        return "PRESERVE_TEST_OR_EVIDENCE"
    if path.startswith(("lib/domains/", "lib/generated/", "lib/surface/",
                         "contracts/", "knowledge/", "docs/", "crates/")):
        return "CONTRACT_OR_DATA_REVIEW"
    if (path.startswith(("lib/", "scripts/", "experiments/", "racket/boot/"))
            or path.startswith("benchmarks/") and path.count("/") == 1):
        return "LIVE_CANDIDATE"
    return "UNCLASSIFIED"


def inspect(source, path, reader, mapping):
    heads, data_words = Counter(), Counter()
    nodes = reader.parse(source)
    stack = list(reversed(nodes))
    while stack:
        node = stack.pop()
        if node.opaque or not node.children:
            continue
        head = node.children[0].atom
        if head in QUOTE_HEADS:
            continue
        if head and BITS8.fullmatch(head):
            heads[head] += 1
        for x in node.children[1:]:
            if x.atom and BITS8.fullmatch(x.atom):
                data_words[x.atom] += 1
        stack.extend(reversed(node.children))
    legacy_anchor = any(heads[x] for x in LEGACY_DEFINE)
    ambiguous = {x: n for x, n in sorted(heads.items())
                 if mapping[x]["classification"] not in (
                     "DIRECT-CURRENT-IDENTITY", "CURRENT-PROJECTION-DERIVED")
                 or len(set(re.findall(r"D[1-9]:[01]{1,9}",
                                      mapping[x].get("current_target") or ""))) != 1}
    d3_findings = reader.scan_lisp(source, path)
    return {
        "legacy_source_anchor": legacy_anchor,
        "old_width_executable_heads": sum(heads.values()),
        "distinct_old_width_heads": len(heads),
        "legacy_word_sites": dict(sorted(heads.items())),
        "old_width_datum_sites_preserved": sum(data_words.values()),
        "ambiguous_old_words": ambiguous,
        "d3_findings": dict(sorted(Counter(x.rule for x in d3_findings).items())),
        "action": ("POSSIBLE_HISTORICAL_SOURCE_REVIEW" if legacy_anchor else
                   "SOURCE_ERA_UNPROVED_REVIEW" if heads else
                   "NO_OLD_WIDTH_CALL_HEADS"),
    }


def census(root=ROOT):
    reader = d3_reader()
    mapping = authority()
    files = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", "*.lisp"],
                           capture_output=True, check=True).stdout.split(b"\0")
    rows = []
    for raw in files:
        if not raw:
            continue
        path = raw.decode("utf-8")
        kind = scope(path)
        row = {"path": path, "scope": kind}
        if kind == "PRESERVE_HISTORICAL":
            row["action"] = "PRESERVE_ORIGINAL_BYTES"
        elif kind == "PRESERVE_TEST_OR_EVIDENCE":
            row["action"] = "PRESERVE_WITNESS_BYTES"
        elif kind == "CONTRACT_OR_DATA_REVIEW":
            row["action"] = "NO_UNPROVEN_REWRITE"
        else:
            location = root / path
            try:
                if location.is_symlink() or not location.is_file():
                    raise ValueError("missing file or symlink")
                row.update(inspect(location.read_text(encoding="utf-8"),
                                   path, reader, mapping))
            except (reader.Unscannable, OSError, UnicodeError,
                    ValueError, RecursionError) as exc:
                row["action"] = "UNSCANNABLE_FAIL_CLOSED"
                row["reason"] = str(exc)
        rows.append(row)
    rows.sort(key=lambda z: z["path"])
    groups = Counter(x["scope"] for x in rows)
    actions = Counter(x["action"] for x in rows)
    findings = Counter()
    for x in rows:
        findings.update(x.get("d3_findings", {}))
    return {
        "schema": "sens-sid8-all-lisp-source-census/v1",
        "policy": "READ_ONLY_NO_SENS_NO_NEW_BRANCH_NO_SEMANTIC_PARITY_CLAIM",
        "summary": {
            "tracked_lisp_files": len(rows),
            "by_scope": dict(sorted(groups.items())),
            "by_action": dict(sorted(actions.items())),
            "old_width_call_heads_reviewed": sum(
                x.get("old_width_executable_heads", 0) for x in rows),
            "old_width_data_atoms_unchanged": sum(
                x.get("old_width_datum_sites_preserved", 0) for x in rows),
            "d3_findings": dict(sorted(findings.items())),
            "unscannable": actions["UNSCANNABLE_FAIL_CLOSED"],
        },
        "files": rows,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--report", type=Path)
    p.add_argument("--strict-parser", action="store_true")
    opt = p.parse_args()
    result = census(opt.root.resolve())
    if opt.report:
        opt.report.parent.mkdir(parents=True, exist_ok=True)
        opt.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    return 2 if opt.strict_parser and result["summary"]["unscannable"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
