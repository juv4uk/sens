#!/usr/bin/env python3
"""М1 #5445 — еволюціонований страж межі «T5 за замовчуванням».

Канонічний фізичний носій — T5 (`.sens`). Дослідний кодек `.senc` (F3/F4,
adaptive/framed) існує як спільний модуль `crates/sens/src/codec/`
з ЯВНИМ профілем (F3/F4/adaptive), НЕ як автовизначення за вмістом.

Страж перевіряє:
  1) у канонічних крейтах немає автовизначення/fallback на `.senc`;
  2) CLI за замовчуванням вимагає `.sens`, але приймає явний `--profile`.
  3) спільний кодек `crates/sens/src/codec/` дозволений (explicit API).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ALLOWED_RESEARCH_PREFIX = "research/"
CANONICAL_DIRS = ("crates/sens", "crates/sens-cli")
SCANNED_SUFFIXES = (".rs", ".toml")

# Заборонено: автовизначення/fallback/implicit codec
FORBIDDEN_IMPLICIT = re.compile(
    r"(?:auto[_-]?detect|fallback|implicit)[_-]?(?:senc|framed|tb33|adaptive)",
    re.IGNORECASE,
)

# Дозволено: явні профілі в спільному кодексі
ALLOWED_EXPLICIT = re.compile(
    r"(?:explicit|profile)[_-]?(?:senc|framed|tb33|adaptive)",
    re.IGNORECASE,
)

CLI_SOURCE = "crates/sens-cli/src/bin/sens-trit.rs"
CLI_REQUIRED_MARKERS = (
    "expected a physical .sens file",  # дефолт межа
    'Some("sens")',                    # перевірка розширення
)

MARKER = "T5-DEFAULT-BOUNDARY"

# Файли, де дозволені дослідничні токени (тести межі)
ALLOWLIST = {
    "crates/sens-cli/tests/codec_boundary_t5_default.rs",
    "crates/sens/src/codec/mod.rs",        # спільний кодек (explicit API)
    "crates/sens/src/codec/frame.rs",      # Frame-3
    "crates/sens/src/codec/tb33.rs",       # Tb-33
    "crates/sens/src/codec/adaptive.rs",   # адаптив
    "crates/sens/src/codec/t5.rs",         # T5 референс
}

SELF_TEST_POSITIVE = [
    "auto_detect_senc",
    "fallback_framed3",
    "implicit_tb33",
    "adaptive_encoder_fallback",
]
SELF_TEST_NEGATIVE = [
    "explicit_senc",
    "profile_framed3",
    "frame3_explicit",
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


def tracked_files(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=root, text=True, capture_output=True, check=True,
    )
    files = []
    for rel in out.stdout.splitlines():
        if rel.startswith("research/"):
            continue
        if not any(rel.startswith(f"{d}/") for d in ("crates/sens", "crates/sens-cli")):
            continue
        if not rel.endswith((".rs", ".toml")):
            continue
        files.append(rel)
    return files


def self_test() -> list[str]:
    problems: list[str] = []
    for token in ["auto_detect_senc", "fallback_framed3", "implicit_tb33"]:
        if not FORBIDDEN_IMPLICIT.search(token):
            problems.append(f"детектор не ловить {token!r}")
    for token in ["explicit_senc", "profile_framed3"]:
        if FORBIDDEN_IMPLICIT.search(token):
            problems.append(f"хибне спрацювання на {token!r}")
    return problems


def main() -> int:
    root = repo_root()

    problems = self_test()
    if problems:
        print(f"{'T5-DEFAULT-BOUNDARY'}: SELF-TEST FAIL — {problems}")
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
        # Тільки implicit/fallback заборонено
        for token in FORBIDDEN_IMPLICIT.findall(text):
            violations.append(f"{rel}: implicit research codec usage {token!r}")

    cli = root / "crates/sens-cli/src/bin/sens-trit.rs"
    if not cli.exists():
        violations.append(f"crates/sens-cli/src/bin/sens-trit.rs: missing canonical CLI source")
    else:
        cli_text = cli.read_text(encoding="utf-8")
        for marker in ("expected a physical .sens file", 'Some("sens")'):
            if marker not in cli_text:
                violations.append(f"CLI: missing boundary marker {marker!r}")

    if violations:
        print(f"T5-DEFAULT-BOUNDARY: BLOCKED — порушено межу T5:")
        for line in violations:
            print(f"  - {line}")
        return 1

    print(
        f"T5-DEFAULT-BOUNDARY: PASS — {scanned} файлів перевірено; "
        f"явні профілі дозволені; дефолт .sens на місці"
    )
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        _problems = self_test()
        if _problems:
            print(f"T5-DEFAULT-BOUNDARY: SELF-TEST FAIL — {_problems}")
            sys.exit(1)
        print(f"T5-DEFAULT-BOUNDARY: SELF-TEST PASS")
        sys.exit(0)
    sys.exit(main())
