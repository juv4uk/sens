#!/usr/bin/env python3
"""Regression guard for #4403 domain-altitude-economy."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "benchmarks" / "domain-altitude-economy" / "run.py"
FIXTURE = ROOT / "benchmarks" / "domain-altitude-economy" / "fixtures" / "synthetic.jsonl"


def load_runner():
    spec = importlib.util.spec_from_file_location("domain_altitude_economy", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load domain-altitude-economy runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    runner = load_runner()
    report = runner.analyze(FIXTURE)

    assert report["schema"] == "sens-domain-altitude-economy/v1"
    assert report["validated_cases"] == 3
    assert report["semantic_authority_changed"] is False
    assert report["wall_clock_measured"] is False

    cases = {case["case_id"]: case for case in report["cases"]}

    tradeoff = cases["tradeoff-positive-dividend"]
    assert tradeoff["pareto_frontier"] == ["expanded-d3", "resident-d8"]
    assert tradeoff["dominance_edges"] == []
    assert tradeoff["residency_dividends"][0]["gross_dividend_bits"] == 1
    assert tradeoff["residency_dividends"][0]["resident_altitude"] == 8
    assert tradeoff["residency_dividends"][0]["expanded_altitude"] == 3

    negative = cases["expanded-dominates-negative-dividend"]
    assert negative["pareto_frontier"] == ["expanded-d3"]
    assert ["expanded-d3", "resident-d8"] in negative["dominance_edges"]
    assert negative["residency_dividends"][0]["gross_dividend_bits"] == -2

    zero = cases["zero-dividend-altitude-win"]
    assert zero["pareto_frontier"] == ["expanded-d3"]
    assert ["expanded-d3", "resident-d6"] in zero["dominance_edges"]
    assert zero["residency_dividends"][0]["gross_dividend_bits"] == 0

    economics = report["resident_economics"]
    assert economics["synthetic:D8:R1"] == {
        "verified_occurrences": 1,
        "gross_dividend_bits": 1,
        "positive_cases": 1,
        "zero_cases": 0,
        "negative_cases": 0,
    }
    assert economics["synthetic:D8:R2"]["negative_cases"] == 1
    assert economics["synthetic:D6:R3"]["zero_cases"] == 1

    # Fail closed when variants are not observationally equivalent.
    bad_rows = [
        {
            "case_id": "bad-parity",
            "variant_id": "resident",
            "program": "11111111",
            "observable_digest": "digest-a",
            "result_kind": "value",
            "role": "resident",
            "resident_id": "synthetic:BAD",
        },
        {
            "case_id": "bad-parity",
            "variant_id": "expanded",
            "program": "111 111 111",
            "observable_digest": "digest-b",
            "result_kind": "value",
            "role": "expanded",
            "resident_id": "synthetic:BAD",
        },
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad.jsonl"
        path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in bad_rows) + "\n",
            encoding="utf-8",
        )
        try:
            runner.analyze(path)
        except ValueError as exc:
            assert "equivalence gate failed" in str(exc)
        else:
            raise AssertionError("digest mismatch did not fail closed")

    print("DOMAIN-ALTITUDE-ECONOMY=PASS")
    print("synthetic_cases=3 pareto_tradeoff=PASS positive_zero_negative_dividend=PASS")
    print("digest_mismatch_fail_closed=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
