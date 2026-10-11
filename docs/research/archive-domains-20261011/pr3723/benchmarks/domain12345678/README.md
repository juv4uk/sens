# D1-D8 exact-domain benchmark (#3001)

This is the current exact-width carrier/runtime baseline across W1..W8.

It is deliberately broader than current semantic authority. Under Contract 11.6,
D1-D7 are the current semantic foundation while D8 remains research. Carrier
measurement does not imply residency or callability.

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

## Contract 11.6 boundary

At the current production API boundary:

- D1/D2 are exact non-callable structural/predicate domains;
- D3/D4/D5/D6 project through `DomainIdentity::core_operation()`;
- D6 callable identity is separate from per-resident executable mechanism coverage;
- D7 is ratified but not generic-callable; D8 is the remaining research carrier;
- all W1..W8 remain valid exact-width transport/carrier cases for this benchmark.

The benchmark records this boundary; it does not create it.
