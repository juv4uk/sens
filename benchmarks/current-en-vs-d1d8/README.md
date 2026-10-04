# Current English surface vs exact-domain lane — CPU evidence

This directory is the CPU evidence lane for #3088 / #3113. Current semantic authority is D1-D4 + D7; any W5/W6/W8 rows are research/mechanical evidence only under #3278.

Its job is deliberately narrow:

```text
English surface
  -> parse
  -> lower
  -> DomainIdentity
  -> execute

exact-domain binary lane
  -> decode
  -> lower
  -> DomainIdentity
  -> execute
```

Both lanes must use the **same compiled helper binary**, the same workload pair,
the same oracle and the same current commit.

The directory/schema identifier `current-en-vs-d1d8` is retained for evidence compatibility only. It does **not** mean D5/D6/D8 are currently ratified semantic domains.

## Fail-closed rule

Timing is allowed only after a workload passes preflight:

1. both lanes parse/decode;
2. both lower to the same span-independent exact-domain trace;
3. no legacy byte-identity AST node is observable after lowering;
4. both execute to the same value/output;
5. any independent expected value/output also matches.

If any check fails, the runner emits **no timing rows** for that workload.

Blocked headline workloads are written to a separate readiness report. They are
never silently removed from the corpus.

## Production corpus status

`workloads.json` contains the eleven #3088 workloads:

`ackermann assoc closures evenodd fib flatten lists loop mapfold member tree`.

At the current reader/runtime boundary they remain explicitly `BLOCKED` by the
already-owned prerequisites such as canonical Number, numeric lexical locals,
the canonical symbol/data boundary and the current one-Core/occupancy/registry
spine.

The benchmark must not invent private syntax to bypass those prerequisites.

## CI-only D3 fixture

`fixtures/d3-smoke.json` is **not** the headline benchmark. It exists only to
prove today that the paired machinery works end-to-end on the common D3 subset.

No performance conclusion may be generalized from this fixture.

## Run

From repository root:

```bash
python3 benchmarks/current-en-vs-d1d8/cpu_runner.py \
  --manifest benchmarks/current-en-vs-d1d8/fixtures/d3-smoke.json \
  --out /tmp/current-en-vs-d1d8.cpu.jsonl \
  --reps 3

python3 benchmarks/current-en-vs-d1d8/validate.py \
  /tmp/current-en-vs-d1d8.cpu.jsonl
```

The runner builds one release helper:

```text
crates/sens/examples/current_en_vs_d1d8_cpu.rs
```

and hashes that exact executable into every evidence row.

## Phases

Current phase names follow the #3116 evidence schema:

- `session` — fresh `Session` plus current Core load;
- `ingest` — English parse or canonical decode;
- `lower` — semantic lowering only;
- `execute` — execute already-lowered expressions in a prepared session;
- `full` — session + ingest + lower + execute;
- `repeated` — repeated execution of already-lowered expressions in one prepared session.

`phase_elapsed_ns` is measured inside the helper around the named phase.

The runner also records whole-helper-process wall/user/sys/RSS separately as
`process_*` metrics. Those process metrics include process startup and
therefore must not be confused with the internal phase timer.

## What this harness does not do yet

It does **not** publish:

- an English-vs-binary ratio;
- a winner;
- a weighted score;
- Cachegrind phase I-refs;
- full-corpus results while readiness is incomplete.

Cachegrind needs phase-scoped instrumentation before its I-ref counts can be
claimed as phase-local. Until that exists, the field is absent rather than
estimated.

Principle: **prove that both surfaces are the same current language first; only
then measure and compare them.**
