# HUMAN-WIRE-1 — direct human binary transport benchmark

Issue: #2642

This is a **MECHANISM** benchmark. It does not create or assign a SENS
semantic domain.

## NEW: T5 multi-program keyed stream emulator (#4447)

Емулятор в `t5_stream.py` передає **послідовність програм**, використовуючи 1τ/3τ імпульси для 0/1, 1τ між бітами, 7τ між доменними словами та **одну тривалу тишу 21τ як завершення кожної програми**. За цією паузою може починатися наступна програма. Файл `.sens` лишається T5 без службового EOS=22.

```shell
python3 benchmarks/human-wire/t5_stream.py demo
python3 benchmarks/human-wire/t5_stream.py send --program '10 001 01' --program '000' --events /tmp/t5-event.json --jitter 0.2
python3 benchmarks/human-wire/t5_stream.py receive --events /tmp/t5-event.json
python3 -m unittest discover -s benchmarks/human-wire -p 'test_t5_stream.py' -v
```

Це механічна симуляція, не готовий радіомодем і не виконавець SENS. До довіреного виконання потрібен канонічний рідер, окрема перевірка цілісності й політика повторів (#2646). [Повне пояснення українською](T5-STREAM-EMU.uk.md).

---
## Question

For the **same complete binary frame**, how much wall-clock time does a human
channel require when transmitted as:

1. hexadecimal characters encoded in International Morse;
2. one-key duration binary (`short=0`, `long=1`);
3. equal-duration two-key binary;
4. fixed-slot press/silence binary with an external clock?

The benchmark deliberately reports **timing units first**. A human sustainable
unit duration is an experimental input, not a theorem.

## Timing model

Reference Morse timing:

- dit = 1 unit;
- dah = 3 units;
- gap inside a character = 1 unit;
- gap between characters = 3 units.

At PARIS 20 WPM, one unit is 60 ms. That fact does **not** imply that a person
can key arbitrary raw bits at the same information rate.

The default duration-binary model uses:

- `0` = 1-unit pulse;
- `1` = 3-unit pulse;
- 1-unit separator between bits.

Therefore one keyed element is not automatically one bit per timing unit.
Payload bit distribution matters.

## Run

```bash
cd benchmarks/human-wire
python3 model.py --hex 00112233445566778899aabbccddeeff --unit-ms 60
```

If the frame includes synchronization, length, checksum/CRC or FEC, include
those bytes in `--hex`. Use `--payload-bits` for the useful application
payload only. This makes framing/check overhead visible in **net payload bit/s**.

JSON:

```bash
python3 model.py --hex 00ff --payload-bits 8 --json
```

## Metrics

The model separates:

- `transmitted_bits`: complete frame size;
- `payload_bits`: useful payload inside that frame;
- `timing_units`: protocol time cost before choosing a human speed;
- `equivalent_frame_bps`: complete-frame information divided by wall time;
- `net_payload_bps`: useful payload divided by wall time.

Do not report checksum as “detects every error”. Real trials must measure
substitution, insertion, deletion, framing loss and retransmission separately.

## Real-key event log

A later physical-keying trial should use append-only CSV:

```text
trial_id,operator,protocol,event_index,onset_ms,offset_ms,decoded,expected,event_class
```

Where `event_class` is one of:

```text
correct
substitution
insertion
deletion
framing-loss
resync
```

Trial metadata must separately record:

```text
frame_sha256
payload_bits
transmitted_bits
unit_target_ms
key/device
decoder_version
training_state
```

Raw events are evidence. A decoder threshold or human skill level is not
language semantics.

## Falsifiers

The “human direct binary channel is better” hypothesis loses if any of these
survive replication:

- direct binary has lower net payload bit/s after framing/retransmission;
- insertion/deletion errors dominate because raw streams are hard to chunk;
- fixed-slot performance depends on machine clocking enough to make the
  “unassisted human” comparison invalid;
- symbolized Morse has enough pattern-level error advantage to beat the raw
  channel despite alphabetic overhead.

The correct outcome may be protocol-dependent rather than a single winner.
