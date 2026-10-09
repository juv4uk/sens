#!/usr/bin/env python3
"""Human AIR/T5 multi-program stream emulator (research, mechanism only).

One pulse encodes exactly one semantic bit of a D1..D9 SENS word:
  0 => 1τ mark; 1 => 3τ mark.
  1τ gap within a word, 7τ gap between domain words,
  21τ terminal gap after a program (one continuous silence).
After a terminal gap the receiver is ready for the NEXT program.

The on-disk .sens T5 codec is a DIFFERENT layer: it packs five logical
trits per byte, uses 2 only BETWEEN words, and obtains EOF from file length.
The timing 21τ EOF is AIR-only, not written to .sens.

This is a deterministic offline event simulator, NOT live Morse radio,
not an executable runtime or a verified semantic oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

SCHEMA = "sens-human-air-t5-stream/research-v1"
MAX_WORDS = 100_000
MAX_EVENTS = 2_000_000
MAX_WIDTH = 9
MAX_PACKED_BYTES = 4 * 1024 * 1024
TRITS_PER_BYTE = 5
SHORT_MARK = 1.0
LONG_MARK = 3.0
INTRA_GAP = 1.0
WORD_GAP = 7.0
FRAME_GAP = 21.0


class ChannelError(ValueError):
    """Malformed physical event/timing or invalid exact-width word."""


def parse_program(text: str) -> list[str]:
    words = text.split()
    if not words:
        raise ChannelError("empty program is not admitted by current T5")
    if len(words) > MAX_WORDS:
        raise ChannelError("too many words")
    for word in words:
        if not 1 <= len(word) <= MAX_WIDTH or any(bit not in "01" for bit in word):
            raise ChannelError("only exact D1..D9 binary words are supported")
    return words


def identity_sha256(words: list[str]) -> str:
    """Digest includes each exact word width; NOT just concatenated data bits."""
    hasher = hashlib.sha256()
    for word in words:
        hasher.update(bytes([len(word)]))
        hasher.update(int(word, 2).to_bytes((len(word) + 7) // 8, "big"))
    return hasher.hexdigest()


def t5_pack(words: list[str]) -> bytes:
    """Canonical owner-selected FILE T5. No 22, only 0..4 pad-2 trits."""
    if not words:
        raise ChannelError("empty T5 program")
    for word in words:
        parse_program(word)  # exact width, no text identifiers
    trits = "2".join(words)
    trits += "2" * (-len(trits) % TRITS_PER_BYTE)
    if len(trits) // TRITS_PER_BYTE > MAX_PACKED_BYTES:
        raise ChannelError("packed T5 file exceeds bound")
    return bytes(int(trits[i:i + 5], 3) for i in range(0, len(trits), 5))


def t5_unpack(data: bytes) -> list[str]:
    if not data or len(data) > MAX_PACKED_BYTES:
        raise ChannelError("missing or oversized T5 bytes")
    if any(byte > 242 for byte in data):
        raise ChannelError("out-of-range physical trit group")
    trits = "".join(f"{byte // 81 % 3}{byte // 27 % 3}{byte // 9 % 3}{byte // 3 % 3}{byte % 3}"
                    for byte in data)
    tail = len(trits) - len(trits.rstrip("2"))
    if tail >= 5:
        raise ChannelError("nonminimal trailing pad (or obsolete 22)")
    words = parse_program(trits[:len(trits) - tail].replace("2", " "))
    if t5_pack(words) != data:
        raise ChannelError("noncanonical T5 representation")
    return words


def _jitter(value: float, amplitude: float, rng: random.Random) -> float:
    return round(value * rng.uniform(1 - amplitude, 1 + amplitude), 6)


def make_stream(programs: list[list[str]], *, jitter: float = 0.0,
                seed: int = 73) -> list[dict[str, Any]]:
    """Alternating mark/gap events. A 21τ gap separates EACH frame, last too."""
    if not programs:
        raise ChannelError("stream needs at least one program")
    if not 0.0 <= jitter <= 0.2:
        raise ChannelError("jitter must be between 0 and 0.20 for calibrated probe")
    rng = random.Random(seed)
    events: list[dict[str, Any]] = []
    start = 0.0
    for program in programs:
        if not program:
            raise ChannelError("empty frame")
        parse_program(" ".join(program))
        for wi, word in enumerate(program):
            for bi, bit in enumerate(word):
                duration = _jitter(SHORT_MARK if bit == "0" else LONG_MARK, jitter, rng)
                events.append({"kind": "mark", "units": duration, "start_units": round(start, 6)})
                start += duration
                if bi != len(word) - 1:
                    gap = INTRA_GAP
                elif wi != len(program) - 1:
                    gap = WORD_GAP
                else:
                    gap = FRAME_GAP
                duration = _jitter(gap, jitter, rng)
                events.append({"kind": "gap", "units": duration, "start_units": round(start, 6)})
                start += duration
                if len(events) > MAX_EVENTS:
                    raise ChannelError("event limit exceeded")
    return events


class Receiver:
    """Incremental fail-closed physical framing. NO automatic code execution."""

    def __init__(self) -> None:
        self.frames: list[list[str]] = []
        self.words: list[str] = []
        self.current_word = ""
        self.want_mark = True
        self.after_frame = False
        self.events_seen = 0

    @staticmethod
    def _mark(units: float) -> str:
        if 0.5 <= units <= 1.5:
            return "0"
        if 2.1 <= units <= 3.9:
            return "1"
        raise ChannelError(f"unrecognized keydown duration: {units}τ")

    @staticmethod
    def _gap(units: float) -> str:
        if 0.5 <= units <= 1.5:
            return "intra"
        if 5.0 <= units <= 9.0:
            return "word"
        if units >= 14.0:
            return "frame"
        raise ChannelError(f"ambiguous silence duration: {units}τ")

    def feed(self, event: dict[str, Any]) -> None:
        self.events_seen += 1
        if self.events_seen > MAX_EVENTS:
            raise ChannelError("event limit exceeded")
        if not isinstance(event, dict):
            raise ChannelError("event must be an object")
        kind = event.get("kind")
        units = event.get("units")
        if type(units) not in (int, float) or not 0.0 < units < 1e9:
            raise ChannelError("invalid event duration")
        if self.want_mark:
            if kind != "mark":
                raise ChannelError("two gaps in a row or a gap before first mark")
            self.current_word += self._mark(float(units))
            if len(self.current_word) > MAX_WIDTH:
                raise ChannelError("word exceeds D9 width")
            self.want_mark = False
            self.after_frame = False
        else:
            if kind != "gap":
                raise ChannelError("adjacent marks without an observable gap")
            gap = self._gap(float(units))
            self.want_mark = True
            if gap != "intra":
                if not self.current_word:
                    raise ChannelError("empty domain word")
                self.words.append(self.current_word)
                self.current_word = ""
                if len(self.words) > MAX_WORDS:
                    raise ChannelError("frame exceeds word limit")
                if gap == "frame":
                    frame = list(self.words)
                    # Physical closure is not an oracle proof. File codec parity
                    # is checked here, grammar is independently Rust-owned.
                    if t5_unpack(t5_pack(frame)) != frame:
                        raise ChannelError("T5 transport parity failure")
                    self.frames.append(frame)
                    self.words = []
                    self.after_frame = True

    def finish(self) -> list[list[str]]:
        if not self.frames:
            raise ChannelError("no completed frame (no final silence)")
        if not self.want_mark or self.words or self.current_word or not self.after_frame:
            raise ChannelError("stream ended before terminal >=14τ silence")
        return self.frames


def receive(events: list[dict[str, Any]]) -> list[list[str]]:
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise ChannelError("invalid event array")
    receiver = Receiver()
    for event in events:
        receiver.feed(event)
    return receiver.finish()


def summary(frames: list[list[str]], events: list[dict[str, Any]],
            *, unit_ms: float, source: list[list[str]] | None = None) -> dict[str, Any]:
    if not 0.0 < unit_ms <= 10_000:
        raise ChannelError("unit_ms outside accepted simulation range")
    seconds = sum(float(e["units"]) for e in events) * unit_ms / 1000.0
    semantic_bits = sum(len(word) for frame in frames for word in frame)
    return {
        "schema": SCHEMA,
        "scope": "MECHANISM_ONLY__NO_ORACLE_EXECUTION",
        "program_count": len(frames),
        "exact_width_programs": [" ".join(f) for f in frames],
        "programs": [
            {"index": i, "words": len(f), "semantic_bits": sum(map(len, f)),
             "typed_sha256": identity_sha256(f), "file_t5_hex": t5_pack(f).hex()}
            for i, f in enumerate(frames)
        ],
        "mark_events": sum(e["kind"] == "mark" for e in events),
        "word_gap_events": sum(e["kind"] == "gap" and 5.0 <= e["units"] <= 9.0 for e in events),
        "frame_gap_events": sum(e["kind"] == "gap" and e["units"] >= 14.0 for e in events),
        "semantic_bits": semantic_bits,
        "total_timing_units": round(sum(float(e["units"]) for e in events), 6),
        "unit_ms": unit_ms,
        "seconds": round(seconds, 6),
        "net_semantic_bits_per_second": round(semantic_bits / seconds, 6),
        "matches_expected_words": frames == source if source is not None else None,
        "warning": "Timed EOF signals silence, not confirmed delivery; CRC/ACK/oracle parity absent.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["demo", "send", "receive"])
    parser.add_argument("--program", action="append", default=[],
                        help="one exact-width D1..D9 program; repeat for streaming")
    parser.add_argument("--events", type=Path, help="JSON event output (send) or input (receive)")
    parser.add_argument("--jitter", type=float, default=0.0,
                        help="deterministic uniform timing jitter <=0.20")
    parser.add_argument("--seed", type=int, default=73)
    parser.add_argument("--unit-ms", type=float, default=60.0)
    args = parser.parse_args(argv)
    try:
        if args.command == "receive":
            if args.events is None:
                raise ChannelError("receive requires --events")
            packet = json.loads(args.events.read_text(encoding="utf-8"))
            if not isinstance(packet, dict) or packet.get("schema") != SCHEMA:
                raise ChannelError("unexpected event stream schema")
            events = packet["events"]
            frames = receive(events)
            result = summary(frames, events, unit_ms=float(packet["unit_ms"]))
        else:
            sources = args.program or ["10 001 01", "10 000 01", "000"]
            programs = [parse_program(value) for value in sources]
            events = make_stream(programs, jitter=args.jitter, seed=args.seed)
            frames = receive(events)
            result = summary(frames, events, unit_ms=args.unit_ms, source=programs)
            if args.command == "send":
                if args.events is None:
                    raise ChannelError("send requires --events")
                args.events.write_text(
                    json.dumps({"schema": SCHEMA, "unit_ms": args.unit_ms,
                                "events": events}, indent=2) + "\n", encoding="utf-8"
                )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["matches_expected_words"] is False:
            return 2
        return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"T5 STREAM ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
