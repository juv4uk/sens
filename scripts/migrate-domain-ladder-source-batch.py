#!/usr/bin/env python3
"""Dry-run historical W8 call heads -> canonical full Ukrainian projections.

--write updates original Lisp only. Never creates .sens or a branch.
No guessing for dual successor MAP, DEFMACRO, D10 or internal mechanisms.
The exact domain/word is verified first; human .lisp heads use the `укр` column,
not a raw binary opcode. No Python evaluator or runtime semantics are added.
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
from domain_tables import read_domain_table
BITS = re.compile(r"[01]{8}\Z")
TARGET = re.compile(r"D(10|[1-9]):([01]+)")
ALLOW = {"DIRECT-CURRENT-IDENTITY", "CURRENT-PROJECTION-DERIVED"}
SCOPES = ("lib/", "knowledge/", "scripts/", "experiments/", "racket/boot/")
SKIP = ("lib/domains/", "lib/generated/", "lib/surface/", "knowledge/archive/",
        "knowledge/d10-source-snapshots/", "research/", "docs/", "tests/")
# Do not impose a file-name-based migration veto. Every tracked source in
# the active scopes reaches the source-era/parser/evidence classification below;
# uncertainty is reported with its concrete reason instead of silently skipped.

# Виконувана таблиця механізмів не підпадає під NONPROGRAM: у ній є живі DEFINE.
# Проходимо звичайну source-era перевірку, не створюючи виконуваних .sens з повітря.

# Current D3 Ukrainian forms have already replaced the historical W8 COND
# in the guard/policy sources. No per-filename source-era override remains.


def _exact_codebook(bits, width, origin):
    """Require all 2**width bitstrings, no decimal IDs or padding aliases."""
    expected = [format(number, f"0{width}b") for number in range(1 << width)]
    if len(bits) != len(expected) or sorted(bits) != expected:
        raise ValueError(f"{origin}: missing, duplicate or wrong-width coordinate")
    return len(expected)


def _git_blob_sha1(payload):
    prefix = b"blob " + str(len(payload)).encode("ascii") + b"\0"
    return hashlib.sha1(prefix + payload).hexdigest()


def verify_full_domain_bitspace(root):
    """Migration PRECONDITION, not an admission of 2046 executable functions.

    Validate D1..D9 against the historical owner foundation, except D7 whose
    current authority is keyboard/v2. D10 is ratified as a complete 1024-code
    catalogue, but every opcode remains execution-blocked pending proof.
    """
    foundation = json.loads((root / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
    d7 = json.loads((root / "knowledge/d7-keyboard-v2-ratified.json").read_text(encoding="utf-8"))
    d10 = json.loads((root / "knowledge/d10-owner-whole-domain-ratification-20261012.json").read_text(encoding="utf-8"))
    pointer = json.loads((root / "knowledge/d10-current-inventory.json").read_text(encoding="utf-8"))
    if foundation.get("status") != "owner-ratified":
        raise ValueError("missing ratified D1-D9 foundation")
    if (d7.get("schema"), d7.get("status"), d7.get("width"), d7.get("capacity"), d7.get("occupancy")) != (
        "sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128
    ):
        raise ValueError("D7 v2 128/128 owner authority drift")
    if not (d10.get("ratified") is True
            and d10.get("ratification_mode") == "ATOMIC_WHOLE_DOMAIN_NOT_PER_RESIDENT"
            and d10["inventory"]["rows"] == 1024
            and d10["inventory"]["code_width_bits"] == 10
            and d10["evidence_separation"]["physical_runtime_t5_opcode_admission"] is False):
        raise ValueError("D10 owner/codebook cannot be mistaken for runtime admission")
    if (pointer["canonical_current"]["git_blob"] != d10["inventory"]["git_blob"]
            or pointer["canonical_current"]["path"] != d10["inventory"]["path"]):
        raise ValueError("D10 owner/current inventory pointer mismatch")
    d10_payload = (root / d10["inventory"]["path"]).read_bytes()
    if _git_blob_sha1(d10_payload) != d10["inventory"]["git_blob"]:
        raise ValueError("D10 source blob changed without owner re-ratification")
    d10_inventory = json.loads(d10_payload)
    if d10_inventory.get("width") != 10 or d10_inventory.get("capacity") != 1024:
        raise ValueError("D10 exact 10-bit inventory drift")
    inventory_rows = d10_inventory.get("rows", [])
    if _exact_codebook([row["coordinate"] for row in inventory_rows], 10, "D10 owner inventory") != 1024:
        raise ValueError("D10 owner coverage incomplete")
    if any(row.get("physical_t5_authorized") is True for row in inventory_rows):
        raise ValueError("D10 physical runtime has not been admitted")
    d7_cells = d7.get("table", [])
    if _exact_codebook([row["bits"] for row in d7_cells], 7, "D7 v2 owner table") != 128:
        raise ValueError("D7 v2 coverage incomplete")
    for number, row in enumerate(d7_cells):
        if row["bits"] != f"{number:07b}" or row["ascii"] != chr(number):
            raise ValueError("D7 v2 ASCII coordinate drift")
    for field in ("ascii", "uk", "san"):
        glyphs = [row[field] for row in d7_cells]
        if any(not isinstance(glyph, str) or len(glyph) != 1 for glyph in glyphs) or len(set(glyphs)) != 128:
            raise ValueError("D7 v2 ambiguous keyboard glyphs: " + field)

    total_cells = 0
    total_bits = 0
    widths = {}
    for width in range(1, 11):
        domain = f"D{width}"
        rows = read_domain_table(root / "lib/domains" / f"d{width}.lisp")
        coordinates = [row.bits for row in rows]
        n = _exact_codebook(coordinates, width, domain + " canonical Lisp")
        if width == 7:
            if set(coordinates) != {row["bits"] for row in d7_cells} or any(row.lisp is not None for row in rows):
                raise ValueError("D7 v2 text coordinate drift or callable injection")
        elif width == 10:
            if set(coordinates) != {row["coordinate"] for row in inventory_rows}:
                raise ValueError("D10 table/inventory mismatch")
        else:
            owner = foundation["domains"].get(domain, {})
            if owner.get("width") != width or set(coordinates) != set(owner.get("residents", {})):
                raise ValueError(domain + " source table disagrees with ratified owner")
        widths[domain] = n
        total_cells += n
        total_bits += n * width
    if total_cells != 2046 or total_bits != 18434:
        raise ValueError("D1-D10 full bitspace total unexpectedly changed")
    return {"typed_coordinates": total_cells, "meaningful_bits": total_bits,
            "counts_by_domain": widths, "runtime_admission_claims_added": 0}


def authority(root):
    # A current migration must not run against a stale D7 owner, damaged D10
    # codebook, or wrongly widened/narrowed D1-D10 coordinates.
    verify_full_domain_bitspace(root)
    a = json.loads((root / "knowledge/sens8-current-coverage-v1.json").read_text())
    f = json.loads((root / "knowledge/d1-d9-foundation.json").read_text())
    if a.get("status") != "AUDIT-COMPLETE" or len(a.get("rows", [])) != 256:
        raise ValueError("unverified historical source crosswalk")
    if f.get("status") != "owner-ratified":
        raise ValueError("missing ratified current foundation")
    # One normative Ukrainian spelling per exact (domain, word) address.
    # Never index these tables by bare payload: D8:00001001 is NOT
    # historical SID8:00001001 (DEFINE -> D4:0011).
    projected = {}
    for width in (3, 4, 5, 6, 8, 9):
        domain = f"D{width}"
        for row in read_domain_table(root / "lib/domains" / f"d{width}.lisp"):
            if not row.ukr or row.ukr == "()":
                raise ValueError(f"missing executable Ukrainian projection: {domain}:{row.bits}")
            projected[(domain, row.bits)] = row.ukr
    mapping, blocked, spellings = {}, {}, {}
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
            spelling = projected.get((domain, word))
            if spelling is None:
                # D7 is text data, D10 is not automatically callable, and
                # an unproved/non-projected target must never become a call.
                blocked[old] = f"no admitted Ukrainian call projection: {domain}:{word}"
                continue
            previous = spellings.get(spelling)
            if previous is not None and previous != (domain, word):
                raise ValueError(f"ambiguous canonical Ukrainian call head: {spelling}")
            spellings[spelling] = (domain, word)
            mapping[old] = spelling
        else:
            blocked[old] = x["classification"]
    if len(mapping) + len(blocked) != 256:
        raise ValueError("all 256 SID8 donor cells must receive an explicit disposition")
    # D10 whole-domain ratification is not executable admission. Only
    # exact addresses with full current call projections are considered.
    return mapping, blocked

def ukrainian_projection(root, mapping):
    """Resolve proved legacy successors through current exact-domain укр rows.

    Historical bytes only select a reviewed crosswalk entry. A current
    domain-qualified row supplies the human spelling; no byte-sized D8
    inference, text fallback, or executable admission is performed here.
    """
    required = set(mapping.values())
    words = {}
    for width in range(1, 11):
        for row in read_domain_table(root / f"lib/domains/d{width}.lisp"):
            if row.bits not in required:
                continue
            value = row.ukr
            if (row.role == "display" or not isinstance(value, str)
                    or not value or value == "()"
                    or any(c.isspace() or c in "()\\\"';" for c in value)):
                raise ValueError(f"D{width}:{row.bits}: missing callable укр projection")
            if row.bits in words and words[row.bits] != value:
                raise ValueError(f"D{width}:{row.bits}: conflicting укр projection")
            words[row.bits] = value
    if set(words) != required:
        raise ValueError("historical successor without an exact укр domain row: "
                         + ", ".join(sorted(required - set(words))))
    return {legacy: words[bits] for legacy, bits in mapping.items()}


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
        if c == chr(96) or c == ",":
            problems.append("quasiquote/unquote needs explicit parser and execution proof")
            i += 2 if src.startswith(",@", i) else 1
            continue
        if src.startswith("#'", i) or c == "'":
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
        for start, stop, українська in reversed(edits):
            output = output[:start] + українська + output[stop:]
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


def guard_module(root):
    name = "domain_ladder_bulk_guard"
    spec = importlib.util.spec_from_file_location(name, root / "scripts/check_d3_legacy_logic.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def run(root, write=False, selected=None):
    mapping, blocked = authority(root)
    # Executable human Lisp uses the full ратифікована «укр» column.
    # Keep rewrite(..., mapping, ...) available only for historical bit-delta witnesses.
    surface_mapping = ukrainian_projection(root, mapping)
    guard = guard_module(root)
    # Повторно використовуємо канонічні Git-blob pins із #4460.
    # Будь-яка зміна навіть одного байта в джерелі залишається BLOCK, а не skip.
    load_nonprogram_classification(root, selected_paths=selected)
    proc = subprocess.run(["git", "ls-files", "-z", "--", "*.lisp"],
                          cwd=root, check=True, capture_output=True)
    paths = sorted(p.decode() for p in proc.stdout.split(b"\0") if p)
    report = []
    for path in paths:
        if selected and path not in selected:
            continue
        if (path.startswith(SKIP) or
                not (path.startswith(SCOPES) or
                     path.startswith("benchmarks/") and path.count("/") == 1)):
            continue
        file = root / path
        if file.is_symlink():
            report.append({"path": path, "status": "blocked", "reasons": ["symlink"]})
            continue
        original = file.read_text(encoding="utf-8")
        # Raw regexes incorrectly attribute generated strings to historical
        # executable W8: e.g. a quoted "(00001001 ...)" source template.
        # Only actual unquoted list heads may establish source-era provenance.
        # Every exact-eight executable candidate needs an actual parse, even
        # when a source file contains no historical DEFINE/DEF anchor.
        possible_legacy = bool(re.search(
            r"\(\s*[01]{8}(?=[\s)])", original))
        active_heads = set()
        if possible_legacy:
            try:
                active_heads = executable_call_heads(original, guard)
            except (guard.Unscannable, RecursionError) as err:
                report.append({"path": path, "status": "blocked",
                               "potential_heads": 0,
                               "reasons": ["source-era parser incomplete: " + str(err)]})
                continue
        has_legacy_definition = bool(active_heads & {"00001001", "00001011"})
        if not has_legacy_definition:
            if not possible_legacy:
                # No old 8-bit executable candidate: this file has nothing
                # to migrate. Do not call a current Ukrainian D3/D4 source
                # "source-era-unproved" merely because it lacks legacy DEFINE.
                report.append({"path": path, "status": "unchanged",
                               "potential_heads": 0, "reasons": []})
                continue
            # An unmatched 8-bit head may be contemporary D8 or historical W8;
            # neither a missing DEFINE nor a bit-pattern match proves its era.
            unproved = sorted(h for h in active_heads if BITS.fullmatch(h))
            report.append({"path": path, "status": "source-era-unproved",
                           "potential_heads": len(unproved),
                           "reasons": (["unattributed 8-bit executable heads: " + ", ".join(unproved)]
                                       if unproved else ["no historical DEFINE/DEF call head"])})
            continue
        if "GENERATED" in original[:360] or "do not hand-edit" in original[:360]:
            report.append({"path": path, "status": "source-era-unproved",
                           "potential_heads": 0,
                           "reasons": ["generated carrier needs generator migration"]})
            continue
        updated, n, problems = rewrite(original, surface_mapping, blocked)
        if n:
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
        "verified_full_ladder_coordinates": 2046,
        "verified_full_ladder_meaningful_bits": 18434,
        "historical_sid8_donor_cells": 256,
        "known_legacy_successors": len(mapping),
        "historical_held_cells": len(blocked),
    }
    return {"schema": "domain_ladder-lisp-source-batch/v1", "summary": summary,
            "semantic_admitted": False, "files": report}

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
