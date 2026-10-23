#!/usr/bin/env python3
"""Аудит текстового перегляду точних слів .bits; НЕ фізичний файл .sens.

Видимі двійкові слова і фізичні байти Zig/T5M — різні носії.
Перевіряємо тільки межі слів у .bits: без кодека, семантики й загального HOLD.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from domain_tables import number_domains  # noqa: E402


def domain_widths(foundation: Path, number_policy: Path) -> set[int]:
    current = json.loads(foundation.read_text(encoding="utf-8"))
    if current.get("status") != "owner-ratified":
        raise ValueError("D1–D11 foundation is not owner-ratified")
    found = current.get("domains", {})
    for width in range(1, 12):
        domain = f"D{width}"
        row = found.get(domain)
        if row is None or int(row.get("width", -1)) != width:
            raise ValueError(f"missing/malformed ratified {domain}")
        if any(len(bits) != width or set(bits) - {"0", "1"} for bits in row["residents"]):
            raise ValueError(f"invalid ratified coordinate in {domain}")
    nums = [width for _, width in number_domains(number_policy)]
    if nums[:5] != [12, 24, 48, 96, 192]:
        raise ValueError("Number D12+ width ladder is invalid")
    return set(range(1, 12)) | set(nums)


def analyze(path: Path, widths: set[int]) -> dict[str, object]:
    if path.suffix != ".bits":
        raise ValueError("expected a textual .bits word view; physical .sens uses Zig/T5M")
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
    view_storage_bits = len(data) * 8
    # ASCII .bits is not the physical T5M carrier.
    # This does not validate AST, call admission or numeric value layout.
    return {
        "source": str(path),
        "word_ladder_valid": True,
        "reader_oracle_validated": False,
        "physical_carrier": "NOT_READ_ZIG_T5M",
        "physical_codec_invoked": False,
        "word_count": len(tokens),
        "domain_widths": [len(word) for word in tokens],
        "semantic_bits": semantic_bits,
        "separator_spaces": separators,
        "view_bytes": len(data),
        "view_storage_bits": view_storage_bits,
        "view_storage_overhead_bits": view_storage_bits - semantic_bits,
        "expected_ascii_view_bits": 8 * (semantic_bits + separators),
        "status": "VISIBLE_WORD_VIEW_ONLY_NOT_ORACLE_VERIFIED",
        "warning": "ASCII .bits is a readable word view, not the Zig/T5M .sens carrier. "
                   "Valid widths do not imply a resident is callable or a program runs.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--foundation", type=Path,
                        default=Path("knowledge/d1-d11-foundation.json"))
    parser.add_argument("--number-widths", type=Path,
                        default=Path("contracts/numeric-domains-ratification.lisp"))
    args = parser.parse_args()
    try:
        result = analyze(args.source, domain_widths(args.foundation, args.number_widths))
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "INVALID", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
