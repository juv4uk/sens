#!/usr/bin/env python3
"""Fail-closed: release packaging surfaces must share one version (gate #1).

Mechanical only. Does not admit programs, does not invent GO, does not
touch knowledge/release-admission-ledger.json.

Checks that:
  * every release crate Cargo.toml package.version equals EXPECTED
  * Cargo.lock has exactly one local package for each release crate at EXPECTED
  * guix.scm (version "…") equals EXPECTED
  * packaging/install.sh embeds EXPECTED and tag s{EXPECTED}
  * scripts/release.lisp mentions EXPECTED as the required release version

Drift fails closed. Absence of a required path fails closed.
"""
from __future__ import annotations

import argparse
import copy
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "0.42.1"
TAG = f"s{EXPECTED}"

RELEASE_CRATES = (
    "sens",
    "sens-cli",
    "sens-host",
    "sens-literate",
    "sens-lsp",
    "sens-semantic",
    "sens-wasm",
)


class AlignmentBlocked(ValueError):
    """Version surfaces disagree or a required path is missing."""


def crate_version(name: str) -> str:
    path = ROOT / "crates" / name / "Cargo.toml"
    if not path.is_file() or path.is_symlink():
        raise AlignmentBlocked(f"missing regular crate manifest: {path}")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    version = data.get("package", {}).get("version")
    if not isinstance(version, str) or not version:
        raise AlignmentBlocked(f"{path}: package.version missing")
    return version



def read_lock_packages() -> list[dict]:
    """Read the ONE workspace lockfile; it is evidence, not a version authority."""
    path = ROOT / "Cargo.lock"
    if not path.is_file() or path.is_symlink():
        raise AlignmentBlocked(f"missing regular workspace lockfile: {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise AlignmentBlocked(f"Cargo.lock: unreadable TOML ({exc})") from exc
    rows = data.get("package")
    if not isinstance(rows, list):
        raise AlignmentBlocked("Cargo.lock: [[package]] table missing")
    return rows


def validate_lock_packages(rows: list[dict]) -> dict[str, str]:
    """Require each release crate exactly once as a local package at EXPECTED."""
    seen: dict[str, str] = {}
    for item in rows:
        if not isinstance(item, dict):
            raise AlignmentBlocked("Cargo.lock: malformed package entry")
        name = item.get("name")
        if name not in RELEASE_CRATES:
            continue
        if name in seen:
            raise AlignmentBlocked(f"Cargo.lock: duplicate release package {name}")
        version = item.get("version")
        if not isinstance(version, str) or version != EXPECTED:
            raise AlignmentBlocked(
                f"Cargo.lock: {name} version {version!r} != {EXPECTED!r}"
            )
        if "source" in item:
            raise AlignmentBlocked(
                f"Cargo.lock: release package {name} must be local, not registry/git"
            )
        seen[name] = version
    missing = set(RELEASE_CRATES) - set(seen)
    if missing:
        raise AlignmentBlocked(
            f"Cargo.lock: missing local release packages {sorted(missing)}"
        )
    return seen


def lock_negative_self_tests(rows: list[dict]) -> None:
    """Mutate parsed data only. Never modify a real lockfile on disk."""
    first = next(i for i, p in enumerate(rows)
                 if isinstance(p, dict) and p.get("name") == RELEASE_CRATES[0])
    stale = copy.deepcopy(rows)
    stale[first]["version"] = "0.41.0"
    absent = [copy.deepcopy(p) for p in rows
              if not (isinstance(p, dict) and p.get("name") == RELEASE_CRATES[0])]
    duplicate = copy.deepcopy(rows)
    duplicate.append(copy.deepcopy(rows[first]))
    external = copy.deepcopy(rows)
    external[first]["source"] = "registry+https://github.com/rust-lang/crates.io-index"
    for label, mutant in (
        ("stale-version", stale),
        ("missing-release-crate", absent),
        ("duplicate-release-crate", duplicate),
        ("registry-impostor", external),
    ):
        try:
            validate_lock_packages(mutant)
        except AlignmentBlocked:
            continue
        raise AssertionError(f"RELEASE_BLOCKED: lockfile mutant escaped: {label}")

def guix_version() -> str:
    path = ROOT / "guix.scm"
    text = path.read_text(encoding="utf-8")
    match = re.search(r'\(version\s+"([0-9]+\.[0-9]+\.[0-9]+)"\)', text)
    if not match:
        raise AlignmentBlocked("guix.scm: (version \"…\") not found")
    return match.group(1)


def install_surfaces() -> list[str]:
    path = ROOT / "packaging" / "install.sh"
    text = path.read_text(encoding="utf-8")
    found: list[str] = []
    for pattern, label in (
        (rf'sens-cli_{re.escape(EXPECTED)}_', "asset name embeds version"),
        (rf"/releases/download/{re.escape(TAG)}/", "download URL embeds tag"),
    ):
        if not re.search(pattern, text):
            raise AlignmentBlocked(f"packaging/install.sh: missing {label}")
        found.append(label)
    for bad in re.findall(r"/releases/download/(s[0-9]+\.[0-9]+\.[0-9]+)/", text):
        if bad != TAG:
            raise AlignmentBlocked(f"packaging/install.sh: unexpected tag {bad}")
    return found


def release_lisp_requires() -> None:
    path = ROOT / "scripts" / "release.lisp"
    text = path.read_text(encoding="utf-8")
    if EXPECTED not in text:
        raise AlignmentBlocked("scripts/release.lisp: expected version string missing")
    if "Потрібна одна версія:" in text and EXPECTED not in text.split("Потрібна одна версія:")[1][:40]:
        raise AlignmentBlocked("scripts/release.lisp: required-version line drifted")


def audit() -> dict:
    versions = {name: crate_version(name) for name in RELEASE_CRATES}
    bad = {name: ver for name, ver in versions.items() if ver != EXPECTED}
    if bad:
        raise AlignmentBlocked(f"crate version drift (want {EXPECTED}): {bad}")
    locked = validate_lock_packages(read_lock_packages())
    if locked != versions:
        raise AlignmentBlocked("Cargo.lock: release crate versions differ from Cargo.toml")
    gv = guix_version()
    if gv != EXPECTED:
        raise AlignmentBlocked(f"guix.scm version {gv!r} != {EXPECTED!r}")
    install_surfaces()
    release_lisp_requires()
    return {
        "schema": "sens-release-version-alignment/v1",
        "kind": "mechanical-gate-not-go",
        "expected": EXPECTED,
        "tag": TAG,
        "crates": versions,
        "cargo_lock": locked,
        "guix": gv,
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        report = audit()
        assert report["status"] == "PASS"
        assert report["expected"] == EXPECTED
        assert report["cargo_lock"] == report["crates"]
        lock_negative_self_tests(read_lock_packages())
        print("RELEASE_VERSION_ALIGNMENT_SELF_TEST_PASS lock_mutants=4")
        return 0
    try:
        report = audit()
    except AlignmentBlocked as err:
        print(f"RELEASE_VERSION_ALIGNMENT_BLOCKED: {err}", file=sys.stderr)
        return 1
    print(
        f"RELEASE_VERSION_ALIGNMENT_PASS expected={EXPECTED} "
        f"crates={len(report['crates'])} locked={len(report['cargo_lock'])} guix={report['guix']} tag={TAG}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
