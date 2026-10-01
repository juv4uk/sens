# Cachegrind join (#2045)

Joins pinned-environment instruction counts onto benchmark-lane raw rows by
`case_id`. Parent gate: **#1987**. Feeds whole-model accounting: #1973.

The three lanes (#2002 semantic-invariance, #2001 generator-economy, #2003
whole-program) emit complete raw rows in the shared #1987 schema but with
`i_refs`/`cpu`/`valgrind_version` **blank** — this sandbox has no gcc/valgrind.
This tool performs the required join, and never invents a number.

## Measurement file format (tab-separated, header required)

```text
case_id <TAB> i_refs [<TAB> cpu <TAB> valgrind_version <TAB> guix_channels_sha <TAB> git_sha <TAB> machine_insts <TAB> code_bytes ...]
```

- `case_id` is mandatory (aliases accepted: `key`, `case`);
- every other column is optional and is copied into the joined output when it
  names a #1987 schema column; unknown columns are preserved as extras;
- a row counts as **provenance-complete** only when `cpu`, `valgrind_version`,
  `guix_channels_sha` and `git_sha` are all non-empty — #1987 forbids comparing
  absolute I-refs across CPUs/Valgrind images without provenance.

## Usage

```bash
python3 benchmarks/cachegrind-join/join_cachegrind.py \
    --lane benchmarks/generator-economy/results/20261001/economy.tsv \
    --lane benchmarks/whole-program-domains/results/20261001/whole_program.tsv \
    --measurements measurements.tsv \
    --out joined.tsv [--require-all]
```

- writes `joined.tsv` in the canonical #1987 column order, one row per lane row,
  with a trailing `join_status` column:
  `matched` | `provenance-incomplete` | `unmatched-measurement`;
- prints honest counts: lane rows, matched, provenance-incomplete, unmatched,
  orphan measurements (measurement `case_id`s no lane row referenced);
- exits non-zero with `--require-all` if any lane row has no measurement
  (fail-closed), so an incomplete join can never be mistaken for a complete one.

## Producing the measurement file on the pinned machine

```bash
# per lane case, on the pinned host (owner i5-6400 / Guix image):
valgrind --tool=cachegrind --cache-sim=no --branch-sim=no \
         --cachegrind-out-file=cg.out ./<lane-binary> <case-args>
# take I refs from cg.out (`I   refs:`) as the median of >=3 runs and record the
# case_id, i_refs, cpu, valgrind_version, guix_channels_sha and git_sha.
```

Do not mix absolute I-refs from different CPUs or Valgrind images in one
comparison; the provenance columns exist to make that mistake visible.

## Synthetic example (`example/`)

`example/lane.sample.tsv`, `example/measurements.synthetic.tsv` and
`example/joined.synthetic.tsv` demonstrate the join and its three statuses.

**They are SYNTHETIC.** The `i_refs` values are deterministic pseudo-values and
the provenance fields literally read `SYNTHETIC-*`. They are **not evidence**,
must never be cited as measurements, and exist only so the join is reviewable
and reproducible. Regenerate the input with:

```bash
python3 join_cachegrind.py --lane example/lane.sample.tsv \
    --make-synthetic-example example/measurements.synthetic.tsv
```

## What this tool does NOT do

- generate or estimate any measurement;
- compare absolute I-refs across environments;
- modify lane rows other than filling measurement columns and adding
  `join_status`.
