# #2054 — selector semantic-authority inventory, first slice

Status: research/read-only migration inventory. No runtime, parser, registry, compiler, or contract behavior is changed.

## Main finding

The current selector family does **not** have one monolithic authority. It already separates into several layers:

1. **CAR/CDR semantic operations** — current Canon primitives with strong runtime witnesses.
2. **Legacy exact-8 root identities** — `00000101` / `00000110`.
3. **Derived descendant mechanisms** — pure-Lisp definitions for `caar`, `cadr`, `cddr`, plus the `cadddr -> fourth` alias.
4. **Legacy descendant identities/surfaces** — `00110011..00110110` registry rows.
5. **Generated projections/docs/tests** — derived from those rows.
6. **CML duplicate mechanisms** — explicit descendant SID branches and dedicated IR vocabulary.

This is useful because the migration does not need to replace all of them at once.

## Critical authority split

The proposed selector pilot should preserve this distinction:

```text
CAR/CDR semantic operations
    remain primitive semantic meaning

old 8-bit CAR/CDR IDs
    become checked compatibility projection

selector descendant meaning
    becomes ordered family law / proof

old descendant 8-bit rows
    become compatibility projection, then deletion/archival candidates

backend CAR/CDR primitives
    remain useful mechanisms
```

So:

> migrating away from exact-8 identity does not mean deleting CAR/CDR primitives.

It means deleting the assumption that their current one-byte addresses are the permanent semantic universe.

## Strongest descendant deletion targets

### SENS

`lib/core.lisp` currently implements:

```text
caar = CAR(CAR(x))
cadr = CAR(CDR(x))
cddr = CDR(CDR(x))
```

and binds `cadddr` to the same closure as `fourth`.

These are already classified by repository audits as pure-Lisp derived functions, not required backend primitives.

Once #2055/#2060 proves the canonical selector law authoritative, these explicit descendant execution definitions become strong deletion candidates.

Human surfaces may remain, but they should resolve to the canonical variable-width selector identity/proof rather than require a dedicated closure definition.

### CML

CML currently duplicates selector knowledge in:

- explicit legacy SID branches in `src/compiler.rs`;
- explicit C backend special cases;
- explicit x86 backend special cases;
- dedicated descendant `PrimOp` variants;
- a name-special `caddr` lowering path.

These are mechanisms, not language authority.

The migration target is:

```text
canonical selector word/proof
    -> ordered CAR/CDR recipe
    -> existing primitive lowering
```

After cml#397/#2058 parity, descendant-specific SID branches are prime deletion targets.

## Important non-collapse rule

Current code already demonstrates a dangerous distinction:

`cadddr` and `fourth` share a closure mechanism.

That does **not** by itself prove semantic identity.

Likewise repository doctrine explicitly keeps `second` distinct from structural `cadr` despite overlapping behavior.

Therefore the migration must move execution authority without silently quotienting:

```text
mechanism equivalence
!=
semantic identity
```

## Recommended reversible order

```text
1. classify current authority (#2054)
2. shadow ordered selector resolver (#2055)
3. dual oracle / rollback (#2060)
4. introduce FunctionWord carrier only on the proven selector path (#2056)
5. transfer selector-family authority
6. make legacy 8-bit rows projections
7. compile static selector proofs away (#2058)
8. delete descendant closure/SID-special mechanisms after rollback window
9. broaden carrier/parser/wire migration only after this vertical slice works
```

This ordering intentionally avoids a global carrier-first rewrite.

## First authority-transfer invariant

At every migration state there must be exactly one declared semantic authority for a selector meaning.

During shadow mode:

```text
old route = authority
new route = oracle candidate
```

After transfer:

```text
new ordered selector law = authority
old row = compatibility / rollback evidence only
```

If both remain sovereign, migration failed.

## Deletion proof target

The first pilot is successful only when at least one of these can disappear without behavior loss:

- explicit descendant Lisp execution definition;
- explicit descendant CML SID branch;
- descendant-specific IR mechanism;
- legacy exact-8 descendant semantic row after compatibility obligations end.

Generated docs and compatibility projections do not count as semantic machinery deletion unless they were previously authoritative.

## Principle

**Preserve the primitive operation; migrate the identity law; delete duplicated descendant machinery.**
