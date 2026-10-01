# Graph-theoretic domain metrics (#1961)

**Agent:** grok-xai  
**Harness:** `benchmarks/domain-graph-metrics/run.py`  
**Raw:** `1961-graph-metrics.tsv`  
**Not:** Cachegrind / SENS runtime I-refs (#1988)

## Approaches

| # | method | question |
|---|--------|----------|
| 1 | Explicit digraph | bīja3 seed + CAR/CDR prefix family as nodes/edges |
| 2 | **Tarjan SCC** | Does prefix generator induce cycles? |
| 3 | DAG height | Longest derivation path in edges |
| 4 | **Hamming-1** same-width edges | Is “cube geometry” the same graph as the generator? |
| 5 | Compression ratio | `nodes / generator_actions` vs flat registry |
| 6 | BFS touch steps | Abstract mechanism steps to expand the family |

## Results (selector family)

| depth | nodes | prefix edges | nontrivial SCC | height | rows/actions |
|------:|------:|-------------:|---------------:|-------:|-------------:|
| 1 | 6 | 4 | **0** | 1 | 3.0 |
| 2 | 14 | 12 | **0** | 2 | 7.0 |
| 4 | 62 | 60 | **0** | 4 | 31.0 |
| 8 | 1022 | 1020 | **0** | 8 | 511.0 |

### Graph facts (replication-invariant for this model)

1. **Prefix graph is a pure DAG** — Tarjan finds **0** nontrivial SCCs at every measured depth. Safe for “root + acyclic suffix program”.
2. **Hamming-1 ≠ prefix generator** — Hamming edges are *same width*; prefix edges *increase width*. `hamming_edges_not_prefix == all hamming edges` by construction. Cube adjacency cannot encode the generator law.
3. **Seed width-3 Hamming density = 12/28 ≈ 0.43** — the 8 seed words are **not** a complete Hamming graph; global “everything is a cube neighbor” is false even at the seed layer.
4. **Compression** grows ~2^depth: two suffix actions generate an exponentially larger explicit table.

## Relation to other benches

| bench | role |
|-------|------|
| this | *structure* of the domain graph |
| #1988 | *CPU* of executing paths on that graph |
| #1973 | *accounting* rows vs identities |
| #1989 | *carrier* for storing a word |

Do not treat DAG height as instruction count.

## Falsifiers reinforced

- Global Hamming-1 as semantic authority — **rejected** (orthogonal to prefix edges; seed incomplete).
- Need for cycles in selector family — **rejected** (SCC trivial).
- Flat table as only scalable representation — **weakened** (exponential row growth vs 2 actions).

## Run

```sh
python3 benchmarks/domain-graph-metrics/run.py
```
