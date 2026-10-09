# D10 symbolic-AI donor audit — 2026-10-09

**Status:** research evidence only; D10 remains unratified. This file does not add selected inventory rows, coordinates, or residents.

## Frozen source snapshot

- Current inventory: `knowledge/d10-v1-semantic-inventory.json`, blob `65014431ac3e64633cd0be3630cfafc5e7a9aea3`.
- Current accounting: **634 selected**, **256 law-forced coordinates**, **378 selected/unplaced**, **390 not yet selected**, **0 ratified residents**.
- Self-host reasoning harvest: `knowledge/d10-selfhost-reason-harvest-v1.json`, blob `1d6eb5aaefde15464dc7a5eb5093d706b6537b18`.
- Donor implementation: `lib/reason.lisp`, blob `dadc52a2f40f2f30ad77642898afb81980044c08`.
- Canonical proposal workflow: `docs/architecture/D10-PROPOSAL-WORKFLOW.uk.md`. Proposal ledger remains governed by #4463 and the selected→ledger gate in PR #4894. This audit intentionally does not claim `NO-MATCH` against D1–D9.

## Symbolic-AI coverage matrix

| Interest / behavior | Evidence already present | Disposition now | Why / falsifier |
|---|---|---|---|
| Backward-chaining rule proof | `PROVE-RULE` at `lib/reason.lisp:243`; harvest row `PROVE-RULE` | **DUPLICATE — do not add** | It already has a selected research row. A new synonym or donor implementation is not a new root. Falsifier for equivalence: demonstrate a distinct observable proof/substitution law, not a different algorithm. |
| Proof-state goal expansion | `PROVE-GOAL-STATE` at `lib/reason.lisp:281` | **DUPLICATE — do not add** | Existing selected row explicitly carries forward substitution and proof sequence. A new candidate needs a behavior that cannot be obtained by this transition plus existing list/unification laws. |
| Ordered proof result aggregation | `MAP-GOAL-RESULTS` at `lib/reason.lisp:295` | **DUPLICATE — do not add** | Already selected; preserving source order is part of its current law. Any proposed result-map helper that only repackages this sequence is a projection. |
| Proof-rule usage counting | `COUNT-USAGE` at `lib/reason.lisp:385`; `MERGE-USAGE` at `lib/reason.lisp:378` | **DUPLICATE — do not add** | Both are already in the harvest. Counts are finite association-list data; host metrics/telemetry are not additional semantics. |
| Claim/evidence/provenance graph | Inventory contains `MAKE-CLAIM`, `MAKE-EVIDENCE`, `EVIDENCE-CLAIM-REF`, `EVIDENCE-SOURCE-REF`, `ADVICE-CONFLICT-PROOF` | **DUPLICATE FAMILY — audit roots, not names** | The existing epistemic family already covers record construction, references, and structured conflict evidence. `PROVENANCE-CHAIN` was previously classified as a projection onto this family. A new root must prove a new transition law, not just nest existing records. |
| Explain a proof to a human | `lib/reason.lisp` documents `reason` as returning substitution/proof pairs; `explain-proof` is a print/display-oriented helper in the current library | **HOLD — effect/value boundary unresolved** | Printing text is not by itself a language-visible symbolic law. Positive witness for a future review: produce a finite structured explanation value with stable rule IDs, premises, substitutions, and source order, without I/O. Falsifiers: output is only formatted text; it is reconstructible from existing proof nodes without a distinct contract; or it loses source order/provenance. |
| Natural-language answer narration | Inventory already contains `NARRATE-PROVED-OUTCOME` and `NARRATE-INVALID-OUTCOME-SHAPE` | **DUPLICATE — do not add** | Narration and invalid-outcome shape already have selected rows. Do not rename the explanation helper into another narration candidate. |
| Lexical environment and capture-safe variable handling | Harvest contains `ENV-LOOKUP`, `RENAME-VARS`, `MY-FORM-REFERENCES-NAME?`, `MY-PARAMS-BIND-NAME?` | **DUPLICATE FAMILY — no new root yet** | Existing rows cover lexical shadowing, variable renaming and source-form binding analysis. Any new metaprogramming candidate must demonstrate an observable law outside those contracts, with quoted forms and nested lexical shadows as negative controls. |
| Forward chaining / multi-match rules | Inventory contains `FIRE-RULES-MULTI` and `FIRE-RULE-MULTI` | **DUPLICATE FAMILY — no new root yet** | Existing forward-rule family covers firing one or many matches. A new agenda/conflict-resolution candidate needs a source-backed, externally observable selection/order law; scheduler implementation alone is mechanism. |
| Chess successor ranking / minimax | Prior exact-measurement/hobby intake records `STABLE-ARGMAX-STATE-SUCCESSOR` as HOLD/derivable-library | **HOLD — derivability attack first** | Need a donor-pinned state transition and deterministic tie law. If the behavior is only `map` successors + score + `argmax`, do not mint a Core root. Falsifier: ties, invalid transitions, or mutation of the input state expose a law not represented by the composition. |
| Astronomy coordinate conversion | Prior intake records `XYZ-TO-RADEC` as HOLD / math-library boundary | **HOLD — domain boundary** | Need exact coordinate conventions, units, origin/axis, singularity behavior and a universal Core-Math argument. Falsifier: result changes under convention or requires domain-specific ephemeris policy. |
| Signal phase unwrapping / finite convolution | Existing peer-owned research records already claim these lines; phase donor evidence was previously marked incomplete | **PEER-OWNERSHIP GATE** | Do not duplicate another worker's candidate. Reopen only after the owner supplies a pinned donor and exact wrap/tie/boundary laws, then compare against the existing record. |
| Pāṇini / Sanskrit grammar | `knowledge/d10-crossrepo-panini-v1.json` already selects pratyāhāra resolution/membership and phonological transformation candidates | **DUPLICATE — extend evidence, not names** | Do not add named sutras, corpus rows, or special-case examples as functions. New candidates must be generic executable operations with a distinct law. |

## Concrete next research action

The highest-value symbolic-AI gap is not another `PROVE-*` name: it is to establish whether **structured proof explanation is already fully derivable from the proof values**.

1. Trace `reason` result shape, proof-node construction, and `explain-proof` call sites at the pinned donor SHA above.
2. Write two positive examples and one falsifier: (a) one rule proving one goal; (b) a two-premise proof preserving source order; (c) a failed goal or reordered rule corpus must not fabricate or reorder proof evidence.
3. Compare the result against `PROVE-RULE`, `PROVE-GOAL-STATE`, `MAP-GOAL-RESULTS`, `COUNT-USAGE`, `MAKE-CLAIM`, `MAKE-EVIDENCE`, and `NARRATE-PROVED-OUTCOME`.
4. If structured explanation is only composition of existing values, record **DERIVED** and stop. If it has a distinct observable language law, open an owner review with a current full D1–D9/D10 dedup and donor provenance. Until then: no ledger row, no coordinate, no ratification.

## Guardrails

- A selected candidate is not an implementation guarantee and is not a ratified resident.
- Do not use stale inventory counts from docs or older harvests as current truth.
- Do not claim D1–D9 `NO-MATCH` without checking the current nine domains at a pinned SHA.
- Do not change the inventory count, proposal ledger, coordinate assignment, or ratification state from this research note.
