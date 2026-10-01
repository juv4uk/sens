# Pure-graph bīja3 support pressure (#2019 companion)

**Agent:** grok-xai  
**Harness:** `benchmarks/domain-graph-pressure/run.py`  
**Independent of:** corpus diagnostic PR #2031 (different input graph)

## Method

Only edges: CAR/CDR **prefix_gen** expansions. Non-selector seeds have **no** outgoing edges in this model.

```text
high support  ≠  necessary root
low support   ≠  removable root
graph absence ≠  logical independence
```

## Result (depth=4 suffix)

| seed | name | support | exclusive dependents |
|------|------|--------:|---------------------:|
| 000 | NIL | 1 | 0 |
| 001 | QUOTE | 1 | 0 |
| 010 | ATOM | 1 | 0 |
| 011 | EQ | 1 | 0 |
| 100 | CONS | 1 | 0 |
| **101** | **CAR** | **31** | **30** |
| **110** | **CDR** | **31** | **30** |
| 111 | COND | 1 | 0 |

Positive control: CAR/CDR each own exclusive selector descendants — matches the spirit of #2031 corpus pressure (CAR/CDR exclusive > 0).

Non-selector seeds show support=1 only because **this graph does not encode** Lisp corpus dependencies. That is intentional honesty, not a deletion warrant.

## Coordination

| artifact | role |
|----------|------|
| #2031 | corpus-declared dependency pressure |
| this | pure generator-graph pressure |
| #1961 graph-metrics | SCC / Hamming / compression |
| #1973 | whole-model accounting consumer |

No production allocation. No seed deletion recommendation.
