#!/usr/bin/env python3
"""T5M (дефолтний) reference-codec benchmark: Python проти асемблера.

5 трітів (0/1, роздільник 2) → 1 байт (3^5 = 243 < 256). Це фізичний носій
SENS; бенчмарк міряє лише кодек (pack/unpack), а не оцінювач SENS і не
виконання мовних програм. Асемблерний бекенд збирається з
research/asm-t5m/t5m_pack.S і порівнюється з Python-еталоном на тому самому
буфері тритів; результат звіряється байт-у-байт ДО замірів.
"""
from __future__ import annotations

import argparse
import ctypes
import csv
import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import D7_TABLE, read_domain_table  # noqa: E402
from sens_t5_t5m_codec import decode_bytes, encode_words, typed_sha256  # noqa: E402

D7 = tuple(row.bits for row in read_domain_table(D7_TABLE))
assert D7 and len(D7) == len(set(D7))  # точні D7-координати, унікальні

ASM_SOURCE = ROOT / "research" / "asm-t5m" / "t5m_pack.S"


def corpus(kind: str, n: int) -> list[str]:
    if kind == "d3":
        return [f"{(i * 5 + 3) % 8:03b}" for i in range(n)]
    if kind == "d7":
        return [D7[(i * 17 + i // 7) % len(D7)] for i in range(n)]
    if kind == "mixed":
        return [f"{(i * 29 + 7) % (1 << (i % 9 + 1)):0{i % 9 + 1}b}" for i in range(n)]
    raise ValueError(f"unknown case: {kind}")


def words_to_trits(words: list[str]) -> list[int]:
    """Слова → плоский потік тритів: роздільник 2 між словами, доповнення 2 до кратного 5."""
    trits: list[int] = []
    for i, word in enumerate(words):
        if i:
            trits.append(2)
        trits.extend(int(c) for c in word)
    while len(trits) % 5:
        trits.append(2)
    return trits


def trits_to_words(trits: list[int]) -> list[str]:
    words: list[str] = []
    current: list[int] = []
    for trit in trits:
        if trit == 2:
            if current:
                words.append("".join(map(str, current)))
                current = []
        else:
            current.append(trit)
    if current:
        words.append("".join(map(str, current)))
    return words


def py_pack(trits: bytes) -> bytes:
    out = bytearray(len(trits) // 5)
    for i in range(0, len(trits), 5):
        v = 0
        for j in range(5):
            v = v * 3 + trits[i + j]
        out[i // 5] = v
    return bytes(out)


def py_unpack(packed: bytes) -> bytes:
    out = bytearray(len(packed) * 5)
    for g, byte in enumerate(packed):
        v = byte
        for j in range(5):
            out[g * 5 + 4 - j] = v % 3
            v //= 3
    return bytes(out)


def build_asm_so() -> Path:
    """Зібрати t5m_pack.S у спільну бібліотеку (cc/gcc/zig cc)."""
    cc = None
    for candidate in ("cc", "gcc", "clang"):
        if shutil.which(candidate):
            cc = [candidate]
            break
    if cc is None and shutil.which("zig"):
        cc = ["zig", "cc"]
    if cc is None:
        raise RuntimeError("немає C-компілятора (cc/gcc/clang/zig) для збірки asm")
    out = Path(tempfile.mkdtemp(prefix="t5m-asm-")) / "libt5m_asm.so"
    subprocess.run(cc + ["-O2", "-shared", "-o", str(out), str(ASM_SOURCE)], check=True)
    return out


def load_asm(so: Path):
    lib = ctypes.CDLL(str(so))
    pack = lib.sens_t5m_pack
    pack.restype = ctypes.c_uint64
    pack.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p]
    unpack = lib.sens_t5m_unpack
    unpack.restype = None
    unpack.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p]

    def asm_pack(trits: bytes) -> bytes:
        out = ctypes.create_string_buffer(len(trits) // 5)
        pack(trits, len(trits), out)
        return out.raw

    def asm_unpack(packed: bytes) -> bytes:
        out = ctypes.create_string_buffer(len(packed) * 5)
        unpack(packed, len(packed), out)
        return out.raw

    return asm_pack, asm_unpack


def median_us(call, *, samples: int, loops: int) -> tuple[float, float]:
    for _ in range(3):
        call()
    times = []
    for _ in range(samples):
        started = time.perf_counter_ns()
        for _ in range(loops):
            call()
        times.append((time.perf_counter_ns() - started) / (1000.0 * loops))
    return statistics.median(times), max(times) - min(times)


def cpu() -> str:
    info = Path("/proc/cpuinfo")
    if info.is_file():
        for line in info.read_text(errors="replace").splitlines():
            if line.startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def git_sha() -> str:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--sizes", default="128,2048")
    ap.add_argument("--samples", type=int, default=9)
    ap.add_argument("--loops", type=int, default=3)
    args = ap.parse_args()
    sizes = [int(x) for x in args.sizes.split(",")]
    if not sizes or min(sizes) < 1 or args.samples < 3 or args.loops < 1:
        ap.error("nonempty positive sizes, samples >= 3 and loops >= 1 required")

    asm_pack, asm_unpack = load_asm(build_asm_so())

    rows = []
    for kind in ("d3", "d7", "mixed"):
        for size in sizes:
            words = corpus(kind, size)
            trits = bytes(words_to_trits(words))
            packed = encode_words(words)  # Python-еталон (повний word→byte)
            asm_packed = asm_pack(trits)
            # Транспорт мусить бути точним ДО замірів.
            if asm_packed != packed:
                raise RuntimeError(f"asm/py T5M mismatch: {kind}/{size}")
            if py_pack(trits) != packed or py_unpack(packed) != trits:
                raise RuntimeError(f"py core mismatch: {kind}/{size}")
            if asm_unpack(packed) != trits or decode_bytes(packed) != words:
                raise RuntimeError(f"lossy T5M transport: {kind}/{size}")
            if trits_to_words(list(asm_unpack(packed))) != words:
                raise RuntimeError("view mismatch")

            asm_enc_us, asm_enc_span = median_us(lambda: asm_pack(trits), samples=args.samples, loops=args.loops)
            py_enc_us, py_enc_span = median_us(lambda: py_pack(trits), samples=args.samples, loops=args.loops)
            full_enc_us, _ = median_us(lambda: encode_words(words), samples=args.samples, loops=args.loops)
            asm_dec_us, asm_dec_span = median_us(lambda: asm_unpack(packed), samples=args.samples, loops=args.loops)
            py_dec_us, py_dec_span = median_us(lambda: py_unpack(packed), samples=args.samples, loops=args.loops)
            full_dec_us, _ = median_us(lambda: decode_bytes(packed), samples=args.samples, loops=args.loops)

            bits = sum(map(len, words))
            rows.append({
                "workload": kind, "words": size, "semantic_bits": bits,
                "t5m_bytes": len(packed), "trits": len(trits),
                "payload_utilization": round(bits / (8 * len(packed)), 6),
                "asm_pack_median_us": round(asm_enc_us, 3),
                "py_pack_median_us": round(py_enc_us, 3),
                "python_encode_words_median_us": round(full_enc_us, 3),
                "asm_unpack_median_us": round(asm_dec_us, 3),
                "py_unpack_median_us": round(py_dec_us, 3),
                "python_decode_bytes_median_us": round(full_dec_us, 3),
                "asm_pack_spread_us": round(asm_enc_span, 3),
                "asm_unpack_spread_us": round(asm_dec_span, 3),
                "py_pack_spread_us": round(py_enc_span, 3),
                "py_unpack_spread_us": round(py_dec_span, 3),
                "typed_word_sha256": typed_sha256(words),
                "t5m_sha256": hashlib.sha256(packed).hexdigest(),
            })
            print(f"{kind}/{size}: T5M={len(packed)} B | pack asm={asm_enc_us:.2f} py={py_enc_us:.2f} us "
                  f"| unpack asm={asm_dec_us:.2f} py={py_dec_us:.2f} us")

    args.out.mkdir(parents=True, exist_ok=True)
    environment = {
        "schema": "sens-t5m-reference-benchmark/v1",
        "git_sha": git_sha(), "cpu": cpu(), "platform": platform.platform(),
        "python": platform.python_version(), "samples": args.samples, "loops": args.loops,
        "codec": "T5M default: 5 trits per byte (3^5=243<256), separator 2",
        "scope": "T5M pack/unpack core only; Python reference vs x86-64 assembler; no SENS execution",
        "comparison": "asm sens_t5m_pack/unpack versus Python py_pack/py_unpack on the same trit buffer",
        "limits": "GitHub shared runner timings are noisy; do not compare across distinct hardware",
        "d7": "D7 exact-width coordinates; unique",
    }
    (args.out / "environment.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.out / "results.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    (args.out / "results.json").write_text(
        json.dumps({"environment": environment, "rows": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    lines = [
        "# SENS T5M (дефолтний) reference benchmark — Python проти асемблера",
        "",
        f"SHA: `{environment['git_sha']}` · CPU: {environment['cpu']}",
        "",
        "| Corpus | Words | T5M bytes | pack asm µs | pack py µs | unpack asm µs | unpack py µs |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['workload']} | {r['words']} | {r['t5m_bytes']} | "
            f"{r['asm_pack_median_us']:.2f} | {r['py_pack_median_us']:.2f} | "
            f"{r['asm_unpack_median_us']:.2f} | {r['py_unpack_median_us']:.2f} |")
    lines.extend([
        "",
        "**Scope:** T5M pack/unpack core (5 трітів/байт), x86-64 асемблер проти Python-еталону. "
        "Не оцінювач SENS і не виконання мовних програм. Точність звірено байт-у-байт до замірів.",
        "",
        "**Reproducibility:** час на shared-runner коливається; не порівнюйте швидкості між різними CPU.",
        "",
    ])
    report = "\n".join(lines)
    (args.out / "report.md").write_text(report, encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
