# W1-W8 exact-domain carrier benchmark under Contract 11.8 (#4129)

This is the implemented exact-width carrier/runtime baseline across W1..W8.
The directory name `domain12345678` is preserved as implementation provenance.

Current semantic authority is Contract 11.8:

- D1-D9 are the ratified current foundation;
- the Rust `BinarySourceWord` / `DomainIdentity` carrier currently materializes
  W1-W8 only;
- D9 therefore appears in this benchmark as explicit `BLOCKED-CARRIER` until
  an exact W9 carrier is implemented;
- carrier measurement never implies callability or mechanism admission.

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
- registry-dependent claims;
- a synthetic W9 representation.

The measured slice covers D1..D8 carrier/lift cost, a mixed-width path, and the
role-specific callable projection boundary. D9 is recorded as blocked rather
than silently omitted or projected through an 8-bit compatibility path.

Packed/framing and registry lanes remain owned by their production paths
(#3580/#3595 and related current owners). Historical D1-D4 benchmark files in
`benchmarks/domain1234/` remain archived comparison evidence.

## Contract 11.8 boundary

At the current production API boundary:

- D1/D2 are exact non-callable structural/predicate domains;
- D3/D4/D5 project through `DomainIdentity::core_operation()`;
- D6 is owner-ratified semantic residency, while generic callable projection
  remains separate/fail-closed here;
- D7 is owner-ratified and not generic-callable by width;
- D8 is owner-ratified current identity and remains distinct from historical
  Sens8/Sid8 compatibility identity;
- D9 is owner-ratified current identity but `W9` is not yet materialized by
  this Rust carrier, so this benchmark reports `BLOCKED-CARRIER`;
- W1..W8 remain valid exact-width transport/carrier cases for this benchmark.

Fresh result rows are tagged:

```text
contract_version = 11.8
semantic_generation = contract-11-8-exact-d1-d9
d9_status = BLOCKED-CARRIER
```

The benchmark records this boundary; it does not create it.
