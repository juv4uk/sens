#!/usr/bin/env python3
"""Механічна перевірка Bash у run: | основного CI, без запуску тестів SENS.

YAML може бути валідним, а вбудований Bash — мати незамкнений if або
heredoc. bash -n перевіряє лише синтаксис; це НЕ оракул семантики Lisp.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github/workflows/ci.yml"
RUN_BLOCK = re.compile(r"^( *)(?:run): *\|[-+]? *$")


def literal_run_blocks(source: str):
    """Розібрати YAML-блоки run: | за відступами без сторонніх залежностей."""
    lines = source.splitlines()
    for index, line in enumerate(lines):
        match = RUN_BLOCK.fullmatch(line)
        if match is None:
            continue
        key_indent = len(match.group(1))
        content: list[str] = []
        for next_line in lines[index + 1 :]:
            indent = len(next_line) - len(next_line.lstrip(" "))
            if next_line.strip() and indent <= key_indent:
                break
            content.append(next_line)
        nonempty = [x for x in content if x.strip()]
        if not nonempty:
            yield index + 1, ""
            continue
        body_indent = min(len(x) - len(x.lstrip(" ")) for x in nonempty)
        body = "\n".join(x[body_indent:] if x.strip() else "" for x in content) + "\n"
        yield index + 1, body


def check(source: str) -> list[str]:
    failures = []
    blocks = list(literal_run_blocks(source))
    if not blocks:
        return ["CI_SHELL_BLOCKED: не знайдено жодного run: |"]
    for line, script in blocks:
        result = subprocess.run(
            ["bash", "-n"], input=script, text=True,
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or "bash -n відхилив блок").strip().splitlines()[0]
            failures.append(
                f"CI_SHELL_BLOCKED file=.github/workflows/ci.yml line={line} "
                f"layer=bash-syntax expected=valid actual={detail}"
            )
    return failures


def self_test() -> None:
    good = "steps:\n  - run: |\n      if true; then\n        echo так\n      fi\n"
    bad = "steps:\n  - run: |\n      if true; then\n        echo ні\n"
    assert not check(good), "самоперевірка: правильний Bash мав пройти"
    assert check(bad), "самоперевірка: незакритий if мав бути BLOCKED"
    blocks = list(literal_run_blocks(good))
    assert len(blocks) == 1 and blocks[0][0] == 2
    print("CI_SHELL_SELF_TEST_PASS valid=1 broken=1")


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        self_test()
        return 0
    if not CI.is_file():
        print("CI_SHELL_BLOCKED: немає ci.yml", file=sys.stderr)
        return 1
    failures = check(CI.read_text(encoding="utf-8"))
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(f"CI_SHELL_PASS: перевірено {len(list(literal_run_blocks(CI.read_text(encoding='utf-8'))))} Bash run-блоків")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
