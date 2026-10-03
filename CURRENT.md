# CURRENT — where the truth actually lives

Українською: це єдина точка входу для «що зараз чинне». Якщо будь-який інший документ, включно з архівом, застарілим планом чи старим рев'ю, суперечить джерелам нижче — **чинні джерела нижче перемагають**. `docs/archive/**` зберігає історію, але не є специфікацією.

This file exists per [`DOC-AUTHORITY-ARCHIVE`](https://github.com/juv4uk/ecosystem/issues/5): **one active truth, many preserved histories**. Read this first. Historical material may explain how SENS arrived here, but it cannot override current contract and executable evidence.

## Authority order (highest wins)

1. **Machine-readable language authority**
   - [`language-contract.lisp`](language-contract.lisp) — current Contract 11.0 domain-qualified observable language contract.
   - [`lib/surface/semantic-registry.lisp`](lib/surface/semantic-registry.lisp) — transitional source/UI routing metadata. Existing eight-bit rows are compatibility projections while #2817 migrates canonical identity to exact domains. A spelling is never semantic identity and does not own meaning.
   - [`tests/fixtures/conformance.lisp`](tests/fixtures/conformance.lisp) and other admitted executable conformance fixtures — behavior evidence independent of one host implementation.
   - SENS no longer has one universal 256-slot function ontology. Canonical identity is `bits + exact domain + admitted/proved law`; current Core domains D1-D6 are width-qualified, and compatibility Sens8/Sid8 does not define canonical identity. Structural `()` is Core.D3 `000` as a semantic object and remains distinct from predicate/number domains.
2. **Ratified ADRs and accepted decisions** — [`docs/adr/`](docs/adr) records scoped decisions. McCarthy/Lisp names in historical ADRs describe provenance or Core1 compatibility; they do not create a second current function ontology.
3. **Reference implementation and substrates**
   - [`crates/sens`](crates/sens) — current Rust reference crate. Rust owns implementation mechanisms, not language meaning.
   - Independent substrates such as C, WASM, FPGA, GraalVM, Common Lisp, Prolog, Datalog, and CLIPS may execute or observe admitted behavior without becoming semantic authority.
4. **Active plans and standing doctrine** — [`AGENTS.md`](AGENTS.md), [`docs/agent-doctrine.md`](docs/agent-doctrine.md), [`PLAN.md`](PLAN.md), [`STATUS.md`](STATUS.md), [`ecosystem-status.md`](ecosystem-status.md), and the currently active scoped plans they reference.
5. **Tests and evidence** — `cargo test --workspace`, `--oracle-check`, focused witnesses, and CI prove what the implementation currently satisfies. A claim without executable or source evidence is a hypothesis, not a fact.

## Current identity rule

The language is **sens / СЕНС**.

```text
00000000
...
11111111
```

Those exact eight-bit forms are the 256 SENS functions. There is no parallel named-function identity layer. Ukrainian, English, Sanskrit, symbolic, and compatibility spellings are source/UI routes only.

`()` is not function `00000000`, function `11111111`, or any other member of the 256-function space. It is a separate structural value.

Historical McCarthy names remain useful when discussing the 1960 evaluator, Core1, migration evidence, or provenance. They are not the current ontology of SENS.

## What is explicitly NOT authoritative

- **`docs/archive/**`** — preserved superseded designs, completed plans, research spikes, historical audits, and reactions.
- Any dated report or PoC not explicitly promoted into the current authority chain.
- A host implementation detail merely because it is implemented in Rust, C, Java, Common Lisp, Prolog, Datalog, CLIPS, or another executor.
- A peer agent's report that something is fixed without a verifiable commit/test/CI witness.
- A human surface spelling as a substitute for the exact eight-bit SENS function it routes to.

## For a new agent starting cold

1. Read `AGENTS.md` and `docs/agent-doctrine.md`.
2. Read `language-contract.lisp` and this file before trusting older design prose.
3. Read `lib/surface/semantic-registry.lisp` only as routing metadata; do not infer function meaning from a spelling.
4. Inspect `crates/sens` for the current Rust reference mechanism and the relevant executable witnesses for the behavior being changed.
5. Run the focused tests for your slice and then the applicable repository gates before claiming the change works.
