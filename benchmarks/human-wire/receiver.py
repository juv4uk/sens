#!/usr/bin/env python3
"""#2671 — fail-closed receiver model for human fixed-slot binary keying.

MECHANISM only. SEMANTIC AUTHORITY = NONE.

This decoder converts timestamped two-key events into fixed clock slots. It
never shifts later payload bits to hide an insertion/deletion-like timing
mistake:

    event stream -> slot verdicts: 0 | 1 | MISSING | COLLISION

Optional phase search consumes a caller-supplied sync prefix. It does not
choose a sync word, CRC, FEC, block size, or ARQ policy; those remain #2646.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Event:
    bit: str
    timestamp_ns: int


@dataclass(frozen=True)
class SlotVerdict:
    slot: int
    status: str
    bit: str | None
    event_count: int
    deltas_ms: tuple[float, ...]


@dataclass(frozen=True)
class DecodeResult:
    frame_start_ns: int
    slot_ns: int
    slot_count: int
    accepted_bits: str
    missing_slots: tuple[int, ...]
    collision_slots: tuple[int, ...]
    outside_events: int
    verdicts: tuple[SlotVerdict, ...]

    @property
    def complete(self) -> bool:
        return not self.missing_slots and not self.collision_slots and self.outside_events == 0


def _validate_event(event: Event) -> None:
    if event.bit not in {"0", "1"}:
        raise ValueError(f"event bit must be 0 or 1, got {event.bit!r}")
    if event.timestamp_ns < 0:
        raise ValueError("event timestamp must be nonnegative")


def decode_fixed_slots(
    events: Iterable[Event],
    *,
    frame_start_ns: int,
    slot_ns: int,
    slot_count: int,
    tolerance_fraction: float = 0.45,
) -> DecodeResult:
    if frame_start_ns < 0:
        raise ValueError("frame_start_ns must be nonnegative")
    if slot_ns <= 0:
        raise ValueError("slot_ns must be positive")
    if slot_count < 0:
        raise ValueError("slot_count must be nonnegative")
    if not 0.0 < tolerance_fraction < 0.5:
        raise ValueError("tolerance_fraction must be within (0, 0.5)")

    buckets: list[list[tuple[Event, int]]] = [[] for _ in range(slot_count)]
    outside = 0
    limit = tolerance_fraction * slot_ns

    for event in events:
        _validate_event(event)
        relative = event.timestamp_ns - frame_start_ns
        slot = int(round(relative / slot_ns))
        if slot < 0 or slot >= slot_count:
            outside += 1
            continue
        ideal_ns = frame_start_ns + slot * slot_ns
        delta = event.timestamp_ns - ideal_ns
        if abs(delta) > limit:
            outside += 1
            continue
        buckets[slot].append((event, delta))

    verdicts: list[SlotVerdict] = []
    accepted: list[str] = []
    missing: list[int] = []
    collisions: list[int] = []

    for slot, bucket in enumerate(buckets):
        deltas = tuple(delta / 1_000_000.0 for _, delta in bucket)
        if not bucket:
            verdicts.append(SlotVerdict(slot, "MISSING", None, 0, ()))
            accepted.append("?")
            missing.append(slot)
            continue
        if len(bucket) != 1:
            verdicts.append(SlotVerdict(slot, "COLLISION", None, len(bucket), deltas))
            accepted.append("?")
            collisions.append(slot)
            continue
        bit = bucket[0][0].bit
        verdicts.append(SlotVerdict(slot, "BIT", bit, 1, deltas))
        accepted.append(bit)

    return DecodeResult(
        frame_start_ns=frame_start_ns,
        slot_ns=slot_ns,
        slot_count=slot_count,
        accepted_bits="".join(accepted),
        missing_slots=tuple(missing),
        collision_slots=tuple(collisions),
        outside_events=outside,
        verdicts=tuple(verdicts),
    )


@dataclass(frozen=True)
class PhaseCandidate:
    frame_start_ns: int
    sync_matches: int
    sync_errors: int
    timing_error_ns: int
    sync_complete: bool


@dataclass(frozen=True)
class PhaseSearch:
    status: str
    chosen_start_ns: int | None
    candidates: tuple[PhaseCandidate, ...]


def search_phase(
    events: Iterable[Event],
    *,
    nominal_start_ns: int,
    slot_ns: int,
    sync_bits: str,
    search_ns: int,
    step_ns: int,
    tolerance_fraction: float = 0.45,
) -> PhaseSearch:
    if not sync_bits or any(bit not in "01" for bit in sync_bits):
        raise ValueError("sync_bits must be a nonempty binary string")
    if search_ns < 0 or step_ns <= 0:
        raise ValueError("search_ns must be >=0 and step_ns must be >0")

    frozen = tuple(events)
    candidates: list[PhaseCandidate] = []
    offset = -search_ns
    while offset <= search_ns:
        start = nominal_start_ns + offset
        if start >= 0:
            decoded = decode_fixed_slots(
                frozen,
                frame_start_ns=start,
                slot_ns=slot_ns,
                slot_count=len(sync_bits),
                tolerance_fraction=tolerance_fraction,
            )
            matches = sum(
                actual == expected
                for actual, expected in zip(decoded.accepted_bits, sync_bits)
            )
            errors = len(sync_bits) - matches
            timing_error_ns = int(
                sum(abs(delta_ms) for row in decoded.verdicts for delta_ms in row.deltas_ms)
                * 1_000_000
            )
            candidates.append(
                PhaseCandidate(
                    frame_start_ns=start,
                    sync_matches=matches,
                    sync_errors=errors,
                    timing_error_ns=timing_error_ns,
                    sync_complete=decoded.complete and errors == 0,
                )
            )
        offset += step_ns

    if not candidates:
        return PhaseSearch("NO-CANDIDATE", None, ())

    best_key = min((row.sync_errors, row.timing_error_ns) for row in candidates)
    best = [
        row for row in candidates
        if (row.sync_errors, row.timing_error_ns) == best_key
    ]
    perfect = [row for row in best if row.sync_complete]
    if len(perfect) == 1:
        return PhaseSearch("LOCKED", perfect[0].frame_start_ns, tuple(candidates))
    if len(perfect) > 1:
        return PhaseSearch("AMBIGUOUS", None, tuple(candidates))
    return PhaseSearch("UNLOCKED", None, tuple(candidates))


def _events_from_trial(path: Path) -> list[Event]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("raw_events")
    if not isinstance(raw, list):
        raise ValueError("trial JSON must contain raw_events list")
    return [Event(bit=str(row["bit"]), timestamp_ns=int(row["timestamp_ns"])) for row in raw]


def self_test() -> None:
    slot_ns = 100_000_000
    start = 1_000_000_000
    bits = "010110"

    perfect = [
        Event(bit, start + i * slot_ns + jitter)
        for i, (bit, jitter) in enumerate(
            zip(bits, (0, 4_000_000, -7_000_000, 2_000_000, 0, -3_000_000))
        )
    ]
    decoded = decode_fixed_slots(
        perfect, frame_start_ns=start, slot_ns=slot_ns, slot_count=len(bits)
    )
    assert decoded.complete
    assert decoded.accepted_bits == bits

    substituted = list(perfect)
    substituted[2] = Event("0" if bits[2] == "1" else "1", substituted[2].timestamp_ns)
    decoded = decode_fixed_slots(
        substituted, frame_start_ns=start, slot_ns=slot_ns, slot_count=len(bits)
    )
    assert decoded.complete
    assert decoded.accepted_bits != bits
    assert decoded.accepted_bits[2] != bits[2]

    missing = perfect[:3] + perfect[4:]
    decoded = decode_fixed_slots(
        missing, frame_start_ns=start, slot_ns=slot_ns, slot_count=len(bits)
    )
    assert decoded.missing_slots == (3,)
    assert decoded.accepted_bits[3] == "?"

    collision = perfect + [Event("1", start + 4 * slot_ns + 1_000_000)]
    decoded = decode_fixed_slots(
        collision, frame_start_ns=start, slot_ns=slot_ns, slot_count=len(bits)
    )
    assert decoded.collision_slots == (4,)
    assert decoded.accepted_bits[4] == "?"

    # A key landing nearer the adjacent clock slot is classified there, creating
    # explicit MISSING/COLLISION evidence rather than shifting the stream.
    jittered = list(perfect)
    jittered[1] = Event(jittered[1].bit, start + 2 * slot_ns - 2_000_000)
    decoded = decode_fixed_slots(
        jittered, frame_start_ns=start, slot_ns=slot_ns, slot_count=len(bits)
    )
    assert 1 in decoded.missing_slots
    assert 2 in decoded.collision_slots

    shifted_start = start + 20_000_000
    shifted = [Event(bit, shifted_start + i * slot_ns) for i, bit in enumerate("01101")]
    phase = search_phase(
        shifted,
        nominal_start_ns=start,
        slot_ns=slot_ns,
        sync_bits="01101",
        search_ns=40_000_000,
        step_ns=10_000_000,
    )
    assert phase.status == "LOCKED"
    assert phase.chosen_start_ns == shifted_start

    # Exact tie control: candidate starts are 20 ms apart and every event
    # sits exactly midway between them. Both candidates decode the same sync
    # perfectly with equal timing residual, so choosing either would be an
    # arbitrary phase preference.
    tie_sync = "01101"
    midpoint_events = [
        Event(bit, start + 10_000_000 + i * slot_ns)
        for i, bit in enumerate(tie_sync)
    ]
    phase = search_phase(
        midpoint_events,
        nominal_start_ns=start + 10_000_000,
        slot_ns=slot_ns,
        sync_bits=tie_sync,
        search_ns=10_000_000,
        step_ns=20_000_000,
    )
    assert phase.status == "AMBIGUOUS"
    assert phase.chosen_start_ns is None
    perfect_candidates = [
        row for row in phase.candidates
        if row.sync_complete and row.sync_errors == 0
    ]
    assert len(perfect_candidates) == 2
    assert len({row.timing_error_ns for row in perfect_candidates}) == 1

    # Neighbor control: moving the same events 5 ms from one candidate makes
    # that candidate uniquely better while both still decode the sync.
    near_left = [
        Event(bit, start + 5_000_000 + i * slot_ns)
        for i, bit in enumerate(tie_sync)
    ]
    phase = search_phase(
        near_left,
        nominal_start_ns=start + 10_000_000,
        slot_ns=slot_ns,
        sync_bits=tie_sync,
        search_ns=10_000_000,
        step_ns=20_000_000,
    )
    assert phase.status == "LOCKED"
    assert phase.chosen_start_ns == start

    print("HUMAN-WIRE-RX-AMBIGUOUS-TIE=PASS")
    print("HUMAN-WIRE-RX=PASS")
    print("SEMANTIC-AUTHORITY=NONE")
    print("RULE=timing-errors-are-explicit-never-silently-shifted")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--trial-json", type=Path)
    ap.add_argument("--frame-start-ns", type=int)
    ap.add_argument("--slot-ms", type=float, default=120.0)
    ap.add_argument("--slot-count", type=int)
    ap.add_argument("--sync-bits")
    ap.add_argument("--phase-search-ms", type=float, default=0.0)
    ap.add_argument("--phase-step-ms", type=float, default=5.0)
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.trial_json is None or args.frame_start_ns is None or args.slot_count is None:
        raise SystemExit("--trial-json, --frame-start-ns and --slot-count are required")

    events = _events_from_trial(args.trial_json)
    slot_ns = int(args.slot_ms * 1_000_000)

    phase = None
    start = args.frame_start_ns
    if args.sync_bits:
        phase = search_phase(
            events,
            nominal_start_ns=start,
            slot_ns=slot_ns,
            sync_bits=args.sync_bits,
            search_ns=int(args.phase_search_ms * 1_000_000),
            step_ns=int(args.phase_step_ms * 1_000_000),
        )
        if phase.status != "LOCKED" or phase.chosen_start_ns is None:
            print(json.dumps({"phase": asdict(phase)}, indent=2, sort_keys=True))
            return 2
        start = phase.chosen_start_ns

    decoded = decode_fixed_slots(
        events,
        frame_start_ns=start,
        slot_ns=slot_ns,
        slot_count=args.slot_count,
    )
    payload = {
        "schema": "human-wire-rx/v1",
        "layer": "MECHANISM",
        "semantic_authority": "NONE",
        "phase": asdict(phase) if phase is not None else None,
        "decode": asdict(decoded),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if decoded.complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
