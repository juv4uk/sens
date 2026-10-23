#!/usr/bin/env python3
"""One genuine pinned Zig 0.16.0 carrier for native H2 SENS fixtures.

Source word splitting and mutation-location checks are NOT semantics.
Only the Zig transport executable constructs and validates physical T5.
The resulting .sens files are evaluated solely by native binary SENS.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys

from sens_t5_t5m_codec import parse_words
from zig_codec_bridge import build_transport, carry_t5, verify_t5

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "cond": ("retired-d3-cond", 4),
    "eq": ("retired-d3-eq", 16),
    "quote": ("retired-quote-inert-d3", 14),
}
PROFILE = "D1-D10_COORDINATES_NOT_EXECUTION"


def checked_words(kind: str) -> tuple[list[str], list[str]]:
    name, mutated_at = CASES[kind]
    files = [ROOT / "tests" / "semantic" / f"{name}-{role}.bits"
             for role in ("law", "mutant")]
    good, bad = [parse_words(file.read_text(encoding="ascii")) for file in files]
    if len(good) != len(bad):
        raise ValueError(f"ZIG_NATIVE_T5_RED id={kind} expected=exact_word_count")
    positions = [i for i, (a, b) in enumerate(zip(good, bad)) if a != b]
    if positions != [mutated_at] or good[mutated_at] != "0" or bad[mutated_at] != "1":
        raise ValueError(f"ZIG_NATIVE_T5_RED id={kind} expected=one_D1_0_to_1")
    if kind == "quote" and good[11:18] != [
        "001", "00", "10", "0", "00", "1", "01"
    ]:
        raise ValueError("ZIG_NATIVE_T5_RED id=quote expected=exact_D2_quote_position")
    return good, bad


def produce(suite: str, out: Path) -> None:
    if suite not in ("d3", "quote"):
        raise ValueError("ZIG_NATIVE_T5_RED expected=d3_or_quote")
    if not out.is_dir() or out.is_symlink():
        raise ValueError("ZIG_NATIVE_T5_RED expected=unaliased_output_directory")
    # One Zig build per suite. No Python encode_projection/decode_bytes.
    binary = build_transport(out / "zig-native-carrier")
    kinds = ("cond", "eq") if suite == "d3" else ("quote",)
    for kind in kinds:
        name, _ = CASES[kind]
        good, bad = checked_words(kind)
        for role, words in (("law", good), ("mutant", bad)):
            physical = carry_t5(binary, " ".join(words) + "\n", codec="t5")
            proof = verify_t5(binary, physical, codec="t5")
            digest = hashlib.sha256(physical).hexdigest()
            if (proof.get("profile") != PROFILE or
                    proof.get("zig_version") != "0.16.0" or
                    proof.get("physical_sha256") != digest or
                    proof.get("zig_binary_sha256") is None):
                raise ValueError(
                    f"ZIG_NATIVE_T5_RED id={name} role={role} "
                    "expected=attested_exact_Zig_physical_receipt")
            suffix = f"{kind}-{role}.sens" if suite == "d3" else f"{role}.sens"
            target = out / suffix
            if target.exists() or target.is_symlink():
                raise ValueError(f"ZIG_NATIVE_T5_RED output_exists={target}")
            target.write_bytes(physical)
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError(f"ZIG_NATIVE_T5_RED output_drift={target}")
            print(
                f"ZIG_NATIVE_T5_CARRY source=tests/semantic/{name}-{role}.bits "
                f"physical_sha256={digest} "
                f"zig_binary_sha256={proof['zig_binary_sha256']} "
                f"profile={PROFILE} semantic_authority=SENS"
            )
        if suite == "d3":
            print(
                f"SENS_T5_PHYSICAL id={kind} words={len(good)} "
                f"width_bits={sum(map(len, good))} mutation=D1:0-to-1 "
                "semantic_pass=NOT_INFERRED"
            )
        else:
            print(
                f"QUOTE_INERT_T5_READY word_count={len(good)} "
                "mutant_changed_words=1 semantic_pass=NOT_INFERRED"
            )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_h2_zig_t5.py d3|quote OUTPUT_DIRECTORY")
    produce(sys.argv[1], Path(sys.argv[2]))
