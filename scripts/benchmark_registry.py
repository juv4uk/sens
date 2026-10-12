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
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = ROOT / "benchmarks"
OUTPUT = BENCHMARKS / "README.md"
MANIFEST_NAME = "bench.json"
SCHEMA_ID = "sens-benchmark-manifest/v1"
EXEMPTION_FILE = BENCHMARKS / "support-exemptions.json"
EXEMPTION_SCHEMA_ID = "sens-benchmark-support-exemptions/1"
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




EXEMPTION_FIELDS = {"path", "reason", "witness", "owner_or_issue", "reviewed_at"}


def validate_support_exemptions(
    path: Path | None = None,
    benchmarks_root: Path | None = None,
    repository_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Load explicit non-stand directory exemptions; never infer exemptions."""
    registry_path = path if path is not None else EXEMPTION_FILE
    benches = benchmarks_root if benchmarks_root is not None else BENCHMARKS
    root = repository_root if repository_root is not None else ROOT
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RegistryError(f"{registry_path}: cannot read support-exemption registry: {error}") from error

    if not isinstance(data, dict) or set(data) != {"schema", "exemptions"}:
        raise RegistryError(f"{registry_path}: expected exactly schema and exemptions")
    if data.get("schema") != EXEMPTION_SCHEMA_ID:
        raise RegistryError(
            f"{registry_path}: schema must be {EXEMPTION_SCHEMA_ID!r}, got {data.get('schema')!r}"
        )
    entries = data.get("exemptions")
    if not isinstance(entries, list):
        raise RegistryError(f"{registry_path}: exemptions must be a list")

    seen: set[str] = set()
    validated: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        label = f"{registry_path}: exemptions[{index}]"
        if not isinstance(entry, dict) or set(entry) != EXEMPTION_FIELDS:
            raise RegistryError(
                f"{label}: expected fields {', '.join(sorted(EXEMPTION_FIELDS))}"
            )

        directory = _nonempty_string(entry["path"], "path", registry_path)
        if directory in {".", ".."} or "/" in directory or "\\" in directory:
            raise RegistryError(f"{label}: path must be one top-level directory name")
        if directory in seen:
            raise RegistryError(f"{registry_path}: duplicate support exemption path {directory!r}")
        seen.add(directory)

        reason = _nonempty_string(entry["reason"], "reason", registry_path)
        owner_or_issue = _nonempty_string(entry["owner_or_issue"], "owner_or_issue", registry_path)
        reviewed_at = _nonempty_string(entry["reviewed_at"], "reviewed_at", registry_path)
        try:
            date.fromisoformat(reviewed_at)
        except ValueError as error:
            raise RegistryError(f"{label}: reviewed_at must be an ISO date YYYY-MM-DD") from error

        directory_path = benches / directory
        if not directory_path.is_dir() or directory_path.resolve().parent != benches.resolve():
            raise RegistryError(f"{label}: exempted directory does not exist at top level: {directory}")
        if (directory_path / MANIFEST_NAME).is_file():
            raise RegistryError(f"{label}: {directory} has {MANIFEST_NAME}; it cannot also be exempted")

        witnesses = entry["witness"]
        if (
            not isinstance(witnesses, list)
            or not witnesses
            or any(not isinstance(item, str) or not item.strip() for item in witnesses)
            or len(set(witnesses)) != len(witnesses)
        ):
            raise RegistryError(f"{label}: witness must be a non-empty list of unique repository paths")
        for witness in witnesses:
            witness_path = Path(witness)
            prefix = Path("benchmarks") / directory
            if witness_path.is_absolute() or ".." in witness_path.parts or witness_path.parts[:2] != prefix.parts:
                raise RegistryError(f"{label}: witness must stay inside benchmarks/{directory}/: {witness}")
            if not (root / witness_path).is_file():
                raise RegistryError(f"{label}: witness file does not exist: {witness}")

        validated.append(
            {
                "path": directory,
                "reason": reason,
                "witness": witnesses,
                "owner_or_issue": owner_or_issue,
                "reviewed_at": reviewed_at,
            }
        )

    return sorted(validated, key=lambda item: item["path"])


def load_support_exemptions() -> list[dict[str, Any]]:
    return validate_support_exemptions()


def report_coverage(manifests: list[dict[str, Any]], exemptions: list[dict[str, Any]]) -> None:
    registered = {item["stand"] for item in manifests}
    exempted = {item["path"] for item in exemptions}
    directories = {
        path.name
        for path in BENCHMARKS.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }
    unclassified = sorted(directories - registered - exempted)
    print(
        "benchmark directory coverage: "
        f"{len(registered)} registered stands; "
        f"{len(exempted)} explicit support exemptions; "
        f"{len(unclassified)} unclassified directories; "
        f"{len(directories)} top-level directories total"
    )
    if unclassified:
        print("unclassified directories: " + ", ".join(unclassified))


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


def render(manifests: list[dict[str, Any]], exemptions: list[dict[str, Any]] | None = None) -> str:
    exemptions = exemptions or []
    lines = [
        "# Benchmark laboratory index",
        "",
        "> **GENERATED FILE — DO NOT EDIT BY HAND.**",
        "> Sources: `benchmarks/*/bench.json` and `benchmarks/support-exemptions.json`.",
        "> Generator: `scripts/benchmark_registry.py`.",
        "> This is discovery metadata only: presence in this table does not grant semantic authority or increase evidence strength.",
        "",
        "Bootstrap rule: existing unregistered stands remain explicit backfill debt tracked by #4172. Any newly created benchmark stand must carry `bench.json`; #4171 guards that ratchet.",
        "",
        f"**Registered stands:** {len(manifests)}",
        f"**Explicit support-directory exemptions:** {len(exemptions)} (not benchmark stands)",
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
            "## Explicit support-directory exemptions (not benchmark stands)",
            "",
            "These directories support corpora, evidence ledgers, blocked-admission records, or consumer documentation. They are not counted as benchmark stands and must not imply a measurement or conformance result.",
            "",
            "| Directory | Reason | Witness | Owner / issue | Reviewed |",
            "|---|---|---|---|---|",
        ]
    )
    for entry in exemptions:
        witness = "<br>".join(f"`{_cell(item)}`" for item in entry["witness"])
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_cell(entry['path'])}`",
                    _cell(entry["reason"]),
                    witness,
                    _cell(entry["owner_or_issue"]),
                    _cell(entry["reviewed_at"]),
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
            "The `--strict` gate rejects every top-level benchmark directory lacking either a valid bench.json manifest or an explicit, source-backed support exemption. The remaining unclassified directories are reported by `--coverage` and stay tracked as backfill debt under #4172.",
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


def check_new_stands(base: str, head: str, exempted_paths: set[str] | None = None) -> None:
    exempted_paths = exempted_paths or set()
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
        if not (BENCHMARKS / stand / MANIFEST_NAME).is_file() and stand not in exempted_paths
    ]
    if missing:
        raise RegistryError(
            "new benchmark stand(s) lack bench.json: " + ", ".join(missing)
        )


def check_strict(exempted_paths: set[str] | None = None) -> None:
    exempted_paths = exempted_paths or set()
    missing = [
        path.name
        for path in sorted(BENCHMARKS.iterdir())
        if path.is_dir()
        and not path.name.startswith(".")
        and not (path / MANIFEST_NAME).is_file()
        and path.name not in exempted_paths
    ]
    if missing:
        raise RegistryError(
            "unclassified benchmark directory(ies): " + ", ".join(missing)
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
        help="fail if any top-level benchmark directory lacks bench.json or explicit support exemption",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="report registered, exempted, and still-unclassified top-level directories without changing files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifests = load_manifests()
        exemptions = load_support_exemptions()
        exempted_paths = {item["path"] for item in exemptions}
        if args.check_new:
            check_new_stands(*args.check_new, exempted_paths=exempted_paths)
        if args.strict:
            check_strict(exempted_paths=exempted_paths)
        if args.coverage:
            report_coverage(manifests, exemptions)

        generated = render(manifests, exemptions)
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

        if args.coverage:
            return 0

        OUTPUT.write_text(generated, encoding="utf-8")
        print(f"wrote {OUTPUT}")
        return 0
    except RegistryError as error:
        print(f"benchmark registry failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
