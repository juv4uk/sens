#!/usr/bin/env python3
"""Read-only provenance audit: D11 test vocabulary must not shadow D3..D10.

This is an observational migration aid, NOT a new semantic contract, codec,
callability gate, or automatic workflow. A failing --strict result is scoped to
the D11 test-vocabulary import in the three-pass migrator. The normal run
reports the finding without creating an unrelated CI empty.

Reproduce:
    python3 scripts/audit-three-pass-d11-resident-shadow.py
    python3 scripts/audit-three-pass-d11-resident-shadow.py --strict
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts" / "migrate-three-pass.py"
FOUNDATION = ROOT / "knowledge" / "d1-d11-foundation.json"
TEST_LEXICON = ROOT / "knowledge" / "d11-testing-vocabulary-ratified.json"
LOWER_DOMAINS = ("D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10")


def git_blob_sha(payload: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
    ).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def lower_first(foundation: dict) -> dict[str, tuple[str, str]]:
    """Mimic the *current* lower-domain first-wins rule; don't mint authority."""
    result: dict[str, tuple[str, str]] = {}
    domains = foundation["domains"]
    for domain in LOWER_DOMAINS:
        values = domains[domain]["residents"]
        for bits, name in values.items():
            if domain == "D3" and name == "EMPTY":
                continue
            result.setdefault(str(name).upper(), (bits, domain))
    return result


def actual_migration_labels(foundation: dict) -> dict[str, tuple[str, str]]:
    # Import the REAL implementation under examination. The standalone audit
    # must not become a second resolver that can falsely report success.
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "audit_d11_three_pass_real_migrator", MIGRATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("three-pass migrator cannot be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # required for dataclass type resolution
    spec.loader.exec_module(module)
    return module.current_residents(foundation)


def report() -> dict:
    foundation = load_json(FOUNDATION)
    lexicon = load_json(TEST_LEXICON)
    if foundation.get("status") != "owner-ratified":
        raise ValueError("extended foundation lacks stated ratification status")
    if (lexicon.get("status") != "UNRATIFIED_REVIEW" or
            lexicon.get("ratified") is not False or lexicon.get("width") != 11):
        raise ValueError("expected unratified exact D11 testing fixture")
    if "not callable Core" not in lexicon.get("semantic_scope", ""):
        raise ValueError("D11 lexicon scope unexpectedly changed; recheck owner authority")
    if not isinstance(lexicon.get("table"), list):
        raise ValueError("D11 testing inventory missing")

    source_d11 = foundation["domains"]["D11"]["residents"]
    lexicon_d11 = {row["bits"]: row["lisp"] for row in lexicon["table"]}
    if source_d11 != lexicon_d11:
        raise ValueError("extended foundation D11 differs from unratified testing fixture")

    baseline = lower_first(foundation)
    observed = actual_migration_labels(foundation)
    overlapping = []
    shadows = []
    for bits, name in lexicon_d11.items():
        key = name.upper()
        canonical_lower = baseline.get(key)
        if canonical_lower is None:
            continue  # unique D11 test name; not itself a callable Core resident
        actual = observed.get(key)
        case = {
            "name": key,
            "lower_domain": canonical_lower[1],
            "lower_bits": canonical_lower[0],
            "d11_test_bits": bits,
            "observed_domain": actual[1] if actual is not None else None,
            "observed_bits": actual[0] if actual is not None else None,
        }
        overlapping.append(case)
        if actual != canonical_lower:
            shadows.append(case)

    raw = MIGRATOR.read_bytes()
    current = foundation.get("current_domains", [])
    duplicates = sorted({name for name in current if current.count(name) > 1})
    omitted = sorted(set(foundation["domains"]) - set(current))
    return {
        "test_id": "three-pass-d11-name-shadow-provenance",
        "layer": "migration-resolution",
        "status": "MIGRATION_OPPORTUNITY" if shadows else "NO_TEST_VOCAB_SHADOW",
        "semantic_authority": "SENS",
        "source_file": "scripts/migrate-three-pass.py",
        "source_git_blob_sha1": git_blob_sha(raw),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "foundation_file": "knowledge/d1-d11-foundation.json",
        "foundation_git_blob_sha1": git_blob_sha(FOUNDATION.read_bytes()),
        "ratified_test_inventory": "knowledge/d11-testing-vocabulary-ratified.json",
        "overlap_count": len(overlapping),
        "shadow_count": len(shadows),
        "shadows": shadows,
        "all_overlaps": overlapping,
        "foundation_index_observation": {
            "duplicate_current_domains": duplicates,
            "domains_omitted_from_current_list": omitted,
        },
        "scope": (
            "Only alternate extended D1-D11 foundation import; default "
            "three-pass foundation is independent D1-D9. D11 test names "
            "do not grant callable or T5 runtime admission."
        ),
        "next_scoped_fix": (
            "Coordinate with active three-pass file owner: preserve the "
            "earlier ratified resident on an exact-name collision; "
            "retain nonoverlapping D11 test vocabulary only as test data."
        ),
        "reproduce": "python3 scripts/audit-three-pass-d11-resident-shadow.py --strict",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict", action="store_true",
        help="exit 1 on an observed D11 name override (manual focused check only)",
    )
    args = parser.parse_args()
    try:
        result = report()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({
            "test_id": "three-pass-d11-name-shadow-provenance",
            "layer": "migration-resolution",
            "status": "HARNESS_ERROR",
            "reason": str(exc),
        }, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    # Observational by default; it does not alter the central automatic CI.
    return 1 if args.strict and result["shadow_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
