# #2489 — SETQ-core placement

Status: research-only.

## Proven input

The historical/semantic Phase-D work has already isolated one new observable capability:

~~~text
nearest-existing shared-location update
~~~

This issue asks whether that capability is honestly one extra bit below a ratified D4 parent.

## Strongest parent: DEFINE

Current D4 DEFINE behaves as:

~~~text
scope = current frame
miss  = create binding
~~~

The SETQ core behaves as:

~~~text
scope = nearest existing binding
miss  = fail
~~~

When the name already exists in the current frame, both update that same location. That makes DEFINE a real semantic-parent candidate rather than a name analogy.

## Two-axis falsifier

The executable model covers the full policy square:

~~~text
                 create          fail
current          DEFINE          current-fail
nearest          nearest-create  SETQ-core
~~~

Search scope and miss policy are independently observable.

### Search scope

With inherited outer X:

~~~text
current-create -> create/shadow inner X; outer observer remains OLD
nearest-create -> update outer X; outer observer sees NEW
~~~

Miss behavior is held fixed.

### Missing-name policy

With no X anywhere:

~~~text
current-create -> create inner X
current-fail   -> explicit error
~~~

Search scope is held fixed.

All four corners have distinct bounded observable signatures.

Therefore:

~~~text
DEFINE -> SETQ-core
changes:
  1. search scope
  2. missing-name policy
~~~

Under #2236 one extra bit may encode one independently observable delta. The direct one-bit DEFINE child hypothesis therefore fails:

~~~text
00110 / 00111 = physically free
but not semantically earned by this parent relation
~~~

Current result:

~~~text
DEFINE-parent = NEEDS-WIDER-WIDTH
~~~

This does not assign any D6 coordinate. A wider placement needs a separate ordering/generator theorem for the two axes.

## Counterparents

### LOOKUP

LOOKUP already owns nearest-existing/fail-style name resolution, but its observable operation is a read/query. SETQ-core is a shared-location state transition. Shared resolution policy alone does not satisfy the #2236 same-base-operation requirement.

### BIND

BIND constructs fresh/batch environment structure. It does not update one already-existing shared location. It is not the same base operation.

## Reproduce

~~~sh
python3 scripts/research-2489-setq-placement.py
~~~

Expected headline:

~~~text
SETQ-PLACEMENT=PASS
DEFINE-TO-SETQ-DELTA-COUNT=2
DEFINE-PARENT-DECISION=NEEDS-WIDER-WIDTH
D5-00111=FREE-NOT-EARNED
~~~

## Principle

**A free child word is not enough. If DEFINE and SETQ differ on two independent binding-policy axes, one suffix bit must not hide both.**
