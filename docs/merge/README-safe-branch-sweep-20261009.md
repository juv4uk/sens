# Safe branch sweep 2026-10-09 — evidence-first

**HOLD — not eligible for direct merge into main.** Canonical verdict ledger [#5131](https://github.com/juv4uk/sens/issues/5131); single-writer integration [#5041](https://github.com/juv4uk/sens/issues/5041).

The existing \`scripts/audit_branch_merges.py\` performs the complete Git ancestry/diff/merge-tree census without writing any refs. The new \`scripts/build_branch_sweep_triage.py\` converts the census into **one row per branch**, with explicit candidates drawn from the UNION of recent 72h + historical research + historically clean Git merges. Outputs: JSON + TSV GitHub Actions artifacts.

**Decisions are fail-closed.**
- \`MERGED-IN\`: proven ancestor or identical changed-file content. Skip replay; preserve provenance.
- \`CONFLICT\`: conflicting / unrelated Git histories. No automatic replay.
- \`HOLD\`: all otherwise unchecked branches. A clean Git tree merge is not ALIVE.
- \`OBSOLETE\` and \`ALIVE\`: never inferred from branch names. Require evidence-pinned individual review in \`docs/merge/branch-sweep-overrides-20261009.json\`. ALIVE additionally requires intact semantic contract, oracle evidence and successful current-head hosted CI.

The GitHub-hosted \`branch-sweep-triage.yml\` runs independent classification and uploads the full catalog, then a separate **fail-closed admission gate** blocks the sweep until no HOLD/CONFLICT candidate remains. Even a complete automatic catalog **does not authorize** a merge; exact SHA + full current-head CI + independent reviewer + single writer are required.

Three initial reviewed branch examples: \`simplify/equal-structural-relation-retire\` (#1795), \`test/116-one-truth-three-paths-red\` (#172), \`simplify/1698-structure-not-ontology\` (#1757) are already strict ancestors of \`main\`: \`MERGED-IN\`, not active code to replay. See [the initial 13-branch ledger](../research/branch-sweep-triage-20261009.md).

No force push, owner-local runner, silent D1–D9 mutation, or bypass of red checks.
