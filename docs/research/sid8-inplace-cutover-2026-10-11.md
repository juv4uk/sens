# SID8 → D1–D9: in-place Lisp source migration (2026-10-11)

This is an execution and blocker ledger, not a claim that the repository is fully migrated.

## Exact completed changes

- **15,898 audited SID8 occurrences replaced** in **86 existing `.lisp` files** in the earlier audited cohorts; three additional local MAP replacements are recorded under blocker 2 below. (library, executable experiments, benchmarks and service programs), on **main**.
- No new Git branches and no `.sens` creation.
- Baseline legacy correspondence: `knowledge/sens8-current-coverage-v1.json` (256 historic cells).
- Only the 171 unambiguous, ratified current targets were used automatically.
- Generic source changes were limited to executable list heads, excluding quoted code, comments, strings and arbitrary data.
- Historical identity tables `lib/core1.lisp` (405) and `lib/meta-eval.lisp` (1263) were treated separately: function-ID data were also rewritten to keep discriminator tables coherent; the latter's historic DEFMACRO identifier was uniquely resolved in the `my-defmacro-name?` context to D5:00011 MACRO.
- The embedded bootstrap `lib/macro.lisp` was **restored**, and its 32 tentative substitutions are **excluded** from the count after Hosted CI exposed an actual runtime dispatch error (exact-width code interpreted as a number, not callable). Never describe that file as migrated.

| Cohort | Migrated counts |
|---|---:|
| unify-observe, result-status, fs, process, tcp, si-derived, content-store | 307 |
| canon, guard, life-1-scheduler, epistemic, quantity, utf8 | 1508 |
| island-lowering, si, translation, meta-eval-first-class, meta-eval-mutual | 807 |
| persistent-map, persistent-vector, unify, reason, lisp-fs | 1281 |
| narrate, understand | 255 |
| compiler-nucleus, mechanism-selector, clips-import, core3 | 863 |
| core1 with its function-identity data | 405 |
| meta-eval with its function-identity data | 1263 |
| core1-compiler-prelude, core1-compiler-sid-resolver, core1-sid8-bootstrap-overlay | 16 |
| `lib/yantra.lisp` — including 4 source-proven one-list D6 MAP calls | 439 |
| `lib/linter.lisp` — including 8 source-proven one-list D6 MAP calls | 407 |
| Five active benchmark programs: arithmetic, closures, lists, parser, recursion | 35 |
| `lib/bridge/prolog-to-datalog.lisp` | 64 |
| Three executable experiments: Core4 logic, predicate carrier, function genealogy | 546 |
| Five scripts: fixtures-for-tier, gen-functions, build-constitution, build-inventory, check-domain-table-readable | 497 |
| Five scripts: check-core1-compiler-sid-resolver, check-core3-profile-contract, check-function-table-mechanisms, check-island-math-evidence, check-kernel-abi-transport-boundary | 804 |
| Five scripts: check-repo-tooling-inventory, generate-meta-semantic-registry, generate-rust-evaluator-dispatch, generate-rust-function-signatures, generate-rust-profile-mechanism-routes | 903 |
| Five scripts: generate-rust-semantic-registry, oracle-batch, machine-authority-guard, program-symbol-table, release | 616 |
| Three scripts: semantic-authority-guard, symbol-table, перевірити-український-профіль | 340 |
| Seven additional scripts / executable experiment (23 source-proven single-list MAP calls) | 1868 |
| Five machine dispatcher, u64 effect, capability and lowering sources | 590 |
| Six x86-64 admission, atoms, encoding, operand, profile and projection sources | 2084 |
| **Total** | **15898** |

## Known fail-closed blockers

1. `00001010` historical DEFMACRO: owner-audited composite `D5:00011 MACRO + D4:0011 DEFINE`; no proven general one-word rewrite. Seen in `lib/forward.lisp`, `lib/world.lisp`, `lib/knowledge.lisp`, `lib/core.lisp`, and `lib/core4.lisp`.
2. `00110111` MAP has two current matches, D6:101000 and D8:11000101; the global legacy mapping remains unresolved. Source-local one-list proofs now migrate 15 calls to D6:101000: 4 in `lib/yantra.lisp`, 8 in `lib/linter.lisp`, 1 in `lib/knowledge.lisp`, and 2 inside `lib/core.lisp`'s `let` expansion. Regression: `tests/test_sid8_d6_map_source_cutover.py`. D8 MAP remains distinct; do not change the normative historical map.
3. Internal helper cells 00011001, 00011111, 00100000, 01000111 have no ratified semantic residents; seen in `lib/core.lisp` / `lib/core4.lisp`.
4. Historical MONO-NS, UNIX-TIME-NOW, NTP-QUERY-RAW await D10 successor authority, including in `lib/time.lisp`.
5. Embedded `lib/macro.lisp` **must not** be mechanically rewritten: Hosted CI `38163596334` confirmed runtime error `expression is not callable` after replacement; file was restored on main in commit `c5253cf7`. Fix the interpreter/domain callable dispatch with an executable witness before retrying that file.
6. Preserve historical audit and benchmark artifacts, and do not silently alter non-head 8-bit data until their identity role has proof.

