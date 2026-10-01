# #2027 first selector self-description benchmark

Environment:
- Intel Core i5-6400 @ 2.70 GHz
- WSL2 kernel 6.18.33.2
- rustc 1.98.1
- Valgrind 3.27.0
- 20,000 explanations per row
- 3 Cachegrind samples
- depths 0,1,2,4,8,16
- repeated and deterministic-random identity workloads

Correctness gate:
- all flat/certificate/graph/hybrid routes reconstruct the same name-erased
  selector explanation tuple `(root, suffix, depth)`;
- parity PASS after fixing one graph-specific suffix orientation bug.

Representative repeated-path I-refs / explanation:

```text
depth   flat    certificate   graph traversal   hybrid hot
0       19.996  10.497        23.997            10.497
1       19.996  10.497        43.996            10.497
2       19.996  10.497        53.996            10.497
4       19.996  10.497        73.996            10.497
8       19.996  10.497       113.996            10.497
16      19.996  10.496       193.997            10.496
```

Random-path results preserve the same qualitative ordering.

Bounded findings:
1. Compact certificate explanation costs roughly half the flat metadata lookup
   in this standalone mechanism model.
2. Explicit graph traversal grows with path depth and is already slower than
   flat metadata at depth 0; by depth 16 it is about 194 I-refs/explanation.
3. Hybrid hot use is essentially identical to certificate use because graph
   verification is paid in preparation, not on every explanation.
4. The explicit graph control also materializes intrinsic selector lineage
   already encoded in the canonical word. PR #2048 independently shows those
   per-node selector facts can be derived rather than stored.
5. The first graph implementation exposed an ordering/canonicalization bug
   before measurement. This is evidence that reconstruction conventions are
   themselves complexity and should be counted.

Interpretation boundary:
- this is a selector positive-control benchmark, not a verdict against typed
  semantic graphs globally;
- recursive/SCC and non-prefix families may still require graph facts that are
  not intrinsic to the word;
- the result supports a role split for the selector family:
  graph/evidence cold, normalized certificate hot.

Research conclusion:
```text
canonical word + small family law
  -> compact certificate
  -> hot explanation / compiler input

typed graph
  -> non-intrinsic evidence / cold verification
```

No production migration is authorized by this benchmark.
