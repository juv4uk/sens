# W1-W8 exact-width carrier benchmark (#3001)

This is the exact-width carrier/runtime baseline under Contract 11.5. Semantic identity authority is D1-D6 CURRENT and D7-D8 RESEARCH; W1-W8 remain mechanical carrier controls. Callability/mechanism coverage is a separate axis.

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
current implementation's callable-projection boundary. That projection is mechanism evidence only and never upgrades or revokes semantic authority. Packed/framing and registry lanes
are added only from their production owners (#3026/#2833 and full-owner
projection -> #2992).

Historical D1-D4 benchmark files remain in `benchmarks/domain1234/` as archived
comparison evidence, but are not the current CI baseline.
