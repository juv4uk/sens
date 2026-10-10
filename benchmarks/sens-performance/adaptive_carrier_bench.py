#!/usr/bin/env python3
"""Парне вимірювання фізичних носіїв T5/F3/F4 без зміни семантики SENS.

Тільки повний розмір із міткою, точні D1–D9 слова та оборотність.
Немає дозволу замінити .sens, чисел GPU/FPGA або оцінки швидкості SENS VM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "framed3"))

import adaptive_encoder as codec  # noqa: E402
import research_codec as frame  # noqa: E402
import tb33_tail_research as tail  # noqa: E402

CORPUS = {
    "порожня-D2": ("10", "01"),
    "цитування": ("10", "001", "00", "000", "01"),
    "вкладення": tuple("10 100 00 10 111 00 1 00 0 01 01".split()),
    "довга-форма": ("10",) + ("00010101",) * 48 + ("01",),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def words_sha(words: tuple[str, ...]) -> str:
    # Окремий префікс довжини захищає ширини та початкові нулі.
    return sha(b"".join(bytes((len(w),)) + w.encode("ascii") for w in words))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError("BLOCKED: " + message)


def choices(words: tuple[str, ...]):
    canonical = codec.кодувати_т5(words)
    require(codec.декодувати_т5(canonical) == words, "T5 roundtrip")
    result = [("T5", canonical, lambda: codec.кодувати_т5(words))]
    try:
        body = frame.encode(words)
    except frame.FrameError:
        pass  # Поза точним рамковим підкласом; НЕ невдалий T5.
    else:
        raw = bytes((codec.МІТКА_РАМКА,)) + body
        require(frame.decode(raw[1:]) == words, "F3 body roundtrip")
        require(codec.прочитати_носій(codec.Носій("рамка3", raw, ".senc")) == words,
                "F3 tagged roundtrip")
        result.append(("F3", raw, lambda: bytes((codec.МІТКА_РАМКА,)) + frame.encode(words)))
    try:
        body = tail.encode(codec.трити(words))
    except tail.TailError:
        pass
    else:
        raw = bytes((codec.МІТКА_ТБ33,)) + body
        require(codec.прочитати_носій(codec.Носій("тб33", raw, ".senc")) == words,
                "F4 tagged roundtrip")
        result.append(("F4", raw, lambda: bytes((codec.МІТКА_ТБ33,)) + tail.encode(codec.трити(words))))
    return result


def timed(fn, expected: bytes, repeat: int) -> list[int]:
    for _ in range(2):
        require(fn() == expected, "warm-up byte drift")
    samples = []
    for _ in range(repeat):
        start = time.perf_counter_ns()
        actual = fn()
        elapsed = time.perf_counter_ns() - start
        require(actual == expected, "measured byte drift")
        samples.append(elapsed)
    return samples


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=11)
    args = ap.parse_args()
    require(args.reps >= 5, "at least five repetitions")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    report = {
        "schema": "sens-adaptive-carrier-bench/v1",
        "git_sha": commit,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "metric": "Python in-process encode wall-clock ns; NOT VM execution",
        "winner_rule": "smallest complete physical byte count including F3/F4 marker; tie T5",
        "corpus": [],
    }
    rng = random.Random(20261010)
    for label, words in CORPUS.items():
        candidates = choices(words)
        selected = codec.найменший_носій(words)
        winner = min(candidates, key=lambda x: len(x[1]))
        require(selected.дані == winner[1], label + " adaptive selection differs")
        require(selected.розширення == (".sens" if winner[0] == "T5" else ".senc"),
                label + " extension mismatch")
        sizes = {name: len(data) for name, data, _ in candidates}
        rows = []
        order = list(range(len(candidates)))
        rng.shuffle(order)
        for index in order:
            name, data, fn = candidates[index]
            samples = timed(fn, data, args.reps)
            rows.append({
                "profile": name,
                "total_physical_bytes": len(data),
                "physical_sha256": sha(data),
                "encode_ns_samples": samples,
                "encode_ns_p50": statistics.median(samples),
                "encode_ns_p95_nearest_rank": sorted(samples)[(95 * len(samples) + 99) // 100 - 1],
            })
        rows.sort(key=lambda row: ("T5", "F3", "F4").index(row["profile"]))
        report["corpus"].append({
            "name": label,
            "typed_words_sha256": words_sha(words),
            "word_count": len(words),
            "size_by_profile_bytes": sizes,
            "winner": winner[0],
            "winner_total_bytes": len(winner[1]),
            "savings_vs_T5_bytes": len(candidates[0][1]) - len(winner[1]),
            "profiles": rows,
        })
        print(f"{label}: T5={sizes['T5']} Б; обрано {winner[0]}={len(winner[1])} Б")
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(args.out.stat().st_size > 0, "empty evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
