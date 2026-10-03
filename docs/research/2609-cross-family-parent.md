# #2609 — typed cross-family parent guard

Status: STRUCTURAL-DISCOVERY research only.

## Question

The post-D4 dataset now contains several independently observed factor families:

```text
MutationFamily
NonLocalControl
SpecialCallProtocol
```

They all use words such as *context*, *environment*, *state* or *caller*, but
vocabulary overlap is not a semantic parent theorem.

The #2236 placement precondition is stronger:

```text
same base semantic object/operation
+ one executable delta
= eligible generated child
```

This research check makes the first line executable.

## Current typed research shapes

```text
MutationFamily
  carrier: shared store/location
  operation: (store,target,value) -> updated store
  observable: store changes; ordinary continuation remains

NonLocalControl
  carrier: dynamic exit context
  operation: (value,exit-context) -> non-local transfer
  observable: continuation is skipped; store remains unchanged

SpecialCallProtocol
  carrier: source invocation/caller context
  operation: syntax/context -> direct value or replacement form
  observable: syntax/call protocol changes; no mutation or non-local transfer required
```

These are proof descriptors, not new runtime types.

## Cross-family result

All six directed cross-family parent attempts are rejected as:

```text
DOMAIN-MISMATCH
NO-PROVED-SAME-BASE-PARENT
```

The result is deliberately narrower than "impossible forever". A future bridge
theorem may reopen a pair, but it must name a common carrier/base operation and
an executable law.

## Positive control

The guard does **not** claim that same family implies a one-bit child.

DEFINE and the SETQ mutation core are in the same binding/mutation family, yet
#2492/#2518 found two independent policy deltas. Therefore:

```text
same-family = necessary candidate condition
same-family != sufficient placement proof
```

## #2508 firewall

Every local family law succeeds under its own declared domain and fails when
cross-applied to another family.

This prevents a shared bit shape, helper or word such as "context" from becoming
semantic authority.

## Reproduce

```sh
python3 scripts/research-2609-cross-family-parent.py
```

Expected headline:

```text
CROSS-FAMILY-PARENT-GUARD=PASS
ROOTS-PROVEN=0
D5-RESIDENTS=0
COORDINATES-ALLOCATED=0
WIDTH-INFERENCE=NONE
```

## Principle

**A new bit may refine a semantic object; it may not silently change what kind
of semantic object is being operated on.**
