# Foundation ladder benchmark (#2111)

This benchmark measures the cost of progressively materializing one fixed
semantic relation:

> two nodes are equivalent iff a declared finite observer signature computed
> from the same finite relation graph is equal.

It is **mechanism evidence**, not semantic authority.

Candidates:

1. `raw-relation` — compare observer facts directly from relation edges;
2. `observer-computed` — construct both complete observer signatures per query;
3. `observer-cached` — prepare signatures once, then compare them;
4. `quotient-class` — prepare observational equivalence classes, then compare class ids;
5. `exact-word` — project quotient classes to exact-width words and compare width+bits;
6. `packed-binary` — checked compact projection of the same quotient coordinate.

Before any performance measurement is accepted, `--verify` exhaustively checks
all node pairs at sizes 32, 128 and 512 against the same reference observer
semantics.

The runner emits:

- `results.tsv` — rows using the shared #1987 benchmark field names plus
  foundation-specific logical counters;
- `raw.log` — parity, native logical-counter runs and raw Cachegrind output;
- `report.md` — compact execute-delta summary;
- Cachegrind data files for audit.

The runner separates:

- preparation;
- total preparation + execution;
- differential execution I refs (`full - prepare`);
- final prepared bytes and peak preparation-state estimate;
- relation-edge reads, observer-field work, quotient lookups and word compares.

No weighted winner is produced. Use the results as a Pareto vector together
with semantic evidence from #2103/#2101/#2096/#2091/#2077 and whole-model
accounting in #1973.
