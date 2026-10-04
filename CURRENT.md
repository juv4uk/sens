# CURRENT — where the truth actually lives

Українською: це єдина точка входу для «що зараз чинне». Якщо будь-який інший документ, включно з архівом, застарілим планом чи старим рев'ю, суперечить джерелам нижче — **чинні джерела нижче перемагають**. `docs/archive/**` зберігає історію, але не є специфікацією.

This file exists per [`DOC-AUTHORITY-ARCHIVE`](https://github.com/juv4uk/ecosystem/issues/5): **one active truth, many preserved histories**. Read this first. Historical material may explain how SENS arrived here, but it cannot override current contract and executable evidence.

## Authority order (highest wins)

1. **Machine-readable language authority**
   - [`language-contract.lisp`](language-contract.lisp) — current Contract 11.2 domain-qualified observable language contract.
   - [`lib/surface/semantic-registry.lisp`](lib/surface/semantic-registry.lisp) — transitional source/UI routing metadata. Existing exact-eight-bit rows are compatibility projections while #2817 migrates canonical identity to exact domains. A spelling is never semantic identity and does not own meaning.
   - [`tests/fixtures/conformance.lisp`](tests/fixtures/conformance.lisp) and other admitted executable conformance fixtures — behavior evidence independent of one host implementation.
   - SENS no longer has one universal 256-slot function ontology. Canonical identity is `exact bits + exact domain + admitted/proved law`. Exact widths W1-W8 remain mechanically representable; current ratified semantic Core domains are D1-D4 and D7, while D5/D6/D8 are UNRATIFIED/RESEARCH under #3278. Historical Sens8/Sid8 is compatibility/provenance only.
2. **Ratified ADRs and accepted decisions** — [`docs/adr/`](docs/adr) records scoped decisions. McCarthy/Lisp names in historical ADRs describe provenance or Core1 compatibility; they do not create a second current function ontology.
3. **Reference implementation and substrates**
   - [`crates/sens`](crates/sens) — current Rust reference crate. Rust owns implementation mechanisms, not language meaning.
   - Independent substrates such as C, WASM, FPGA, GraalVM, Common Lisp, Prolog, Datalog, and CLIPS may execute or observe admitted behavior without becoming semantic authority.
4. **Active plans and standing doctrine** — [`AGENTS.md`](AGENTS.md), [`docs/agent-doctrine.md`](docs/agent-doctrine.md), [`PLAN.md`](PLAN.md), [`STATUS.md`](STATUS.md), [`ecosystem-status.md`](ecosystem-status.md), and the currently active scoped plans they reference.
5. **Tests and evidence** — `cargo test --workspace`, `--oracle-check`, focused witnesses, and CI prove what the implementation currently satisfies. A claim without executable or source evidence is a hypothesis, not a fact.

## Current identity rule

The language is **sens / СЕНС**.

```text
semantic object
=
exact binary number
+ exact domain
+ admitted / proved law
```

Current Core examples:

```text
D1  PredicateBit
D2  racana2 structure
D3  bīja3 foundation — 000 (), 001 QUOTE, 010 ATOM, 011 CDR, 100 CAR, 101 EQ, 110 COND, 111 CONS
D4  full compact bootstrap — 0000 APPLY, 0001 EVAL, 0010 LAMBDA, 0011 DEFINE, 0100 NOT, 0101 NULL, 0110 CDAR, 0111 CDDR, 1000 CAAR, 1001 CADR, 1010 LOOKUP, 1011 BIND, 1100 EVCON, 1101 EVLIS, 1110 LIST, 1111 APPEND
D5  UNRATIFIED / RESEARCH — clean-room rebuild #3279
D6  UNRATIFIED / RESEARCH — clean-room rebuild #3280
D7  Sound7 + local śloka/sūtra ordinal domain
D8  UNRATIFIED / RESEARCH — clean-room rebuild #3281
```

Owner ratification #3202 fixes the D3/bīja3 A map above under laws L1–L5. Owner ratification #3272 fixes the full compact D4 16/16 map above; intermediate clean-room D4 maps are research provenance only. Any current implementation or fixture that still uses the superseded ordering `011=COND, 100=CONS, 101=CAR, 110=CDR, 111=EQ` is migration debt tracked by #3203/#2055/#3205/#3206, not an alternate language law.

Equal packed bits in two domains do not imply equal identity. In particular an eight-bit D8 research carrier is not historical Sens8 merely because both occupy eight physical bits. D7 is Sound7/local-ordinal identity and does not inherit selector/callable law from width. Width alone does not mint meaning or callability. Ukrainian, English, Sanskrit, symbolic, and compatibility spellings remain source/UI projections only.

Historical exact-eight-bit Sens8/Sid8/Function8 forms remain bounded compatibility, transport, backend and provenance mechanisms while #2817 migrates runtime consumers. They are not current universal semantic authority.

Structural `()` is the admitted Core.D3 `000` object. It is not historical exact-eight-bit `00000000`, PredicateBit `0`, or Number zero; those equal-looking numeric payloads remain distinct across domains.

Historical McCarthy names remain useful when discussing the 1960 evaluator, Core1, migration evidence, or provenance. They do not create a second current identity ontology.

## What is explicitly NOT authoritative

- **`docs/archive/**`** — preserved superseded designs, completed plans, research spikes, historical audits, and reactions.
- Any dated report or PoC not explicitly promoted into the current authority chain.
- A host implementation detail merely because it is implemented in Rust, C, Java, Common Lisp, Prolog, Datalog, CLIPS, or another executor.
- A peer agent's report that something is fixed without a verifiable commit/test/CI witness.
- A human surface spelling as a substitute for the exact domain-qualified semantic object it routes to.

## For a new agent starting cold

1. Read `AGENTS.md` and `docs/agent-doctrine.md`.
2. Read `language-contract.lisp` and this file before trusting older design prose.
3. Read `lib/surface/semantic-registry.lisp` only as transitional routing/compatibility metadata; do not infer domain membership or meaning from a spelling or eight-bit row.
4. Inspect `crates/sens` for the current Rust reference mechanism and the relevant executable witnesses for the behavior being changed.
5. Run the focused tests for your slice and then the applicable repository gates before claiming the change works.
