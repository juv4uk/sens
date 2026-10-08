# Core-Math selector involution (#3345)

Bounded current-law probe under #3331.

Coordinate law:

```text
dual_w(x) = x XOR (2^w - 1)
```

Independent semantic law:

```text
toggle CAR <-> CDR at every selector choice
```

Current D3-D5 selector family: 14 residents / 7 semantic dual pairs.

Expected result:

- semantic/coordinate commute: 14/14;
- involution replay: 14/14;
- false `XOR 1` control: 0/14;
- false MSB-only toggle: 0/14;
- exact random-placement probability that all seven semantic pairs accidentally
  align with the width-local complement involution:
  `1 / 828,316,125`.

This is family-local. It does not assert that XOR-complement is a global
semantic duality for every D4/D5 resident.
