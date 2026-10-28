#!/usr/bin/env python3
"""Паритет міжмовного корпусу ENERGY-02 (#6287).

НАВІЩО: порівнювати енергію/час мов можна лише тоді, коли всі реалізації
роблять ТУ САМУ функціональну одиницю і дають ПЕРЕВІРЮВАНИЙ вихід. Інакше
вимірюється різна робота, і числа нічого не означають.

Два різні розміри, і їх не можна плутати:
  • VERIFY_SIZE — малий вхід, на якому перевіряється КОРРЕКТНІСТЬ (паритет);
  • MEASURE_SIZE — великий вхід із маніфесту, на якому міряють час/пам'ять/енергію.

Паритет НЕ доводить швидкість. Він доводить лише, що порівнюються однакові дії.

Кожна задача має еталонний вихід, обчислений тут (референсна реалізація
Python). Реалізація іншою мовою проходить, лише якщо її вихід збігається:
  • check=exact    — точна рівність;
  • check=bitwise  — побітова рівність серіалізованого виходу;
  • check=tolerance— числова похибка в межах tolerance (наперед заданого).

Запуск: python3 benchmarks/language-energy-study/parity_check.py [--selftest]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent / "corpus" / "manifest.json"
REQUIRED_FIELDS = ("id", "axis", "functional_unit", "input", "contract", "check")
VALID_CHECKS = ("exact", "bitwise", "tolerance")


# --------------------------------------------------------------------------
# Референсні реалізації. МАЛІ входи — це перевірка коректності, не вимір.
# --------------------------------------------------------------------------

def ref_T01(n: int) -> str:
    def fib(k: int) -> int:
        return k if k < 2 else fib(k - 1) + fib(k - 2)
    return str(fib(n))


def ref_T02(n: int) -> str:
    total = sum((Fraction(1, k) for k in range(1, n + 1)), Fraction(0))
    return f"{total.numerator}/{total.denominator}"


def ref_T03(lines: int) -> str:
    rows = [f"k{(i * 7919) % 1000}=v{i}" for i in range(lines)]
    keys = sorted(r.split("=", 1)[0] for r in rows)
    return hashlib.sha256("\n".join(keys).encode()).hexdigest()


def _lcg(seed: int, count: int) -> list[int]:
    x = seed & 0xFFFFFFFFFFFFFFFF
    out = []
    for _ in range(count):
        x = (x * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        out.append(x)
    return out


def ref_T04(n: int, seed: int) -> str:
    return hashlib.sha256(
        ",".join(str(v) for v in sorted(_lcg(seed, n))).encode()).hexdigest()


def ref_T05(n: int, k: int) -> str:
    return str(sum(len(list(range(k))) for _ in range(n)))


def ref_T06(lines: int) -> str:
    payload = "".join(f"line-{i:06d}\n" for i in range(lines))
    back = payload.splitlines()
    return f"{len(payload.encode())}:{len(back)}"


def ref_T07(n: int) -> str:
    """Контракт T07 — ЧИСЛОВА похибка, тому еталон повертає число, а не хеш.

    Сума всіх елементів добутку — скаляр, який чутливий до кожного елемента,
    але порівнюється з допуском. Хеш тут був би неправильним: він перетворює
    tolerance-перевірку на побітову і ламає сам сенс задачі T07.
    """
    a = [[1.0 if (i + j) % 7 else 0.5 for j in range(n)] for i in range(n)]
    total = 0.0
    for i in range(n):
        for j in range(n):
            total += sum(a[i][k] * a[k][j] for k in range(n))
    return f"{total:.12f}"


def ref_T08(n: int) -> str:
    versions = []
    current = ()
    for i in range(n):
        current = current + (i,)
        if i % 1000 == 0:
            versions.append(len(current))
    return hashlib.sha256(",".join(map(str, versions + [len(current)])).encode()).hexdigest()


def ref_T09(n: int, seed: int) -> str:
    return str(sum(bin(v).count("1") for v in _lcg(seed, n)))


PY_MODULES = {
    "T01-symbolic-recursion": "ref_T01", "T02-exact-rationals": "ref_T02",
    "T03-parsing-text": "ref_T03", "T04-sorting": "ref_T04",
    "T05-allocation-gc": "ref_T05", "T06-io": "ref_T06",
    "T07-matrices": "ref_T07", "T08-persistent-structures": "ref_T08",
    "T09-bit-operations": "ref_T09",
}

REFERENCE = {
    "T01-symbolic-recursion": lambda i: ref_T01(i["n"]),
    "T02-exact-rationals": lambda i: ref_T02(i["n"]),
    "T03-parsing-text": lambda i: ref_T03(i["lines"]),
    "T04-sorting": lambda i: ref_T04(i["n"], i["seed"]),
    "T05-allocation-gc": lambda i: ref_T05(i["n"], i["k"]),
    "T06-io": lambda i: ref_T06(i["lines"]),
    "T07-matrices": lambda i: ref_T07(i["n"]),
    "T08-persistent-structures": lambda i: ref_T08(i["n"]),
    "T09-bit-operations": lambda i: ref_T09(i["n"], i["seed"]),
}

# Малі входи для ПЕРЕВІРКИ КОРЕКТНОСТІ — навмисно менші за вимірювальні.
VERIFY_SIZE = {
    "T01-symbolic-recursion": {"n": 12},
    "T02-exact-rationals": {"n": 20},
    "T03-parsing-text": {"lines": 50},
    "T04-sorting": {"n": 500, "seed": 7},
    "T05-allocation-gc": {"n": 200, "k": 4},
    "T06-io": {"lines": 100},
    "T07-matrices": {"n": 6},
    "T08-persistent-structures": {"n": 500},
    "T09-bit-operations": {"n": 2000, "seed": 3},
}


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(doc: dict) -> list[str]:
    """Схема маніфесту. Повертає список проблем (порожній = ок)."""
    problems: list[str] = []
    if doc.get("schema") != "sens-energy-corpus/v1":
        problems.append("schema must be sens-energy-corpus/v1")
    tasks = doc.get("tasks")
    if not isinstance(tasks, list):
        return problems + ["tasks must be a list"]
    if not 8 <= len(tasks) <= 10:
        problems.append(f"tasks must be 8..10, got {len(tasks)}")
    seen_ids, seen_axes = set(), set()
    for n, t in enumerate(tasks):
        if not isinstance(t, dict):
            problems.append(f"tasks[{n}] not an object")
            continue
        for field in REQUIRED_FIELDS:
            if field not in t:
                problems.append(f"tasks[{n}] missing {field}")
        tid = t.get("id")
        if tid in seen_ids:
            problems.append(f"duplicate id {tid}")
        seen_ids.add(tid)
        if t.get("axis") in seen_axes:
            problems.append(f"duplicate axis {t.get('axis')} — осі мусять бути різні")
        seen_axes.add(t.get("axis"))
        if t.get("check") not in VALID_CHECKS:
            problems.append(f"{tid}: check must be one of {VALID_CHECKS}")
        if t.get("check") == "tolerance" and not isinstance(t.get("tolerance"), (int, float)):
            problems.append(f"{tid}: tolerance check needs numeric tolerance")
        if tid not in REFERENCE:
            problems.append(f"{tid}: no reference implementation")
    return problems


def golden(task_id: str) -> str:
    return REFERENCE[task_id](VERIFY_SIZE[task_id])


def compare(task: dict, actual: str) -> tuple[bool, str]:
    """Порівнює вихід реалізації з еталоном за контрактом задачі."""
    expected = golden(task["id"])
    kind = task["check"]
    if kind in ("exact", "bitwise"):
        ok = actual.strip() == expected.strip()
        return ok, "PARITY_OK" if ok else f"PARITY_FAILED expected={expected[:32]} actual={actual[:32]}"
    if kind == "tolerance":
        try:
            ok = abs(float(actual) - float(expected)) <= float(task["tolerance"])
        except (TypeError, ValueError):
            return False, "PARITY_FAILED non-numeric output for tolerance check"
        return ok, "PARITY_OK" if ok else "PARITY_FAILED beyond tolerance"
    return False, f"PARITY_FAILED unknown check {kind}"


def run_external(task: dict, command: str, timeout_s: float = 120.0) -> tuple[bool, str]:
    """Запускає ЗОВНІШНЮ реалізацію задачі й порівнює її вихід з еталоном.

    Чому так: інакше паритет лишається паперовим — маніфест без способу
    перевірити реальний бінарник. Команда отримує вхід задачі через змінні
    середовища (VERIFY_SIZE) і мусить надрукувати рівно один рядок — вихід.

    НЕ міряє час/енергію. Лише вердикт «та сама дія чи ні».
    """
    import os
    import subprocess

    env = dict(os.environ)
    env["TASK_ID"] = task["id"]
    for key, value in VERIFY_SIZE[task["id"]].items():
        env["TASK_" + key.upper()] = str(value)
    try:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True,
                              timeout=timeout_s, env=env)
    except subprocess.TimeoutExpired:
        return False, f"PARITY_FAILED timeout after {timeout_s}s"
    except OSError as exc:
        return False, f"PARITY_FAILED cannot execute: {exc}"
    if proc.returncode != 0:
        return False, f"PARITY_FAILED exit={proc.returncode} stderr={proc.stderr.strip()[:120]}"
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    if len(lines) != 1:
        return False, f"PARITY_FAILED expected exactly 1 output line, got {len(lines)}"
    return compare(task, lines[0])


def selftest() -> int:
    """Доводить, що паритет ЛОВИТЬ підміну, а не погоджується на все."""
    doc = load_manifest()
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if cond:
            print(f"  PASS  {name}")
        else:
            failures.append(f"{name}: {detail}")
            print(f"  FAIL  {name} — {detail}")

    print("[1] Схема маніфесту")
    problems = validate_manifest(doc)
    check("маніфест валідний", not problems, "; ".join(problems[:3]))

    print("\n[2] Кількість і різнорідність")
    check("8..10 задач", 8 <= len(doc["tasks"]) <= 10, f"{len(doc['tasks'])}")
    axes = {t["axis"] for t in doc["tasks"]}
    check("усі осі різні", len(axes) == len(doc["tasks"]), f"{len(axes)} осей")

    print("\n[3] Коректна реалізація проходить")
    for t in doc["tasks"]:
        ok, verdict = compare(t, golden(t["id"]))
        check(f"{t['id']} приймається", ok, verdict)

    print("\n[4] Підміна виходу відхиляється")
    for t in doc["tasks"]:
        ok, verdict = compare(t, golden(t["id"]) + "x")
        check(f"{t['id']} зіпсований вихід → PARITY_FAILED", not ok, verdict)

    print("\n[5] Порожній вихід відхиляється")
    for t in doc["tasks"]:
        ok, _ = compare(t, "")
        check(f"{t['id']} порожній вихід відхилено", not ok, "прийнято порожнє")

    print("\n[6] Порівнюються однакові дії, а не різна робота")
    check("перевірочні входи МЕНШІ за вимірювальні",
          all(VERIFY_SIZE[t["id"]] != t["input"] for t in doc["tasks"]),
          "хтось використав вимірювальний вхід для паритету")

    print("\n" + "=" * 60)
    if failures:
        print(f"ПРОВАЛЕНО {len(failures)}:")
        for f in failures:
            print("  •", f)
        return 1
    print("ПАРИТЕТ-МАШИНА: УСІ ПЕРЕВІРКИ ПРОЙДЕНО")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--golden", metavar="TASK_ID")
    ap.add_argument("--run", metavar="COMMAND",
                    help="зовнішня реалізація; отримує TASK_* у середовищі, друкує 1 рядок")
    ap.add_argument("--task", metavar="TASK_ID", help="з --run: яку задачу перевіряти")
    args = ap.parse_args()
    if args.golden:
        print(golden(args.golden))
        return 0
    if args.run:
        if not args.task:
            print("--run потребує --task")
            return 2
        doc = load_manifest()
        task = next((t for t in doc["tasks"] if t["id"] == args.task), None)
        if task is None:
            print(f"невідома задача {args.task}")
            return 2
        ok, verdict = run_external(task, args.run)
        print(f"{task['id']}: {verdict}")
        return 0 if ok else 1
    if args.selftest:
        return selftest()
    problems = validate_manifest(load_manifest())
    for p in problems:
        print("PROBLEM:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
