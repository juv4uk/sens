# Independent semantic reconstruction benchmark

**Issue:** #2138  
**Benchmark authority:** #1987  
**Foundation:** #2103 #2107 #2104 #2118  
**Self-description consumer:** #2022

This benchmark asks a stronger conformance question than ordinary output parity:

> can two independently encoded implementations reconstruct the same semantic
> structure without sharing node IDs, table slots, source order, human names,
> precomputed class IDs, or binary coordinates?

## First bounded family

The input is finite typed DAG evidence. The two sides receive independent local
encodings:

- different node tokens;
- different local role tokens;
- different local relation-kind tokens;
- different row order.

They share only the admitted lower schema that says what each local role/relation
token means in the benchmark contract.

Duplicate evidence rows are present and declared non-semantic for this family.

## Two reconstruction algorithms

1. **partition refinement** — iteratively refines classes from admitted roles and
   typed outgoing target classes until the partition stabilizes;
2. **recursive certificate** — recursively constructs typed structural
   certificates with memoization and deduplicates equal certificates.

The implementations do not compare internal class numbers.

Both emit an exact name-erased quotient certificate whose class coordinates are
reconstructed bottom-up from structure.

## Run

```sh
python3 benchmarks/independent-reconstruction/run.py --smoke
python3 benchmarks/independent-reconstruction/run.py \
  --out /tmp/independent-reconstruction/results
```

Outputs are TSV + JSON.

## Required parity

Every positive case requires:

- exact canonical certificate parity;
- fixed semantic-query answer parity;
- invariance under local renaming and evidence-row permutation.

Negative controls must all be detected:

- one relation-kind change;
- one target/incidence change;
- one extra disconnected residue role.

## Metrics

Portable logical counters are primary:

- evidence reads;
- items entering sorts;
- partition-refinement rounds;
- certificate constructions;
- memo hits;
- quotient classes/edges;
- prepared payload bytes;
- peak logical objects;
- semantic query steps.

Python wall time is diagnostic only. A native/Cachegrind implementation can be
added later under #1987 without changing the semantic workload.

## Interpretation

A passing result proves only the bounded reconstruction statement for this DAG
family. It does **not** prove:

- that all SENS semantics is a DAG;
- that relation kinds are derivable rather than admitted;
- that binary words are foundational;
- that two arbitrary implementations are extensionally complete.

The useful result is narrower: local names and table coordinates are unnecessary
for recovering the tested structure.
