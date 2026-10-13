#!/usr/bin/env python3
"""Механічний бюджет GitHub Actions; семантику визначає лише двійковий SENS."""
import json
from pathlib import Path
import re
import sys

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github/workflows"
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
                    raise ValueError(f"очікується єдиний push main: {sorted(automatic)}")
                block = found["push"]
                if not re.search(r"^\s+branches:\s*\[main\]", block, re.M):
                    raise ValueError("push не обмежений main")
                if not re.search(r"^\s+paths:\s*$", block, re.M):
                    raise ValueError("відсутній вузький paths-фільтр")
                if "tags:" in block:
                    raise ValueError("push тегів заборонений")
                auto.append(path.name)
            elif automatic:
                raise ValueError(f"додатковий автоматичний тригер {sorted(automatic)}")
        except (ValueError, OSError) as exc:
            errors.append(f"{path.name}: {exc}")
    if auto != ["ci.yml"]:
        errors.append(f"очікується один ci.yml, знайдено {auto}")
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
