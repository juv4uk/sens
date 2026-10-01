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


## Evidence tiers

The primary reproducible CPU row for #1987 is the pinned-Guix run recorded in
`evidence/pinned-guix-i5-6400-f954fb9.md` and its compact TSV. It was executed
through `guix time-machine -C channels.scm` on owner hardware.

The GitHub-hosted workflow is deliberately labeled `hosted-smoke`. It reruns
semantic parity and Cachegrind with the hosted Rust toolchain, publishes raw
artifacts, and checks that the pinned primary evidence remains versioned. It is
a secondary portability/regression witness, not a substitute for the pinned
environment.

GitHub's distro `apt guix 1.4.0` currently fails while bootstrapping the
repository's modern pinned channels before this harness starts; that
infrastructure problem is tracked separately in #2146 rather than weakening the
pinned-environment requirement.
