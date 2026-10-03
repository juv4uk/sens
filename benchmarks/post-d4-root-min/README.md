# Post-D4 root minimization

Phase: **SENS-DERIVATION**. Parent: #2617.

This directory asks a narrower question than structural factor discovery:

> Which bounded-independent observations remain semantic roots after attempting
> reconstruction from D1-D4, already-proved roots, explicit data structures and
> ordinary composition?

A successful whole-program encoding is not automatically a local derivation.
The project-wide rule is #2468: changing unrelated caller/observer protocols
proves global compilability, not source-boundary semantic identity.

Allowed result vocabulary:

```text
PROVEN-ROOT
DERIVED
POLICY-OVER-ROOT
CARRIER-PREMISE
UNRESOLVED
```

Every result keeps width and coordinate separate. No script in this directory
may allocate D5/D6 residents.

Current first slice:
- #2628 shared-location-update -> bounded `CARRIER-PREMISE`;
- explicit frames/store algorithms are D3/D4-computable;
- the missing local authority is the ambient/current shared-location carrier
  needed by an unchanged pre-existing `observer()`.
