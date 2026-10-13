#!/usr/bin/env python3
"""Механічний бюджет GitHub Actions; семантику визначає лише двійковий SENS."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
ON = re.compile(r"""^['"]?on['"]?:\s*(.*)$""")
EVENT = re.compile(r"^  ([\w-]+):")


def events(source):
    lines = source.splitlines()
    for i, line in enumerate(lines):
        match = ON.match(line)
        if match is None:
            continue
        tail = match.group(1).split(" #", 1)[0].strip()
        if tail:
            if tail.startswith("[") and tail.endswith("]"):
                return {name.strip().strip("'\""): "" for name in tail[1:-1].split(",") if name.strip()}
            if re.fullmatch(r"[\w-]+", tail):
                return {tail: ""}
            raise ValueError("непідтримана форма події")
        found = {}
        current = None
        for row in lines[i + 1:]:
            if row.strip() and not row[0].isspace() and not row.startswith("#"):
                break
            event = EVENT.match(row)
            if event:
                current = event.group(1)
                found[current] = row
            elif current is not None:
                found[current] += "\n" + row
        return found
    raise ValueError("відсутнє on:")



def verify_migration_source_shapes():
    """Mechanical guard only: exact-domain source boundaries, never a truth table."""
    errors = []
    try:
        reason = (ROOT / "lib/reason.lisp").read_text(encoding="utf-8")
        start = reason.find("(0011 reason-index?")
        end = reason.find("(0011 міркування-пошук-кошика", start)
        if end < 0:
            end = reason.find("(0011 reason-index-linear", start)
        if start < 0 or end < 0:
            errors.append("reason.lisp: cannot isolate reason-index? production form")
        else:
            body = reason[start:end]
            ordered = [
                "((010 value) #d1:0)",
                "((0101 value) #d1:0)",
                "((010 (100 value))",
                "((101 (100 value) *reason-index-schema*)",
            ]
            positions = [body.find(token) for token in ordered]
            if any(position < 0 for position in positions) or positions != sorted(positions):
                errors.append(
                    "reason.lisp: require exact D1 atom-reject, D4 NULL, "
                    "D3 ATOM(CAR), then D3 EQ in that order"
                )
    except OSError as exc:
        errors.append(f"reason.lisp: {exc}")

    try:
        source = (ROOT / "lib/narrate.lisp").read_text(encoding="utf-8")
        active = "\n".join(
            line for line in source.splitlines() if not line.lstrip().startswith(";")
        )
        start = active.find("(0011 narrate-proper-list?")
        end = active.find("(0011 narrate-fact", start)
        if start < 0 or end < 0:
            errors.append("narrate.lisp: cannot isolate structural arity helpers")
        else:
            helpers = active[start:end]
            required = (
                "(0011 narrate-proper-list?",
                "(0011 narrate-list-exact-two?",
                "(0011 narrate-list-exact-three?",
                "((010 value)",
                "((0101 value)",
                "(011 value)",
            )
            for token in required:
                if token not in helpers:
                    errors.append(f"narrate.lisp: required exact-width structure missing: {token}")
            if "000000" in helpers or "11110111" in helpers:
                errors.append("narrate.lisp: D6 LENGTH or D8 EQUAL returned to arity helpers")
            if "#d1:" in helpers:
                errors.append("narrate.lisp: compatibility D1 projection used instead of raw one-bit words")
        if "(0011 narrate-outcome-arity?" in active:
            errors.append("narrate.lisp: legacy arity function still present")
    except OSError as exc:
        errors.append(f"narrate.lisp: {exc}")

    for error in errors:
        print("SENS_SOURCE_BOUNDARY_FAIL", error, flush=True)
    if not errors:
        print(
            "SENS_SOURCE_BOUNDARY_PASS "
            "reason-index?=D1/D4/D3-before-EQ; "
            "narrate=raw-D1+D3/D4-without-D6/D8",
            flush=True,
        )
    return errors


def verify():
    paths = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
    if not paths:
        raise ValueError("відсутні workflow")
    errors = []
    auto = []
    for path in paths:
        try:
            found = events(path.read_text(encoding="utf-8"))
            if not found:
                raise ValueError("порожні тригери")
            automatic = set(found) - {"workflow_dispatch", "workflow_call"}
            if path.name == "ci.yml":
                if automatic != {"push"}:
                    raise ValueError(f"очікується єдиний push для всіх гілок: {sorted(automatic)}")
                block = found["push"]
                if not re.search(r"^\s+branches:\s*\['\*\*'\]\s*$", block, re.M):
                    raise ValueError("push мусить охоплювати всі гілки без винятків")
                for disallowed in ("paths:", "paths-ignore:", "tags:", "tags-ignore:", "branches-ignore:"):
                    if disallowed in block:
                        raise ValueError("push не може фільтрувати коміти: " + disallowed)
                auto.append(path.name)
            elif automatic:
                raise ValueError(f"додатковий автоматичний тригер {sorted(automatic)}")
        except (ValueError, OSError) as exc:
            errors.append(f"{path.name}: {exc}")
    if auto != ["ci.yml"]:
        errors.append(f"очікується один ci.yml, знайдено {auto}")
    errors.extend(verify_migration_source_shapes())
    for error in errors:
        print("SENS_CI_BUDGET_FAIL", error, flush=True)
    if errors:
        return 1
    print("SENS_CI_BUDGET_PASS " + json.dumps({
        "workflow_files": len(paths),
        "automatic_workflows": auto,
        "semantic_authority": "physical_binary_SENS",
    }, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(verify())
