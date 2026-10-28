#!/usr/bin/env python3
"""Physical-only Rust/Python/C time, memory and RAPL experiment. Not a SENS oracle."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "benchmarks" / "measurement-triad"))
import verdict

CORPUS = ROOT / "lib/core4.lisp"
OBS = re.compile(r"^PHYSICAL_COPY\tbytes=(\d+)\tcopies=(\d+)\tobserved=(\d+)$")
USAGE = re.compile(r"^METRIC_RSS_KIB=(\d+)\tuser_s=([0-9.]+)\tsys_s=([0-9.]+)$")
KV = re.compile(r"([A-Za-z_]+)=([^ \r\n]+)")


def parse_sample_output(stdout: str, expected: str, *, metered: bool) -> dict | None:
    """Fail closed on extra lines, missing/duplicate observations, and forged meter scope.

    This verifies the *reported* byte parity. It does not prove that an
    optimizer retained every memcpy/copy_from_slice (see #6288 audit).
    """
    lines = stdout.splitlines()
    observations = [line for line in lines if OBS.fullmatch(line)]
    if observations != [expected]:
        raise RuntimeError(
            f"PHYSICAL_PARITY_MISMATCH: expected {expected!r} received {observations!r}")
    if not metered:
        if lines != [expected]:
            raise RuntimeError("unexpected physical stdout (unmetered)")
        return None
    rapl = [line for line in lines if line.startswith("RUST_RAPL_PACKAGE ")]
    if len(rapl) != 1 or len(lines) != 2 or lines[0] != expected:
        raise RuntimeError("RAPL observation ambiguous/missing or unexpected stdout")
    fields: dict[str, str] = {}
    for field in rapl[0].split()[1:]:
        if field.count("=") != 1:
            raise RuntimeError("malformed RAPL observation field")
        key, value = field.split("=", 1)
        if not re.fullmatch(r"[A-Za-z_]+", key) or not value or key in fields:
            raise RuntimeError("duplicate/invalid RAPL observation field")
        fields[key] = value
    if fields.get("status") != "MEASURED" or fields.get("scope") != "whole_package_not_process":
        raise RuntimeError("invalid RAPL status/scope; CPU package != process energy")
    try:
        energy, elapsed = int(fields["energy_uj"]), int(fields["elapsed_ns"])
    except (KeyError, ValueError) as exc:
        raise RuntimeError("invalid RAPL energy/time counters") from exc
    if energy <= 0 or elapsed <= 0:
        raise RuntimeError("nonpositive hardware energy/time")
    return {"energy_uj": energy, "elapsed_ns": elapsed,
            "scope": "whole_package_not_process"}


def parse_resource_usage(raw: str) -> dict:
    """GNU time %M: peak process RSS on Linux, not total system memory."""
    match = USAGE.fullmatch(raw.strip())
    if not match or int(match[1]) <= 0:
        raise RuntimeError("missing/invalid process peak RSS / user / system metrics")
    return {"peak_rss_kib": int(match[1]),
            "user_s": float(match[2]), "sys_s": float(match[3])}


def checked(args: list[str]) -> str:
    p = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=120)
    if p.returncode:
        raise RuntimeError(f"command {args[:2]} failed: {p.stderr[-800:]}")
    return p.stdout.strip()


def optional_read(path: Path) -> str:
    try:
        return path.read_text().strip()
    except OSError:
        return "unknown"


def sensor_state() -> str:
    zones = []
    for zone in Path("/sys/class/powercap").glob("intel-rapl:[0-9]*"):
        if not re.fullmatch(r"intel-rapl:\d+", zone.name):
            continue
        if not re.fullmatch(r"package-\d+", optional_read(zone / "name")):
            continue
        if all(p.is_file() and os.access(p, os.R_OK)
               for p in (zone / "energy_uj", zone / "max_energy_range_uj")):
            zones.append(zone)
    return "RAPL_AVAILABLE" if len(zones) == 1 else (
        "MULTIPLE_RAPL_PACKAGES" if zones else "RAPL_UNAVAILABLE")


def physical_expected(copies: int) -> str:
    data = CORPUS.read_bytes()
    if not data:
        raise RuntimeError("physical corpus is empty")
    checksum = sum(data[i % len(data)] for i in range(copies))
    return f"PHYSICAL_COPY\tbytes={len(data)}\tcopies={copies}\tobserved={checksum}"


def measure(command: list[str], copies: int, out: Path, meter: Path | None,
            expected: str) -> dict:
    with tempfile.NamedTemporaryFile(dir=out, suffix=".usage", delete=False) as f:
        usage = Path(f.name)
    try:
        command = ["/usr/bin/time", "-f",
                   "METRIC_RSS_KIB=%M\tuser_s=%U\tsys_s=%S",
                   "-o", str(usage), *command, str(CORPUS), str(copies)]
        if meter:
            command = [str(meter), "--", *command]
        begin = time.perf_counter_ns()
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
        wall_host_ns = time.perf_counter_ns() - begin
        if run.returncode:
            raise RuntimeError(f"execution failed: {run.returncode}: {run.stderr[-600:]}")
        measured = parse_sample_output(run.stdout, expected, metered=meter is not None)
        result = {"wall_time_ns": wall_host_ns, **parse_resource_usage(usage.read_text()),
                  "energy_uj": None}
        if measured is not None:
            result.update({"energy_uj": measured["energy_uj"],
                           "wall_time_ns": measured["elapsed_ns"],
                           "host_wrapper_wall_ns": wall_host_ns,
                           "scope": measured["scope"]})
        return result
    finally:
        usage.unlink(missing_ok=True)


def experiment(blocks: int, pairs: int, copies: int, seed: int, out: Path) -> None:
    if not 8 <= blocks <= 64 or not 4 <= pairs <= 30 or not 1 <= copies <= 8_192:
        raise ValueError("requires 8..64 blocks, 4..30 balanced pairs, 1..8192 copies")
    if CORPUS.stat().st_size * copies > 3 * 1024 ** 3:
        raise ValueError("copy-traffic-per-process exceeds 3 GiB budget")
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sens-physical-") as tmp:
        binary_dir = Path(tmp)
        rust, c_binary = binary_dir / "copy-rust", binary_dir / "copy-c"
        checked(["rustc", "--edition=2021", "-O", "-C", "target-cpu=x86-64",
                 str(HERE / "copy.rs"), "-o", str(rust)])
        checked(["cc", "-std=c11", "-O2", "-Wall", "-Wextra",
                 str(HERE / "copy.c"), "-o", str(c_binary)])
        commands = {"rust": [str(rust)], "c": [str(c_binary)],
                    "python": [sys.executable, str(HERE / "copy.py")]}
        sensor = sensor_state()
        meter = None
        if sensor == "RAPL_AVAILABLE":
            meter = binary_dir / "rapl"
            checked(["rustc", "--edition=2021", "-O",
                     str(ROOT / "benchmarks/mechanism/rapl-energy-bench.rs"),
                     "-o", str(meter)])
        expected = physical_expected(copies)
        for command in commands.values():
            if checked([*command, str(CORPUS), str(copies)]) != expected:
                raise RuntimeError("PHYSICAL_PARITY_MISMATCH on warmup")
        cpu = "unknown"
        for line in optional_read(Path("/proc/cpuinfo")).splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
        try:
            affinity = ",".join(map(str, sorted(os.sched_getaffinity(0))))
        except (OSError, AttributeError):
            affinity = "unknown"
        ids = [rust, c_binary, HERE / "copy.py"]
        provenance = {
            "git_sha": checked(["git", "rev-parse", "HEAD"]),
            "binary_sha256": ",".join(hashlib.sha256(p.read_bytes()).hexdigest() for p in ids),
            "cpu_model": cpu, "rustc": checked(["rustc", "--version"]),
            "os": platform.platform(), "affinity": affinity,
            "governor": optional_read(Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")),
            "turbo": optional_read(Path("/sys/devices/system/cpu/intel_pstate/no_turbo")),
            "timing_source": "Rust Instant(child)/Python perf_counter_ns(process)",
            "python": platform.python_version(), "cc": checked(["cc", "--version"]).splitlines()[0],
            "energy_sensor": sensor, "measurement_boundary": "process startup+physical copies",
            "physical_work": f"{copies} byte-buffer copies from lib/core4.lisp",
            "audit_copy_retention": "NOT_VERIFIED_BY_BYTE_PARITY_OR_CHECKSUM",
            "measurement_phase": "warm-cache; every invocation includes fresh process startup; compilation excluded",
            "study_seed": seed, "study_blocks": blocks, "study_pairs_per_candidate": pairs,
            "rust_flags": "--edition=2021 -O -C target-cpu=x86-64",
            "c_flags": "-std=c11 -O2 -Wall -Wextra",
            "language_semantics": "NOT_TESTED",
        }
        (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
        by_candidate = {"python": [], "c": []}
        samples = []
        rng = random.Random(seed)
        for block in range(blocks):
            candidates = ["python", "c"]
            rng.shuffle(candidates)
            for candidate in candidates:
                flip = rng.randrange(2)
                for index in range(pairs):
                    order = "AB" if (index + flip) % 2 == 0 else "BA"
                    observations = {}
                    for label in order:
                        language = "rust" if label == "A" else candidate
                        observations[label] = measure(commands[language], copies, out, meter, expected)
                        samples.append({"block": block + 1, "pair": index + 1,
                                        "order": order, "language": language,
                                        **observations[label]})
                    by_candidate[candidate].append({
                        "process_id": f"block-{block+1:02d}", "order": order,
                        "baseline_ns": observations["A"]["wall_time_ns"],
                        "candidate_ns": observations["B"]["wall_time_ns"],
                        "baseline_peak_rss_kib": observations["A"]["peak_rss_kib"],
                        "candidate_peak_rss_kib": observations["B"]["peak_rss_kib"],
                        "baseline_energy_uj": observations["A"]["energy_uj"],
                        "candidate_energy_uj": observations["B"]["energy_uj"],
                    })
        (out / "raw-samples.json").write_text(json.dumps(samples, indent=2) + "\n")
        reports = {}
        for candidate, pairs_data in by_candidate.items():
            reports[candidate] = {}
            for metric in ("wall_time_ns", "peak_rss_kib", "energy_uj"):
                if metric == "energy_uj" and meter is None:
                    reports[candidate][metric] = {"status": "ENERGY_NOT_MEASURED", "reason": sensor}
                    continue
                doc = {"schema": verdict.PHYSICAL_SCHEMA, "metric": metric,
                       "parity": {"passed": True, "oracle_id": "physical-exact-copy"},
                       "provenance": provenance, "pairs": pairs_data}
                reports[candidate][metric] = verdict.analyze(doc, draws=4000, seed=seed)
        (out / "paired-report.json").write_text(json.dumps(reports, indent=2) + "\n")
        lines = ["### SENS · експериментальна фізична вартість мов",
                 f"SHA {provenance['git_sha']} · {blocks} блоків × {pairs} пар · {copies} копій",
                 "",
                 "| Кандидат / Rust | Час (B/A, 95% ДІ) | Peak RSS (B/A, 95% ДІ) | Енергія (B/A, 95% ДІ) |",
                 "|:--|:--|:--|:--|"]
        for candidate in ("python", "c"):
            def fmt(metric: str) -> str:
                item = reports[candidate][metric]
                if item.get("ratio") is None:
                    return item["status"]
                lo, hi = item["ci95_ratio"]
                return f"{item['ratio']:.3f} [{lo:.3f}, {hi:.3f}]"
            lines.append(f"| {candidate} | {fmt('wall_time_ns')} | "
                         f"{fmt('peak_rss_kib')} | {fmt('energy_uj')} |")
        lines.extend(["", f"RAPL: {sensor}. Дослід на shared GitHub runner — не рейтинг.",
                      "AUDIT: retention of each full copy under C/Rust optimizer NOT_VERIFIED; checksum is insufficient.",
                      "Витрати компіляції виключено. Старт процесу включено. "
                      "CPU package RAPL включає фон; без датчика джоулі не виміряно.",
                      "SENS-мовні закони цим фізичним стендом НЕ перевіряються."])
        summary = "\n".join(lines) + "\n"
        (out / "summary.md").write_text(summary)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as f:
                f.write(summary)
        print(f"::notice title=Physical language energy/time study::Rust/C/Python "
              f"blocks={blocks} pairs={pairs} energy={sensor} "
              f"scope=EXPLORATORY SHA={provenance['git_sha'][:12]}")
        print(summary)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--blocks", type=int, default=8)
    p.add_argument("--pairs", type=int, default=4)
    p.add_argument("--copies", type=int, default=8192)
    p.add_argument("--seed", type=int, default=20261028)
    p.add_argument("--out", type=Path, default=Path(".ci-physical-study"))
    a = p.parse_args()
    try:
        experiment(a.blocks, a.pairs, a.copies, a.seed, a.out.resolve())
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as e:
        print(f"PHYSICAL_STUDY_BLOCKED {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
