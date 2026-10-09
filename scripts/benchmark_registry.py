#!/usr/bin/env python3
"""Generate and validate the benchmark laboratory discovery index.

The benchmark manifests are discovery metadata only. They do not grant semantic
authority and must not raise the evidence strength already earned by a stand.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = ROOT / "benchmarks"
OUTPUT = BENCHMARKS / "README.md"
MANIFEST_NAME = "bench.json"
SCHEMA_ID = "sens-benchmark-manifest/v1"
ROLES = {"MEASUREMENT", "CONFORMANCE", "FALSIFIER", "RESEARCH"}
REQUIRED = {
    "schema",
    "stand",
    "wing",
    "roles",
    "question",
    "claim",
    "witness",
    "status",
    "generation",
    "axis",
    "reproduce",
}


class RegistryError(ValueError):
    pass


def _nonempty_string(value: Any, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistryError(f"{path}: {field} must be a non-empty string")
    return value.strip()


def validate_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RegistryError(f"{path}: cannot read manifest: {error}") from error

    if not isinstance(data, dict):
        raise RegistryError(f"{path}: manifest must be a JSON object")

    missing = sorted(REQUIRED - data.keys())
    unknown = sorted(data.keys() - REQUIRED)
    if missing:
        raise RegistryError(f"{path}: missing fields: {', '.join(missing)}")
    if unknown:
        raise RegistryError(f"{path}: unknown fields: {', '.join(unknown)}")

    if data["schema"] != SCHEMA_ID:
        raise RegistryError(
            f"{path}: schema must be {SCHEMA_ID!r}, got {data['schema']!r}"
        )

    stand = _nonempty_string(data["stand"], "stand", path)
    if stand != path.parent.name:
        raise RegistryError(
            f"{path}: stand {stand!r} must match directory {path.parent.name!r}"
        )

    for field in (
        "wing",
        "question",
        "claim",
        "status",
        "generation",
        "axis",
        "reproduce",
    ):
        data[field] = _nonempty_string(data[field], field, path)

    roles = data["roles"]
    if (
        not isinstance(roles, list)
        or not roles
        or any(not isinstance(role, str) or role not in ROLES for role in roles)
        or len(set(roles)) != len(roles)
    ):
        raise RegistryError(
            f"{path}: roles must be a non-empty unique list from {sorted(ROLES)}"
        )

    witness = data["witness"]
    if (
        not isinstance(witness, list)
        or not witness
        or any(not isinstance(item, str) or not item.strip() for item in witness)
    ):
        raise RegistryError(f"{path}: witness must be a non-empty string list")

    return data


def load_manifests() -> list[dict[str, Any]]:
    manifests = [
        validate_manifest(path)
        for path in sorted(BENCHMARKS.glob(f"*/{MANIFEST_NAME}"))
    ]
    seen: set[str] = set()
    for data in manifests:
        stand = data["stand"]
        if stand in seen:
            raise RegistryError(f"duplicate benchmark stand: {stand}")
        seen.add(stand)
    return manifests


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def render(manifests: list[dict[str, Any]]) -> str:
    lines = [
        "# Benchmark laboratory index",
        "",
        "> **GENERATED FILE — DO NOT EDIT BY HAND.**",
        "> Sources: `benchmarks/*/bench.json`.",
        "> Generator: `scripts/benchmark_registry.py`.",
        "> This is discovery metadata only: presence in this table does not grant semantic authority or increase evidence strength.",
        "",
        "Bootstrap rule: existing unregistered stands remain explicit backfill debt tracked by #4172. Any newly created benchmark stand must carry `bench.json`; #4171 guards that ratchet.",
        "",
        f"**Registered stands:** {len(manifests)}",
        "",
        "| Stand | Wing | Role | Question | Claim boundary | Witness | Status | Generation | Axis | Reproduce |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for data in manifests:
        witness = "<br>".join(f"`{_cell(item)}`" for item in data["witness"])
        roles = "<br>".join(f"`{_cell(role)}`" for role in data["roles"])
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_cell(data['stand'])}`",
                    _cell(data["wing"]),
                    roles,
                    _cell(data["question"]),
                    _cell(data["claim"]),
                    witness,
                    _cell(data["status"]),
                    _cell(data["generation"]),
                    f"`{_cell(data['axis'])}`",
                    f"`{_cell(data['reproduce'])}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Rules",
            "",
            "The registry answers *where to look* and *what strength a stand may claim*. Semantic authority remains where the language contract says it lives. A benchmark result is evidence, not a ratification mechanism.",
            "",
            "Regenerate or verify from the repository root:",
            "",
            "```bash",
            "python3 scripts/benchmark_registry.py",
            "python3 scripts/benchmark_registry.py --check",
            "```",
            "",
            "After #4172 backfills the historical laboratory, CI can switch to `--strict`, which rejects every top-level benchmark directory without a manifest rather than only rejecting newly introduced ones.",
            "",
        ]
    )
    return "\n".join(lines)


def _base_has_stand(base: str, stand: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{base}:benchmarks/{stand}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def check_new_stands(base: str, head: str) -> None:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--name-status",
            "--diff-filter=AR",
            base,
            head,
            "--",
            "benchmarks",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RegistryError(result.stderr.strip() or "git diff failed")

    new_stands: set[str] = set()
    for raw in result.stdout.splitlines():
        parts = raw.split("\t")
        if len(parts) < 2:
            continue
        path = parts[-1]
        chunks = Path(path).parts
        if len(chunks) < 3 or chunks[0] != "benchmarks":
            continue
        stand = chunks[1]
        stand_path = BENCHMARKS / stand
        if not stand_path.is_dir():
            continue
        if not _base_has_stand(base, stand):
            new_stands.add(stand)

    missing = [
        stand
        for stand in sorted(new_stands)
        if not (BENCHMARKS / stand / MANIFEST_NAME).is_file()
    ]
    if missing:
        raise RegistryError(
            "new benchmark stand(s) lack bench.json: " + ", ".join(missing)
        )


def check_strict() -> None:
    missing = [
        path.name
        for path in sorted(BENCHMARKS.iterdir())
        if path.is_dir() and not path.name.startswith(".") and not (path / MANIFEST_NAME).is_file()
    ]
    if missing:
        raise RegistryError(
            "unclassified benchmark stand(s): " + ", ".join(missing)
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if benchmarks/README.md is stale",
    )
    parser.add_argument(
        "--check-new",
        nargs=2,
        metavar=("BASE", "HEAD"),
        help="fail if a benchmark stand created between BASE and HEAD lacks bench.json",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail if any top-level benchmark directory lacks bench.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifests = load_manifests()
        if args.check_new:
            check_new_stands(*args.check_new)
        if args.strict:
            check_strict()

        generated = render(manifests)
        if args.check:
            try:
                current = OUTPUT.read_text(encoding="utf-8")
            except OSError as error:
                raise RegistryError(f"{OUTPUT}: cannot read generated index: {error}") from error
            if current != generated:
                print(
                    f"{OUTPUT} is stale; run python3 scripts/benchmark_registry.py",
                    file=sys.stderr,
                )
                return 1
            print(f"benchmark registry projection is current: {OUTPUT}")
            return 0

        OUTPUT.write_text(generated, encoding="utf-8")
        print(f"wrote {OUTPUT}")
        return 0
    except RegistryError as error:
        print(f"benchmark registry failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
