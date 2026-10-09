# L1–L7: owner-ratified legacy → canonical migration gate

Status: **owner decision 2026-10-09**, tracked in [#5029](https://github.com/juv4uk/sens/issues/5029). This document does **not** ratify new domain coordinates.

## Decision table

| Rule | Canonical action | Failure / handoff |
|---|---|---|
| L1 | COND queries return **exact D1 PredicateBit 1/0**; exhausted COND returns **structural D3 EMPTY ()**, not D1 0 | Unproved query type = BLOCK; no host truthiness |
| L2 | Only the specific COND clause query \`(t <expr>)\` becomes \`(1 <expr>)\` | A free \`t\`, quoted \`t\`, data or lexical shadow must not be rewritten |
| L3 | Executable heads route via admitted D1–D10 domain tables | Missing coordinate = BLOCK + owner-facing D10 proposal; no invented code and no passthrough |
| L4 | \`equal?\` / \`null\`: an already **proved semantic bridge** to a D8 resident, else a **law-derived** D3 expansion | Matching spelling is not proof: absent evidence = BLOCK |
| L5 | Remove retired \`structural-kind\` and \`identity-relation\` from the **active corpus**, retain provenance in archaeology | No automatic deletion of executable code or oracle evidence |
| L6 | Regenerate stale fixtures by the canonical generator | No hand-edited expected values |
| L7 | If the existing reader cannot parse the input, leave source untouched and report in a separate owner-review list | No guessed syntax repairs |

## Executable preflight

\`scripts/audit-l1-l7-canon.py\` is a **read-only implementation slice**. It reuses the existing \`migrate-three-pass.py\` parser, resolver and binary T5 encoder, instead of introducing a second Python reader. It applies only the deterministic L2 rewrite to an **in-memory AST**; L1 requires a statically admitted predicate role, and L3–L5 block unsupported semantics.

\`\`\`sh
python3 scripts/audit-l1-l7-canon.py --self-test
python3 scripts/audit-l1-l7-canon.py lib --report /tmp/sens-l1-l7.json
\`\`\`

The JSON report separates \`BLOCK\`, \`UNPARSEABLE_L7\`, \`REGENERATE_L6\`, \`NEEDS_INDEPENDENT_ORACLE\`, and \`DIGEST_MATCH_ONLY\`. It has explicit \`owner_review_unparseable\` and \`owner_review_blocked\` queues. Exit status 2 indicates unresolved work; input \`.lisp\` and existing \`.sens\` are never modified.

An optional independent digest manifest can be supplied:

\`\`\`sh
python3 scripts/audit-l1-l7-canon.py lib \
  --oracle-manifest /tmp/source-pinned-oracle-digests.json \
  --report /tmp/sens-l1-l7.json
\`\`\`

Manifest mapping: \`{"relative/file.lisp": {"source_sha256": "...", "physical_sha256": "...", "typed_word_sha256": "..."}}\`. A digest match only says the bytes/typed words are equal to that pinned oracle projection; **it does not prove semantic equivalence**. Historical and current execution witnesses still need to run in the established proof-admission tool (\`scripts/admit-t5-migration.py\`). Do not publish physical artifacts on digest agreement alone.

## Remaining blockers and non-claims

1. The existing Python parser is **not** the Rust canonical reader. Reader parity is an outstanding hard gate; this preflight cannot authorize mass publishing or certify that all legal current SENS syntax is recognized.
2. \`migrate-three-pass.py\` currently has an unknown-head passthrough path. This audit rejects its resulting nonzero count but has **not** changed production migration behavior; no \`main\` mutation is implied.
3. D10 current coordinates/proposals need their own ratified authority. The D1–D9 foundation cannot be stretched to D10 by guessing.
4. The D8 resident named \`EQUAL\` does **not** prove that historical \`equal?\` is its exact synonym. There is no automatically admitted \`null\` expansion in this gate. Those source forms remain BLOCK until owner law/proof.
5. Retired-code deletion and fixture regeneration are separate review/generation changes. This tool intentionally performs neither operation.
6. A changed \`COND\` AST does not replace runtime verification of \`COND\` exhaustion or exact predicate dispatch.

## Required completion sequence

existing canonical reader (or proved parity with it) → L1–L7 semantic pass → exact-width/T5 emitter → independently executed historical/current oracles → SHA-256 comparison → hosted GitHub CI green → one-writer review → merge to main.

Never mark an unproved file migrated; preserve every L7 original for owner review.
