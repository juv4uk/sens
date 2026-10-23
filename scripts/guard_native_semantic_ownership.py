#!/usr/bin/env python3
"""Механічний охоронець: новий закон має виконуваний Lisp → Zig/T5M → SENS маршрут.

Це аудит джерел та CI, а НЕ семантичний оракул. Історичні борги не сертифікуються.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNNER = Path("scripts/prove-lisp-semantic-t5m.sh")
CI = Path(".github/workflows/ci.yml")

SEMANTIC_PATH = re.compile(r"tests/semantic/[\wА-Яа-яІіЇїЄєҐґ.\-]+\.lisp")
LAW_SUFFIX = re.compile(r"^(?P<stem>.+?)-(?:law|laws)\.lisp$")
MUTANT_SUFFIX = re.compile(r"^(?P<stem>.+?)-mutant\.lisp$")
EVAL_CALL = re.compile(r"\b(?:eval|eval_str|eval_source|evaluate|execute_lisp|run_lisp)\s*\(")
HOST_EXPECTED_VALUE = re.compile(r"\bassert_(?:eq|ne)!\s*\(|\bassert!\s*\(")


def declared_sources(runner: str) -> set[str]:
    # Сама згадка шляху, echo чи коментар не є виконанням.
    live = [line.split("#", 1)[0].strip()
            for line in runner.splitlines() if line.split("#", 1)[0].strip()]
    invocations = [line for line in live
                   if re.match(r"^run_case\s+run_(?:law|bound_law|type_rejection)\s+", line)]
    declared: set[str] = set()
    for line in invocations:
        declared.update(SEMANTIC_PATH.findall(line))
    # Залежні DEFINE збираються cat у тимчасове джерело;
    # цей bundle зараховується лише якщо run_case справді його викликає.
    for line in live:
        if not re.match(r"^cat\s+", line):
            continue
        sources = SEMANTIC_PATH.findall(line)
        destination = re.search(r">\s*[\"']?\$([A-Za-z_][A-Za-z_0-9]*)", line)
        if destination:
            name = destination.group(1)
            if any(re.search(r"\$" + re.escape(name) + r"\b", call)
                   for call in invocations):
                declared.update(sources)
    return declared


def companion_for_law(path: str) -> str | None:
    name = Path(path).name
    if name.startswith("language-law-"):
        return path.replace("/language-law-", "/language-mutant-", 1)
    found = LAW_SUFFIX.fullmatch(name)
    return str(Path(path).with_name(found.group("stem") + "-mutant.lisp")) if found else None


def companions_for_mutant(path: str) -> list[str]:
    name = Path(path).name
    if name.startswith("language-mutant-"):
        return [path.replace("/language-mutant-", "/language-law-", 1)]
    found = MUTANT_SUFFIX.fullmatch(name)
    if not found:
        return []
    return [str(Path(path).with_name(found.group("stem") + suffix))
            for suffix in ("-law.lisp", "-laws.lisp", "-positive.lisp")]


def audit_added_paths(added: list[str], runner: str, ci: str, exists, read_file) -> list[str]:
    errors: list[str] = []
    routed = declared_sources(runner)
    if "bash scripts/prove-lisp-semantic-t5m.sh" not in ci:
        errors.append("NATIVE_LANGUAGE_RUNNER_NOT_IN_CI file=.github/workflows/ci.yml")
    for stage in ("--t5m-mint", "verify-view", "--t5m-pair", "sens-standalone"):
        if stage not in runner:
            errors.append(f"NATIVE_LANGUAGE_CORRIDOR_MISSING stage={stage}")
    for path in sorted(set(added)):
        if path.startswith("tests/semantic/") and path.endswith(".lisp"):
            if not exists(path):
                errors.append(f"SENS_LAW_SOURCE_MISSING source={path}")
                continue
            if path not in routed:
                errors.append(
                    f"SENS_LAW_NOT_REGISTERED source={path} runner={RUNNER} "
                    "expected=run_case/native-T5M")
            counterpart = companion_for_law(path)
            if counterpart:
                if not exists(counterpart):
                    errors.append(
                        f"SENS_LAW_MUTANT_MISSING source={path} expected={counterpart}")
                elif counterpart not in routed:
                    errors.append(
                        f"SENS_LAW_MUTANT_NOT_ROUTED source={path} expected={counterpart}")
            alternatives = companions_for_mutant(path)
            if alternatives:
                existing_positive = [candidate for candidate in alternatives if exists(candidate)]
                if not existing_positive:
                    errors.append(
                        f"SENS_LAW_POSITIVE_MISSING source={path} "
                        f"expected=one-of:{','.join(alternatives)}")
                elif not any(candidate in routed for candidate in existing_positive):
                    errors.append(
                        f"SENS_LAW_POSITIVE_NOT_ROUTED source={path} "
                        f"expected=one-of:{','.join(existing_positive)}")
        # Вузька, перевірювана ознака НОВОГО Rust-оракула: eval + assert(Value).
        # Тести Rust I/O, парсера, аварій та байтового механізму не блокуємо.
        if (path.startswith("crates/") and "/tests/" in path
                and path.endswith(".rs") and exists(path)):
            host = read_file(path)
            if (EVAL_CALL.search(host) and HOST_EXPECTED_VALUE.search(host)
                    and re.search(r"\b(?:Value::|PredicateBit|is_truthy\b|truth_value\b)", host)):
                errors.append(
                    f"HOST_SEMANTIC_ORACLE_ADDED source={path} "
                    "move=tests/semantic/*.lisp")
    return errors


def added_since(base: str, head: str) -> list[str]:
    # NUL роздільники зберігають UTF-8 назви; без shell-розбору файлів.
    result = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--name-only", "-z", "--diff-filter=A",
         base, head, "--", "tests/semantic/", "crates/"],
        cwd=ROOT, capture_output=True, check=True)
    return [part.decode("utf-8") for part in result.stdout.split(b"\0") if part]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()
    try:
        added = added_since(args.base, args.head)
        runner = (ROOT / RUNNER).read_text(encoding="utf-8")
        ci = (ROOT / CI).read_text(encoding="utf-8")
        errors = audit_added_paths(
            added, runner, ci,
            lambda p: (ROOT / p).is_file() and not (ROOT / p).is_symlink(),
            lambda p: (ROOT / p).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError, subprocess.CalledProcessError) as exc:
        print(f"::error::SENS_LANGUAGE_OWNERSHIP_GATE_FAILURE actual={exc}", file=sys.stderr)
        return 2
    for error in errors:
        print(f"::error::REGRESSION layer=test-authority {error}", file=sys.stderr)
    print(f"SENS_LANGUAGE_OWNERSHIP_AUDIT added={len(added)} rejected={len(errors)} "
          "semantic=NOT_ASSERTED native_runner=REQUIRED")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
