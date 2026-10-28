#!/usr/bin/env python3
"""Offline evidence-integrity check for ENERGY-06; not a reproduction verdict."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SCHEMA = "sens-energy-artifact/pilot-v1"
REQUIRED_FILES = {
    "raw_samples": "raw-samples.json",
    "provenance": "provenance.json",
    "paired_report": "paired-report.json",
    "summary": "summary.md",
}
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
MAX_BYTES = 32 * 1024 * 1024

class InvalidArtifact(ValueError):
    pass

def demand(yes: bool, reason: str) -> None:
    if not yes:
        raise InvalidArtifact(reason)

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InvalidArtifact(f"unreadable JSON: {path.name}") from exc


def verify_pairs(raw: list[dict]) -> dict[str, int]:
    """Verify actual adjacent AB/BA launches, not merely a reported checksum."""
    demand(len(raw) % 2 == 0, "unpaired raw launch")
    observed = {}
    used = set()
    for offset in range(0, len(raw), 2):
        first, second = raw[offset:offset + 2]
        block, pair, order = first.get("block"), first.get("pair"), first.get("order")
        demand(type(block) is int and block > 0
               and type(pair) is int and pair > 0,
               f"raw pair {offset // 2} invalid positive block/pair")
        demand(order in ("AB", "BA") and all(
            (item.get("block"), item.get("pair"), item.get("order"))
            == (block, pair, order) for item in (first, second)),
            f"raw pair {offset // 2} mismatched block/pair/order")
        languages = (first["language"], second["language"])
        demand(languages.count("rust") == 1 and len(set(languages)) == 2,
               f"raw pair {offset // 2} must contain rust and one candidate")
        candidate = second["language"] if first["language"] == "rust" else first["language"]
        expected = ("rust", candidate) if order == "AB" else (candidate, "rust")
        demand(languages == expected,
               f"raw pair {offset // 2} order contradicts launches")
        key = (block, candidate, pair)
        demand(key not in used, f"duplicate raw pair {key}")
        used.add(key)
        observed.setdefault((block, candidate), []).append((pair, order))

    blocks = {block for block, _ in observed}
    demand(blocks == set(range(1, len(blocks) + 1)),
           "raw block sequence incomplete")
    for block in blocks:
        comparisons = {candidate: observed.get((block, candidate))
                       for candidate in ("python", "c")}
        demand(all(comparisons.values()),
               f"raw block {block} missing comparison candidate")
        demand(len(comparisons["python"]) == len(comparisons["c"]),
               f"raw block {block} candidate pair counts differ")
        for candidate, pairs in comparisons.items():
            pairs = sorted(pairs)
            demand(len(pairs) >= 4,
                   f"raw block {block} {candidate} has fewer than four pairs")
            demand([item[0] for item in pairs] == list(range(1, len(pairs) + 1)),
                   f"raw block {block} {candidate} pair index gap")
            demand(all(pairs[i][1] != pairs[i - 1][1]
                       for i in range(1, len(pairs))),
                   f"raw block {block} {candidate} does not alternate AB/BA")
    return {language: sum(len(rows) for (block, lang), rows in observed.items()
                          if lang == language)
            for language in ("python", "c")}


def verify(manifest_path: Path) -> dict:
    demand(manifest_path.is_file() and not manifest_path.is_symlink(), "missing or linked manifest")
    root = manifest_path.resolve().parent
    manifest = load_json(manifest_path)
    demand(isinstance(manifest, dict), "manifest must be an object")
    demand(manifest.get("schema") == SCHEMA, "unsupported schema")
    sha = manifest.get("source_sha")
    demand(isinstance(sha, str) and SHA.fullmatch(sha) is not None, "missing exact source SHA")
    demand(manifest.get("independent_reproduction") == "NOT_REPRODUCED",
           "cannot certify third-party reproduction with this checker")
    energy = manifest.get("energy_status")
    demand(energy in ("ENERGY_NOT_MEASURED", "MEASURED"), "invalid energy status")
    files = manifest.get("files")
    demand(isinstance(files, dict) and set(files) == set(REQUIRED_FILES), "missing/extra evidence files")
    evidence = {}
    for name, filename in REQUIRED_FILES.items():
        spec = files[name]
        demand(isinstance(spec, dict) and set(spec) == {"path", "sha256"}, f"bad file entry {name}")
        relative = spec["path"]
        digest = spec["sha256"]
        demand(relative == filename, f"noncanonical evidence path {name}")
        demand(isinstance(digest, str) and DIGEST.fullmatch(digest) is not None,
               f"invalid sha256 {name}")
        path = root / relative
        demand(path.is_file() and not path.is_symlink() and path.resolve().parent == root,
               f"missing, linked or escaping evidence {name}")
        demand(0 < path.stat().st_size <= MAX_BYTES, f"empty or oversized evidence {name}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        demand(actual == digest, f"tampered evidence {name}")
        evidence[name] = path
    provenance = load_json(evidence["provenance"])
    raw = load_json(evidence["raw_samples"])
    report = load_json(evidence["paired_report"])
    demand(isinstance(provenance, dict) and provenance.get("git_sha") == sha,
           "evidence does not match source SHA")
    demand(provenance.get("language_semantics") == "NOT_TESTED",
           "physical study must not claim SENS semantics")
    demand(isinstance(raw, list) and len(raw) > 0, "raw samples missing")
    demand(isinstance(report, dict) and all(x in report for x in ("python", "c")),
           "paired-report comparisons incomplete")
    meter_present = energy == "MEASURED"
    demand((provenance.get("energy_sensor") == "RAPL_AVAILABLE") == meter_present,
           "energy status contradicts sensor provenance")
    for index, sample in enumerate(raw):
        demand(isinstance(sample, dict), f"sample {index} not an object")
        demand(sample.get("language") in ("python", "rust", "c"),
               f"sample {index} language invalid")
        demand(type(sample.get("wall_time_ns")) is int and sample["wall_time_ns"] > 0,
               f"sample {index} duration invalid")
        demand(type(sample.get("peak_rss_kib")) is int and sample["peak_rss_kib"] > 0,
               f"sample {index} RSS invalid")
        if meter_present:
            demand(type(sample.get("energy_uj")) is int and sample["energy_uj"] > 0,
                   f"sample {index} missing physical energy")
            demand(sample.get("scope") == "whole_package_not_process"
                   and sample.get("time_boundary") == "RAPL_meter_wraps_usr_bin_time",
                   f"sample {index} invalid meter boundary")
            demand(type(sample.get("wrapped_once")) is bool
                   and isinstance(sample.get("counter"), str)
                   and Path(sample["counter"]).is_absolute()
                   and Path(sample["counter"]).name == "energy_uj",
                   f"sample {index} missing counter provenance")
        else:
            demand(sample.get("energy_uj") is None,
                   f"sample {index} fabricated energy without a sensor")
            demand("scope" not in sample and "counter" not in sample,
                   f"sample {index} has unexplained meter claims")
            demand(sample.get("time_boundary") == "host_wrapper_includes_subprocess",
                   f"sample {index} time boundary invalid")
    pair_counts = verify_pairs(raw)
    for language in ("python", "c"):
        info = report[language]
        for metric in ("wall_time_ns", "peak_rss_kib"):
            metric_report = info.get(metric) if isinstance(info, dict) else None
            demand(isinstance(metric_report, dict)
                   and type(metric_report.get("pairs")) is int
                   and metric_report["pairs"] == pair_counts[language],
                   f"report {language}/{metric} does not match raw paired launches")
        demand(isinstance(info, dict) and "energy_uj" in info,
               f"missing statistical evidence {language}")
        energy_item = info["energy_uj"]
        demand(isinstance(energy_item, dict), "bad energy report")
        if not meter_present:
            demand(energy_item.get("status") == "ENERGY_NOT_MEASURED"
                   and "ratio" not in energy_item and "ci95_ratio" not in energy_item,
                   f"numeric energy claim without sensor: {language}")
        else:
            demand(energy_item.get("status") != "ENERGY_NOT_MEASURED",
                   f"measured raw energy contradicted by report: {language}")
    return {"source_sha": sha, "raw_samples": len(raw),
            "energy_status": energy, "independent_reproduction": "NOT_REPRODUCED"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.manifest)
    except InvalidArtifact as exc:
        print(f"ARTIFACT_INTEGRITY_BLOCKED reason={exc}", file=sys.stderr)
        return 2
    print("ARTIFACT_INTEGRITY=PASS "
          f"sha={result['source_sha']} raw_samples={result['raw_samples']} "
          f"energy={result['energy_status']} "
          "independent_reproduction=NOT_REPRODUCED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
