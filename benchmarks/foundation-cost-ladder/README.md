# Foundation cost ladder

**Issue:** #2115  
**Benchmark gate:** #1987  
**Foundation inputs:** #2103 #2105 #2107 #2101 #2096 #2091 #2077

This benchmark asks one semantic question in six representations:

```text
raw relation
 -> indexed observer
 -> cached observer
 -> observational quotient
 -> exact word coordinate
 -> packed binary coordinate
```

The observation is deliberately narrow and explicit:

```text
sig_O(x) = { a | exists y. x -a-> y }
x ≈_O y iff sig_O(x) = sig_O(y)
```

Every candidate must return identical answers. The benchmark measures **where work is paid**, not which representation owns semantic truth.

## Run

```sh
python3 benchmarks/foundation-cost-ladder/run.py --smoke
python3 benchmarks/foundation-cost-ladder/run.py --out /tmp/foundation-cost-ladder/results
```

Outputs are TSV + JSON.

## Metrics

Deterministic logical metrics are primary:

- relation facts touched;
- indexed reads;
- signature constructions;
- cache / quotient lookups;
- exact-word symbol comparisons;
- packed comparisons;
- prepared object count;
- modeled prepared payload bytes.

`prepare_ns` and `execute_ns` are diagnostics only. Do not declare a winner from Python wall time.

The benchmark explicitly separates preparation from execution. Cached/quotient/word/packed candidates are not allowed to hide the work that creates their derived view.

## Interpretation guard

A fast quotient, word, or packed coordinate is an implementation result. It is **not evidence that quotient classes, words, or packed integers are the semantic foundation**.

Native Cachegrind/I-ref work should reuse the same corpus and query semantics under #1987.
