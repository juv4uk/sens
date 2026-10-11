# #2214 — Pareto witness: `0101` vs `1001` vs `00101`

Status: research benchmark; no production allocation.

The current evidence proves three separate things:

1. an eager/raw discriminator is necessary (#2193);
2. one transformer capability is sufficient (#2196);
3. LAMBDA is the strongest known typed parent (#2198).

It does **not** yet prove that width 5 is the minimum honest width, because D4 still has the free exact words `0101` and `1001`, and the ratified weak suffix law does not exclude a staged/context-expanding resident (#2158, #2162, #2204).

## Exact payload cost

Framing is excluded here. These are semantic payload bits only.

| Occurrences | D4 candidate | Packed bytes | D5 candidate | Packed bytes |
|---:|---:|---:|---:|---:|
| 1 | 4 bits | 1 | 5 bits | 1 |
| 8 | 32 bits | 4 | 40 bits | 5 |
| 64 | 256 bits | 32 | 320 bits | 40 |
| 1024 | 4096 bits | 512 | 5120 bits | 640 |

Thus 4→5 costs exactly one semantic bit per occurrence, or 25% on this identity lane. Padding in the final physical byte is transport space and is not counted as language meaning.

## Separate proof axes

The executable witness deliberately does not invent one score.

- `0101` and `1001`: shorter, but require coherent D4 revision and currently have only allocation-only placement evidence.
- `00101`: one bit wider, but preserves the confirmed typed refinement `0010 LAMBDA -> 00101 TRANSFORMER` and does not reopen the D4 map.

Under these independent objectives all three remain Pareto-live. Therefore the current machine conclusion is:

```text
D5-WIDTH-LOWER-BOUND=NOT-PROVED
```

That result may change only when a new ratified theorem falsifies the shorter models or changes an explicit input assumption.

## Reproduce

```sh
python3 scripts/bench-2214-domain-width-pareto.py
```

## Principle

**Spend bits only when they buy a stronger law; spend proof facts only when they buy real semantic compression.**
