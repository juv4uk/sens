# D7 LocalOrdinal corpus (#2739)

Generated from the pinned transmitted Śiva-sūtra canon. The committed projection lives under `fixtures/` because the D7 lock is identity authority and must travel with an explicit machine witness.

This corpus means only:

```text
D7 LocalOrdinal 1..14
-> exact 7-bit provenance/source-order coordinate
-> donor Śiva-sūtra record
```

It does **not** mean:
- arithmetic Number;
- D7 -> D24/D48 widening;
- grammar dependency from ordinal adjacency;
- D14 grammatical identity;
- occupancy of any other D7 coordinate.

Regenerate/check with the pinned upstream checkout:

```sh
python3 benchmarks/d7-local-ordinal-corpus/generate.py \
  --upstream-root .upstream/shiva-sutras --check
```
