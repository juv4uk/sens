# Compact mixed-boundary index benchmark (#2265)

This research-only benchmark continues the #2247/#2264 packed-payload work.

It asks a different question:

> once exact-width words are densely packed, what metadata is worth keeping if
> callers need random word access without decoding the whole payload?

Every candidate must recover the exact pair:

```text
(width, bits)
```

for the same deterministic query corpus before Cachegrind evidence is accepted.

## Candidates

- `formula` — fixed-width negative control: offset = index × width, zero boundary metadata.
- `usize` — one host `usize` start offset per word plus final end offset.
- `u32` — one 32-bit start offset per word plus final end offset.
- `cp8-K` — one u32 checkpoint every K words + one width byte per word.
- `cp3-K` — one u32 checkpoint every K words + packed 3-bit `width-1` stream.
- `cache2` — decoded hot cache with one width byte + one raw byte per word.

For `usize` / `u32`, width is recovered from adjacent offsets. The benchmark
therefore does not silently grant those candidates a free width stream.

For `cache2`, the packed payload may be cold/discarded after decode, so active
hot bytes are the two-byte exact cache only.

## Accounting

The runner separates:

- packed payload bytes;
- candidate metadata bytes;
- active query working-set bytes;
- index preparation I refs;
- query I refs/access;
- D1 and LLd misses;
- local width-stream steps/access;
- exact provenance.

Preparation is subtracted from query measurements. Correctness runs happen
outside the measured Cachegrind path.

The report marks the non-dominated Pareto set on:

```text
(active bytes, query I/access)
```

only. It deliberately computes no weighted winner.

## Checkpoint sweep

The canonical research sweep is:

```text
K = 8, 16, 32, 64, 256
```

A smaller K spends more checkpoint bytes to reduce local width scanning.
A larger K saves metadata but scans more width cells per random lookup.

## Boundaries

This benchmark does not:

- choose #2189 framing;
- define EOS;
- turn width metadata into language semantics;
- change `BitPacker`;
- claim a compact index is canonical;
- infer a whole-program source distribution from synthetic schedules.

A framing/index mechanism can consume these results later, but it must still
satisfy exact-width identity and the framing laws independently.
