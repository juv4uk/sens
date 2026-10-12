# In-place SID8 → ratified domain words: executable Lisp witness cohorts

**State:** source-only migration, **not** a physical T5 admission or an executable-oracle parity certificate. Changes are on `main` with no new branches and no generated `.sens` files. Do not rewrite immutable `*-before.lisp` golden snapshots.

Historical identity source: `knowledge/sens8-current-coverage-v1.json`. Only a single audited ratified D1–D9 successor may replace an **executable call head**. The original Git blobs remain accessible for independent source comparisons.

## Committed work: 29 original .lisp files, 2806 actual substitutions

| Cohort | Original .lisp witness | Replaced call heads |
|---|---|---:|
| 1 | content-store-authority-witness | 31 |
| 1 | life-1-contract-witness | 134 |
| 1 | life-1-scheduler-witness | 72 |
| 1 | meta-semantic-registry-witness | 113 |
| 1 | narrate-outcome-authority-witness | 56 |
| 1 | persistent-vector-balance-witness | 23 |
| 1 | process-load-witness | 7 |
| 1 | prolog-datalog-bridge-witness | 11 |
| 1 | reason-index-authority-witness | 51 |
| 1 | scientific-constant-knowledge-projection-witness | 21 |
| 1 | world-transition-witness | 38 |
| **1** | **Subtotal, 11 sources** | **557** |
| 2 | machine-register-width-witness | 77 |
| 2 | x86-64-instruction-set-witness | 40 |
| 2 | structural-observation-contract-witness | 184 |
| 2 | native-first-coverage-ledger-witness | 240 |
| 2 | native-first-dispatch-witness | 22 |
| 2 | native-first-execution-witness | 20 |
| 2 | native-first-parity-witness | 18 |
| 2 | native-first-totality-witness | 14 |
| 2 | mechanism-selector-1047-witness | 48 |
| 2 | mathematical-result-taxonomy-witness | 143 |
| 2 | machine-current-gpr-atoms-witness | 432 |
| 2 | translation-symbol-boundary-witness | 63 |
| **2** | **Subtotal, 12 sources** | **1301** |
| 3 | decimal-comma-authority-witness | 65 |
| 3 | exact-quantity-arithmetic-witness | 89 |
| 3 | island-compat-witness | 152 |
| 3 | island-lowering-1048-witness | 44 |
| 3 | postcore-peer-materialization-witness | 406 |
| 3 | yantraos-bridge-witness | 192 |
| **3** | **Subtotal, 6 sources** | **948** |
| **ALL** | **29 in-place .lisp sources** | **2806** |

Paths are `tests/fixtures/<witness>.lisp`.

## Fail-closed evidence

- Tests: `tests/test_sid8_witness_source_cutover.py`, `tests/test_sid8_witness_second_cohort.py`, and `tests/test_sid8_witness_third_cohort.py`.
- CI: `.github/workflows/sid8-witness-source-cutover.yml`, running all three test files.
- Each case independently obtains the **original immutable Git blob** and compares it to the current source with the existing canonical Lisp parser in `scripts/audit_lisp_migration_edits.py`. It rejects list-shape, binding, string, quoted-data, or non-head alterations. It also checks exact per-file token substitution counts, total 2806.
- For `x86-64-instruction-set-witness.lisp`, 60 apparent 8-bit list heads were found, **but only 40 were executable**. The other 20 occurred in quoted data and were deliberately left unchanged.
- Cohorts 1 and 2 were verified with GitHub Actions [successful lexical/AST source checks](https://github.com/juv4uk/sens/actions/runs/38191263390). The expanded 29-source check is [run 38191448405](https://github.com/juv4uk/sens/actions/runs/38191448405).

## Not yet proved / exclusions

- AST-preservation `LEXICAL_CONTEXT_ONLY` is **not** a semantic equivalence proof, nor independent physical T5 executable admission.
- General `lib/core.lisp`, `lib/core4.lisp`, `lib/world.lisp`, `lib/forward.lisp`, and D10 source-only candidates retain unresolved compound operations or explicit donor-machine semantics. Do **not** coerce `DEFMACRO`, `MAP`, D10 candidate cells, or unmapped internal helper words to a guessed domain resident.
- Historical `tests/fixtures/*-before.lisp` and archived benchmark/provenance snapshots are intentionally excluded from bulk replacement.
- General Hosted CI was already failing on source/oracle and legacy logic checks at pre-cohort `b07c24d1...` (run 38190472154); do not report those gates as passing because a scoped witness audit passed.
