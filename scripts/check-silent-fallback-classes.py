#!/usr/bin/env python3
"""#2134 — silent-fallback sweep.

For a language that sells itself on *named refusals*, any silent "almost right"
is poison. This scanner names the classes of silent fallback that already exist
in the live tree and refuses to let a NEW one appear unnamed.

It does NOT try to fix the existing sites and it is not a blanket gate: it takes
`knowledge/silent-fallback-inventory.lisp` as a baseline, and fails only when a
site appears that the baseline does not name. Known sites pass; disappeared sites
are reported as stale (informational).

Named classes
-------------
1. total-serializer-fallback : a total serializer whose `_` arm drops to the
   human rendering path (#1877: `_ => render(value, true)`).
2. implicit-default-flag     : a keyed lookup turned into a boolean so that a
   MISSING field silently reads as false (#1664: `alist_flag`).
3. fail-fast-hides-suites    : a CI step running a whole cargo test workspace
   without `--no-fail-fast`, so the first failing binary hides the rest
   (cml#394).
4. silent-regeneration       : a generator template (or a generated artifact)
   still carrying legacy 3-field COND control, so the artifact is rebuilt *back*
   into an illegal state, silently and repeatedly (#2291).

Usage
-----
    python3 scripts/check-silent-fallback-classes.py --root . \
        --inventory knowledge/silent-fallback-inventory.lisp
    python3 scripts/check-silent-fallback-classes.py --root . --emit-inventory
    python3 scripts/check-silent-fallback-classes.py --self-test
"""

from __future__ import annotations

import argparse
import os
import re
import sys

SKIP_DIRS = {".git", "target", "node_modules", "vendor", "dist", "build"}

