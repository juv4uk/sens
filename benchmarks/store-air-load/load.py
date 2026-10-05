#!/usr/bin/env python3
"""Заповнення LOAD-полів STORE -> AIR -> LOAD через Cachegrind.

Скрипт не створює нового loader-а. Він повторно використовує:
- current_en_vs_d1d8_cpu для paired text/canonical phases;
- startup_bench для чинного Core bootstrap breakdown.

LOAD-поля є phase-derived evidence:
- decode_i_refs / parse_i_refs = ingest - baseline;
- lower_i_refs = lower - ingest;
- ready_i_refs = ready - baseline;
- cold_total_i_refs = full - baseline;
- warm_incremental_i_refs = slope repeated(N=1,10,100).

Whole-process totals не видаються за parser/decode cost.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
from pathlib import Path

REPEAT_LADDER = (1, 10, 100)
CORE_MODES = ("session", "bytes", "decode", "parse", "macro", "core")
CANDIDATES = {
    "canonical-packed": "canonical-d1d8",
    "text-surface": "english-surface",
}
SOURCE_KEYS = {
    "canonical-packed": "canonical_source",
    "text-surface": "english_source",
}
IREF_RE = re.compile(r"I\s+refs:\s*([\d,]+)")


def cachegrind_i_refs(command: list[str]) -> int:
    proc = subprocess.run(
        [
            "valgrind",
            "--tool=cachegrind",
            "--cache-sim=no",
            "--cachegrind-out-file=/dev/null",
            *command,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"cachegrind failed ({proc.returncode}): {' '.join(command)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    match = IREF_RE.search(proc.stderr)
    if match is None:
        raise RuntimeError(f"Cachegrind did not report I refs:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def median_i_refs(command: list[str], reps: int) -> int:
    values = [cachegrind_i_refs(command) for _ in range(reps)]
    return int(statistics.median(values))


def slope(xs: tuple[int, ...], ys: list[int]) -> float:
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom == 0:
        raise ValueError("repeat ladder must contain distinct values")
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom


def read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        row = json.loads(raw)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: row must be an object")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path}: empty JSONL")
    return rows


def load_fixtures(path: Path) -> dict[str, dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError("fixtures must be a list")
    result: dict[str, dict[str, object]] = {}
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            raise ValueError("fixture must be an object")
        fixture_id = fixture.get("id")
        if not isinstance(fixture_id, str) or not fixture_id:
            raise ValueError("fixture id is required")
        result[fixture_id] = fixture
    return result


def write_source(tmp: Path, fixture_id: str, representation: str, source: str) -> Path:
    suffix = "canonical" if representation == "canonical-packed" else "english"
    path = tmp / f"{fixture_id}.{suffix}.lisp"
    path.write_text(source, encoding="utf-8")
    return path


def measure_candidate(
    helper: Path,
    candidate: str,
    source_path: Path,
    reps: int,
) -> dict[str, object]:
    def mode(phase: str, repeat: int | None = None) -> int:
        command = [str(helper), candidate, phase, str(source_path)]
        if repeat is not None:
            command.append(str(repeat))
        return median_i_refs(command, reps)

    raw = {
        phase: mode(phase)
        for phase in ("baseline", "ingest", "lower", "ready", "full")
    }
    repeated = {repeat: mode("repeated", repeat) for repeat in REPEAT_LADDER}

    ingest_delta = raw["ingest"] - raw["baseline"]
    lower_delta = raw["lower"] - raw["ingest"]
    ready_delta = raw["ready"] - raw["baseline"]
    full_delta = raw["full"] - raw["baseline"]
    warm_slope = slope(REPEAT_LADDER, [repeated[n] for n in REPEAT_LADDER])

    for name, value in (
        ("ingest-baseline", ingest_delta),
        ("lower-ingest", lower_delta),
        ("ready-baseline", ready_delta),
        ("full-baseline", full_delta),
    ):
        if value < 0:
            raise ValueError(f"negative phase delta {name}: {value}")
    if warm_slope < 0:
        raise ValueError(f"negative repeated-call slope: {warm_slope}")

    return {
        "raw_i_refs": raw,
        "repeated_i_refs": {str(k): v for k, v in repeated.items()},
        "ingest_delta_i_refs": ingest_delta,
        "lower_delta_i_refs": lower_delta,
        "ready_delta_i_refs": ready_delta,
        "cold_total_delta_i_refs": full_delta,
        "warm_incremental_i_refs": int(round(warm_slope)),
    }


def measure_core_bootstrap(
    helper: Path,
    fasl: Path,
    reps: int,
) -> dict[str, object]:
    raw: dict[str, int] = {}
    for mode in CORE_MODES:
        command = [str(helper), mode]
        if mode in {"bytes", "decode"}:
            command.append(str(fasl))
        raw[mode] = median_i_refs(command, reps)

    base = raw["session"]
    return {
        "raw_i_refs": raw,
        "delta_vs_session_i_refs": {
            mode: raw[mode] - base for mode in CORE_MODES if mode != "session"
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="input_jsonl", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path(__file__).with_name("fixtures.json"),
    )
    parser.add_argument("--helper", type=Path, required=True)
    parser.add_argument("--startup-helper", type=Path, required=True)
    parser.add_argument("--fasl", type=Path, default=Path("lib/core.lisp.fasl"))
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument(
        "--only",
        default="",
        help="comma-separated paired fixture ids; empty means all paired fixtures",
    )
    args = parser.parse_args()

    if args.reps < 1:
        raise ValueError("--reps must be >= 1")

    helper = args.helper.resolve()
    startup_helper = args.startup_helper.resolve()
    fasl = args.fasl.resolve()
    fixtures_path = args.fixtures.resolve()
    for path in (helper, startup_helper, fasl, fixtures_path):
        if not path.exists():
            raise FileNotFoundError(path)

    rows = read_jsonl(args.input_jsonl.resolve())
    fixtures = load_fixtures(fixtures_path)
    selected = {value for value in args.only.split(",") if value}
    paired_ids = {
        fixture_id
        for fixture_id, fixture in fixtures.items()
        if fixture.get("kind") == "paired-program"
    }
    if selected:
        unknown = sorted(selected - paired_ids)
        if unknown:
            raise ValueError(f"--only contains non-paired/unknown fixtures: {unknown}")
        target_ids = selected
    else:
        target_ids = paired_ids

    core_bootstrap = measure_core_bootstrap(startup_helper, fasl, args.reps)

    import tempfile

    with tempfile.TemporaryDirectory(prefix="sens-store-air-load-load-") as tmp_name:
        tmp = Path(tmp_name)
        measurements: dict[tuple[str, str], dict[str, object]] = {}

        for fixture_id in sorted(target_ids):
            fixture = fixtures[fixture_id]
            for representation, candidate in CANDIDATES.items():
                source_key = SOURCE_KEYS[representation]
                source = fixture.get(source_key)
                if not isinstance(source, str) or not source:
                    raise ValueError(f"{fixture_id}: missing {source_key}")
                source_path = write_source(tmp, fixture_id, representation, source)
                measurements[(fixture_id, representation)] = measure_candidate(
                    helper,
                    candidate,
                    source_path,
                    args.reps,
                )

    enriched = 0
    for row in rows:
        fixture_id = str(row.get("fixture_id", ""))
        representation = str(row.get("representation", ""))
        key = (fixture_id, representation)
        measurement = measurements.get(key)
        if measurement is None:
            continue

        ingest_delta = int(measurement["ingest_delta_i_refs"])
        if representation == "canonical-packed":
            row["decode_i_refs"] = ingest_delta
            row["parse_i_refs"] = None
        else:
            row["decode_i_refs"] = None
            row["parse_i_refs"] = ingest_delta

        row["lower_i_refs"] = int(measurement["lower_delta_i_refs"])
        row["ready_i_refs"] = int(measurement["ready_delta_i_refs"])
        row["cold_total_i_refs"] = int(measurement["cold_total_delta_i_refs"])
        row["warm_incremental_i_refs"] = int(measurement["warm_incremental_i_refs"])

        provenance = row.get("provenance")
        if not isinstance(provenance, dict):
            provenance = {}
            row["provenance"] = provenance
        provenance["load_measurement"] = {
            "tool": "valgrind-cachegrind",
            "cache_sim": False,
            "reps": args.reps,
            "phase_definition": {
                "decode_or_parse": "ingest - baseline",
                "lower": "lower - ingest",
                "ready": "ready - baseline",
                "cold_total": "full - baseline",
                "warm_incremental": "OLS slope of repeated raw I refs at N=1,10,100",
            },
            **measurement,
        }
        provenance["core_bootstrap"] = core_bootstrap
        enriched += 1

    if enriched == 0:
        raise ValueError("no paired STORE/AIR rows were enriched")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    print(
        f"enriched {enriched} paired representation rows "
        f"for {len(target_ids)} fixture(s) -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        RuntimeError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(2)
