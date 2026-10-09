#!/usr/bin/env python3
"""D10 #4013 music notation: candidate-only, executable two-model falsification.

Source: W3C MusicXML 4.0 Pitch and Transpose sections; this script does NOT
claim an official MusicXML executable reference implementation. The two math
oracles are independently coded (natural pitch class table vs diatonic
interval construction) and leave external importer / historical-law review
on HOLD. NEVER select, assign a D10 coordinate, or publish physical .sens.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "knowledge/d10-music-enharmonic-primary-review-v1.json"
D10 = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "contracts/d1-d9-foundation-ratification.lisp"
NAMES = ("ENHARMONIC-SPELLING-DISTINCT?", "NOTATED-CHROMATIC-INTERVAL")
SCALE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
ORDER = tuple(SCALE)
INCREMENTS = (2, 2, 1, 2, 2, 2, 1)


class ReviewBlocked(ValueError):
    pass


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def pitch(value: object) -> tuple[str, int, int]:
    if (not isinstance(value, (list, tuple)) or len(value) != 3
            or not isinstance(value[0], str) or value[0] not in SCALE
            or type(value[1]) is not int or not -2 <= value[1] <= 2
            or type(value[2]) is not int or not 0 <= value[2] <= 9):
        raise ReviewBlocked("PITCH: exact MusicXML pitch (step, -2..2 integer alter, 0..9 octave) required")
    return value[0], value[1], value[2]


def semitone_direct(value: object) -> int:
    step, alter, octave = pitch(value)
    return 12 * (octave + 1) + SCALE[step] + alter


def semitone_intervals(value: object) -> int:
    """Independent stepwise oracle; no lookup of the semitone base table."""
    step, alter, octave = pitch(value)
    distance = 0
    for i in range(ORDER.index(step)):
        distance += INCREMENTS[i]
    return (octave + 1) * sum(INCREMENTS) + distance + alter


def enharmonic_direct(a: object, b: object) -> int:
    p, q = pitch(a), pitch(b)
    return int(p != q and semitone_direct(p) == semitone_direct(q))


def enharmonic_independent(a: object, b: object) -> int:
    p, q = pitch(a), pitch(b)
    # Compare semitones WITHOUT mapping away the notated spelling.
    return int(semitone_intervals(p) == semitone_intervals(q) and any(x != y for x, y in zip(p, q)))


def notated_interval(a: object, b: object) -> tuple[int, int]:
    p, q = pitch(a), pitch(b)
    step_delta = 7 * (q[2] - p[2]) + (ORDER.index(q[0]) - ORDER.index(p[0]))
    semitone_delta = semitone_direct(q) - semitone_direct(p)
    return step_delta, semitone_delta


def notated_interval_independent(a: object, b: object) -> tuple[int, int]:
    p, q = pitch(a), pitch(b)
    # Explicit diatonic positions and independently accumulated pitch.
    pos1 = p[2] * len(ORDER) + ORDER.index(p[0])
    pos2 = q[2] * len(ORDER) + ORDER.index(q[0])
    return pos2 - pos1, semitone_intervals(q) - semitone_intervals(p)


def check_examples(candidate: dict) -> int:
    name = candidate["semantic_name"]
    if name == NAMES[0]:
        runner, runner2 = enharmonic_direct, enharmonic_independent
    elif name == NAMES[1]:
        runner, runner2 = notated_interval, notated_interval_independent
    else:
        raise ReviewBlocked("NAME: unexpected candidate")
    count = 0
    if len(candidate["positive_witnesses"]) < 2 or len(candidate["falsifiers"]) < 2:
        raise ReviewBlocked("EVIDENCE: require at least two positives and falsifiers")
    for record in (*candidate["positive_witnesses"], *candidate["falsifiers"]):
        a, b = pitch(record["a"]), pitch(record["b"])
        actual, independent = runner(a, b), runner2(a, b)
        if actual != independent:
            raise ReviewBlocked(f"ORACLE: disagreement {name}: {a!r} {b!r}")
        if "expected" in record:
            expectation = record["expected"]
            normalized = list(actual) if isinstance(actual, tuple) else actual
            if normalized != expectation:
                raise ReviewBlocked(f"WITNESS: wrong expected result {name}: {record!r}")
        if "forbid" in record:
            forbidden = record["forbid"]
            normalized = list(actual) if isinstance(actual, tuple) else actual
            if normalized == forbidden:
                raise ReviewBlocked(f"FALSIFIER: forbidden result observed {name}: {record!r}")
        count += 1
    return count


def verify(root: Path = ROOT) -> dict:
    path = root / SOURCE.relative_to(ROOT)
    item = json.loads(path.read_text(encoding="utf-8"))
    inventory = json.loads((root / D10.relative_to(ROOT)).read_text(encoding="utf-8"))
    source = item["source"]
    snap = item["snapshot"]
    accounting = item["accounting"]
    candidates = item["candidates"]

    if (item["schema"] != "d10-music-enharmonic-primary-review/v1"
            or item["status"] != "RESEARCH-ONLY-HOLD-INDEPENDENT-REVIEW"
            or source["primary_standard"] != "MusicXML 4.0"
            or source["url"] != "https://www.w3.org/2021/06/musicxml40/tutorial/midi-compatible-part/"
            or source["schema_url"] != "https://www.w3.org/2021/06/musicxml40/listings/musicxml.xsd"):
        raise ReviewBlocked("SOURCE: approved primary MusicXML 4.0 and HOLD research status required")
    if (git_blob_sha((root / FOUNDATION.relative_to(ROOT)).read_bytes()) != snap["foundation_git_blob"]
            or inventory["accounting"]["selected_semantic_candidates"] < snap["d10_selected_at_claim"]
            or inventory["accounting"]["ratified_d10_residents"] != snap["ratified_d10_at_claim"] != 0):
        raise ReviewBlocked("AUTHORITY: ratified foundation changed, D10 regressed, or D10 research ratified")
    expected_counts = {"research_candidate_rows": 2, "selected_added": 0,
                       "coordinates_assigned": 0, "ratified_added": 0, "physical_sens_written": 0}
    if accounting != expected_counts:
        raise ReviewBlocked("COUNT: research cannot mint selected, coordinates, ratification or .sens")
    if (len(candidates) != 2 or tuple(c["semantic_name"] for c in candidates) != NAMES
            or len({c["stable_id"] for c in candidates}) != 2):
        raise ReviewBlocked("NAME: require precisely two independently named candidates")
    selected = {r["semantic_name"].upper() for r in inventory["rows"]}
    if any(n in selected for n in NAMES):
        raise ReviewBlocked("DEDUP: research overlaps a selected D10 root")
    witnesses = 0
    for candidate in candidates:
        if (candidate["decision"] != "HOLD-REVIEW-D10-CANDIDATE"
                or candidate["coordinate"] is not None or candidate["ratified"] is not False
                or candidate["selected"] is not False
                or "EXTERNAL-MUSICXML-CONFORMER-NOT-YET-EXECUTED" not in candidate["oracle_status"]
                or candidate["surfaces"]["sym"] is not None
                or not candidate["dedup_attack"] or not candidate["semantic_law"]):
            raise ReviewBlocked("REVIEW: no coordinates, false assertions or premature selection")
        witnesses += check_examples(candidate)

    # Strong falsifiers: reject microtones and temperament extrapolation.
    for bad in (["C", 0.5, 4], ["C", True, 4], ["C", 0, 10], ["H", 0, 4],
                ["C", -3, 4], ["C", 0, 4.0], ["C", 0], {"step": "C"}):
        try:
            pitch(bad)
        except ReviewBlocked:
            pass
        else:
            raise ReviewBlocked(f"INPUT: rejected case unexpectedly accepted: {bad!r}")

    tested_pairs = 0
    # Exhaustive finite subdomain; numerical oracle uses two different
    # algorithms and checks reciprocal/asymmetric behavior.
    for a in itertools.product(ORDER, range(-2, 3), range(3, 6)):
        if semitone_direct(a) != semitone_intervals(a):
            raise ReviewBlocked("ORACLE: scalar mismatch")
        for b in itertools.product(ORDER, range(-2, 3), range(3, 6)):
            one = enharmonic_direct(a, b)
            two = enharmonic_independent(a, b)
            intr = notated_interval(a, b)
            if (one != two or intr != notated_interval_independent(a, b)
                    or one != enharmonic_direct(b, a)
                    or intr != tuple(-x for x in notated_interval(b, a))
                    or (a == b and (one != 0 or intr != (0, 0)))):
                raise ReviewBlocked("ORACLE: bounded independent witness divergence")
            tested_pairs += 1

    # Human behavioral dedup and external conformer remain separate unmet gates.
    return {
        "schema": item["schema"], "status": "RESEARCH-VALIDATED-HOLD-NOT-SELECTED",
        "current_selected": inventory["accounting"]["selected_semantic_candidates"],
        "candidate_count": len(candidates), "evidence_examples": witnesses,
        "two_model_bounded_pairs": tested_pairs, "coordinates_assigned": 0,
        "ratified": 0, "external_source_oracle": "NOT_EXECUTED",
        "D1_D9_behavioral_dedup": "REVIEW_REQUIRED",
        "selected_delta": 0,
    }


if __name__ == "__main__":
    try:
        result = verify()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    except (ReviewBlocked, OSError, ValueError, KeyError, TypeError) as exc:
        print("D10-MUSIC-HOLD: BLOCKED " + str(exc), file=sys.stderr)
        raise SystemExit(2)
