# #1970 — Function8 assumption inventory, first bounded pass

Status: **research / read-only**. This report does not change runtime, contracts, reader, wire format, or the function table.

## Result

The exact-8 assumption is not one thing. The first repository pass separates four materially different cases:

1. **Semantic/reader blockers** — must change before variable-width identities can become production language law.
2. **Serialization/schema blockers** — can coexist through versioning, but the new canonical format needs a variable-width representation.
3. **Backend fast paths** — 8-bit machinery is mechanically useful and does not need to disappear merely because the ontology changes.
4. **Tests/docs/history** — important for ratchets and clarity, but not runtime semantics.

The important migration rule is therefore:

```text
remove exact-width authority
!=
remove every one-byte mechanism
```

A `Sens8 -> [Option<PrimitiveFn>; 256]` dispatch table can remain a good backend optimization for legacy/anchor functions even if canonical identity later becomes a bounded variable-width word/path.

## Hard blockers found in SENS

The first pass identifies these as direct blockers to production variable-width identity:

- `language-contract.lisp`: `sid8-function-space` explicitly declares the complete function space to be exactly 256 eight-bit words.
- `contracts/core-profile-contract.lisp`: `shared-function8` makes exact width part of cross-Core authority.
- `scripts/sid8-only-ontology-guard.sh`: CI guards exact width rather than only the useful no-named-ontology law.
- `crates/sens/src/sens.rs`: `Sens` is currently an alias of `Sens8`; constructor/macro require exactly eight bits.
- `crates/sens/src/parser.rs`: a binary token becomes `ExprKind::Sid` only when `token.len() == 8`.
- `crates/sens/src/syntax.rs`: FASL/SID representation stores one packed byte.
- registry/ownership/numeric-inventory validators contain `^[01]{8}$` as schema authority.
- `knowledge/guard-reference.lisp` still describes exact-eight identity as a standing owner law.
- CI/workflow callers still enforce several of those exact-width validators.

These should be migrated only after the research model is ratified; this audit does **not** recommend weakening them now.

## Cross-repository blocker: CML

A read-only audit of `juv4uk/cml` shows that CML is not merely using one old adapter. Exact-8 identity is currently embedded across its compiler boundary:

- `Expr::Sid(sens::Sid8)` in the AST;
- `Ir::Sid(sens::Sid8)` in the backend-neutral IR;
- direct-source parsing recognizes canonical callable identity only when token width is exactly 8;
- `semantic.rs` treats the complete `00000000..11111111` domain as the language function space;
- `build.rs` parses registry identity into `u8`, emits `Sid8`, and formats IDs as exactly eight bits;
- `upstream_sid_bridge.rs` lowers registry-owned callables into `Sid8`;
- CML vendors the old SENS language contract with `sid8-function-space`;
- `.github/workflows/sid8-issue-lifecycle-guard.yml` automatically reopens CML issue 238 when its “permanent SID8-only constitution” is closed.

Therefore CML must be treated as a **real consumer migration dependency** before SENS can expose new variable-width callable identities to the compiler.

This still does **not** mean every Sid8 backend specialization must disappear. Known eight-bit anchors can remain direct fast paths after CML gains a width-neutral canonical identity carrier.

## Mechanisms that can survive

The following are not evidence that the language itself must remain exact-8:

- `PRIMITIVE_TABLE: [Option<PrimitiveFn>; 256]`;
- `packed_byte()` direct indexing;
- legacy one-byte wire/FASL Function8 frames;
- deprecated `Sid8 = Sens8` compatibility adapter;
- existing 8-bit generated registry rows;
- benchmark parsers for the historical table;
- CML backend pattern matches for existing Sid8 anchors.

A future runtime/compiler can legitimately have:

```text
canonical variable-width identity
        |
        +-- legacy/anchor Sens8 -> O(1) / direct backend fast path
        |
        +-- longer/path identity -> generator / sparse / derived route
```

without reintroducing a flat 256-peer semantic ontology.

## Migration ordering suggested by evidence

Do not migrate implementation bottom-up. The safe dependency direction is:

```text
1. ratify width-neutral identity law
2. replace exact-width semantic/CI authority
3. introduce width-neutral canonical identity representation in SENS
4. teach reader/AST/registry schema
5. version FASL/wire
6. expose the new identity through the SENS API
7. migrate CML AST/IR/build-time registry bridge
8. preserve or adapt 256-byte / Sid8 fast paths where profitable
9. migrate tests/docs/bench tooling
```

This order prevents a mechanical refactor from accidentally becoming semantic authority and prevents CML from pinning SENS back to the old type through its public API.

## Coordination

This is still a bounded audit. Remaining parallel lanes can add evidence without changing production:

- additional Rust Value/Environment/code-slot types;
- necessary forms and semantic registry consumers;
- FASL/wire call sites and versioning assumptions;
- other cross-repository consumers;
- archived documentation separated from active authority.

Machine-readable rows live in `docs/research/1970-function8-assumption-inventory.tsv`.

## Principle

**Keep 8 bits where they are a useful representation; remove 8 bits where they are an unjustified semantic axiom.**