## 2026-10-11 context-specific D6 MAP witness

- Four historical MAP calls in `lib/yantra.lisp` map exactly one collection via `json->tool-call`, `encode-tool-call`, `encode-message`, or `tc-id` ⇒ D6:101000. Commit [`87a66ea`](https://github.com/juv4uk/sens/commit/87a66ea04d19a0c2256251a275697bc7249215b2), 439 source-level substitutions. Hosted CI, parentheses and safe-batch migration checks PASS on that commit.
- Eight historical MAP calls in `lib/linter.lisp` map one `bindings` or `params` list through a lambda ⇒ D6:101000. Commit [`7000e91`](https://github.com/juv4uk/sens/commit/7000e9122341cacecdcde9f7f1fa11baf9a450d2), 407 substitutions. Hosted CI, parentheses and safe-batch checks PASS on that commit. Historical `head 00001010` DEFMACRO datum deliberately retained; this is data, not a function call head.
- Source-local assertions: `tests/test_sid8_d6_map_source_cutover.py`. The audited old `00110111` globally still has two same-named D6/D8 successors, so **do not edit the normative old-coverage mapping to one successor**.
- This is **source-level replacement only**; 12 green MAP source sites do not independently prove cross-oracle runtime equivalence or full physical file admission.

## 2026-10-11 expanded source migration cohort (32 more files)

- Directly on `main`: 32 source files beyond the earlier 36, 3,805 further historical SID8 executable-head substitutions; verified via GitHub compare against main commit `768b8d6` through `394ba53` showing exactly **32 changed `.lisp` files** and 32 atomic source commits.
- Changed categories: 5 active small benchmarks; 1 `lib/bridge` executable; 3 executable research experiments (non-archived); 23 Lisp tooling, guard, code-generation, release and verification scripts.
- Historical source code used as **data** is intentionally not modified by the head-only migrator. Examples of preserved historical data: `experiments/function-genealogy.lisp` and `scripts/check-core1-compiler-sid-resolver.lisp`. Never treat those literal old IDs as callable heads without semantic evidence.
- **Does not touch** `benchmarks/sens-surface/results/`, archived source snapshots, ratification contracts or versioned historical proof fixtures; changing them would falsify earlier evidence.
- Last source cohort [Hosted CI PASS](https://github.com/juv4uk/sens/actions/runs/38166695598) on commit `394ba53`. Pre-existing independent [T5 inventory M0 FAIL](https://github.com/juv4uk/sens/actions/runs/38166695668) records a live/manifest drift; no claim of overall green CI or all-oracle executable semantic parity.
- No `.sens` outputs, branch creation, or retrospective historical rewriting was performed.

## 2026-10-11 next wide direct-to-main cutover (18 files)

- **18 further original `.lisp` files, 4542 SID8 executable heads** replaced in place, without creating a branch or `.sens` file. No generated encoder coverage tables or immutable benchmark history modified.
- 7 scripts/experiments: `scripts/build-dependency-classification.lisp` (496), `scripts/check-core4-predicate-answer-scale.lisp` (182), `scripts/check-core4-predicate-answer-boundary.lisp` (61), `experiments/probabilistic-decision-jev-like.lisp` (264), `scripts/generate-function-table.lisp` (209), `scripts/generate-uk-surface-audit.lisp` (285), `scripts/verify-repo.lisp` (371) = 1868 heads. In this set **23 formerly ambiguous historical MAP heads** are verified to accept exactly one sequence and therefore use **D6:101000**. The D8 MAP remains distinct and the global audit map is unchanged.
- 11 machine sources: `lib/machine/dispatch/native-first-coverage.lisp` (2), `lib/machine/dispatch/native-first-parity.lisp` (76), `lib/machine/effects/u64.lisp` (134), `lib/machine/capability-axis.lisp` (14), `lib/machine/lowering/semantic-x86-64.lisp` (364), `lib/machine/admission/x86-64.lisp` (582), `lib/machine/atoms/x86-64.lisp` (482), `lib/machine/encoding/x86-64.lisp` (640), `lib/machine/operands/x86-64.lisp` (172), `lib/machine/profile/minimal-runtime-x86-64.lisp` (139), `lib/machine/projection/x86-64.lisp` (69) = 2674 heads. The machine evidence generators remain untouched.
- New source guard: `tests/test_sid8_broad_source_cutover.py` and `tests/test_sid8_machine_source_cutover.py` plus dedicated CI workflows. [Broad source regression PASS](https://github.com/juv4uk/sens/actions/runs/38167970204), [machine source regression PASS](https://github.com/juv4uk/sens/actions/runs/38168282905), [Hosted CI PASS](https://github.com/juv4uk/sens/actions/runs/38168282909). These are **not** full historical-old-vs-new semantic oracle or physical T5 admission claims.

## Additional exact-domain source cohort — 2026-10-11 late cutover

The previously published 86-file / 15,898-occurrence census above is an earlier
baseline, **not** a live all-repository completion count. The following source
changes were independently verified by Git object write receipts after that
baseline and must not be silently double-counted:

- Five Lisp policy records: `knowledge/foreign-tools-census.lisp`,
  `knowledge/language-policy.lisp`, `knowledge/swarm-legacy-deprecation.lisp`,
  `knowledge/swarm-no-live-callers-audit.lisp`,
  `knowledge/file-authority-policy.lisp`: 10 historical executable DEFINE/QUOTE
  heads moved into ratified D4:0011 / D3:001 in a single main commit
  `9e78972c866461dc36736d2b58dc10ec2c51d3d7`. Historical quoted data remained intact.
- `lib/machine/lowering/semantic-effects.lisp` (13), and
  `examples/ukrainian-greeting.lisp` (14): 27 additional audited call-head
  replacements, main commit `bc47ca0926dc764581463be53603625dedda90de`.
- `knowledge/guard-runtime-policy.lisp`: 36 additional audited source heads
  replaced, with the unique fallback host `t` condition mapped explicitly to
  admitted D1 `1` in predicate position. Main commit
  `ea37c962d6b3e151ecb73d5ec706875040869ad9`.
- **Net new in this cohort: 8 modified original Lisp files, 73 former SID8 call
  heads replaced, 1 explicit host-T to D1 predicate correction.**
- Independent positive/negative tests:
  `tests/test_d3_legacy_logic_guard.py`,
  `tests/test_sid8_policy_source_cutover.py`,
  `.github/workflows/sid8-policy-source-cutover.yml`.
  These are source-form tests, **not** runtime semantic parity certificates.
- Stale machine-integrity guard detected by CI: it demanded 15 historical
  `(00001001 ...)` definitions despite all three full machine sources having
  migrated to `(0011 ...)`. Commit
  `f665a1b7323bf35ed123db2210399943683b7385` updated the exact required
  markers and added a negative test that old SID8 cannot satisfy those markers.
  The independent `lisp-paren-balance` workflow passed on that commit.

### Intentionally held sources

- `knowledge/guard-fact-policy.lisp` and
  `scripts/{enforce-island-math-evidence,enforce-function-table-mechanisms,semantic-authority-guard-enforce}.lisp`
  still carry legacy COND clauses, expected-result fields or host truth values.
  These cannot be made exact two-field D3:110 by only changing the eight-bit word.
- `lib/function-table-mechanisms.lisp` stores a table of historical identities.
  Its row heads are *data*, not executable call heads; do not blindly shorten them.
- `lib/machine/block.lisp` retains immutable historical source provenance for
  the independent physical admission proof and must not be rewritten without
  that proof. `racket/boot/core.lisp` contains composite DEFMACRO and likewise
  requires a separate cutover.
- The new strict D3 scanner reports existing historical logic as blockers; do
  not weaken it to obtain a superficial green CI or claim old/new full parity.

## Safety of completion claims

- Syntax/Hosted CI green on intermediate migrated cohorts; T5 file-authority and migration readiness gates separately remain fail-closed on historical corpus.
- No claim of semantic equivalence for all rewrites yet; independent oracle/runtime parity remains required.
- Do not call this a completed all-repository SID8 retirement, and do not delete the old correspondence ledger while unresolved cells remain.
