# Whole-model Pareto consumer

**Issue:** #1973  
**Protocol:** #1987

Joins **published** evidence from domain benches into one vector.
Does not re-implement #1988 / #1989 / #1993 harnesses.

| input | axis |
|-------|------|
| #1973 machinery ledger | rows / generators / identities |
| #1988 | execution route I-refs |
| #1989 | carrier I-refs / ceilings |
| #1993 | framing decode (provisional) |
| generator-economy | rule vs rows avoided |

Artifacts:
- `docs/research/1973-pareto-from-published.tsv`
- `docs/research/1973-pareto-from-published.md`

```sh
python3 benchmarks/generator-economy/run.py
```
