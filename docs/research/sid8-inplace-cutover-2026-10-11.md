# SID8 → D1–D9: in-place Lisp source migration (2026-10-11)

This is an execution and blocker ledger, not a claim that the repository is fully migrated.

## Exact completed changes

- **6705 SID8 occurrences replaced** in **34 existing `.lisp` library files**, on **main**.
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
| **Total** | **6705** |

## Known fail-closed blockers

1. `00001010` historical DEFMACRO: owner-audited composite `D5:00011 MACRO + D4:0011 DEFINE`; no proven general one-word rewrite. Seen in `lib/forward.lisp`, `lib/world.lisp`, `lib/knowledge.lisp`, `lib/core.lisp`, and `lib/core4.lisp`.
2. `00110111` MAP has two current matches, D6:101000 and D8:11000101. Seen in `lib/knowledge.lisp`, `lib/linter.lisp`, `lib/yantra.lisp`, `lib/core.lisp`.
3. Internal helper cells 00011001, 00011111, 00100000, 01000111 have no ratified semantic residents; seen in `lib/core.lisp` / `lib/core4.lisp`.
4. Historical MONO-NS, UNIX-TIME-NOW, NTP-QUERY-RAW await D10 successor authority, including in `lib/time.lisp`.
5. Embedded `lib/macro.lisp` **must not** be mechanically rewritten: Hosted CI `38163596334` confirmed runtime error `expression is not callable` after replacement; file was restored on main in commit `c5253cf7`. Fix the interpreter/domain callable dispatch with an executable witness before retrying that file.
6. Preserve historical audit and benchmark artifacts, and do not silently alter non-head 8-bit data until their identity role has proof.

## Safety of completion claims

- Syntax/Hosted CI green on intermediate migrated cohorts; T5 file-authority and migration readiness gates separately remain fail-closed on historical corpus.
- No claim of semantic equivalence for all rewrites yet; independent oracle/runtime parity remains required.
- Do not call this a completed all-repository SID8 retirement, and do not delete the old correspondence ledger while unresolved cells remain.
