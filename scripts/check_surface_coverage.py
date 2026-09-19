#!/usr/bin/env python3
"""Перевіряє, що runtime public names класифіковані byte-SID registry.

Сире runtime inventory може містити історичні/host-oriented spellings. Воно не
є semantic authority. Єдина authority — `semantic-registry.lisp`; кожна видима
публічна назва повинна бути surface name деякої byte SID.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_FILE = REPO_ROOT / "lib" / "surface" / "semantic-registry.lisp"
INVENTORY_FILE = REPO_ROOT / "lib" / "surface" / "uk-inventory.lisp"
CORE_LIB = REPO_ROOT / "lib" / "core.lisp"
SURFACE = re.compile(r"\(([A-Za-z][A-Za-z0-9-]*)\s+(\(\)|[^\s()]+)\)")


def extract_registry_names(path: Path) -> set[str]:
    names: set[str] = set()
    for surface, name in SURFACE.findall(path.read_text(encoding="utf-8")):
        if len(name) >= 2 and name[0] == name[-1] == '"':
            name = name[1:-1]
        if name not in ("—", "()"):
            names.add(name)
    return names


def extract_inventory_names(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    names = set()
    groups = (
        "canon|necessary-forms|language-macros|compatibility-forms|"
        "root-builtins|core-library"
    )
    for match in re.finditer(rf"\(({groups})\s+", text):
        start = match.end()
        depth = 1
        index = start
        while index < len(text) and depth > 0:
            if text[index] == "(":
                depth += 1
            elif text[index] == ")":
                depth -= 1
            index += 1
        for word in text[start:index - 1].split():
            word = word.strip("()")
            if word and not word.startswith(";"):
                names.add(word)
    return names


def extract_core_public_names(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    names = set()
    internal_markers = {"-onto", "-iter", "-step", "make-", "-helper", "-aux", "my-postcore-"}
    for pattern in (r"\(def\s+(\S+)\s+", r"\(defmacro\s+(\S+)\s+"):
        for match in re.finditer(pattern, text):
            name = match.group(1)
            if not any(marker in name for marker in internal_markers):
                names.add(name)
    return names


def main() -> int:
    for path in (REGISTRY_FILE, INVENTORY_FILE, CORE_LIB):
        if not path.exists():
            print(f"ERROR: required file not found: {path}", file=sys.stderr)
            return 2

    registry_names = extract_registry_names(REGISTRY_FILE)
    inventory_names = extract_inventory_names(INVENTORY_FILE)
    core_names = extract_core_public_names(CORE_LIB)
    eligible = inventory_names | core_names

    internal_markers = {"-onto", "-iter", "-step", "make-", "-helper", "-aux", "my-postcore-"}
    unclassified = {
        name for name in eligible - registry_names
        if not any(marker in name for marker in internal_markers)
    }

    if unclassified:
        print("SURFACE DRIFT DETECTED")
        print("=" * 60)
        print("Ці public runtime names не належать жодній numeric semantic identity:")
        for name in sorted(unclassified):
            print(f"  - {name}")
        print(f"Total unclassified: {len(unclassified)}")
        print("Add them to lib/surface/semantic-registry.lisp with an explicit status.")
        return 1

    print("OK: every eligible runtime name is classified by byte-SID semantic registry.")
    print(f"  Registry surface names: {len(registry_names)}")
    print(f"  Inventory names: {len(inventory_names)}")
    print(f"  Core public names: {len(core_names)}")
    print(f"  Total eligible: {len(eligible)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
