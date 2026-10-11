# #1989 identity-carrier benchmark

Research-only mechanism benchmark. It does not choose SENS semantics or a
production representation.

Candidates:

- `sens8`: current u8/Sens8 mechanism baseline, width 8 only;
- `inline64`: explicit width + 64-bit inline payload;
- `bitbytes`: explicit width + heap byte payload;
- `spill`: small-inline through width 64, heap spill above 64.

The benchmark keeps exact width as part of identity and never round-trips
through text.

## Metrics

`run.py` uses the repository Cachegrind convention:

```text
valgrind --tool=cachegrind --cache-sim=no
```

For each row it runs identical `prepare` and `full` processes and reports:

```text
operation I refs = median(full I refs) - median(prepare I refs)
```

Manual allocation counters count allocations caused inside the operation loop;
candidate preparation is excluded.

## Smoke

```bash
python3 benchmarks/identity-carrier/run.py --smoke
```

The smoke intentionally focuses on:
- width-8 equality against Sens8;
- the 64 -> 65 small-inline spill boundary;
- width-128 heap equality/prefix.

A full matrix is available by omitting `--smoke`; it is intended for CI or a
dedicated benchmark run.

Raw output follows the #1987 evidence discipline and lands in
`docs/research/1989-carrier-bench.tsv`.

Do not compare these I-ref numbers with another Valgrind/Guix environment
without matching provenance.
