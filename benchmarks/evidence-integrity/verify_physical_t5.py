#!/usr/bin/env python3
"""Independently verify one *measured* physical T5 transport report.

This is an evidence-integrity check, NOT a SENS semantic or native-speed oracle.
Run the existing physical benchmark first; this checker never edits inputs and
does not trust a PASS field, self-declared SHA, or a precomputed median.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words, typed_sha256  # noqa: E402
from sens_t5_spaced_view import canonical_view, parse_view  # noqa: E402

SCHEMA = "sens-physical-t5-measurement/v1"
UNIT = "ns_per_decode_encode_roundtrip"
LANE = "CPython transport-mechanism-only; not SENS execution vs Python"


class InvalidEvidence(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidEvidence(message)


def positive_int(value: object, name: str, minimum: int = 1) -> int:
    require(type(value) is int and value >= minimum, f"{name}: expected integer >= {minimum}")
    return value


def finite_positive(value: object, name: str) -> float:
    require(type(value) in (int, float), f"{name}: expected numeric timing")
    result = float(value)
    require(math.isfinite(result) and result > 0, f"{name}: expected finite positive timing")
    return result


def close(measured: object, calculated: float, name: str) -> None:
    value = finite_positive(measured, name)
    require(math.isclose(value, calculated, rel_tol=1e-12, abs_tol=1e-9),
            f"{name}: inconsistent with independent calculation")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rooted_file(root: Path, relative: object) -> Path:
    require(isinstance(relative, str) and relative and "\\" not in relative,
            "fixture must be a canonical relative POSIX path")
    rel = Path(relative)
    require(not rel.is_absolute() and rel.as_posix() == relative and
            all(p not in ("", ".", "..") for p in relative.split("/")) and
            relative.endswith(".sens"), "unsafe or non-.sens fixture path")
    full = root / rel
    require(not full.is_symlink(), f"{relative}: symlink not admitted")
    require(full.is_file() and full.resolve().is_relative_to(root.resolve()),
            f"{relative}: file missing or outside checkout")
    return full


def verify_case(case: dict, root: Path) -> dict:
    relative = case.get("fixture")
    physical_path = rooted_file(root, relative)
    view_path = physical_path.with_suffix("")
    source_path = physical_path.with_suffix(".lisp")
    for path in (view_path, source_path):
        require(not path.is_symlink() and path.is_file(),
                f"{relative}: missing or symlinked same-stem projection")
    physical = physical_path.read_bytes()
    view = view_path.read_bytes()
    source = source_path.read_bytes()
    require(len(physical) > 0 and len(source) > 0, f"{relative}: empty input")
    words = decode_bytes(physical)
    require(bool(words) and encode_words(words) == physical, f"{relative}: invalid T5 roundtrip")
    require(parse_view(view) == words and canonical_view(words) == view,
            f"{relative}: spaced bits are not the canonical physical view")

    reference = {
        "physical_sha256": digest(physical),
        "view_sha256": digest(view),
        "lisp_sha256": digest(source),
        "typed_word_sha256": typed_sha256(words),
        "physical_bytes": len(physical),
        "view_bytes": len(view),
        "lisp_bytes": len(source),
        "word_count": len(words),
        "semantic_bit_count": sum(map(len, words)),
    }
    for key, expected in reference.items():
        require(case.get(key) == expected and
                (type(case.get(key)) is int if type(expected) is int else type(case.get(key)) is str),
                f"{relative}: {key} does not match independently read inputs")
    require(case.get("status") == "PASS_TRANSPORT_ONLY", f"{relative}: wrong transport status")
    require(case.get("semantic_oracle_parity") == "NOT_MEASURED" and
            case.get("native_execution") == "NOT_MEASURED",
            f"{relative}: unearned execution/oracle claim")
    close(case.get("view_over_physical_size_ratio"), len(view)/len(physical),
          f"{relative}: view size ratio")
    close(case.get("lisp_over_physical_size_ratio"), len(source)/len(physical),
          f"{relative}: Lisp size ratio")

    timing = case.get("timings")
    require(type(timing) is dict and timing.get("unit") == UNIT,
            f"{relative}: missing or mislabelled transport timings")
    reps = positive_int(timing.get("repetitions"), f"{relative}: repetitions", minimum=3)
    positive_int(timing.get("iterations_per_rep"), f"{relative}: iterations", minimum=10)
    samples = {}
    for kind in ("t5", "view"):
        a = timing.get(kind+"_samples")
        require(type(a) is list and len(a) == reps, f"{relative}: {kind} sample count mismatch")
        samples[kind] = [
            finite_positive(value, f"{relative}: {kind} sample {i}") for i, value in enumerate(a)
        ]
        close(timing.get(kind+"_median_ns"), statistics.median(samples[kind]),
              f"{relative}: {kind} median")
    close(timing.get("t5_over_view_time_ratio"),
          statistics.median(samples["t5"]) / statistics.median(samples["view"]),
          f"{relative}: timing ratio")
    return {
        "fixture": relative,
        "physical_sha256": digest(physical),
        "typed_word_sha256": typed_sha256(words),
        "samples_per_lane": reps,
        "measured_transport_only": True,
        "oracle_parity_proved": False,
        "native_execution_measured": False,
    }


def verify(report: dict, root: Path, expected_sha: str) -> dict:
    require(type(report) is dict and report.get("schema") == SCHEMA,
            "unknown physical report schema")
    require(type(expected_sha) is str and len(expected_sha) == 40 and
            all(ch in "0123456789abcdef" for ch in expected_sha),
            "expected commit must be an exact 40-hex Git SHA")
    require(report.get("git_sha") == expected_sha, "report generated for another commit")
    require(report.get("lane") == LANE, "this report is not the transport-only lane")
    require(report.get("all_transport_preflights_passed") is True, "report preflight flag false")
    for field in ("cpu", "os", "python", "timer"):
        require(type(report.get(field)) is str and report[field].strip(),
                f"missing provenance: {field}")
    fixtures = report.get("fixtures")
    require(type(fixtures) is list and bool(fixtures), "report has no actual fixture measurements")
    seen: set[str] = set()
    verified = []
    for row in fixtures:
        require(type(row) is dict, "fixture row is not a dictionary")
        relative = row.get("fixture")
        require(relative not in seen, "duplicate fixture in evidence")
        seen.add(relative)
        verified.append(verify_case(row, root))
    return {
        "schema": "sens-physical-t5-evidence-integrity/v1",
        "git_sha": expected_sha,
        "verification": "PASS_TRANSPORT_EVIDENCE_ONLY",
        "verified_cases": verified,
        "semantic_oracle": "NOT_PROVED",
        "native_speedup": "NOT_MEASURED",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--expected-sha", required=True)
    args = ap.parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        verdict = verify(report, args.root.resolve(strict=True), args.expected_sha)
        print(json.dumps(verdict, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print(f"PHYSICAL T5 EVIDENCE REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
