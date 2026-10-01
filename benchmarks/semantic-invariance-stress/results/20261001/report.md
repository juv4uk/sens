# #2002 semantic-invariance stress — first result

Run: 2026-10-01, `benchmarks/semantic-invariance-stress/invariance_suite.py`.

## Headline

```text
preserving mutations:  1200   canonical drift: 0
negative controls:        6   failed to drift: 0
mechanism tokens (spread over the same rows): 44 .. 78
VERDICT: INVARIANT
```

**Bounded result:** across 1200 deterministic semantics-preserving mutations
(compositions of rename / alpha-rename / inline / factor / reorder / whitespace /
shorthand-spelling / alias-intro) over a selector base and a recursive-SCC base,
the canonical identity — word, root, selector path, width, class — did not move
once. The mechanism ledger moved the whole time (44..78 tokens), i.e. the source
really did change while the meaning did not.

All six negative controls drifted, each on `canonical_word`:

```text
base/swap-selectors      canonical_word 2fd572dcc2df3dcd != 1b4d08f82dc49f82
base/change-constant     canonical_word 2301a0958e062c24 != c649b0876caadaf6
base/swap-cons-args      canonical_word 2fd572dcc2df3dcd != bf69183b56295fbe
recursive-scc/swap-selectors  1b62d4dcc0bca284 != 190961c16225bf38
recursive-scc/change-constant 1b62d4dcc0bca284 != c10d2fae9c416df7
recursive-scc/swap-cons-args  1b62d4dcc0bca284 != 7645e539f515d547
```

## Acceptance checklist (#2002)

- [x] generated mutation suite;
- [x] >= 1000 semantics-preserving mutations (1200);
- [x] recursive / SCC fixture;
- [x] zero canonical drift on admitted equivalences;
- [ ] CPU / compiler cost reported separately — **pending pinned environment**
      (`i_refs`/`cpu`/`valgrind_version` blank in the raw rows; join on `case_id`);
- [x] negative / unknown controls preserved (controls drift; unknown equivalences
      are never forced equal — the harness has no forced-equality path).

## Falsifiers from the issue — status

| falsifier | status |
|---|---|
| helper rename changes canonical word | not observed (600 rename rows) |
| helper insertion changes bit width/path | not observed (inline/factor rows) |
| SCC-internal refactor remints identity | not observed (recursive-SCC rows) |
| source order changes allocation | not observed (reorder rows; allocation field pending) |

## Provenance

```json
{"python": "3.12.13", "machine": "x86_64", "platform": "Linux ... x86_64", "mechanism_tokens_min": 44, "mechanism_tokens_max": 78}
```

Raw rows: `invariance.tsv` (1206 rows, shared #1987 schema).

## Honest limits

This is a model of the invariance law, not the production canonicaliser, and it
carries **no CPU metric yet**. It establishes the *property* (refactors do not
remint meaning) on a bounded, deterministic corpus; it does not establish any
performance ordering, and it does not ratify a carrier or a domain model.
