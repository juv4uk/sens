# Whole-program domains benchmark (#2003)

Parent benchmark gate: **#1987**. Whole-model accounting: #1973. Corpus: #1962.
Execution: #1988. Carrier: #1989. Framing: #1993. Compiler: juv4uk/cml#397.

> **A beautiful micro-mechanism is not a language win until a whole program
> still benefits.**

Benchmark-only research harness. It edits nothing in the runtime, contracts or
function table.

## What it does

A real (small) Lisp I / Lisp 1.5 evaluator — CAR/CDR/CONS/ATOM/EQ/COND, LAMBDA,
DEFINE, plus a Lisp 1.5 library (`append`, `member`, `equal`, `assoc`, `pairlis`,
`evcon`, `evlis`) and a **meta-circular `eval`** — runs the same bounded
programs through four pipeline variants that differ **only in identity
resolution**:

| variant | resolution strategy | charged |
|---|---|---|
| `flat` | materialise every callable identity once | one table, 1 lookup/call |
| `root-suffix` | walk the root's bit path per call | path length per call, no table |
| `hybrid` | builtin roots fast-path, library callables fall back to a residue table | fallback counted separately |
| `compiled` | precompute a call-site descriptor once | lowering once, zero per-call walk |

## Oracle parity first

Every variant must produce the **identical** result for every workload; a
mismatch is a FAIL, never a metric. The harness asserts this before reporting.

## Phases (counted separately, differential)

`tokenize`, `parse`, semantic `word_decode`, `framing`, `carrier`, semantic
`resolve`, `residue`, `lower` (compiler), `exec`.

## Workloads

`selector-heavy`, `append-list`, `member-equal`, `assoc-pairlis`,
`eval-apply-lisp15` (meta-circular Lisp 1.5), `mixed-residue`. Each is measured
cold (`r1`), warm (`r10`) and hot (`r100`) so one-time preparation is amortised.

## Cost model, stated honestly

These are real counter increments inside the evaluator: **logical steps, not
instruction counts**. Absolute values are model-specific and are not comparable
with a C/Cachegrind lane. `i_refs`, `machine_insts`, `code_bytes`, `cpu`,
`valgrind_version` are intentionally blank and must be joined on `case_id` from
the pinned environment.

## Run

```bash
python3 benchmarks/whole-program-domains/whole_program.py \
    --tsv benchmarks/whole-program-domains/results/<date>/whole_program.tsv
```

## Output schema

Raw rows follow the shared #1987 schema verbatim (33 columns, blank when not
applicable) plus lane-specific columns: `oracle_result` and the nine
`phase_*` counters.

## What this harness does NOT claim

- no instruction counts, no wall-time winner;
- no production carrier/reader/table/compiler edit;
- no semantic validity inferred from the economy of a pipeline variant.
