# W1-W8 exact-width mechanism benchmark (#3001)

This is the carrier/runtime mechanism baseline for exact widths W1-W8. Current semantic authority is D1-D4 + D7; W5/W6/W8 remain UNRATIFIED / RESEARCH under #3278.

The benchmark consumes production APIs only:

```text
Bits<N>
 -> BinarySourceWord::WN
 -> DomainIdentity::DN
 -> exact (domain,width,payload)
```

It deliberately does not contain:
- a benchmark-local owner/residency table;
- human-name lookup;
- legacy Sens8/Function8 identity;
- inferred callability from occupancy;
- registry-dependent claims.

The first slice measures W1..W8 carrier/lift cost, a mixed-width path, and the
current callable-projection boundary. Width membership never implies semantic admission. Packed/framing and registry lanes
are added only from their production owners. Revoked D5/D6/D8 donor maps are
never a current semantic denominator; any future rows require fresh ratification.

Historical D1-D4 benchmark files remain in `benchmarks/domain1234/` as archived
comparison evidence, but are not the current CI baseline.
