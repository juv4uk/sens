# Semantic-invariance stress benchmark (#2002)

Parent benchmark gate: **#1987**. Semantic invariance: #1969. Equivalence:
#1964 / #1967. Corpus: #1962.

> **The language may notice harder source, but it must not mistake a refactor
> for a new meaning.**

This is a benchmark-only research harness. It edits nothing in the runtime,
contracts or function table.

## What it measures

Two ledgers, kept strictly apart:

| ledger | fields | must |
|---|---|---|
| **semantic** | `canonical_word`, `root`, `path`, `width`, `class` | stay invariant under semantics-preserving refactors |
| **mechanism** | source tokens, definition count, normal nodes, expansion steps | may change freely |

The property under test:

```text
semantically equivalent?  YES  -> canonical identity/path must stay stable
                          NO / UNKNOWN -> no forced equality
```

## Model (bounds stated honestly)

A minimal Lisp I / Lisp 1.5 selector language:

- primitives addressed by exact Function8 code (`car`, `cdr`, `cons`, `atom`,
  `eq`, `cond`, `plus`, `mul`) — the codes are declared once in the harness and
  are **never inferred from a human name**;
- named helper definitions `(def name (lambda (params) body))`;
- selector shorthands (`cadr` == `(car (cdr x))`) — the Lisp I -> Lisp 1.5
  representation axis.

Canonical identity of an observed entry is computed **after** normalisation that
expands helpers **by definition, not by name**, then flattens selector chains to
an exact bit path (`car=0`, `cdr=1`). A call to a helper already on the expansion
stack is an SCC self-reference, recognised **structurally**, so renaming a
recursive helper cannot move its identity.

This is a *model* of the invariance law, not the production canonicaliser. Its
job is to falsify the claim cheaply and deterministically; when the real
domain-graph/carrier canonicaliser lands (#1961/#1962/#1978) this corpus should
be replayed against it unchanged.

## Mutation classes

Semantics-preserving (must NOT drift):

- helper rename; alpha-rename;
- inline helper; factor/unfactor;
- reorder independent definitions;
- whitespace / layout;
- Lisp I -> Lisp 1.5 representation change (`cadr` <-> `(car (cdr x))`);
- alias introduction/removal where identity is proven.

Negative controls (MUST drift): selector swap (`car` <-> `cdr`), constant
change, non-commutative argument swap. A control that does not actually change
the source it is applied to is **skipped, never counted** as evidence.

Each preserving row is a deterministic *composition* of 1..3 applicable classes
plus a layout delta, so every row is a genuinely different program, not a padded
clone.

## Run

```bash
python3 benchmarks/semantic-invariance-stress/invariance_suite.py \
    --tsv benchmarks/semantic-invariance-stress/results/<date>/invariance.tsv
```

Exit status is non-zero if any admitted equivalence drifts or any negative
control fails to drift.

## Output schema

Raw rows follow the shared #1987 schema verbatim (33 columns, blank when not
applicable), plus four lane-specific columns appended at the end:
`mutation_class`, `expectation`, `canonical_drift`, `detail`.

`tree_steps` = normalised nodes, `registry_lookups` = definitional expansion
steps, `semantic_depth` = selector path width, `corpus_sha` = sha256 of the base
source.

## What this harness does NOT claim

- **No CPU metric yet.** `i_refs`, `cpu`, `valgrind_version` are intentionally
  blank: this sandbox has no `gcc`/`valgrind`. Cachegrind I-refs for the same
  corpus must be produced on the pinned environment (owner hardware / Guix) and
  joined on `case_id`; until then no performance claim is made here.
- No wall-time winner. This lane is a *property* lane: its primary result is a
  drift count, which is a mechanical law result, not a timing.
- No production carrier/reader edit.
