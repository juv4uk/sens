# #1993 framing-decode benchmark

Research-only benchmark for raw-wire framing cost.

It intentionally stops at an exact decoded handoff:

```text
(bit offset, width)
```

Carrier construction is owned by #1989 and semantic execution by #1988.

The benchmark is a two-axis matrix:

- word codec: Width3+escape vs gamma-only vs candidate S from #3155;
- message boundary: raw exact-bit slice, stop-bit, outer gamma payload length,
  or container-owned valid-bits metadata.

This avoids treating container EOS as though it were a competing semantic word
codec.

Correctness includes all widths 1..8, 9, 16, 32, 64, 65, 128; mixed/corpus
programs; and truncated rejection for every codec/wrapper combination.

Candidate S is benchmarked as transport framing only. For widths 1..8 it
encodes the exact D1..D8 record prefix from #3155. Wider generic benchmark
words use S's BinaryNumber record prefix and canonical no-leading-zero payload.
Local/Sound classes are outside this CPU slice; #3155 owns their injectivity
evidence. No prefix is semantic identity.

Run:

```sh
python3 benchmarks/framing-decode/run.py --smoke --out /tmp/sens-1993
```

Full evidence:

```sh
python3 benchmarks/framing-decode/run.py --samples 3 --cpu 0
```

Cachegrind execution cost is pairwise `full - prepare`, preserving raw sample
values and wire-bit accounting separately.

## Новий повний фізичний Frame3 v2 (11.10.2026)

[SHA-пінований звіт T5/v1/v2: повні байти, Rust encode/decode p50/p95, негативні свідки](results/frame3-v2-2026-10-11.uk.md). Це opt-in S3/02, не новий `.sens` default; короткі файли T5 компактніші, повтори в Frame3 можуть бути компактнішими.

## Нові парні фізичні вимірювання Frame3

[14-корпусний парний бенчмарк T5/S3v1/S3v2, усі фізичні байти та p50/p95 (11.10.2026)](results/frame3-v2-paired-2026-10-11.uk.md). [Повна TSV-таблиця](results/frame3-v2-paired-2026-10-11.tsv). Сирі 1764 семпли прив'язані до SHA в Actions артефакті; рангові байти рахуються окремо від службових і не вважаються фізичним файлом.
