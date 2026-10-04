# D1-D8 exact-domain benchmark (#3001)

This is the current carrier/runtime baseline for the ratified D1-D8 binary-domain paradigm.

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

The first slice measures D1..D8 carrier/lift cost, a mixed-width path, and the
role-specific callable projection boundary. Packed/framing and registry lanes
are added only from their production owners (#3026/#2833 and full-owner
projection -> #2992).

Historical D1-D4 benchmark files remain in `benchmarks/domain1234/` as archived
comparison evidence, but are not the current CI baseline.
