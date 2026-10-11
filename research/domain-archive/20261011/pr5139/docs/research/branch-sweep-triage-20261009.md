# Safe branch sweep · triage ledger · 2026-10-09

> **WORK IN PROGRESS / NOT READY TO MERGE.** This is an additive, non-normative audit ledger only. Current main snapshot `61c81b9bac3f2a9224bcbd49fb227e59251acf3d`; recorded source branches must be compared again before admission. Canonical coordination and the complete triage acceptance criteria: [#5132](https://github.com/juv4uk/sens/issues/5132), merge queue [#5041](https://github.com/juv4uk/sens/issues/5041). The branch sweep MUST NOT land in main until every source is classified, duplicate historical semantics are excluded, and current-head required CI is green.

Four allowed verdicts: `MERGED-IN` = already ancestor/current content; `OBSOLETE` = contradicts current ratified semantic authority; `ALIVE` = current compatible and proven new change; `CONFLICT` = human review needed (Git or semantic conflict, partial content already merged). Unknown branches are implicitly **UNCLASSIFIED / BLOCKED**, not ALIVE.

## Snapshot #1 — 13 branches checked against 61c81b9bac3f2a9224bcbd49fb227e59251acf3d

| Branch (all juv4uk/sens) | Source head SHA | Ahead / behind | Verdict | Proof / disposition |
|---|---|---:|---|---|
| `simplify/equal-structural-relation-retire` | `552d103e57887d2ec0cf0a10128329c5c8b26c05` | 0 / 5117 | MERGED-IN | Strict main ancestor; never replay retired semantics |
| `test/116-one-truth-three-paths-red` | `39e06d41365c3f2c9a3c4d9509b7062e4e242c6e` | 0 / 6664 | MERGED-IN | Strict main ancestor; historical RED test NOT current normative |
| `simplify/1698-structure-not-ontology` | `6021b25251cde3b0a975e195fd54279eef6af13d` | 0 / 5151 | MERGED-IN | Strict main ancestor; no novel diff |
| `research/d10-hardware-law-triage-20261009` | `697af600aae8cd41e9901f3c1718e5b6215f0ea4` | 0 / 3674 | MERGED-IN | Strict main ancestor |
| `research/d10-gps-means-ends-oplink-1958-20261009` | `ad262769b41dc664c6211b0cb67427892ab6ca73` | 0 / 3681 | MERGED-IN | Strict main ancestor |
| `research/d10-temporal-stp-20261009` | `2274cbb2481e1830fcb682942b6768df719cdf4a` | 0 / 3679 | MERGED-IN | Strict main ancestor |
| `research/d10-wsm24-chamfer-law-20261009` | `4510dbf02a877dfcb500c5ee3c61944a3118b069` | 0 / 3710 | MERGED-IN | Strict main ancestor |
| `research/d6-v2-laws-current-main-20261009` | `1b71143ab52a1783bd4bc8f0772ae2004e316698` | 0 / 3740 | MERGED-IN | Strict main ancestor |
| `research/d6-nth-maplist-sublis-main-replay-20261009` | `34b73e1929651b5db5731b3d9aa84863c6b9a3df` | 0 / 3735 | MERGED-IN | Strict main ancestor |
| `research/d10-flavors-restarts-law-proposals-20261009` | `92773df56553027ef34ad394735ad2457622747f` | 4 / 3772 | CONFLICT | 2/4 content blobs match main; JSON and test differ; preserve current main pending law/oracle diff |
| `research/d10-lisp15-appendix-reconcile-20261009` | `022c4b9d6bf0697e50125af5cc3d5e58f58b19af` | 9 / 3740 | CONFLICT | 2/5 content blobs match main; workflow/checker/test differ; do not backport silently |
| `research/d10-historical-primary-manual-reconcile-20261009` | `f406b42d93807c0847712492f53c0962464b1ddc` | 6 / 3751 | CONFLICT | 3/4 blobs match main; checker differs |
| `research/d8-lisp15-appendix-preservation-20261009` | `c53ef63ec2e7887ad34ad91dbfa1659a80c6ef0f` | 4 / 3742 | CONFLICT | 3/4 blobs match main; checker differs |

**Snapshot result:** 9 MERGED-IN, 4 CONFLICT, 0 ALIVE admitted, 0 obsolete proven; this is ONLY this 13-branch sample, **not** the total historical census. `CONFLICT` means *do not merge the branch*: individually prove current behavior, independent oracles and compatibility before an `ALIVE` replay.

## Admission gate

- [ ] Full census: all 6–9 October branches, all historical research branches, all other eligible historical branches across relevant repos
- [ ] Every examined branch classified with source SHA, main SHA, content SHA evidence and action
- [ ] No obsolete semantics, already-present blobs, or conflicting tests in sweep diff
- [ ] Only individually accepted ALIVE changes; all conflicts resolved by one responsible agent per record
- [ ] Required current-head GitHub-hosted CI SUCCESS; SKIPPED is not hardware parity
- [ ] Independent review; single-writer merge by expected HEAD SHA, no forced merges

## Snapshot #2 — eight further historical research branches

| Branch | Source head SHA | Ahead / behind | Verdict | Proof / disposition |
|---|---|---:|---|---|
| `research/d10-astrophoto-pinhole-exact-rays-20261009` | `a75f8fcd8ddf71bf46399c0d025c5db12959ff14` | 0 / 3697 | MERGED-IN | Strict main ancestor |
| `research/d10-floyd-hoare-inductive-safety-witness-20261009` | `ce648690ebfac27dfadf84dfc84464353037660a` | 0 / 3368 | MERGED-IN | Strict main ancestor |
| `research/d10-brzozowski-1964-symbolic-ai-derivative` | `1f26b6e5c306274eb11ed9bdcb21fbb8bca7e0cc` | 0 / 3679 | MERGED-IN | Strict main ancestor |
| `research/d10-ebg-operational-horn-proof-20261009` | `212af51d151cf8c374de728e61f8ad54384b0109` | 0 / 3682 | MERGED-IN | Strict main ancestor |
| `research/d10-clhs-streams-census-20261009` | `2aff2dc905306be892f70e929fa3cb8720e3c8b7` | 0 / 3709 | MERGED-IN | Strict main ancestor |
| `research/d10-clhs-pathnames-dictionary-20261009` | `086c31c2a059f7cc02fda20b2f2bb115de4f5082` | 0 / 3714 | MERGED-IN | Strict main ancestor |
| `research/d8-d9-overflow-provenance-archive-20261009` | `dde89211bd3df03c8062d65a0018e4116061b5ea` | 4 / 3730 | CONFLICT | 3/4 blobs already equal main, checker differs; preserve newer checker |
| `research/d10-dung-grounded-argumentation-20261009` | `3277cc4ce8b6953523f2110033b0862d2963a19e` | 9 / 3119 | CONFLICT | 5/5 research files match main, but historical D10 proposal ledger/test edits cannot override present ledger |

**Cumulative snapshots #1 + #2:** 21 branches checked: **15 MERGED-IN**, **6 CONFLICT**, **0 ALIVE** admitted, 0 OBSOLETE proven. This remains a small, evidence-pinned subset of all historical branches. It is NOT permission to merge the sweep.

## Snapshot #3 — six further SHA-pinned 2026-10-09 research branches

Verified against pinned `main@61c81b9bac3f2a9224bcbd49fb227e59251acf3d`; numbers may be stale if the moving main advances, but ancestor-only cases remain no-op on a strictly advancing main.

| Branch | Head SHA | Ahead / behind | Verdict | Evidence / action |
|---|---|---:|---|---|
| `research/d10-chess-zero-sum-castling-roots-20261009` | `7705bc5d4a1402a27427d091ebb49e39c22c98d3` | 0 / 3716 | **MERGED-IN** | Strict ancestor of pinned main; zero unique commits; SKIP; https://github.com/juv4uk/sens/compare/61c81b9...research/d10-chess-zero-sum-castling-roots-20261009 |
| `research/d10-binary-state-shortest-witness-20261009` | `489feab5d95854cd6c80bf7d89d15c32995da69e` | 0 / 3697 | **MERGED-IN** | Strict ancestor of pinned main; zero unique commits; SKIP; https://github.com/juv4uk/sens/compare/main...research/d10-binary-state-shortest-witness-20261009 |
| `research/d10-1971-strips-goal-regression-20261009` | `f36ab1d835d4f468765bdf8b5e9010961b6f203c` | 0 / 3679 | **MERGED-IN** | Strict ancestor of pinned main; zero unique commits; SKIP; https://github.com/juv4uk/sens/compare/main...research/d10-1971-strips-goal-regression-20261009 |
| `research/d10-conditions-finish-20261009` | `1fc3782058c301e58754e43114ddf4ee5d9333e0` | 10 / 3678 | **OBSOLETE** | Closed-unmerged #5019 was explicitly superseded by owner single-stream #4901; old 634 D10 snapshot and ledger; SKIP-CLOSE-DUPLICATE; https://github.com/juv4uk/sens/pull/5019 |
| `research/d10-cyclic-word-canon-fresh-main-20261009` | `557b9693dbc6c7634d0450be96d38d5ac78f9a76` | 10 / 3708 | **CONFLICT** | Closed-unmerged #4944 overlaps cyclic least-rotation #4945, with unresolved empty-word contract; HOLD-DEDUPE; https://github.com/juv4uk/sens/pull/4944 |
| `research/d10-atms-strips-symbolic-foundations-20261009` | `d58ecb391a5a6758c4ebd6f8752e9ec158755f3e` | 4 / 3690 | **CONFLICT** | Closed-unmerged #4985 has old 634 ledger and ATMS/STRIPS overlap requiring cross-check vs #4958/#4992; HOLD-DEDUPE; https://github.com/juv4uk/sens/pull/4985 |

Cumulative three samples: **27 source branches checked: 18 MERGED-IN, 1 OBSOLETE, 8 CONFLICT, 0 ALIVE admitted**. Every other source remains UNCLASSIFIED/HOLD; the sweep **must not merge into main**. Semantic overlap is distinct from Git conflict, and an ancestor branch's historical truth-machine tests gain no current normative authority.
