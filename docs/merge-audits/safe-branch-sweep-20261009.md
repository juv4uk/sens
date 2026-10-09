# Safe branch sweep 2026-10-09 — audit ledger (partial)

**Status: PARTIAL / NO-MERGE-TO-MAIN.** This is a source-branch triage ledger, not proof of completion. Single-writer admission per [issue #5133](https://github.com/juv4uk/sens/issues/5133); merge queue [#5041](https://github.com/juv4uk/sens/issues/5041).

Sweep baseline (at initial creation): `19f64724a57b5d5c86c54fa2c9d5cf7c093323b9`. The eight ancestry comparisons below were refreshed relative to moving main at `466848dfaa8582310c616b4b92cb7a97074e3ada`; ancestry ahead=0 stays valid if main advances without reset. Behind counts are a historical snapshot.

| Source branch | Verified source head SHA | Ahead / behind | Verdict | Why / action |
|---|---|---|---|---|
| `simplify/equal-structural-relation-retire` | `552d103e57887d2ec0cf0a10128329c5c8b26c05` | 0 / 5119 | **MERGED-IN** | Legacy structural equality; no unique commits; exclude |
| `test/116-one-truth-three-paths-red` | `39e06d41365c3f2c9a3c4d9509b7062e4e242c6e` | 0 / 6666 | **MERGED-IN** | Historical RED truth machinery; no unique commits; exclude |
| `simplify/1698-structure-not-ontology` | `6021b25251cde3b0a975e195fd54279eef6af13d` | 0 / 5153 | **MERGED-IN** | Legacy structural-kind semantics; no unique commits; exclude |
| `research/d10-astrophoto-pinhole-exact-rays-20261009` | `a75f8fcd8ddf71bf46399c0d025c5db12959ff14` | 0 / 3699 | **MERGED-IN** | Already ancestor; exclude |
| `research/d10-chess-zero-sum-castling-roots-20261009` | `7705bc5d4a1402a27427d091ebb49e39c22c98d3` | 0 / 3718 | **MERGED-IN** | Already ancestor; exclude |
| `research/d10-clhs-streams-census-20261009` | `2aff2dc905306be892f70e929fa3cb8720e3c8b7` | 0 / 3711 | **MERGED-IN** | Already ancestor; exclude |
| `research/d10-binary-state-shortest-witness-20261009` | `489feab5d95854cd6c80bf7d89d15c32995da69e` | 0 / 3699 | **MERGED-IN** | Already ancestor; exclude |
| `research/d10-1971-strips-goal-regression-20261009` | `f36ab1d835d4f468765bdf8b5e9010961b6f203c` | 0 / 3681 | **MERGED-IN** | Already ancestor; exclude |

## Other reviewed candidates (not admitted)

| Candidate | Verdict | Evidence | Action |
|---|---|---|---|
| `research/d10-conditions-finish-20261009` | **OBSOLETE** | [#5019](https://github.com/juv4uk/sens/pull/5019) closed without merge and explicitly superseded by the owner single-stream Conditions [#4901](https://github.com/juv4uk/sens/pull/4901) | Do not import stale proposal ledger or duplicate the D10 Conditions selection |
| `research/d10-cyclic-word-canon-fresh-main-20261009` | **CONFLICT** (semantic dedup) | [#4944](https://github.com/juv4uk/sens/pull/4944) closed without merge because [#4945](https://github.com/juv4uk/sens/pull/4945) overlaps on least cyclic rotation and differs on empty-word contract | Owner must decide exact behavior; do not silently merge both roots |
| `research/d10-clips-library-harvest-20261009` | **MERGED-IN** (content) | [#4767](https://github.com/juv4uk/sens/pull/4767) merged; research report and harvest JSON source blobs matched main at audit | Do not resurrect older D10 inventory snapshot |
| `research/d8-d9-overflow-provenance-archive-20261009` | **MERGED-IN** (content) | [#4860](https://github.com/juv4uk/sens/pull/4860) merged; research and provenance blobs matched main at audit | Preserve historical data only |
| `research/d10-atms-strips-symbolic-foundations-20261009` | **CONFLICT** (overlap review) | [#4985](https://github.com/juv4uk/sens/pull/4985) closed unmerged; ATMS/STRIPS topic overlaps [#4958](https://github.com/juv4uk/sens/pull/4958) and [#4992](https://github.com/juv4uk/sens/pull/4992); old D10 snapshot 634 | Do not apply old central ledger or claim an independent semantic resident without dedup |

## Required gates before promoting any ALIVE material

Each pending source branch must get `repository, head SHA, current main SHA, Git ahead/behind, changed-file list, semantic-contract and legacy tests audit, dedup/provenance, targeted and full hosted CI (with URLs), verdict, reviewer`. The full last-72h plus historical research and conflict-free branch inventory is **not yet classified**. No release candidate is ready to go to main; zero unresolved items allowed in any proposed release subset.

**ALIVE admission** requires a nonduplicated portable law or verifiable research artifact, no accidental semantic mutation, a clean source/provenance record, and green required checks. If the candidate conflicts with the current owner-led D10 ledger, preserve it as archival evidence in a separate PR rather than merge old domain inventory.
