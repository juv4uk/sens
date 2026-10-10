# SENS Framed-3 — bounded research witness (NOT .sens)

**2026-10-10. Status: experimental, not ratified.** The first D2 word
'10' opens the program; the last D2 word '01' closes it. This profile
applies ONLY to a single outer list: SENS otherwise permits atomic and
multi-form top-level programs. No runtime or canonical .sens T5 is changed.

## Bits, trits, bytes, and EOF

- D2 10 and 01 are exact two-bit words. Between binary source words,
  T5 inserts one ternary *transport* separator 2 (not before the first
  word or after the last).
- T5 may end with 0..4 padding 2 trits, because five trits fill a byte.
  EOF supplies physical byte length, not a semantic end-of-program token.
- Framed-3 enumerates strings anchored 10 2 ... 2 01 without adjacent 22.
  It ranks each length class into a minimal *byte-count bucket*.
  The physical byte count identifies exact trit count with no padding.
- Nested D2 10 and 01 words stay intact. An internal 01 only closes one
  nested level. Complete D2 syntax is owned by the canonical SENS reader,
  **not** by this conservative Python transport proof.
- This is one WHOLE 128-trit-bounded frame, NOT restartable 3-byte streaming
  blocks. Network/FPGA requires a separately proved end-of-frame protocol.

## Capacity upper bound

| Bytes | Trit lengths | Count of possible framed strings | 2^(8*bytes) |
|---:|:---|---:|---:|
| 1 | 5–11 | 139 | 256 |
| 2 | 12–17 | 57,504 | 65,536 |
| 3 | 18–22 | 8,716,160 | 16,777,216 |
| 4 | 23–28 | 3,639,777,792 | 4,294,967,296 |
| 5 | 29–33 | 551,698,345,984 | 1,099,511,627,776 |

The ranking count is an intentionally conservative SUPERSET of actual
D2 syntax and D1–D9 word constraints. Encoder/decoder reject invalid
words, excess nesting closure, and unused codepoints.

## Reproduce from repo root

    python3 research/framed3/research_codec.py
    python3 -m unittest discover -s research/framed3 -p 'test_*.py' -v

| Exact D2 word sequence | T5 | Framed-3 | Experimental bytes |
|---|---:|---:|---|
| 10 01 | 1 B | 1 B | 00 |
| 10 001 00 000 01 | 4 B | 2 B | 23 d0 |
| 10 100 00 10 111 00 1 00 0 01 01 | 7 B | 5 B | 21 09 89 5e b5 |

These bytes ARE NOT standard .sens T5 bytes and may coincide with bytes
meaning something else under T5. Never silently switch the existing loader.
Roundtrips and size wins do NOT prove canonical Rust reader parity,
runtime speed, corruption detection, or arbitrary-length streamability.
Checksum/error framing is independent follow-up research.

Issues: #5293 (Rust parity), #5294 (release benchmarks), #5295
(streams/EOF), #5296 (information theory), and existing #4445 (codec race).
Integrate the research stand only; changing canonical wire requires separate
ratification and CI evidence.