HUMAN_SERIALIZER = re.compile(r"render|serial|wire|canonical|encode|to_string|display", re.I)
FLAG_NAME = re.compile(r"(flag|present|is_|has_|active|admitted|enabled)", re.I)
HUMAN_PATH_CALL = re.compile(r"render\(|to_string\(|format!\(|display\(")
FLAG_DERIVE = re.compile(r"matches!\(|\.any\(|\.map\(|\.find\(")
FLAG_LOOKUP = re.compile(r"alist_field\(|\balist\b|\bentries\b")
FLAG_EXPLICIT_MISSING = re.compile(r"unwrap_or\(true\)|unwrap_or_else\(\s*\|\|\s*true")
FN_RE = re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(")


def walk(root, exts):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if any(name.endswith(e) for e in exts):
                yield os.path.join(dirpath, name)


def norm(snippet: str) -> str:
    return re.sub(r"\s+", " ", snippet.strip())


def three_field_clauses(line: str):
    """Paren-aware: top-level lists of exactly 3 sublists (legacy COND clause)."""
    out, i, n = [], 0, len(line)
    while i < n:
        if line[i] != "(":
            i += 1
            continue
        depth, j, top, child_start = 0, i, [], None
        while j < n:
            c = line[j]
            if c == "(":
                if depth == 1:
                    child_start = j
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 1 and child_start is not None:
                    top.append(line[child_start:j + 1])
                    child_start = None
                elif depth == 0:
                    break
            j += 1
        if depth == 0 and len(top) == 3 and all(t.startswith("(") for t in top):
            out.append(line[i:j + 1])
        i += 1
    return out


def detect_total_serializer_fallback(root):
    """A `_ =>` arm inside a human serializer fn that calls the human path."""
    hits = []
    for path in walk(root, (".rs",)):
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        fn = None
        for i, line in enumerate(lines):
            m = FN_RE.match(line)
            if m:
                fn = m.group(1)
            if fn and HUMAN_SERIALIZER.search(fn) and re.match(r"^\s*_\s*=>", line):
                arm = line + " " + (lines[i + 1] if i + 1 < len(lines) else "")
                if HUMAN_PATH_CALL.search(arm):
                    hits.append(("total-serializer-fallback", path, i + 1, line.strip()))
    return hits


def detect_implicit_default_flag(root):
    """A keyed lookup turned into a bool, so a missing field reads as false."""
    hits = []
    for path in walk(root, (".rs",)):
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(lines):
            m = FN_RE.match(line)
            if not m or not FLAG_NAME.search(m.group(1)):
                continue
            body, depth, started = [], 0, False
            for j in range(i, min(i + 40, len(lines))):
                body.append(lines[j])
                depth += lines[j].count("{") - lines[j].count("}")
                if "{" in lines[j]:
                    started = True
                if started and depth <= 0:
                    break
            blob = "\n".join(body)
            if ("-> bool" in blob and FLAG_LOOKUP.search(blob) and FLAG_DERIVE.search(blob)
                    and not FLAG_EXPLICIT_MISSING.search(blob)):
                hits.append(("implicit-default-flag", path, i + 1, line.strip()))
    return hits


def detect_fail_fast_hides_suites(root):
    """A workflow running a whole cargo workspace without --no-fail-fast."""
    hits = []
    wf = os.path.join(root, ".github", "workflows")
    if not os.path.isdir(wf):
        return hits
    for path in walk(wf, (".yml", ".yaml")):
        for i, line in enumerate(open(path, encoding="utf-8", errors="replace").read().splitlines()):
            s = line.strip()
            if s.startswith("#") or "cargo test" not in line:
                continue
            if re.search(r"--workspace|--all\b|--all-targets", line) and "--no-fail-fast" not in line:
                hits.append(("fail-fast-hides-suites", path, i + 1, s))
    return hits


def detect_silent_regeneration(root):
    """Legacy 3-field COND control in a generator template or generated artifact."""
    hits = []
    for path in walk(root, (".lisp",)):
        rel = os.path.relpath(path, root)
        if not (rel.startswith(os.path.join("scripts", "generate"))
                or rel.startswith(os.path.join("lib", "generated"))):
            continue
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        depth, cond_depth = 0, None
        for i, line in enumerate(lines):
            if cond_depth is None and re.search(r"\(00000111\b", line):
                cond_depth = depth
            if cond_depth is not None:
                for clause in three_field_clauses(line):
                    hits.append(("silent-regeneration", path, i + 1, clause))
                    break
            depth += line.count("(") - line.count(")")
            if cond_depth is not None and depth <= cond_depth:
                cond_depth = None
    return hits


DETECTORS = [
    detect_total_serializer_fallback,
    detect_implicit_default_flag,
    detect_fail_fast_hides_suites,
    detect_silent_regeneration,
]


def scan(root):
    hits = []
    for fn in DETECTORS:
        hits.extend(fn(root))
    out = []
    for cls, path, line, snippet in hits:
        rel = os.path.relpath(path, root)
        out.append({"class": cls, "file": rel, "line": line,
                    "key": f"{cls}|{rel}|{norm(snippet)}", "snippet": norm(snippet)})
    return sorted(out, key=lambda h: (h["class"], h["file"], h["line"]))


INV_SITE = re.compile(
    r'\(site\s+\(class\s+"([^"]+)"\)\s+\(file\s+"([^"]+)"\)\s+'
    r'\(key\s+"((?:[^"\\]|\\.)*)"\)\s+\(line\s+"(\d+)"\)\)')


def read_inventory(path):
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return {}
    return {m.group(3).replace('\\"', '"'): (m.group(1), m.group(2), int(m.group(4)))
            for m in INV_SITE.finditer(text)}


def emit_inventory(hits):
    lines = [
        ";; Silent-fallback inventory (#2134).",
        ";; Baseline for scripts/check-silent-fallback-classes.py: a known site passes,",
        ";; a NEW unnamed site fails. Regenerate with --emit-inventory.",
        ";; Classes: total-serializer-fallback | implicit-default-flag |",
        ";;          fail-fast-hides-suites | silent-regeneration.",
        "(silent-fallback-inventory",
    ]
    for h in hits:
        key = h["key"].replace('"', '\\"')
        lines.append(f'  (site (class "{h["class"]}") (file "{h["file"]}") '
                     f'(key "{key}") (line "{h["line"]}"))')
    lines.append(")")
    return "\n".join(lines) + "\n"


def compare(hits, baseline):
    current = {h["key"]: h for h in hits}
    new = [h for k, h in current.items() if k not in baseline]
    stale = [k for k in baseline if k not in current]
    return new, stale


def run(root, inventory_path, emit):
    hits = scan(root)
    if emit:
        sys.stdout.write(emit_inventory(hits))
        return 0
    baseline = read_inventory(inventory_path) if inventory_path else {}
    new, stale = compare(hits, baseline)
    print(f"(silent-fallback-scan (sites {len(hits)}) (known {len(hits) - len(new)}) "
          f"(new {len(new)}) (stale {len(stale)}))")
    for h in hits:
        mark = "NEW " if h["key"] not in baseline else "    "
        print(f"  {mark}{h['class']:28} {h['file']}:{h['line']}")
    if new:
        print("\nsilent-fallback-violation: a site is not named in the inventory.")
        print("  Name it in the inventory, or make the fallback explicit / a named refusal.")
        for h in new:
            print(f"  - {h['class']}: {h['file']}:{h['line']}  {h['snippet'][:80]}")
        return 1
    for k in stale:
        cls, f, line = baseline[k]
        print(f"  (stale baseline entry: {cls} {f}:{line})")
    print("(silent-fallback-ok)")
    return 0


# --- self-test ---------------------------------------------------------------

SELFTEST_TREE = {
    "crates/sens/src/value.rs": (
        "fn render_canonical_wire(value: &Value) -> String {\n"
        "    match value {\n"
        "        Value::Text7(text) => text.to_canonical_wire_token(),\n"
        "        _ => render(value, true),\n"
        "    }\n"
        "}\n"),
    "crates/sens/src/clean.rs": (
        "fn render_exhaustive(value: &Value) -> String {\n"
        "    match value {\n"
        "        Value::Text7(t) => t.to_canonical_wire_token(),\n"
        "        Value::Number(n) => n.to_string(),\n"
        "    }\n"
        "}\n"),
    "crates/sens/tests/semantic_authority.rs": (
        "fn alist_flag(entries: &[Expr], key: &str) -> bool {\n"
        "    matches!(alist_field(entries, key).map(|v| &v.kind),\n"
        "        Some(ExprKind::Symbol(s)) if &**s == \"t\")\n"
        "}\n"),
    "crates/sens/src/predicates.rs": (
        "pub fn is_atom(&self) -> bool {\n"
        "    matches!(self, Value::Atom(_))\n"
        "}\n"),
    "crates/sens/tests/ok.rs": (
        "fn alist_flag_strict(entries: &[Expr], key: &str) -> bool {\n"
        "    alist_field(entries, key).map(|v| is_yes(v)).unwrap_or(true)\n"
        "}\n"),
    ".github/workflows/ci.yml": "        run: cargo test --workspace\n",
    ".github/workflows/ok.yml": "        run: cargo test --workspace --no-fail-fast\n",
    ".github/workflows/note.yml": "        # `cargo test --workspace` belongs to full-nightly\n",
    "scripts/generate-meta-semantic-registry.lisp": (
        '(00001001 render-projection\n'
        '      "      (00000111\\n"\n'
        '      "        ((00000010 entry) () (00000001 ()))\\n")\n'),
    "lib/generated/clean.lisp": "(00000111 ((test) (expr)))\n",
}


def self_test():
    import tempfile
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        for rel, content in SELFTEST_TREE.items():
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(content)
        hits = scan(tmp)
        got = {h["class"] for h in hits}
        expect = {"total-serializer-fallback", "implicit-default-flag",
                  "fail-fast-hides-suites", "silent-regeneration"}
        for cls in sorted(expect):
            ok = cls in got
            failures += 0 if ok else 1
            print(f"  [{'ok' if ok else 'FAIL'}] detects {cls}")
        clean_hits = [h for h in hits if h["file"] in
                      ("crates/sens/src/clean.rs", "crates/sens/src/predicates.rs",
                       "crates/sens/tests/ok.rs", ".github/workflows/ok.yml",
                       ".github/workflows/note.yml", "lib/generated/clean.lisp")]
        ok = not clean_hits
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] negatives stay clean "
              f"({len(clean_hits)} false hits: {[h['file'] for h in clean_hits]})")
        baseline = {h["key"]: None for h in hits}
        new, stale = compare(hits, baseline)
        ok = not new and not stale
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] baseline round-trips "
              f"(new {len(new)}, stale {len(stale)})")

        inventory_path = os.path.join(tmp, "silent-fallback-inventory.lisp")
        open(inventory_path, "w", encoding="utf-8").write(emit_inventory(hits))
        parsed = read_inventory(inventory_path)
        ok = all(
            key in parsed and parsed[key][2] == h["line"]
            for h in hits
            for key in [h["key"]]
        )
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] emitted quoted line provenance parses back "
              f"({len(parsed)} sites)")
        extra = list(hits) + [{"class": "total-serializer-fallback", "file": "x.rs", "line": 1,
                               "key": "total-serializer-fallback|x.rs|_ => render(y, true)",
                               "snippet": "_ => render(y, true)"}]
        new, _ = compare(extra, baseline)
        ok = len(new) == 1
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] a new site is flagged ({len(new)} new)")
    if failures:
        print(f"silent-fallback-selftest-failed ({failures})")
        return 1
    print("(silent-fallback-selftest-ok (4 classes, 6 negatives, baseline, delta))")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--inventory", default="knowledge/silent-fallback-inventory.lisp")
    ap.add_argument("--emit-inventory", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return run(args.root, args.inventory, args.emit_inventory)


if __name__ == "__main__":
    sys.exit(main())
