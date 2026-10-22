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
        selectors = (
            "(визначити режим-індексу-міркування\n  (функція (індекс-правил)\n    (друге індекс-правил)))",
            "(визначити правила-індексу-міркування\n  (функція (індекс-правил)\n    (третє індекс-правил)))",
            "(визначити кошики-індексу-міркування\n  (функція (індекс-правил)\n    (третє (решта індекс-правил))))",
        )
        for selector in selectors:
            if selector not in reason:
                errors.append("reason.lisp: змінено структуру українських D4/D5 селекторів")
        start = reason.find("(визначити індекс-міркування?")
        end = reason.find("(визначити міркування-пошук-кошика", start)
        if start < 0 or end < 0:
            errors.append("reason.lisp: неможливо виокремити індекс-міркування?")
        else:
            body = reason[start:end]
            ordered = (
                "((атом? вхідне-значення) ні)",
                "((порожній? вхідне-значення) ні)",
                "((атом? (перше вхідне-значення))",
                "((тотожне? (перше вхідне-значення) схема-індексу-міркування)",
            )
            positions = [body.find(token) for token in ordered]
            if any(position < 0 for position in positions) or positions != sorted(positions):
                errors.append(
                    "reason.lisp: потрібен порядок D3 ATOM, D4 NULL, "
                    "D3 ATOM(CAR), далі D3 EQ"
                )
    except OSError as exc:
        errors.append(f"reason.lisp: {exc}")

    try:
        source = (ROOT / "lib/narrate.lisp").read_text(encoding="utf-8")
        active = "\n".join(
            line for line in source.splitlines() if not line.lstrip().startswith(";")
        )
        start = active.find("(визначити список-завершується-порожнім?")
        end = active.find("(визначити пояснити-факт", start)
        if start < 0 or end < 0:
            errors.append("narrate.lisp: cannot isolate structural arity helpers")
        else:
            helpers = active[start:end]
            required = (
                "(визначити список-завершується-порожнім?",
                "(визначити список-із-рівно-двох-елементів?",
                "(визначити список-із-рівно-трьох-елементів?",
                "((атом? значення)",
                "((порожній? значення)",
                "(решта значення)",
            )
            for token in required:
                if token not in helpers:
                    errors.append(f"narrate.lisp: required exact-width structure missing: {token}")
            if "000000" in helpers or "11110111" in helpers:
                errors.append("narrate.lisp: D6 LENGTH or D8 EQUAL returned to arity helpers")
            if "#d1:" in helpers:
                errors.append("narrate.lisp: compatibility D1 projection used instead of raw one-bit words")
        if "(визначити narrate-outcome-arity?" in active:
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
                if automatic != {"push", "pull_request"}:
                    raise ValueError(
                        "очікується один централізований автоматичний workflow "
                        "для push і pull_request чинної main: " + str(sorted(automatic))
                    )
                block = found["push"]
                if not re.search(r"^\s+branches:\s*\[main\]\s*$", block, re.M):
                    raise ValueError("push мусить охоплювати чинний main")
                for disallowed in ("paths:", "paths-ignore:", "tags:", "tags-ignore:", "branches-ignore:"):
                    if disallowed in block:
                        raise ValueError("push не може фільтрувати коміти: " + disallowed)
                pr_block = found["pull_request"]
                if not re.search(r"^\s+branches:\s*\[main\]\s*$", pr_block, re.M):
                    raise ValueError("pull_request має перевіряти чинний main")
                for disallowed in ("paths:", "paths-ignore:", "branches-ignore:", "types:"):
                    if disallowed in pr_block:
                        raise ValueError("pull_request не може фільтрувати потрібні перевірки: " + disallowed)
                auto.append(path.name)
            elif automatic:
                raise ValueError(f"додатковий автоматичний тригер {sorted(automatic)}")
        except (ValueError, OSError) as exc:
            errors.append(f"{path.name}: {exc}")
    if auto != ["ci.yml"]:
        errors.append(f"очікується один ci.yml, знайдено {auto}")
    errors.extend(verify_migration_source_shapes())
    # Owner decision (2026-10-14): named native executor receipts and
    # arbitrary native-vs-Rust parity quotas are NOT required. They may run,
    # but absence of --require or scan-executors must not freeze migration.
    # Preserve the independent truth-in-label contract: any step that DOES
    # claim a binary SENS executor must actually invoke that executor.
    ci_text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    for step in ci_text.split("      - name: ")[1:]:
        if "--layer eval" in step and "target/debug/sens" not in step:
            errors.append("UNINFORMATIVE-EXECUTOR: eval label without native SENS invocation")
        if "semantic_authority=binary-SENS" in step and "target/debug/sens" not in step:
            errors.append("UNINFORMATIVE-EXECUTOR: false binary-SENS executor label")
    # Механічний Python-guard не визначає семантику і не потребує
    # вигаданої мітки CI_GLUE_NO_SEMANTICS для кожного виклику.
    for error in errors:
        print("SENS_CI_BUDGET_FAIL", error, flush=True)
    if errors:
        return 1
    print("SENS_CI_BUDGET_PASS " + json.dumps({
        "workflow_files": len(paths),
        "automatic_workflows": auto,
        "ci_role": "mechanical_workflow_budget_only",
    }, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(verify())
