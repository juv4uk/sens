#!/usr/bin/env python3
"""Суворий аудит пробілів між двійковими словами SENS; НЕ пакувальник.

Видимі двійкові слова і фізичні байти файла — різні одиниці обліку.
Це інструментальне підтвердження лексики, не ратифікований .sens codec.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


def domain_widths(foundation: Path, number_policy: Path) -> set[int]:
    current = json.loads(foundation.read_text(encoding="utf-8"))
    number = json.loads(number_policy.read_text(encoding="utf-8"))
    if current.get("status") != "owner-ratified":
        raise ValueError("D1-D9 foundation is not owner-ratified")
    found = current.get("domains", {})
    for width in range(1, 10):
        domain = f"D{width}"
        row = found.get(domain)
        if row is None or int(row.get("width", -1)) != width:
            raise ValueError(f"missing/malformed ratified {domain}")
        if any(len(bits) != width or set(bits) - {"0", "1"} for bits in row["residents"]):
            raise ValueError(f"invalid ratified coordinate in {domain}")
    if number.get("status") != "owner-ratified":
        raise ValueError("Number width policy is not owner-ratified")
    nums = number.get("ratified_prefix_bits", [])
    if nums[:3] != [24, 48, 96] or any(b != 2 * a for a, b in zip(nums, nums[1:])):
        raise ValueError("Number width ladder is invalid")
    return set(range(1, 10)) | set(nums)


def analyze(path: Path, widths: set[int]) -> dict[str, object]:
    if path.suffix != ".sens":
        raise ValueError("expected a .sens filename")
    data = path.read_bytes()
    # In this research/audit lane only ASCII spaces preserve domain boundaries.
    # Do NOT accept a naked joined payload or Unicode whitespace.
    if not data or re.fullmatch(rb"[01]+(?: [01]+)*", data) is None:
        raise ValueError("source must be nonempty 0/1 words separated by single ASCII spaces")
    tokens = data.decode("ascii").split(" ")
    illegal = sorted(set(len(word) for word in tokens) - widths)
    if illegal:
        raise ValueError(f"unratified/unsupported word widths: {illegal}")
    semantic_bits = sum(map(len, tokens))
    separators = len(tokens) - 1
    physical_bits = len(data) * 8
    # This does not validate the SENS AST, call admission or numeric value layout.
    return {
        "source": str(path),
        "word_ladder_valid": True,
        "reader_oracle_validated": False,
        "physical_bit_exact": physical_bits == semantic_bits,
        "word_count": len(tokens),
        "domain_widths": [len(word) for word in tokens],
        "semantic_bits": semantic_bits,
        "separator_spaces": separators,
        "physical_bytes": len(data),
        "physical_bits": physical_bits,
        "physical_overhead_bits": physical_bits - semantic_bits,
        "expected_ascii_physical_bits": 8 * (semantic_bits + separators),
        "status": "BLOCKED_PHYSICAL_BIT_EXACT" if physical_bits != semantic_bits
                  else "WORD_SPACING_ONLY_NOT_ORACLE_VERIFIED",
        "warning": "Literal ASCII 0/1 and separator spaces consume eight physical bits each. "
                   "WORD-LADDER-VALID does not imply PHYSICAL-BIT-EXACT or runnable SENS.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--foundation", type=Path,
                        default=Path("knowledge/d1-d9-foundation.json"))
    parser.add_argument("--number-widths", type=Path,
                        default=Path("knowledge/number-width-ratified.json"))
    parser.add_argument("--require-physical-exact", action="store_true",
                        help="fail if physical file bits differ from domain-word bit sum")
    args = parser.parse_args()
    try:
        result = analyze(args.source, domain_widths(args.foundation, args.number_widths))
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "INVALID", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.require_physical_exact and not result["physical_bit_exact"] else 0


if __name__ == "__main__":
    sys.exit(main())
