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
