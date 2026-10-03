#!/usr/bin/env python3
"""#2645 — local two-key human binary trial harness + deterministic scorer.

Mechanism/human-factors only.

Defaults:
    key A -> bit 0
    key L -> bit 1
    Enter -> finish trial
    Esc   -> abort

The harness consumes #2647 deterministic stimuli.  CI uses only synthetic
self-tests/dry-runs; those are explicitly marked non-human.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import importlib.util
import json
from pathlib import Path
import select
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
CHUNKING_PATH = ROOT / "benchmarks" / "human-wire" / "chunking.py"


def load_chunking():
    spec = importlib.util.spec_from_file_location("human_wire_chunking", CHUNKING_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class RawEvent:
    bit: str
    key: str
    timestamp_ns: int
    slot_index: int | None = None
    late_ms: float | None = None
    early_ms: float | None = None


def align(expected: str, observed: str) -> list[tuple[str, int | None, int | None]]:
    """Levenshtein alignment with deterministic tie-breaking.

    Returns tuples:
      MATCH/SUB(expected_index, observed_index)
      DEL(expected_index, None)
      INS(None, observed_index)
    """

    n, m = len(expected), len(observed)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = dp[i - 1][j - 1] + (expected[i - 1] != observed[j - 1])
            delete = dp[i - 1][j] + 1
            insert = dp[i][j - 1] + 1
            dp[i][j] = min(diag, delete, insert)

    out: list[tuple[str, int | None, int | None]] = []
    i, j = n, m
    while i or j:
        # Prefer diagonal when tied: it makes substitutions explicit rather
        # than inventing delete+insert pairs.
        if i and j:
            cost = expected[i - 1] != observed[j - 1]
            if dp[i][j] == dp[i - 1][j - 1] + cost:
                out.append(
                    (
                        "MATCH" if cost == 0 else "SUB",
                        i - 1,
                        j - 1,
                    )
                )
                i -= 1
                j -= 1
                continue
        if i and dp[i][j] == dp[i - 1][j] + 1:
            out.append(("DEL", i - 1, None))
            i -= 1
            continue
        if j and dp[i][j] == dp[i][j - 1] + 1:
            out.append(("INS", None, j - 1))
            j -= 1
            continue
        raise AssertionError("alignment backtrack failed")

    out.reverse()
    return out


def longest_error_burst(kinds: list[str]) -> int:
    best = cur = 0
    for kind in kinds:
        if kind == "MATCH":
            cur = 0
        else:
            cur += 1
            best = max(best, cur)
    return best


def score(
    *,
    condition: dict,
    raw_events: list[RawEvent],
    trial_id: str,
    training_session: str,
    mode: str,
    synthetic: bool,
) -> tuple[list[dict], dict]:
    expected = condition["stimulus_bits"]
    observed = "".join(event.bit for event in raw_events)
    alignment = align(expected, observed)

    rows = []
    kinds = [kind for kind, _, _ in alignment]
    pending_resync = False
    resync_durations_ms: list[float] = []
    last_indel_ts: int | None = None

    for event_index, (kind, expected_index, observed_index) in enumerate(alignment):
        raw = raw_events[observed_index] if observed_index is not None else None
        expected_bit = expected[expected_index] if expected_index is not None else ""
        observed_key = raw.key if raw is not None else ""

        if kind in {"INS", "DEL"}:
            pending_resync = True
            if raw is not None:
                last_indel_ts = raw.timestamp_ns

        resync_event = False
        if pending_resync and kind == "MATCH":
            resync_event = True
            if raw is not None and last_indel_ts is not None:
                resync_durations_ms.append(
                    (raw.timestamp_ns - last_indel_ts) / 1_000_000.0
                )
            pending_resync = False
            last_indel_ts = None

        if expected_index is None:
            word_index = ""
            within_word_index = ""
            boundary_after = ""
        else:
            word_index, within = divmod(expected_index, condition["word_width"])
            within_word_index = within
            boundary_after = str(
                within == condition["word_width"] - 1
                and expected_index != len(expected) - 1
            ).lower()

        rows.append(
            {
                "trial_id": trial_id,
                "condition_id": condition["condition_id"],
                "payload_hash": condition["stimulus_hash"],
                "payload_bits": condition["payload_bits"],
                "word_width": condition["word_width"],
                "boundary_mode": condition["boundary_mode"],
                "sequence_pattern": condition["sequence_pattern"],
                "event_index": event_index,
                "expected_bit": expected_bit,
                "observed_key": observed_key,
                "timestamp_ns": raw.timestamp_ns if raw is not None else "",
                "slot_index": raw.slot_index if raw is not None and raw.slot_index is not None else "",
                "word_index": word_index,
                "within_word_index": within_word_index,
                "boundary_after": boundary_after,
                "late_ms": (
                    f"{raw.late_ms:.3f}"
                    if raw is not None and raw.late_ms is not None
                    else ""
                ),
                "early_ms": (
                    f"{raw.early_ms:.3f}"
                    if raw is not None and raw.early_ms is not None
                    else ""
                ),
                "substitution": str(kind == "SUB").lower(),
                "insertion": str(kind == "INS").lower(),
                "deletion": str(kind == "DEL").lower(),
                "resync_event": str(resync_event).lower(),
                "operator_training_session": training_session,
            }
        )

    matches = kinds.count("MATCH")
    substitutions = kinds.count("SUB")
    insertions = kinds.count("INS")
    deletions = kinds.count("DEL")

    if len(raw_events) >= 2:
        duration_s = (
            raw_events[-1].timestamp_ns - raw_events[0].timestamp_ns
        ) / 1_000_000_000.0
    else:
        duration_s = 0.0

    raw_rate = len(raw_events) / duration_s if duration_s > 0 else None
    correct_rate = matches / duration_s if duration_s > 0 else None

    metrics = {
        "trial_id": trial_id,
        "condition_id": condition["condition_id"],
        "mode": mode,
        "synthetic": synthetic,
        "human_measurement": not synthetic,
        "training_session": training_session,
        "payload_bits": len(expected),
        "observed_key_events": len(raw_events),
        "correct_matches": matches,
        "substitutions": substitutions,
        "insertions": insertions,
        "deletions": deletions,
        "edit_distance": substitutions + insertions + deletions,
        "substitution_rate_per_payload_bit": substitutions / len(expected),
        "insertion_rate_per_payload_bit": insertions / len(expected),
        "deletion_rate_per_payload_bit": deletions / len(expected),
        "longest_error_burst": longest_error_burst(kinds),
        "duration_s_first_to_last_key": duration_s if duration_s > 0 else None,
        "raw_keyed_symbols_per_s": raw_rate,
        "correct_payload_bits_per_s": correct_rate,
        "mean_resync_ms": (
            sum(resync_durations_ms) / len(resync_durations_ms)
            if resync_durations_ms
            else None
        ),
        "interpretation_guard": (
            "synthetic rows are harness tests only"
            if synthetic
            else "one operator trial; aggregate uncertainty/learning separately"
        ),
    }
    return rows, metrics


class KeyReader:
    def __init__(self):
        self._windows = sys.platform.startswith("win")
        self._old = None

    def __enter__(self):
        if self._windows:
            return self
        import termios
        import tty

        fd = sys.stdin.fileno()
        self._old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        return self

    def __exit__(self, exc_type, exc, tb):
        if not self._windows and self._old is not None:
            import termios

            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._old)

    def read(self, timeout_s: float = 0.05) -> str | None:
        if self._windows:
            import msvcrt

            deadline = time.monotonic() + timeout_s
            while time.monotonic() < deadline:
                if msvcrt.kbhit():
                    return msvcrt.getwch()
                time.sleep(min(0.005, timeout_s))
            return None

        ready, _, _ = select.select([sys.stdin], [], [], timeout_s)
        if ready:
            return sys.stdin.read(1)
        return None


def display_stimulus(condition: dict) -> str:
    bits = condition["stimulus_bits"]
    width = condition["word_width"]
    if condition["boundary_mode"] == "explicit-cue":
        return "|".join(bits[i : i + width] for i in range(0, len(bits), width))
    # Continuous and silent-known deliberately do not render visual separators.
    return bits


def collect_interactive(
    condition: dict,
    *,
    mode: str,
    key_zero: str,
    key_one: str,
    slot_ms: float,
    audio_click: bool,
) -> list[RawEvent]:
    keymap = {key_zero.lower(): ("0", key_zero), key_one.lower(): ("1", key_one)}
    print(f"condition={condition['condition_id']}  bits={condition['payload_bits']}")
    print(f"0={key_zero!r}  1={key_one!r}  Enter=finish  Esc=abort")
    print(display_stimulus(condition))
    input("Press Enter to arm the trial...")

    events: list[RawEvent] = []
    start_ns = time.monotonic_ns()
    next_slot = 0

    with KeyReader() as reader:
        while True:
            now_ns = time.monotonic_ns()
            if mode == "fixed-slot":
                elapsed_ms = (now_ns - start_ns) / 1_000_000.0
                due_slot = int(elapsed_ms // slot_ms)
                while next_slot <= due_slot and next_slot < condition["payload_bits"]:
                    if audio_click:
                        print("\a", end="", flush=True)
                    next_slot += 1
                if elapsed_ms >= condition["payload_bits"] * slot_ms + slot_ms:
                    break

            key = reader.read(0.01)
            if key is None:
                continue
            if key == "\x1b":
                raise KeyboardInterrupt("trial aborted")
            if key in {"\r", "\n"}:
                break
            mapped = keymap.get(key.lower())
            if mapped is None:
                continue

            bit, key_label = mapped
            ts = time.monotonic_ns()
            if mode == "fixed-slot":
                elapsed_ms = (ts - start_ns) / 1_000_000.0
                slot_index = int(round(elapsed_ms / slot_ms))
                ideal_ms = slot_index * slot_ms
                delta = elapsed_ms - ideal_ms
                late_ms = max(0.0, delta)
                early_ms = max(0.0, -delta)
            else:
                slot_index = len(events)
                late_ms = None
                early_ms = None

            events.append(
                RawEvent(
                    bit=bit,
                    key=key_label,
                    timestamp_ns=ts,
                    slot_index=slot_index,
                    late_ms=late_ms,
                    early_ms=early_ms,
                )
            )

    print()
    return events


def synthetic_events(bits: str, *, slot_ms: float) -> list[RawEvent]:
    start = 1_000_000_000
    step = int(slot_ms * 1_000_000)
    return [
        RawEvent(
            bit=bit,
            key="A" if bit == "0" else "L",
            timestamp_ns=start + index * step,
            slot_index=index,
            late_ms=0.0,
            early_ms=0.0,
        )
        for index, bit in enumerate(bits)
    ]


def find_condition(chunking, condition_id: str) -> dict:
    conditions = chunking.make_conditions(chunking.load_fixture())
    for row in conditions:
        if row["condition_id"] == condition_id:
            return row
    available = ", ".join(sorted(row["condition_id"] for row in conditions))
    raise SystemExit(f"unknown condition {condition_id!r}; available: {available}")


def write_outputs(out: Path, rows: list[dict], metrics: dict, raw_events: list[RawEvent]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    chunking = load_chunking()
    with (out / "event-log.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=chunking.EVENT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (out / "trial.json").write_text(
        json.dumps(
            {
                "schema": "human-key-trial/v1",
                "metrics": metrics,
                "raw_events": [asdict(event) for event in raw_events],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def self_test() -> None:
    chunking = load_chunking()
    condition = find_condition(chunking, "D3-silent-known-randomized")
    expected = condition["stimulus_bits"]

    # Perfect.
    perfect = synthetic_events(expected, slot_ms=60.0)
    rows, metrics = score(
        condition=condition,
        raw_events=perfect,
        trial_id="self-perfect",
        training_session="0",
        mode="fixed-slot",
        synthetic=True,
    )
    assert metrics["edit_distance"] == 0
    assert metrics["correct_matches"] == len(expected)
    assert len(rows) == len(expected)

    # One substitution.
    bits = list(expected)
    bits[5] = "1" if bits[5] == "0" else "0"
    sub = synthetic_events("".join(bits), slot_ms=60.0)
    _, metrics = score(
        condition=condition,
        raw_events=sub,
        trial_id="self-sub",
        training_session="0",
        mode="fixed-slot",
        synthetic=True,
    )
    assert metrics["substitutions"] == 1
    assert metrics["insertions"] == 0
    assert metrics["deletions"] == 0

    # One insertion.
    ins_bits = expected[:7] + ("1" if expected[7] == "0" else "0") + expected[7:]
    ins = synthetic_events(ins_bits, slot_ms=60.0)
    _, metrics = score(
        condition=condition,
        raw_events=ins,
        trial_id="self-ins",
        training_session="0",
        mode="fixed-slot",
        synthetic=True,
    )
    assert metrics["edit_distance"] >= 1
    assert metrics["insertions"] >= 1

    # One deletion.
    dele = synthetic_events(expected[:9] + expected[10:], slot_ms=60.0)
    _, metrics = score(
        condition=condition,
        raw_events=dele,
        trial_id="self-del",
        training_session="0",
        mode="fixed-slot",
        synthetic=True,
    )
    assert metrics["edit_distance"] >= 1
    assert metrics["deletions"] >= 1

    print("SELF-TEST=PASS")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--condition", default="D3-silent-known-randomized")
    ap.add_argument("--session", default="1")
    ap.add_argument("--mode", choices=("self-paced", "fixed-slot"), default="self-paced")
    ap.add_argument("--slot-ms", type=float, default=120.0)
    ap.add_argument("--key-zero", default="a")
    ap.add_argument("--key-one", default="l")
    ap.add_argument("--audio-click", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("/tmp/human-key-trial"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        return 0

    chunking = load_chunking()
    condition = find_condition(chunking, args.condition)
    trial_id = str(uuid.uuid4())

    if args.dry_run:
        raw_events = synthetic_events(condition["stimulus_bits"], slot_ms=args.slot_ms)
        synthetic = True
    else:
        raw_events = collect_interactive(
            condition,
            mode=args.mode,
            key_zero=args.key_zero,
            key_one=args.key_one,
            slot_ms=args.slot_ms,
            audio_click=args.audio_click,
        )
        synthetic = False

    rows, metrics = score(
        condition=condition,
        raw_events=raw_events,
        trial_id=trial_id,
        training_session=args.session,
        mode=args.mode,
        synthetic=synthetic,
    )
    write_outputs(args.out, rows, metrics, raw_events)

    print(json.dumps(metrics, indent=2, sort_keys=True))
    if synthetic:
        print("INTERPRETATION=SYNTHETIC-HARNESS-CHECK-NOT-HUMAN-DATA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
