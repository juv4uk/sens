# #2668 — independent root-domain attack

Research-only R3 lane for #2662.

Question:

> Can parentless semantic roots form a separate exact Core domain without
> recreating a flat arbitrary table?

This lane distinguishes two things that are easy to collapse:

1. **membership law** — which semantic objects qualify as roots;
2. **identity constructor** — how qualifying roots receive exact binary
   identities/widths.

The current executable result is expected to be:

```text
ROOT-DOMAIN = TABLE-RELOCATION-UNDER-CURRENT-EVIDENCE
MEMBERSHIP-PREDICATE = COHERENT-RESEARCH-CLASS
EXACT-WIDTH = UNKNOWN
COORDINATE = UNPLACED
```

Negative controls:

- discovery-order numbering;
- human-label sorting;
- width from current root count.

Merged #2681 additionally proves that a lawless one-root exact domain has no canonical width or coordinate under XOR automorphisms. The PROVEN-ROOT predicate remains a coherent research membership class, but it is not sufficient to establish an exact domain.

Proof-derived identity is not evaluated here; it is handed to #2669.

Run:

```bash
python3 benchmarks/independent-root-domain/run.py \
  --out /tmp/independent-root-domain
```
