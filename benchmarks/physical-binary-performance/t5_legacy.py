#!/usr/bin/env python3
"""Measure physical SENS transport and execution, not Rust test duration.

Each sample launches a new process. The first timed sample is reported
separately from warm OS-cache medians; these are NOT in-process warm VM timings.
The two independent CLI entry points must emit identical observable bytes
before latency or size comparisons are admitted. No latency thresholds, no
invented speedup claims, and no name/semantic tables in the measurement code.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_t5m_codec import decode_bytes, encode_words, typed_sha256

# Фізичні, вже зафіксовані T5-взірці різних доменних операцій.
# Паритет stdout є умовою заміру, а НЕ незалежним семантичним законом.
FIXTURES = (
    "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "tests/fixtures/migration-multiform-cohort-main/two-forms.sens",
    "tests/fixtures/migration-d1-cond-cohort/branch.sens",
    "tests/fixtures/migration-pair-cohort-main/pair-cons.sens",
    "tests/fixtures/migration-pair-cohort-main/pair-car-cdr.sens",
    "tests/fixtures/migration-d4-selector-cohort/caar.sens",
    "tests/fixtures/migration-eq-cond-cohort-main/eq-cond-select.sens",
    "tests/fixtures/migration-eq-cond-cohort-main/eq-cond-skip.sens",
)
LANES = ("sens-exec", "sens-trit-eval", "sens-trit-open")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_word_projection(payload: bytes) -> bytes:
    """Return the canonical ASCII D1-D9 word stream represented by a T5 file.

    This is a physical transport projection, not an AST/source reconstruction.
    Keep exact word boundaries and one terminal LF explicit so the Rust
    encoder can be compared against the committed physical bytes.
    """
    words = decode_bytes(payload)
    if encode_words(words) != payload:
        raise ValueError("noncanonical T5 payload in canonical word projection")
    return (" ".join(words) + chr(10)).encode("ascii")


def invoke(argv: list[str], *, timeout: int = 30) -> tuple[float, bytes]:
    start = time.perf_counter_ns()
    proc = subprocess.run(
        argv, cwd=ROOT, capture_output=True, check=False, timeout=timeout
    )
    elapsed = (time.perf_counter_ns() - start) / 1_000_000.0
    if proc.returncode != 0:
        raise RuntimeError(
            f"benchmark command returned {proc.returncode}: {argv!r}\n"
            f"{proc.stderr.decode('utf-8', errors='replace')[-2000:]}"
        )
    return elapsed, proc.stdout


def percentile_nearest_rank(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def cpu_model() -> str:
    path = Path("/proc/cpuinfo")
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.partition(":")[2].strip()
    return platform.processor() or "unknown"


def i_refs(argv: list[str]) -> int:
    cmd = [
        "valgrind", "--tool=cachegrind", "--cache-sim=no", "--branch-sim=no",
        "--cachegrind-out-file=/dev/null", *argv,
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, check=False, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(
            f"cachegrind failed: {cmd!r}\n"
            f"{proc.stderr.decode('utf-8', errors='replace')[-2000:]}"
        )
    match = re.search(rb"I\s+refs:\s+([\d,]+)", proc.stderr)
    if not match:
        raise RuntimeError("Cachegrind did not report instruction references")
    return int(match.group(1).replace(b",", b""))



def action_notice(runtime: dict, encoding: dict) -> str:
    """One measured process-latency annotation per parity-admitted T5 program."""
    if runtime["fixture"] != encoding["committed_fixture"] or runtime["lane"] != "sens-exec":
        raise ValueError("annotation requires matching physical T5 execution and encoding")
    if encoding["bytewise_matches_committed"] is not True:
        raise ValueError("annotation requires proven identical T5 bytes")
    return (
        f"::notice title=SENS physical T5 · {Path(runtime['fixture']).name}::"
        f"execution p50={runtime['median_wall_ms']:.3f} ms; "
        f"p95={runtime['p95_wall_ms']:.3f} ms; "
        f"encode p50={encoding['encode_median_wall_ms']:.3f} ms; "
        f"T5={runtime['physical_bytes']} B; "
        f"view/T5={runtime['visible_to_physical_ratio']:.3f}x; "
        "parity=PASS; process startup and I/O included; legacy T5 corpus"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens", type=Path, required=True)
    parser.add_argument("--sens-trit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=21)
    parser.add_argument("--warmup", type=int, default=4)
    parser.add_argument("--cachegrind", action="store_true")
    args = parser.parse_args()
    if args.reps < 5 or args.warmup < 1:
        parser.error("reps must be >= 5 and warmup >= 1")

    sens = str(args.sens.resolve())
    trit = str(args.sens_trit.resolve())
    for exe in (sens, trit):
        if not Path(exe).is_file():
            raise RuntimeError(f"compiled binary not found: {exe}")
    if args.cachegrind and not shutil.which("valgrind"):
        raise RuntimeError("requested Cachegrind but valgrind is not installed")

    # Прив'язуємо фізичні вимірювання до справжніх байтів обох CLI.
    binary_sha256 = {
        "sens": sha256(Path(sens).read_bytes()),
        "sens-trit": sha256(Path(trit).read_bytes()),
    }
    codec_sha256 = sha256((ROOT / "scripts" / "sens_t5_t5m_codec.py").read_bytes())
    benchmark_sha256 = sha256(Path(__file__).read_bytes())

    args.out.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    raw_rows: list[dict] = []
    summaries: list[dict] = []

    # Encode each source in an isolated directory before timing execution.
    # sens-trit encode produces the physical packed T5 artifact; it is not a
    # native machine-code compiler. Every generated artifact must equal the
    # committed .sens bytes, otherwise no runtime measurements are admitted.
    compile_tmp = tempfile.TemporaryDirectory(prefix="sens-physical-t5-encode-")
    compile_root = Path(compile_tmp.name)
    compiled_files: dict[str, Path] = {}
    compile_summaries: list[dict] = []
    compile_raw_rows: list[dict] = []
    compile_warmup, compile_reps = 1, 5

    source_projections: dict[str, bytes] = {}
    for fixture_index, fixture in enumerate(FIXTURES):
        committed_physical = ROOT / fixture
        if not committed_physical.is_file():
            raise RuntimeError(f"fixture missing: {fixture}")
        committed_bytes = committed_physical.read_bytes()
        if not committed_bytes:
            raise RuntimeError(f"empty physical fixture: {fixture}")

        # The committed T5 file is the physical authority for this transport
        # measurement. Its exact-width word projection is decoded independently
        # and then re-encoded by the Rust CLI. Historical sibling .lisp files
        # are intentionally not used as T5 sources: some contain pre-cutover
        # AST syntax (for example (00000001 ()), not canonical 0/1 word streams.
        try:
            source_bytes = canonical_word_projection(committed_bytes)
        except ValueError as error:
            raise RuntimeError(f"{fixture}: independent Python T5 projection failed: {error}") from error
        source_projections[fixture] = source_bytes
        source_label = f"{fixture}#canonical-word-projection"

        encode_samples: list[float] = []
        result_path: Path | None = None
        artifact_digest = ""
        for iteration in range(compile_warmup + compile_reps):
            invocation_dir = compile_root / f"{fixture_index:02d}-encode-{iteration:02d}"
            invocation_dir.mkdir(parents=True)
            staged_source = invocation_dir / f"{Path(fixture).stem}.lisp"
            staged_source.write_bytes(source_bytes)
            elapsed, encoder_stdout = invoke([trit, "encode", str(staged_source)])
            generated = staged_source.with_suffix(".sens")
            if not generated.is_file():
                raise RuntimeError(f"{fixture}: encoder returned success without a .sens artifact")
            generated_bytes = generated.read_bytes()
            if generated_bytes != committed_bytes:
                raise RuntimeError(
                    f"{fixture}: canonical word projection re-encoded to different T5 bytes"
                )
            if b"VERIFIED " not in encoder_stdout:
                raise RuntimeError(f"{fixture}: encode did not emit its verification witness")
            artifact_digest = sha256(generated_bytes)
            if iteration >= compile_warmup:
                encode_samples.append(elapsed)
                compile_raw_rows.append({
                    "sha": commit,
                    "source": source_label,
                    "rep": iteration - compile_warmup + 1,
                    "wall_ms": f"{elapsed:.6f}",
                    "source_sha256": sha256(source_bytes),
                    "artifact_sha256": artifact_digest,
                    "bytewise_matches_committed": "true",
                })
            result_path = generated

        assert result_path is not None
        compiled_files[fixture] = result_path
        compile_summary = {
            "source": source_label,
            "committed_fixture": fixture,
            "source_bytes": len(source_bytes),
            "physical_t5_bytes": len(committed_bytes),
            "source_sha256": sha256(source_bytes),
            "artifact_sha256": artifact_digest,
            "bytewise_matches_committed": True,
            "source_kind": "canonical word projection decoded from committed physical artifact",
            "warmup_processes": compile_warmup,
            "measured_processes": len(encode_samples),
            "encode_median_wall_ms": round(statistics.median(encode_samples), 6),
            "encode_p95_wall_ms": round(percentile_nearest_rank(encode_samples, 0.95), 6),
            "encode_samples_wall_ms": [round(value, 6) for value in encode_samples],
        }
        compile_summaries.append(compile_summary)
        print(
            f"encode {source_label} -> {len(committed_bytes)}B T5, "
            f"median={compile_summary['encode_median_wall_ms']:.3f}ms, bytewise=PASS",
            flush=True,
        )

    for fixture in FIXTURES:
        physical = ROOT / fixture
        if not physical.is_file():
            raise RuntimeError(f"fixture missing: {fixture}")
        source_bytes = source_projections[fixture]
        # Runtime lanes execute the newly encoded temporary artifact, and its
        # bytes must remain exactly the committed physical fixture.
        payload = compiled_files[fixture].read_bytes()
        if payload != physical.read_bytes():
            raise RuntimeError(f"{fixture}: compiled artifact changed after encode admission")
        if not payload:
            raise RuntimeError(f"fixture empty: {fixture}")

        commands = {
            "sens-exec": [sens, str(compiled_files[fixture])],
            "sens-trit-eval": [trit, "eval", str(compiled_files[fixture])],
            "sens-trit-open": [trit, "open", str(compiled_files[fixture])],
        }
        # Перед замірами: дві виконавчі доріжки повинні збігатися.
        # Окремий Python T5-декодер доводить точну транспортну проєкцію,
        # але сам по собі НЕ встановлює семантичних законів мови.
        first_invocations = {lane: invoke(cmd) for lane, cmd in commands.items()}
        baseline = {lane: result for lane, (_, result) in first_invocations.items()}
        if baseline["sens-exec"] != baseline["sens-trit-eval"]:
            raise RuntimeError(f"{fixture}: two execution lanes disagree")
        words = decode_bytes(payload)
        if encode_words(words) != payload:
            raise RuntimeError(f"{fixture}: T5 roundtrip disagrees with physical file")
        visible = (" ".join(words) + "\n").encode("ascii")
        if baseline["sens-trit-open"] != visible:
            raise RuntimeError(f"{fixture}: Rust T5 view differs from independent Python decode")
        visible_bytes = len(visible)
        dimensions = {
            "fixture": fixture,
            "source_bytes": len(source_bytes),
            "source_sha256": sha256(source_bytes),
            "encode_median_wall_ms": next(
                item["encode_median_wall_ms"] for item in compile_summaries
                if item["committed_fixture"] == fixture
            ),
            "physical_bytes": len(payload),
            "visible_binary_bytes": visible_bytes,
            "visible_to_physical_ratio": round(visible_bytes / len(payload), 5),
            "physical_sha256": sha256(payload),
            "exact_word_count": len(words),
            "typed_words_sha256": typed_sha256(words),
            "execution_stdout_sha256": sha256(baseline["sens-exec"]),
            "visible_sha256": sha256(visible),
            "mechanism_parity": "PASS",
            "independent_t5_roundtrip": "PASS",
        }

        samples: dict[str, list[float]] = {lane: [] for lane in LANES}
        # Перший вимір — preflight invocation, до всіх прогрівів бенчмарка.
        # Це НЕ гарантія порожнього OS page cache.
        first_sample = {lane: elapsed for lane, (elapsed, _) in first_invocations.items()}
        # Rotate order each repetition so one lane cannot always benefit from
        # the same OS cache state. Never label subprocess medians "warm VM".
        for iteration in range(args.reps + args.warmup):
            order = LANES[iteration % 3 :] + LANES[: iteration % 3]
            for lane in order:
                elapsed, output = invoke(commands[lane])
                if output != baseline[lane]:
                    raise RuntimeError(
                        f"{fixture}: nondeterministic output in {lane} at {iteration}"
                    )
                if iteration >= args.warmup:
                    samples[lane].append(elapsed)
                    raw_rows.append(
                        {
                            "sha": commit,
                            "fixture": fixture,
                            "lane": lane,
                            "rep": iteration - args.warmup + 1,
                            "wall_ms": f"{elapsed:.6f}",
                            "stdout_sha256": sha256(output),
                        }
                    )

        for lane in LANES:
            values = samples[lane]
            row = {
                **dimensions,
                "lane": lane,
                "reps": len(values),
                "first_process_ms": round(first_sample[lane], 6),
                "median_wall_ms": round(statistics.median(values), 6),
                "p95_wall_ms": round(percentile_nearest_rank(values, 0.95), 6),
                "min_wall_ms": round(min(values), 6),
                "max_wall_ms": round(max(values), 6),
                "wall_cv": round(statistics.pstdev(values) / statistics.mean(values), 6),
                "cachegrind_i_refs": None,
            }
            if args.cachegrind:
                row["cachegrind_i_refs"] = i_refs(commands[lane])
            summaries.append(row)
        print(
            f"{fixture}: transport={len(payload)} bytes, visible={visible_bytes} "
            f"bytes, execution/parity=PASS",
            flush=True,
        )

    # Програму не можна непомітно змінити посеред одного набору замірів.
    if binary_sha256 != {
        "sens": sha256(Path(sens).read_bytes()),
        "sens-trit": sha256(Path(trit).read_bytes()),
    }:
        raise RuntimeError("benchmark executable changed during measurements")

    with (args.out / "raw.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(raw_rows[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(raw_rows)
    with (args.out / "compile-raw.tsv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "sha", "source", "rep", "wall_ms", "source_sha256",
            "artifact_sha256", "bytewise_matches_committed",
        ]
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(compile_raw_rows)
    report = {
        "schema": "sens-physical-binary-performance/v1",
        "commit_sha": commit,
        "utc": datetime.now(timezone.utc).isoformat(),
        "executable_sha256": binary_sha256,
        "benchmark_sha256": benchmark_sha256,
        "t5_codec_sha256": codec_sha256,
        "github_hosted_provenance": {
            "runner_name": os.getenv("RUNNER_NAME", "local"),
            "runner_environment": os.getenv("RUNNER_ENVIRONMENT", "unknown"),
            "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
            "workflow_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        },
        "measurement": "first preflight invocation and process-per-call wall latency after warmups; OS cache state uncontrolled",
        "in_process_warm_execution_measured": False,
        "cross_machine_relative_rank_admissible": False,
        "semantic_correctness_oracle": "EXTERNAL_NOT_PROVEN_BY_THIS_BENCH",
        "transport_parity_oracle": "INDEPENDENT_PYTHON_T5_ROUNDTRIP_AND_EXACT_VIEW",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": cpu_model(),
        "python": sys.version.split()[0],
        "reps": args.reps,
        "warmup": args.warmup,
        "cachegrind_enabled": args.cachegrind,
        "source_to_t5_encoding": {
            "method": "sens-trit encode on canonical paired .lisp source",
            "claim_boundary": "physical packed T5 encoding; not native machine-code compilation",
            "warmup_processes_per_source": compile_warmup,
            "measured_processes_per_source": compile_reps,
            "bytewise_match_required": True,
            "results": compile_summaries,
            "raw_samples_file": "compile-raw.tsv",
        },
        "results": summaries,
    }
    (args.out / "results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Фізична двійкова SENS — вимірювання часу й щільності",
        "",
        f"Commit: `{commit}`; runner CPU: {cpu_model()}",
        "",
        f"CLI SHA256: sens=`{binary_sha256['sens']}`; sens-trit=`{binary_sha256['sens-trit']}`.",
        f"Codec SHA256: `{codec_sha256}`; benchmark SHA256: `{benchmark_sha256}`.",
        "",
        "## Source → фізичне T5 кодування",
        "",
        "| Джерело | Source bytes | T5 bytes | encode median, ms | encode p95, ms | Байтова тотожність |",
        "|---|---:|---:|---:|---:|---|",
        *[f"| {Path(row['source']).name} | {row['source_bytes']} | {row['physical_t5_bytes']} | {row['encode_median_wall_ms']:.3f} | {row['encode_p95_wall_ms']:.3f} | PASS |" for row in compile_summaries],
        "",
        "Це процесне source→packed-T5 кодування, а не генерація нативного машинного коду.",
        "До runtime вимірів допускається лише артефакт, байти якого точно збігаються з канонічним `.sens`.",
        "",
        "| Програма | Шлях | Медіана, мс | p95, мс | Перший preflight, мс | I refs |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summaries:
        refs = str(row["cachegrind_i_refs"]) if row["cachegrind_i_refs"] is not None else "—"
        lines.append(
            f"| {Path(row['fixture']).name} | {row['lane']} | "
            f"{row['median_wall_ms']:.3f} | {row['p95_wall_ms']:.3f} | "
            f"{row['first_process_ms']:.3f} | {refs} |"
        )
    lines.extend(
        [
            "",
            "## Реальна щільність",
            "",
            "| Файл | Фізичні байти | Видимі ASCII-байти | Видимі / фізичні |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in summaries[::3]:
        lines.append(
            f"| {Path(row['fixture']).name} | {row['physical_bytes']} | "
            f"{row['visible_binary_bytes']} | {row['visible_to_physical_ratio']:.3f}× |"
        )
    lines.extend(
        [
            "",
            "Обидві CLI-дороги дали однакові байти результату. Це лише parity",
            "механізмів; семантичні закони встановлюють Lisp-оракули.",
            "Кожна вибірка запускає **новий процес**. p95 — nearest-rank;",
            "міжмашинні порівняння без однакового обладнання невалідні.",
            "Час відлічується навколо subprocess і включає startup, I/O та stdout.",
            "Перший preflight замір перед прогрівами; холодний OS page cache НЕ доведений.",
            "Видимі байти рахуються з канонічним кінцевим LF, перевіреним Python T5-кодеком.",
            "Ширина кожного слова збережена в typed SHA256; це транспортний доказ.",
            "",
        ]
    )
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    if os.environ.get("GITHUB_ACTIONS") == "true":
        compiled = {row["committed_fixture"]: row for row in compile_summaries}
        for runtime in summaries:
            if runtime["lane"] == "sens-exec":
                print(action_notice(runtime, compiled[runtime["fixture"]]))
    compile_tmp.cleanup()


if __name__ == "__main__":
    main()
