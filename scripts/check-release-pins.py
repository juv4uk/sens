#!/usr/bin/env python3
"""Fail-closed guard: release-path toolchain/action pins must stay reproducible.

Locks the RELEASE.md gate #3 invariant. It asserts, for the release-path
workflows only:

* the pinned Rust channel in ``rust-toolchain.toml`` equals the
  ``dtolnay/rust-toolchain`` ref used by every release-path workflow;
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

# A `uses:` step line, optionally a list item, optionally annotated `# tag`.
USES = re.compile(r"^\s*-?\s*uses:\s*(\S+)(?:\s+#\s*\S+)?\s*$")
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


def check(root: Path = ROOT) -> tuple[str, list[str]]:
    channel = pinned_channel(root)
    errors: list[str] = []
    for rel in RELEASE_WORKFLOWS:
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}: release-path workflow is missing")
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = USES.match(line)
            if match is None:
                continue
            ref = match.group(1)
            if LOCAL.fullmatch(ref):
                continue
            if "@" not in ref:
                errors.append(f"{rel}:{lineno}: uses without a ref: {ref}")
                continue
            action, _, pin = ref.rpartition("@")
            if action == TOOLCHAIN_ACTION:
                if pin != channel:
                    errors.append(
                        f"{rel}:{lineno}: toolchain {pin} != pinned channel {channel}"
                    )
            elif not SHA.fullmatch(pin):
                errors.append(
                    f"{rel}:{lineno}: {action} not pinned to a 40-hex SHA (got {pin!r})"
                )
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
