#!/usr/bin/env python3
"""Побудувати індекс історії для охоронця — один прохід по ВСІЙ історії комітів.

Навіщо: охоронець з --when робить `git log -S` на КОЖНЕ визначення — це десятки
повільних викликів. Тут ми один раз проходимо всю історію (git log --name-only
--reverse) і запам'ятовуємо, коли кожен файл і кожне визначення з'явились уперше.
Далі охоронець читає цей індекс — миттєво.

Що в індексі:
  files: {шлях: {first_sha, first_date, first_subject}}   — коли файл створено
  defs:  {"шлях:ім'я": {sha, date, subject}}               — коли визначення введено

Індекс — кеш, не істина: якщо чогось немає, охоронець усе одно вміє запитати git.

Приклад:
    python3 scripts/build-guard-history-index.py
    python3 scripts/build-guard-history-index.py --out knowledge/guard-history-index.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "knowledge" / "guard-history-index.json"
DEF = re.compile(r"\(" + "визначити" + r"\s+([^\s()]+)")
TRACKED = ("lib/", "tests/semantic/", "benchmarks/")


def git(*args: str) -> str:
    return subprocess.run(["git", "-c", "core.quotepath=false", *args],
                          cwd=ROOT, capture_output=True, text=True, check=False).stdout


def build() -> dict:
    files: dict[str, dict] = {}
    defs: dict[str, dict] = {}
    # Один прохід: найстаріші спершу, з переліком файлів на кожен коміт.
    log = git("log", "--all", "--reverse", "--name-only",
              "--format=@@%H|%ad|%s", "--date=short")
    sha = date = subject = ""
    for line in log.splitlines():
        if line.startswith("@@"):
            sha, date, subject = line[2:].split("|", 2)
            continue
        rel = line.strip()
        if not rel or not rel.endswith(".lisp") or not rel.startswith(TRACKED):
            continue
        if rel not in files:  # перше створення файлу
            files[rel] = {"first_sha": sha[:9], "first_date": date, "first_subject": subject[:80],
                          "commits": 0, "last_sha": "", "last_date": "", "active_days": []}
            text = git("show", f"{sha}:{rel}")
            for m in DEF.finditer(text):
                key = f"{rel}:{m.group(1)}"
                defs.setdefault(key, {"sha": sha[:9], "date": date, "subject": subject[:80]})
        # активність: скільки разів файл змінювали, коли востаннє, у які дні
        e = files[rel]
        e["commits"] += 1
        e["last_sha"] = sha[:9]
        e["last_date"] = date
        if date not in e["active_days"]:
            e["active_days"].append(date)
    hot = sorted(files.items(), key=lambda kv: -kv[1]["commits"])[:15]
    return {"schema": "sens.guard-history-index/v2", "files": files, "defs": defs,
            "hot_files": [{"path": k, **{x: v[x] for x in ("commits", "first_date", "last_date",
                                                           "active_days")}} for k, v in hot],
            "counts": {"files": len(files), "defs": len(defs)}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="індекс історії для охоронця")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)
    idx = build()
    Path(args.out).write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ІНДЕКС ІСТОРІЇ: {idx['counts']['files']} файлів, {idx['counts']['defs']} визначень "
          f"→ {Path(args.out).relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
