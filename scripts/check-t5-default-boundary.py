#!/usr/bin/env python3
"""М1 #5445 — статичний fail-closed страж межі «T5 за замовчуванням».

Канонічний фізичний носій — T5 (`.sens`). Дослідний кодек `.senc` (F3/F4,
adaptive/framed) існує лише як окремий явний режим у `research/` і НЕ має
протікати в канонічні крейти `crates/sens` та `crates/sens-cli`.

Страж перевіряє ДВІ речі:
  1) у канонічних крейтах немає жодної згадки дослідного кодека (межа
     тримається за відсутністю — регресійний бар'єр);
  2) межа, що вже фізично є в CLI (перевірка розширення `.sens`), на місці.

Це НЕ зміна canonical loader і НЕ новий кодек — це заморожування наявного
інваріанта. Self-test доводить, що детектор справді ловить заборонені токени.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ALLOWED_RESEARCH_PREFIX = "research/"
CANONICAL_DIRS = ("crates/sens", "crates/sens-cli")
SCANNED_SUFFIXES = (".rs", ".toml")

FORBIDDEN = re.compile(
    r"\.senc\b|framed[-_]?3|framed[-_]?4|tb-?33|adaptive[_-]?encoder",
    re.IGNORECASE,
)

CLI_SOURCE = "crates/sens-cli/src/bin/sens-trit.rs"
CLI_REQUIRED_MARKERS = (
    "expected a physical .sens file",  # read_sens: межa розширення
    'Some("sens")',                    # фактична перевірка розширення
)

MARKER = "T5-DEFAULT-BOUNDARY"

# Цей негативний свідок НАВМИСНЕ називає `.senc`, щоб довести відмову.
ALLOWLIST = {"crates/sens-cli/tests/codec_boundary_t5_default.rs"}

SELF_TEST_POSITIVE = [
    "x.senc",
    "a.senc",
    "framed3",
    "framed_3",
    "framed-4",
    "tb33",
    "tb-33",
    "adaptive_encoder",
    "adaptive-encoder",
]
SELF_TEST_NEGATIVE = [
    "AESENC",
    "presence",
    "frame3",
    "tb3",
    "t33",
    "encoder",
]


def repo_root() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, capture_output=True, check=True,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def detect(text: str) -> list[str]:
    return [m.group(0) for m in FORBIDDEN.finditer(text)]


def tracked_files(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=root, text=True, capture_output=True, check=True,
    )
    files = []
    for rel in out.stdout.splitlines():
        if rel.startswith(ALLOWED_RESEARCH_PREFIX):
            continue
        if not any(rel.startswith(f"{d}/") for d in CANONICAL_DIRS):
            continue
        if not rel.endswith(SCANNED_SUFFIXES):
            continue
        files.append(rel)
    return files


def self_test() -> list[str]:
    problems: list[str] = []
    for token in SELF_TEST_POSITIVE:
        if not FORBIDDEN.search(token):
            problems.append(f"детектор не ловить {token!r}")
    for token in SELF_TEST_NEGATIVE:
        if FORBIDDEN.search(token):
            problems.append(f"хибне спрацювання на {token!r}")
    return problems


def main() -> int:
    root = repo_root()

    problems = self_test()
    if problems:
        print(f"{MARKER}: SELF-TEST FAIL — {problems}")
        return 1

    violations: list[str] = []
    scanned = 0
    for rel in tracked_files(root):
        if rel in ALLOWLIST:
            continue
        path = root / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        for token in sorted(set(FORBIDDEN.findall(text))):
            violations.append(f"{rel}: forbidden research-codec token {token!r}")

    cli = root / CLI_SOURCE
    if not cli.exists():
        violations.append(f"{CLI_SOURCE}: missing canonical CLI source")
    else:
        cli_text = cli.read_text(encoding="utf-8")
        for marker in CLI_REQUIRED_MARKERS:
            if marker not in cli_text:
                violations.append(f"{CLI_SOURCE}: missing boundary marker {marker!r}")

    if violations:
        print(f"{MARKER}: BLOCKED — канонічна межа T5 порушена:")
        for line in violations:
            print(f"  - {line}")
        return 1

    print(
        f"{MARKER}: PASS — {scanned} канонічних файлів без дослідного кодека; "
        f"межа розширення .sens на місці"
    )
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        _problems = self_test()
        if _problems:
            print(f"{MARKER}: SELF-TEST FAIL — {_problems}")
            sys.exit(1)
        print(f"{MARKER}: SELF-TEST PASS")
        sys.exit(0)
    sys.exit(main())
