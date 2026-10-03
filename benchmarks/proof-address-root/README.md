# #2669 proof-addressed root identity

Research-only SENS-DERIVATION falsifier.

This benchmark asks whether a normalized proof/certificate address can itself
become the exact semantic identity of a parentless root.

It uses two controls:

1. **Selector generation certificate** — the certificate replays an identity
   whose exact domain and coordinate are already determined by the selector
   generator law. Different certificate serializations may hash differently
   while replaying the same semantic coordinate.

2. **Non-local-exit root** — roothood is already proven, but exact width and
   coordinate remain unresolved. Equivalent proof presentations are normalized,
   then projected to several digest widths.

The important distinction is:

```text
canonical/stable certificate
!=
exact semantic domain
```

A normalized proof may be useful for provenance, self-description, replay or
verification. Under the current #2490 ontology, it does not become Core
semantic authority unless an additional law proves:

```text
proof calculus
+ canonical normalization
+ exact semantic domain
+ canonical binary construction
```

while keeping storage/hash/execution width non-authoritative.

Expected result:

```text
PROOF-ADDRESS=CERTIFICATE-ONLY
EXACT-SEMANTIC-DOMAIN=UNRESOLVED
ROOT-IDENTITY-WIDTH=UNKNOWN
COORDINATE=UNPLACED
NEW-RESIDENTS=0
```
