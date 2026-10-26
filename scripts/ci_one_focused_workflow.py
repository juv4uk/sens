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
                # Реліз запускається ВИКЛЮЧНО по тегу s<version> — це явна дія
                # власника, а не автозапуск на кожен коміт. Такий push не
                # споживає бюджет гілкового CI, тому дозволяємо РІВНО його:
                # push із фільтром tags і БЕЗ фільтра branches. Усе інше —
                # додатковий автоматичний тригер і далі провал.
                tag_only = (
                    automatic == {"push"}
                    and "tags:" in found["push"]
                    and "branches:" not in found["push"]
                    and "branches-ignore:" not in found["push"]
                )
                if not tag_only:
                    raise ValueError(f"додатковий автоматичний тригер {sorted(automatic)}")
        except (ValueError, OSError) as exc:
            errors.append(f"{path.name}: {exc}")
    if auto != ["ci.yml"]:
        errors.append(f"очікується один ci.yml, знайдено {auto}")
    # Синтаксис/семантику D1–D10 перевіряє SENS/Zig runtime у CI.
    # Текстова форма селекторів може законно змінюватися: не ставити
    # реліз/міграцію в залежність від Python-зіставлення рядків.
    # Owner decision (2026-10-14): named native executor receipts and
    # arbitrary native-vs-Rust parity quotas are NOT required. They may run,
    # but absence of --require or scan-executors must not freeze migration.
    # Preserve the independent truth-in-label contract: any step that DOES
    # claim a binary SENS executor must actually invoke that executor.
    # Ручна зміна main: перевіряємо job-level умову ДО checkout,
    # build та використання write-token. Це CI-механізм, не SENS-оракул.
    promote_path = WORKFLOWS / "contest-promote.yml"
    try:
        promote_text = promote_path.read_text(encoding="utf-8")
        must_guard = (
            "  promote:\n"
            "    if: ${{ github.event_name == 'workflow_dispatch' "
            "&& github.ref == 'refs/heads/main' }}\n"
        )
        if must_guard not in promote_text:
            errors.append(
                "CONTEST_PROMOTE_UNSAFE_REF id=contest-promote layer=actions "
                "expected=main-only-job actual=unguarded-or-different-guard "
                "reproduce='python3 scripts/ci_one_focused_workflow.py'"
            )
    except OSError as exc:
        errors.append(f"CONTEST_PROMOTE_MISSING_CONFIG path={promote_path}: {exc}")
    ci_text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    # Механічна перевірка YAML-метаданих, а не оракул семантики Lisp.
    # Виявляємо повтори кроків та id при помилковому злитті ci.yml.
    for field, pattern in (
        ("name", r"^      - name: (.+?)\s*$"),
        ("id", r"^        id:\s*([a-zA-Z][a-zA-Z0-9_-]*)\s*$"),
    ):
        # Повтор шукаємо В МЕЖАХ ОДНОГО job, а не по всьому файлу: два різні
        # jobs законно можуть мати крок з однаковою назвою (наприклад,
        # «Build native SENS» у двох незалежних перевірках). Охоронець ловить
        # саме помилкове злиття в одному job, як і сказано в коментарі вище.
        matches = re.findall(pattern, ci_text, flags=re.MULTILINE)
        if field == "name" and not matches:
            errors.append("CI_STEPS_MISSING: немає іменованих кроків")
        duplicates = set()
        for job_block in re.split(r"^  [a-zA-Z][a-zA-Z0-9_-]*:\s*$", ci_text, flags=re.MULTILINE):
            seen: set[str] = set()
            for item in re.findall(pattern, job_block, flags=re.MULTILINE):
                if item in seen:
                    duplicates.add(item)
                seen.add(item)
        if duplicates:
            errors.append(
                "CI_STEPS_DUPLICATED field=" + field
                + " entries=" + ", ".join(sorted(duplicates))
            )
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
