# Ratified D1-D4 foundation benchmark

This lane replaces the old CI comparison of English Lisp against historical
8-bit SENS identities. The active baseline is the owner-ratified exact-width
foundation recorded in #2151 and #2162.

## Measured foundation

```text
D1  PredicateBit(Bit1)   answer
D2  Racana2(Bit2)        structure
D3  Bija3(Bit3)          foundational action
D4  Bit4                 ratified bootstrap address width
```

D4 is measured through a benchmark-local transparent wrapper because production
D4 semantics is still implemented under #2169. The benchmark does not create a
second semantic role table.

## Cases

- `d1`, `d2`, `d3`, `d4`: identical construct -> typed wrapper ->
  packed read -> last-bit read loop, so cross-width ratios are meaningful.
- `ladder`: exact append D1->D2->D3->D4, parent, and prefix operations.
- `selector`: D3 selector roots `101` and `110` extended to the ratified
  generated D4 selector words `1010/1011/1100/1101`.
- `mixed`: typed mixed-domain dispatch without numeric width collapse.

Every run verifies the exact-width mechanics before Cachegrind measurement.
The primary metric is CPU instruction references (I refs); the same-iteration
empty-loop baseline is subtracted and three repetitions are reported.

## Non-goals

This is mechanism evidence, not semantic authority. It does not:

- compare human spellings to binary identities;
- use historical Function8 low nibbles as D1-D4 mappings;
- allocate the two free D4 words;
- redefine D1-D4 roles;
- infer semantic parenthood from benchmark speed.
