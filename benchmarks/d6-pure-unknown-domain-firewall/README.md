# #2679 — D6 PURE-UNKNOWN domain firewall

Research-only. No coordinate is allocated.

This lane applies the already-proved #2508 domain-separation law to the 44
`PURE-UNKNOWN` coordinates from the canonical D6 frontier.

For every PURE-UNKNOWN 6-bit value, the executable matrix constructs four
same-payload lookalikes:

1. selector-path semantic object;
2. exact-Q factor semantic object;
3. HUMAN-WIRE framing/mechanism value;
4. GC/runtime mechanism tag.

Expected result:

```text
foreign semantic domain -> DOMAIN-MISMATCH
mechanism-only source    -> MECHANISM-NONAUTHORITY
```

The matrix is 44 × 4 = 176 attacks.

A synthetic bridge-positive self-test is included only to prove that the
firewall is conditional rather than absolute. Crossing is accepted only when a
claim explicitly supplies all of:

```text
same semantic object
same semantic law
target Core D6 domain
cross-proof
witness
```

The synthetic control is not a real bridge and cannot mutate D6 occupancy.

## Principle

**Same bits and same machine transform are reusable representation facts, not
semantic citizenship. Domain authority must be proved independently.**
