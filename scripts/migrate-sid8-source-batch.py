#!/usr/bin/env python3
"""Dry-run all active .lisp source for safe in-place SID8 -> domain substitutions.

--write updates original Lisp only. Never creates .sens or a branch.
No guessing for dual successor MAP, DEFMACRO, D10 or internal mechanisms.
D3 guard rejects old three-field COND and host truth after rewriting.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
# Тестовий importlib.spec_from_file_location не додає scripts/ в sys.path.
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from report_original_migration_candidates import load_nonprogram_classification
BITS = re.compile(r"[01]{8}\Z")
TARGET = re.compile(r"D([1-9]):([01]{1,9})")
ALLOW = {"DIRECT-CURRENT-IDENTITY", "CURRENT-PROJECTION-DERIVED"}
SCOPES = ("lib/", "knowledge/", "scripts/", "experiments/", "racket/boot/")
SKIP = ("lib/domains/", "lib/generated/", "lib/surface/", "knowledge/archive/",
        "knowledge/d10-source-snapshots/", "research/", "docs/", "tests/")
HOLDS = {"lib/macro.lisp", "lib/machine/block.lisp"}

# Ця декларативна схема вже включена до незалежного SHA-прикріпленого
# non-program manifest; ніколи не видавати її записи за виклики функцій.
PINNED_SCHEMA_METADATA = "lib/function-table-mechanisms.lisp"

# The five pinned service/policy sources were migrated only at D4 DEFINE/LAMBDA
# heads. Their surviving 8-bit D3 COND forms remain HISTORICAL, not current D8.
# Do not let removal of the old D4 definition head hide legacy blockers from
# the fail-closed inventory. Revisit this pin only after executable D3 parity.
PARTIAL_D4_WITH_LEGACY_D3 = {
    "knowledge/guard-reference.lisp",
    "knowledge/guard-fact-policy.lisp",
    "scripts/semantic-authority-guard-enforce.lisp",
}


def authority(root):
    a = json.loads((root / "knowledge/sens8-current-coverage-v1.json").read_text())
    f = json.loads((root / "knowledge/d1-d9-foundation.json").read_text())
    if a.get("status") != "AUDIT-COMPLETE" or len(a.get("rows", [])) != 256:
        raise ValueError("unproved SID8 coverage")
    if f.get("status") != "owner-ratified":
        raise ValueError("missing ratified current foundation")
    mapping, blocked = {}, {}
    for x in a["rows"]:
        old = x["legacy_code"]
        if not BITS.fullmatch(old) or old in mapping or old in blocked:
            raise ValueError("duplicate legacy code: " + old)
        all_targets = {(f"D{d}", v) for d, v in TARGET.findall(x.get("current_target") or "")}
        if x["classification"] in ALLOW and len(all_targets) == 1:
            domain, word = next(iter(all_targets))
            owner = f["domains"].get(domain, {})
            if owner.get("width") != len(word) or word not in owner.get("residents", {}):
                raise ValueError("not a ratified current resident: " + old)
            mapping[old] = word
        else:
            blocked[old] = x["classification"]
    return mapping, blocked

def rewrite(src, mapping, blocked):
    stack, edits, problems = [], [], []
    quote = False
    i = 0
    while i < len(src):
        c = src[i]
        if src.startswith("#;", i):
            problems.append("reader skip #; needs parser proof")
            i += 2
            continue
        if src.startswith("#|", i):
            depth = 1
            i += 2
            while depth and i < len(src):
                if src.startswith("#|", i):
                    depth += 1
                    i += 2
                elif src.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                problems.append("unclosed block comment")
            continue
        if c == ";":
            while i < len(src) and src[i] != "\n":
                i += 1
            continue
        if c == '"':
            i += 1
            closed = False
            while i < len(src):
                if src[i] == "\\":
                    i += 2
                elif src[i] == '"':
                    i += 1
                    closed = True
                    break
                else:
                    i += 1
            if not closed:
                problems.append("unclosed string")
            continue
        if src.startswith("#'", i) or c in ("'", chr(96)):
            quote = True
            i += 2 if src.startswith("#'", i) else 1
            continue
        if c == "(":
            parent = stack[-1] if stack else None
            if parent and parent["first"]:
                parent["first"] = False
            nested = quote or bool(parent and (parent["quoted"] or parent["quote_children"]))
            stack.append({"first": True, "quoted": nested, "quote_children": False})
            quote = False
            i += 1
            continue
        if c == ")":
            if stack:
                stack.pop()
            else:
                problems.append("extra close")
            quote = False
            i += 1
            continue
        if c.isspace():
            i += 1
            continue
        if c == ",":
            quote = True
            i += 2 if src.startswith(",@", i) else 1
            continue
        start = i
        while i < len(src) and not src[i].isspace() and src[i] not in "()'\",;" + chr(96) and not src.startswith("#|", i):
            i += 1
        if i == start:
            i += 1
            continue
        token = src[start:i]
        f = stack[-1] if stack else None
        if f and f["first"]:
            f["first"] = False
            if not f["quoted"] and BITS.fullmatch(token):
                if token in mapping:
                    edits.append((start, i, mapping[token]))
                else:
                    problems.append(token + ": " + blocked.get(token, "unknown"))
            if token in {"00000001", "001", "QUOTE", "quote", "як-є"}:
                f["quote_children"] = True
        quote = False
    if stack:
        problems.append("unclosed list")
    output = src
    if not problems:
        for start, stop, word in reversed(edits):
            output = output[:start] + word + output[stop:]
    return output, len(edits), sorted(set(problems))

def executable_call_heads(source, guard):
    """Only executed list heads; ignore comments, strings, and quoted datum.

    The existing canonical D3 Lisp parser is used for attribution. An
    unparseable candidate must block, never silently become current source.
    """
    result = set()
    nodes = list(guard.parse(source))
    while nodes:
        node = nodes.pop()
        if node.opaque or not node.children:
            continue
        head = node.children[0].atom
        if head in guard.QUOTE:
            continue
        if head is not None:
            result.add(head)
        nodes.extend(node.children)
    return result


# Existing historically pinned active programs contain W8 call heads whose
# bits are ALSO modern D8 residents with different meanings. A ratified
# successor is not an executable mechanism. Never reinterpret these as D8.
PINNED_W8_COLLISIONS = {
    "knowledge/guard-fact-policy.lisp": {
        "10011100": ("LET", "D6", "001000", "CADDDAAR"),
    },
    "scripts/semantic-authority-guard-enforce.lisp": {
        "01001011": ("READ-ALL", "D9", "110101001", "ABS∘RECIP"),
        "10100110": ("READ-FILE", "D9", "110110111", "1/"),
    },
}


def pinned_cross_domain_blockers(root, path, active_heads, mapping):
    """Fail closed on independently identified historical call-head collisions.

    Ratified identity alone never proves a D6/D9 executable route. This
    check is source-specific; unknown eras are NEVER globally treated as W8.
    """
    expected = PINNED_W8_COLLISIONS.get(path)
    if not expected:
        return []
    data = json.loads((root / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
    d8 = data["domains"]["D8"]["residents"]
    d6 = json.loads((root / "knowledge/d6-mechanism-ledger.json").read_text(encoding="utf-8"))
    d6_status = {row["coordinate"]: row["mechanism_status"] for row in d6["rows"]}
    reasons = []
    for old, (name, domain, bits, current_d8) in expected.items():
        if old not in active_heads:
            continue
        if (mapping.get(old) != bits
                or data["domains"][domain]["residents"].get(bits) != name
                or d8.get(old) != current_d8):
            raise ValueError(f"pinned W8 source successor drift: {path}: {old}")
        mechanism = (d6_status.get(bits, "UNVERIFIED") if domain == "D6"
                     else "NOT_ATTESTED_BY_THIS_SOURCE_CENSUS")
        reasons.append(
            f"W8_CROSS_DOMAIN_EXECUTION_BLOCK: {old} historical {name} -> "
            f"{domain}:{bits} ({mechanism}); current D8:{old} is {current_d8}"
        )
    return reasons


def guard_module(root):
    name = "sid8_bulk_guard"
    spec = importlib.util.spec_from_file_location(name, root / "scripts/check_d3_legacy_logic.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def run(root, write=False, selected=None):
    mapping, blocked = authority(root)
    guard = guard_module(root)
    # Повторно використовуємо канонічні Git-blob pins із #4460.
    # Будь-яка зміна навіть одного байта в джерелі залишається BLOCK, а не skip.
    reviewed = load_nonprogram_classification(root)
    pinned = reviewed.get(PINNED_SCHEMA_METADATA)
    if pinned is None or pinned["cohort"] != "schema":
        raise ValueError("missing independently reviewed schema metadata authority")
    proc = subprocess.run(["git", "ls-files", "-z", "--", "*.lisp"],
                          cwd=root, check=True, capture_output=True)
    paths = sorted(p.decode() for p in proc.stdout.split(b"\0") if p)
    report = []
    for path in paths:
        if selected and path not in selected:
            continue
        if (path in HOLDS or path.startswith(SKIP) or
                not (path.startswith(SCOPES) or
                     path.startswith("benchmarks/") and path.count("/") == 1)):
            continue
        file = root / path
        if file.is_symlink():
            report.append({"path": path, "status": "blocked", "reasons": ["symlink"]})
            continue
        if path == PINNED_SCHEMA_METADATA:
            report.append({
                "path": path, "status": "nonprogram-data-reviewed",
                "source_git_blob_sha": pinned["source_git_blob_sha"],
                "potential_heads": 0,
                "reasons": ["SHA-pinned schema metadata; never executable migration credit"],
            })
            continue
        original = file.read_text(encoding="utf-8")
        # Raw regexes incorrectly attribute generated strings to historical
        # executable W8: e.g. a quoted "(00001001 ...)" source template.
        # Only actual unquoted list heads may establish source-era provenance.
        possible_legacy = bool(re.search(
            r"\(\s*(?:00001001|00001011)(?=[\s)])", original))
        possible_pinned_d3 = (
            path in PARTIAL_D4_WITH_LEGACY_D3
            and bool(re.search(r"\(\s*(?:00000111|110)(?=[\s)])", original))
        )
        active_heads = set()
        if possible_legacy or possible_pinned_d3:
            try:
                active_heads = executable_call_heads(original, guard)
            except (guard.Unscannable, RecursionError) as err:
                report.append({"path": path, "status": "blocked",
                               "potential_heads": 0,
                               "reasons": ["source-era parser incomplete: " + str(err)]})
                continue
        has_legacy_definition = bool(active_heads & {"00001001", "00001011"})
        has_pinned_legacy_d3 = (
            path in PARTIAL_D4_WITH_LEGACY_D3
            and bool(active_heads & {"00000111", "110"})
        )
        if not (has_legacy_definition or has_pinned_legacy_d3):
            report.append({"path": path, "status": "source-era-unproved",
                           "potential_heads": 0,
                           "reasons": ["no historical DEFINE/DEF call head"]})
            continue
        if "GENERATED" in original[:360] or "do not hand-edit" in original[:360]:
            report.append({"path": path, "status": "source-era-unproved",
                           "potential_heads": 0,
                           "reasons": ["generated carrier needs generator migration"]})
            continue
        updated, n, problems = rewrite(original, mapping, blocked)
        problems.extend(pinned_cross_domain_blockers(root, path, active_heads, mapping))
        if n or has_pinned_legacy_d3:
            try:
                problems.extend(x.rule + " at line " + str(x.line)
                                for x in guard.scan_lisp(updated, path))
            except (guard.Unscannable, RecursionError) as err:
                problems.append("D3 parser incomplete: " + str(err))
        status = "blocked" if problems else "admitted" if n else "unchanged"
        item = {"path": path, "status": status, "potential_heads": n,
                "reasons": sorted(set(problems))[:40]}
        if status == "admitted":
            item["before_sha256"] = hashlib.sha256(original.encode()).hexdigest()
            item["after_sha256"] = hashlib.sha256(updated.encode()).hexdigest()
            if write:
                file.write_bytes(updated.encode("utf-8"))
        report.append(item)
    summary = {
        "scanned": len(report),
        "admitted_files": sum(x["status"] == "admitted" for x in report),
        "admitted_heads": sum(x["potential_heads"] for x in report if x["status"] == "admitted"),
        "blocked_files": sum(x["status"] == "blocked" for x in report),
        "write": write,
    }
    return {"schema": "sid8-lisp-source-batch/v1", "summary": summary, "files": report}

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--root", type=Path, default=ROOT)
    args.add_argument("--write", action="store_true")
    args.add_argument("--report", type=Path)
    args.add_argument("--select", nargs="*")
    opt = args.parse_args()
    value = run(opt.root.resolve(), opt.write, set(opt.select) if opt.select else None)
    if opt.report:
        opt.report.parent.mkdir(parents=True, exist_ok=True)
        opt.report.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    print(json.dumps(value["summary"], ensure_ascii=False))
