#!/usr/bin/env python3
"""Fail-closed: release packaging surfaces must share one version (gate #1).

Mechanical only. Does not admit programs, does not invent GO, does not
touch knowledge/release-admission-ledger.json.

Checks that:
  * every release crate Cargo.toml package.version equals EXPECTED
  * guix.scm (version "…") equals EXPECTED
  * packaging/install.sh embeds EXPECTED and tag l{EXPECTED}
  * scripts/release.lisp mentions EXPECTED as the required release version

Drift fails closed. Absence of a required path fails closed.
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "0.42.0"
TAG = f"l{EXPECTED}"

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
    for bad in re.findall(r"/releases/download/(l[0-9]+\.[0-9]+\.[0-9]+)/", text):
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
        print("RELEASE_VERSION_ALIGNMENT_SELF_TEST_PASS")
        return 0
    try:
        report = audit()
    except AlignmentBlocked as err:
        print(f"RELEASE_VERSION_ALIGNMENT_BLOCKED: {err}", file=sys.stderr)
        return 1
    print(
        f"RELEASE_VERSION_ALIGNMENT_PASS expected={EXPECTED} "
        f"crates={len(report['crates'])} guix={report['guix']} tag={TAG}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
