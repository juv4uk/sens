#!/usr/bin/env python3
"""Парні фізичні бенчмарки T5/F3/Tb-33: дослід, не новий формат .sens."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "framed3"))
sys.path.insert(0, str(ROOT / "scripts"))

import adaptive_encoder as adaptive  # noqa: E402
import research_codec as frame3  # noqa: E402
import tb33_tail_research as tb33  # noqa: E402
import sens_t5_codec as oracle_t5  # noqa: E402

FIXTURES = (
    "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "tests/fixtures/migration-atom-cohort/atom-empty.sens",
    "tests/fixtures/migration-d1-cond-cohort/branch.sens",
)


class EvidenceError(ValueError):
    """Вимірювання без автентичного корпусу або паритету не допускається."""


def corpus():
    cases = [
        ("порожній-вираз", ("10", "01"), "точні-слова"),
        ("цитата-порожнього", ("10", "001", "00", "000", "01"), "точні-слова"),
        ("вкладення", tuple("10 100 00 10 111 00 1 00 0 01 01".split()), "точні-слова"),
    ]
    for count in (2, 8, 16):
        cases.append((f"мультиформа-{count}", ("10", "001", "00", "000", "01") * count, "синтетичне-D2"))
    for path in FIXTURES:
        p = ROOT / path
        if not p.is_file() or p.is_symlink():
            raise EvidenceError(f"бракує обов'язкової фізичної T5-фікстури: {path}")
        raw = p.read_bytes()
        words = tuple(oracle_t5.decode_bytes(raw))
        if oracle_t5.encode_words(list(words)) != raw:
            raise EvidenceError(f"неавтентична фікстура T5: {path}")
        cases.append((path, words, "git-T5"))
    return cases


def candidates(words):
    baseline = oracle_t5.encode_words(list(words))
    if adaptive.кодувати_т5(words) != baseline:
        raise EvidenceError("два незалежні T5-кодери не погодились побайтово")
    if tuple(oracle_t5.decode_bytes(baseline)) != words:
        raise EvidenceError("фізичний T5 не відновив точні слова")
    options = {
        "T5": (
            lambda: adaptive.кодувати_т5(words),
            lambda b: adaptive.прочитати_носій(adaptive.Носій("т5", b, ".sens")),
            baseline,
        )
    }
    try:
        raw = bytes((adaptive.МІТКА_РАМКА,)) + frame3.encode(words)
        options["F3"] = (
            lambda: bytes((adaptive.МІТКА_РАМКА,)) + frame3.encode(words),
            lambda b: adaptive.прочитати_носій(adaptive.Носій("рамка3", b, ".senc")),
            raw,
        )
    except frame3.FrameError:
        pass
    try:
        trits = adaptive.трити(words)
        raw = bytes((adaptive.МІТКА_ТБ33,)) + tb33.encode(trits)
        options["Tb33"] = (
            lambda: bytes((adaptive.МІТКА_ТБ33,)) + tb33.encode(adaptive.трити(words)),
            lambda b: adaptive.прочитати_носій(adaptive.Носій("тб33", b, ".senc")),
            raw,
        )
    except tb33.TailError:
        pass
    for name, (encode, decode, raw) in options.items():
        if not isinstance(raw, bytes) or encode() != raw or tuple(decode(raw)) != words:
            raise EvidenceError(f"порушено exact-word roundtrip: {name}")
        if name != "T5":
            try:
                oracle_t5.decode_bytes(raw)
            except oracle_t5.SensT5Error:
                pass
            else:
                raise EvidenceError(f"незаконне прийняття {name} як .sens")
    selection = adaptive.найменший_носій(words)
    if tuple(adaptive.прочитати_носій(selection)) != words:
        raise EvidenceError("адаптивний носій не відновлює програму")
    expected = min(len(v[2]) for v in options.values())
    if len(selection.дані) != expected:
        raise EvidenceError("адаптивний вибір не мінімізує перевірені фізичні байти")
    if len(selection.дані) == len(baseline) and selection.профіль != "т5":
        raise EvidenceError("за рівності повинен перемагати T5")
    return options, selection


def negative_controls():
    for marker in (243, 244, 242):
        try:
            oracle_t5.decode_bytes(bytes((marker,)))
        except oracle_t5.SensT5Error:
            continue
        raise EvidenceError(f"канонічний T5 прийняв заборонений байт {marker}")
    for profile, bad in (("рамка3", b"\xf4"), ("тб33", b"\xf3")):
        for raw in (bad, b""):
            try:
                adaptive.прочитати_носій(adaptive.Носій(profile, raw, ".senc"))
            except adaptive.ПомилкаНосія:
                continue
            raise EvidenceError(f"маркер або усічення прийнято: {profile}")
    for words in (("0000000000",), ("2",), ("",)):
        try:
            adaptive.найменший_носій(words)
        except adaptive.ПомилкаНосія:
            continue
        raise EvidenceError("недопустиме точне слово прийнято")


def quantile(values, percent):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(len(ordered) * percent / 100) - 1)]


def bench(options, warmup, reps, inner):
    funcs = {}
    for key, (encode, decode, raw) in options.items():
        funcs[(key, "encode")] = encode
        funcs[(key, "decode")] = lambda raw=raw, decode=decode: decode(raw)
    for _ in range(warmup):
        for fun in funcs.values():
            for _ in range(inner):
                fun()
    samples = {name: [] for name in funcs}
    keys = list(funcs)
    for turn in range(reps):
        order = keys[turn % len(keys):] + keys[:turn % len(keys)]
        for key in order:
            fun = funcs[key]
            t0 = time.perf_counter_ns()
            for _ in range(inner):
                fun()
            duration = time.perf_counter_ns() - t0
            if duration <= 0:
                raise EvidenceError("неправильний час таймера")
            samples[key].append(duration / inner)
    return {
        name: {
            kind: {
                "median_ns": statistics.median(samples[(name, kind)]),
                "p95_ns": quantile(samples[(name, kind)], 95),
                "raw_ns_per_operation": samples[(name, kind)],
            }
            for kind in ("encode", "decode")
        }
        for name in options
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="тільки oracle і негативні свідки")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--reps", type=int, default=15)
    parser.add_argument("--inner", type=int, default=25)
    parser.add_argument("--warmup", type=int, default=3)
    args = parser.parse_args()
    if args.reps < 10 or args.inner < 1 or args.warmup < 1:
        raise SystemExit("BLOCKED: замало повторів/прогріву")
    negative_controls()
    cases = []
    totals = {"T5": 0, "adaptive": 0}
    for label, words, origin in corpus():
        if not words or any(not isinstance(w, str) or not 1 <= len(w) <= 9 for w in words):
            raise EvidenceError(f"недійсний корпус: {label}")
        options, selection = candidates(words)
        baseline_size = len(options["T5"][2])
        totals["T5"] += baseline_size
        totals["adaptive"] += len(selection.дані)
        row = {
            "name": label, "origin": origin, "words": len(words),
            "source_sha256": hashlib.sha256(" ".join(words).encode("ascii")).hexdigest(),
            "profiles": {
                key: {"status": "AVAILABLE", "bytes_including_marker": len(value[2]),
                      "physical_sha256": hashlib.sha256(value[2]).hexdigest()}
                for key, value in options.items()
            },
            "chosen": selection.профіль, "chosen_bytes": len(selection.дані),
        }
        for key in ("F3", "Tb33"):
            if key not in row["profiles"]:
                row["profiles"][key] = {"status": "UNSUPPORTED"}
        if not args.check:
            measured = bench(options, args.warmup, args.reps, args.inner)
            for key, timings in measured.items():
                row["profiles"][key].update(timings)
        cases.append(row)
    if args.check:
        print(f"CODEC-MATRIX-ORACLE: PASS — {len(cases)} корпусів, негативні контролі")
        return
    if not args.out:
        raise SystemExit("BLOCKED: задайте --out для сирого JSON")
    digest = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                            text=True, capture_output=True, check=True).stdout.strip()
    result = {
        "schema": "sens-physical-codec-paired-research/v1",
        "authority": "RESEARCH_ONLY; SENS .sens = T5",
        "commit": digest,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0], "host": platform.platform(),
        "machine": platform.machine(), "runner": os.getenv("RUNNER_NAME", "local"),
        "timing": "Python-only; no Rust, D2 parse, cold-start or GPU speed claim",
        "warmup": args.warmup, "reps": args.reps, "inner": args.inner,
        "total_bytes": totals,
        "corpus_savings_pct": round(100 * (totals["T5"] - totals["adaptive"]) / totals["T5"], 3),
        "cases": cases,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CODEC-MATRIX-BENCH: {len(cases)} справжніх/похідних корпусів")
    print(f"T5={totals['T5']} B, адаптивний={totals['adaptive']} B, "
          f"виграш={result['corpus_savings_pct']}%; Python-вимірювання в {args.out}")


if __name__ == "__main__":
    try:
        main()
    except (EvidenceError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"CODEC-MATRIX-BLOCKED: {error}", file=sys.stderr)
        raise SystemExit(2)
