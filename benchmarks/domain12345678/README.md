# W1-W8 exact-width mechanics benchmark (#3001 / #3290)

This lane measures exact-width carrier mechanics. It is **not** a claim that
every width is a currently ratified semantic domain.

Current Contract 11.3 authority is:

```text
semantic current:  D1 D2 D3 D4 D5 D7
semantic research: D6 D8
mechanical widths: W1 W2 W3 W4 W5 W6 W7 W8
```

The benchmark consumes production APIs only:

```text
Bits<N>
 -> BinarySourceWord::WN
 -> DomainIdentity::DN
 -> exact (domain,width,payload)
```

That pipeline proves representation and identity mechanics. Width existence by
itself never grants semantic residency or callability.

It deliberately does not contain:
- a benchmark-local owner/residency table;
- human-name lookup;
- legacy Sens8/Function8 identity;
- inferred callability from width or occupancy;
- registry-dependent semantic claims.

The first slice measures W1..W8 carrier/lift cost, a mixed-width path, and the
production callable-projection boundary. D5 may be semantically current while a
specific resident still lacks an invocation mechanism and fails closed. D6/D8
rows are mechanism/research controls only.

Packed/framing and registry lanes are added only from their production owners
(#3026/#2833 and the exact-domain projection work).

Historical D1-D4 benchmark files remain in `benchmarks/domain1234/` as archived
comparison evidence, but are not the current mechanics baseline.
