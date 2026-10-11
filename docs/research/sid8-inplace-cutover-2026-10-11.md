# SID8 → D1–D9: in-place Lisp source migration (2026-10-11)

This is an execution and blocker ledger, not a claim that the repository is fully migrated.

## Exact completed changes

- **7551 SID8 occurrences replaced** in **36 existing `.lisp` library files**, on **main**.
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
| **Total** | **7551** |

## Known fail-closed blockers

1. `00001010` historical DEFMACRO: owner-audited composite `D5:00011 MACRO + D4:0011 DEFINE`; no proven general one-word rewrite. Seen in `lib/forward.lisp`, `lib/world.lisp`, `lib/knowledge.lisp`, `lib/core.lisp`, and `lib/core4.lisp`.
2. `00110111` MAP has two current matches, D6:101000 and D8:11000101. Still unresolved in other sources including `lib/knowledge.lisp` and `lib/core.lisp`. All 12 occurrences in `lib/yantra.lisp` and `lib/linter.lisp` have been source-proven as one-list MAP and migrated to D6:101000; D8 MAP remains distinct.
3. Internal helper cells 00011001, 00011111, 00100000, 01000111 have no ratified semantic residents; seen in `lib/core.lisp` / `lib/core4.lisp`.
4. Historical MONO-NS, UNIX-TIME-NOW, NTP-QUERY-RAW await D10 successor authority, including in `lib/time.lisp`.
5. Embedded `lib/macro.lisp` **must not** be mechanically rewritten: Hosted CI `38163596334` confirmed runtime error `expression is not callable` after replacement; file was restored on main in commit `c5253cf7`. Fix the interpreter/domain callable dispatch with an executable witness before retrying that file.
6. Preserve historical audit and benchmark artifacts, and do not silently alter non-head 8-bit data until their identity role has proof.

## 2026-10-11 context-specific D6 MAP witness

- Four historical MAP calls in `lib/yantra.lisp` map exactly one collection via `json->tool-call`, `encode-tool-call`, `encode-message`, or `tc-id` ⇒ D6:101000. Commit [`87a66ea`](https://github.com/juv4uk/sens/commit/87a66ea04d19a0c2256251a275697bc7249215b2), 439 source-level substitutions. Hosted CI, parentheses and safe-batch migration checks PASS on that commit.
- Eight historical MAP calls in `lib/linter.lisp` map one `bindings` or `params` list through a lambda ⇒ D6:101000. Commit [`7000e91`](https://github.com/juv4uk/sens/commit/7000e9122341cacecdcde9f7f1fa11baf9a450d2), 407 substitutions. Hosted CI, parentheses and safe-batch checks PASS on that commit. Historical `head 00001010` DEFMACRO datum deliberately retained; this is data, not a function call head.
- Source-local assertions: `tests/test_sid8_d6_map_source_cutover.py`. The audited old `00110111` globally still has two same-named D6/D8 successors, so **do not edit the normative old-coverage mapping to one successor**.
- This is **source-level replacement only**; 12 green MAP source sites do not independently prove cross-oracle runtime equivalence or full physical file admission.

## Safety of completion claims

- Syntax/Hosted CI green on intermediate migrated cohorts; T5 file-authority and migration readiness gates separately remain fail-closed on historical corpus.
- No claim of semantic equivalence for all rewrites yet; independent oracle/runtime parity remains required.
- Do not call this a completed all-repository SID8 retirement, and do not delete the old correspondence ledger while unresolved cells remain.
