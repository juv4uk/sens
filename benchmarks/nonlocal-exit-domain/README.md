# #2663 — non-local-exit exact-domain falsifier

Research-only positive control for #2662.

This lane asks one narrow question: given that non-local-exit is already a
proven parentless semantic root, what current evidence can select its exact
binary domain?

It does not rediscover roothood, allocate a coordinate, mutate D5/D6 occupancy,
or make an owner decision.

Expected bounded result:

```text
D5-ELIGIBLE = NO
D6-ELIGIBLE = UNRESOLVED
MINIMUM-EXACT-DOMAIN = UNRESOLVED
COORDINATE = UNPLACED
```

The anti-numerology rule is explicit:

```text
independent observable facts
!= exact bit width
!= existing domain membership
!= coordinate
```

Run:

```bash
python3 benchmarks/nonlocal-exit-domain/run.py --out /tmp/nonlocal-exit-domain
```
