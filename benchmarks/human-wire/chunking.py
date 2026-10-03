#!/usr/bin/env python3
"""#2647 — deterministic D1-D5 human-keying chunking stimuli.

Human-factors/mechanism only.  This generator creates equal-payload-bit
conditions and event-log-compatible templates.  It produces no empirical human
performance claim.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "benchmarks" / "human-wire" / "payloads.json"

BOUNDARY_MODES = ("continuous", "silent-known", "explicit-cue")
SEQUENCE_MODES = ("randomized", "repeated-control")
WIDTHS = (1, 2, 3, 4, 5)

EVENT_FIELDS = [
    "trial_id",
    "condition_id",
    "payload_hash",
    "payload_bits",
    "word_width",
    "boundary_mode",
    "sequence_pattern",
    "event_index",
    "expected_bit",
    "observed_key",
    "timestamp_ns",
    "slot_index",
    "word_index",
    "within_word_index",
    "boundary_after",
    "late_ms",
    "early_ms",
    "substitution",
    "insertion",
    "deletion",
    "resync_event",
    "operator_training_session",
]


def payload_from_seed(bits: int, seed: int) -> str:
    rng = random.Random(seed)
    value = rng.getrandbits(bits)
    return f"{value:0{bits}b}"


def sha(bits: str) -> str:
    return hashlib.sha256(bits.encode("ascii")).hexdigest()


def load_fixture() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fixture = next(
        row for row in data["fixtures"] if row["id"] == "equal-width-study-fixture"
    )
    assert fixture["payload_bits"] == 480
    assert fixture["word_widths"] == [1, 2, 3, 4, 5]
    return fixture


def repeated_bits(base_bits: str, width: int) -> str:
    word = base_bits[:width]
    count = len(base_bits) // width
    return word * count


def make_conditions(fixture: dict) -> list[dict]:
    base = payload_from_seed(fixture["payload_bits"], fixture["seed"])
    rows = []
    for width in WIDTHS:
        assert len(base) % width == 0
        word_count = len(base) // width
        for boundary in BOUNDARY_MODES:
            for sequence in SEQUENCE_MODES:
                bits = base if sequence == "randomized" else repeated_bits(base, width)
                cue_events = word_count - 1 if boundary == "explicit-cue" else 0
                total_slots = len(bits) + cue_events
                condition_id = f"D{width}-{boundary}-{sequence}"
                rows.append(
                    {
                        "condition_id": condition_id,
                        "word_width": width,
                        "boundary_mode": boundary,
                        "sequence_pattern": sequence,
                        "payload_bits": len(bits),
                        "word_count": word_count,
                        "boundary_cue_events": cue_events,
                        "cue_overhead_slots": cue_events,
                        "total_stimulus_slots": total_slots,
                        "stimulus_hash": sha(bits),
                        "stimulus_bits": bits,
                    }
                )

    # Deterministic randomized presentation order to avoid fixed width-order bias.
    rng = random.Random(2647)
    rng.shuffle(rows)
    for index, row in enumerate(rows):
        row["presentation_order"] = index
    return rows


def event_template_rows(condition: dict) -> list[dict]:
    rows = []
    bits = condition["stimulus_bits"]
    width = condition["word_width"]
    for index, bit in enumerate(bits):
        word_index, within = divmod(index, width)
        boundary_after = within == width - 1 and index != len(bits) - 1
        rows.append(
            {
                "trial_id": "",
                "condition_id": condition["condition_id"],
                "payload_hash": condition["stimulus_hash"],
                "payload_bits": condition["payload_bits"],
                "word_width": width,
                "boundary_mode": condition["boundary_mode"],
                "sequence_pattern": condition["sequence_pattern"],
                "event_index": index,
                "expected_bit": bit,
                "observed_key": "",
                "timestamp_ns": "",
                "slot_index": index,
                "word_index": word_index,
                "within_word_index": within,
                "boundary_after": str(boundary_after).lower(),
                "late_ms": "",
                "early_ms": "",
                "substitution": "",
                "insertion": "",
                "deletion": "",
                "resync_event": "",
                "operator_training_session": "",
            }
        )
    return rows


def validate(conditions: list[dict]) -> dict:
    assert len(conditions) == 30
    assert {row["word_width"] for row in conditions} == set(WIDTHS)
    assert {row["boundary_mode"] for row in conditions} == set(BOUNDARY_MODES)
    assert {row["sequence_pattern"] for row in conditions} == set(SEQUENCE_MODES)
    assert all(row["payload_bits"] == 480 for row in conditions)

    by_key = {
        (row["word_width"], row["boundary_mode"], row["sequence_pattern"]): row
        for row in conditions
    }
    assert len(by_key) == 30

    for width in WIDTHS:
        expected_words = 480 // width
        for sequence in SEQUENCE_MODES:
            continuous = by_key[(width, "continuous", sequence)]
            silent = by_key[(width, "silent-known", sequence)]
            explicit = by_key[(width, "explicit-cue", sequence)]
            assert continuous["word_count"] == expected_words
            assert silent["cue_overhead_slots"] == 0
            assert continuous["cue_overhead_slots"] == 0
            assert explicit["cue_overhead_slots"] == expected_words - 1
            assert explicit["total_stimulus_slots"] == 480 + expected_words - 1

    return {
        "conditions": 30,
        "payload_bits_per_condition": 480,
        "widths": list(WIDTHS),
        "boundary_modes": list(BOUNDARY_MODES),
        "sequence_modes": list(SEQUENCE_MODES),
        "human_trials_recorded": 0,
        "best_width_claim": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    fixture = load_fixture()
    conditions = make_conditions(fixture)
    summary = validate(conditions)

    public_rows = [
        {k: v for k, v in row.items() if k != "stimulus_bits"}
        for row in sorted(conditions, key=lambda r: r["presentation_order"])
    ]

    with (args.out / "experiment-matrix.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(public_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(public_rows)

    stimuli = {
        "schema": "human-wire-chunking-stimuli/v1",
        "authority": "human-factors-research-only",
        "source_manifest": "benchmarks/human-wire/payloads.json",
        "fixture_id": fixture["id"],
        "conditions": conditions,
        "guards": [
            "all conditions carry exactly 480 payload bits",
            "explicit boundary cues pay one extra stimulus slot per word boundary",
            "semantic labels are absent from motor stimuli",
            "repeated-control is analyzed separately from randomized payloads",
            "no human performance conclusion exists until real event logs are recorded",
        ],
    }
    (args.out / "stimuli.json").write_text(
        json.dumps(stimuli, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Event-log-compatible template for #2645. One representative randomized
    # condition per width keeps the template compact while preserving schema.
    template_conditions = [
        next(
            row for row in conditions
            if row["word_width"] == width
            and row["boundary_mode"] == "silent-known"
            and row["sequence_pattern"] == "randomized"
        )
        for width in WIDTHS
    ]
    template_rows = []
    for condition in template_conditions:
        template_rows.extend(event_template_rows(condition))

    with (args.out / "event-log-template.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=EVENT_FIELDS)
        writer.writeheader()
        writer.writerows(template_rows)

    result = {
        "schema": "human-wire-chunking-result/v1",
        "summary": summary,
        "fixture": {
            "id": fixture["id"],
            "payload_bits": fixture["payload_bits"],
            "seed": fixture["seed"],
        },
        "cue_overhead_by_width": {
            str(width): (480 // width) - 1
            for width in WIDTHS
        },
        "event_log_fields": EVENT_FIELDS,
        "interpretation": (
            "stimulus-generation only; width effects, uncertainty and learning "
            "require measured #2645 event logs"
        ),
    }
    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D1-D5 human-keying chunking matrix — #2647",
        "",
        "Conditions: **30**",
        "Payload bits per condition: **480**",
        "Human trials recorded by this generator: **0**",
        "",
        "| width | words | explicit boundary cue slots |",
        "|---:|---:|---:|",
    ]
    for width in WIDTHS:
        words = 480 // width
        report.append(f"| D{width} | {words} | {words - 1} |")
    report += [
        "",
        "Boundary conditions:",
        "- continuous raw fixed-slot bits;",
        "- silent/no-cue boundaries known from task structure;",
        "- explicit boundary cue, charged as stimulus overhead.",
        "",
        "Sequence controls:",
        "- randomized deterministic payload;",
        "- repeated-word control.",
        "",
        "No width is ranked. Any speed/error/learning conclusion requires real",
        "event logs from #2645 and uncertainty analysis.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
