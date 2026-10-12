#!/usr/bin/env python3
"""Fail-closed guard: release-path toolchain/action pins must stay reproducible.

Locks the RELEASE.md gate #3 invariant. It asserts, for the release-path
workflows only:

* the pinned Rust channel in ``rust-toolchain.toml`` equals the
  ``dtolnay/rust-toolchain`` ref used by every release-path workflow, **and**
  equals any ``with: toolchain:`` value on that step (so a step cannot pin the
  ref and request a different toolchain);
* every other ``uses:`` action in those workflows is pinned to an immutable
  40-hex commit SHA (an optional ``# tag`` comment is allowed), so a floating
  major tag can never silently change what builds a published artifact.

It is a packaging/reproducibility guard only: it grants no semantic admission
and does not run the release. Absence, drift, or an unpinned action fails closed.
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RELEASE_WORKFLOWS = (
    ".github/workflows/release.yml",
    ".github/workflows/release-preflight.yml",
    ".github/workflows/release-smoke-short.yml",
    ".github/workflows/current-binary-preflight.yml",
    ".github/workflows/publish-binary-master.yml",
)

STEP = re.compile(r"^\s*-\s")
USES_LINE = re.compile(r"^\s*-?\s*uses:\s*(\S+)\s*$")
TOOLCHAIN_LINE = re.compile(r"^\s*toolchain:\s*[\"']?([^\"'\s]+)[\"']?\s*$")
SHA = re.compile(r"[0-9a-f]{40}\Z")
LOCAL = re.compile(r"\./\S+\Z")
TOOLCHAIN_ACTION = "dtolnay/rust-toolchain"


def pinned_channel(root: Path = ROOT) -> str:
    path = root / "rust-toolchain.toml"
    if not path.is_file():
        raise ValueError("rust-toolchain.toml is missing")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    channel = data.get("toolchain", {}).get("channel")
    if not isinstance(channel, str) or not channel.strip():
        raise ValueError("rust-toolchain.toml has no pinned [toolchain].channel")
    return channel.strip()


def _steps(text: str) -> list[tuple[int, list[str]]]:
    """Split a workflow into step blocks by ``- `` list items, with line numbers."""
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] | None = None
    start = 0
    for lineno, line in enumerate(text.splitlines(), 1):
        if STEP.match(line):
            if current is not None:
                blocks.append((start, current))
            current = [line]
            start = lineno
        elif current is not None:
            current.append(line)
    if current is not None:
        blocks.append((start, current))
    return blocks


def check(root: Path = ROOT) -> tuple[str, list[str]]:
    channel = pinned_channel(root)
    errors: list[str] = []
    for rel in RELEASE_WORKFLOWS:
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}: release-path workflow is missing")
            continue
        for start, block in _steps(path.read_text(encoding="utf-8")):
            uses = None
            toolchains: list[str] = []
            for line in block:
                match = USES_LINE.match(line)
                if match:
                    uses = match.group(1)
                tool = TOOLCHAIN_LINE.match(line)
                if tool:
                    toolchains.append(tool.group(1))
            if uses is None or LOCAL.fullmatch(uses):
                continue
            if "@" not in uses:
                errors.append(f"{rel}:{start}: uses without a ref: {uses}")
                continue
            action, _, pin = uses.rpartition("@")
            if action == TOOLCHAIN_ACTION:
                if pin != channel:
                    errors.append(f"{rel}:{start}: toolchain ref {pin} != pinned channel {channel}")
                for requested in toolchains:
                    if requested != channel:
                        errors.append(
                            f"{rel}:{start}: with: toolchain {requested} != pinned channel {channel}"
                        )
            elif not SHA.fullmatch(pin):
                errors.append(f"{rel}:{start}: {action} not pinned to a 40-hex SHA (got {pin!r})")
    return channel, errors


def main(argv: list[str]) -> int:
    try:
        channel, errors = check()
    except (ValueError, OSError, tomllib.TOMLDecodeError) as exc:
        print(f"RELEASE_PINS_BLOCKED: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"RELEASE_PINS_BLOCKED: {error}", file=sys.stderr)
        return 1
    print(f"RELEASE_PINS_PASS channel={channel} workflows={len(RELEASE_WORKFLOWS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
