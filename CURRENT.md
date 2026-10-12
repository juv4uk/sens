# CURRENT — where the truth actually lives

Українською: це єдина точка входу для «що зараз чинне». Якщо будь-який інший документ, включно з архівом, застарілим планом чи старим рев'ю, суперечить джерелам нижче — **чинні джерела нижче перемагають**. `docs/archive/**` зберігає історію, але не є специфікацією.

This file exists per [`DOC-AUTHORITY-ARCHIVE`](https://github.com/juv4uk/ecosystem/issues/5): **one active truth, many preserved histories**. Read this first. Historical material may explain how SENS arrived here, but it cannot override current contract and executable evidence.

## Authority order (highest wins)

1. **Machine-readable language authority**
   - [`language-contract.lisp`](language-contract.lisp) — current Contract 11.9, preserving the Contract 11.8 D1–D9 foundation contract and adding separately ratified D10.
   - [`lib/domains/d1.lisp`](lib/domains/d1.lisp) … [`lib/domains/d9.lisp`](lib/domains/d9.lisp) — canonical human-readable domain tables, **one domain per file**, columns `ук → укр → san → en → LISP → sym`, where `ук` is the compact coding surface and `укр` is the expanded Ukrainian explanation. Surface markers are synchronized across programming surfaces: predicates use `?` in `ук/укр/en`, destructive operations use `!` in `ук/укр/en`; `san` does not use these punctuation markers. D7 has 126 semantic rows and omits owner-reserved `0100001` / `0101010`; no aggregate cross-domain table is authoritative.
   - [`lib/surface/semantic-registry.lisp`](lib/surface/semantic-registry.lisp) — migration input only. Existing exact-eight-bit rows are historical crosswalk evidence, not an executable registry or a source of current identity. All live consumers are to move to generated exact-domain ownership; spelling never owns meaning.
   - [`tests/fixtures/conformance.lisp`](tests/fixtures/conformance.lisp) and other admitted executable conformance fixtures — behavior evidence independent of one host implementation.
   - SENS no longer has one universal 256-slot function ontology. Canonical identity is `exact bits + exact domain + admitted/proved law`. Exact widths W1-W9 are mechanically representable by the domain ladder; D9 uses a distinct non-truncating carrier. Generic callability remains fail-closed and requires an explicit mechanism. Current ratified semantic Core domains are D1–D9 under foundation #4008; D10 is a separately governed research/placement domain, not an implicit extension of Core. D7 is owner-ratified 126/128; D8 is owner-ratified 256/256; D9 is owner-ratified 512/512. `Sens8`/SID8/Function8 is retired as semantic or runtime authority and may exist only as migration evidence until each active consumer is converted.
   - Current generation boundary: Contract 11.9 preserves D1–D9 and recognizes owner-ratified D10 as a WHOLE 1024/1024 domain (2026-10-12), not a per-resident or physical T5 admission. D10 F1/F2/F3/T5 evidence gates are pending; numeric D24+ remains separately owner-ratified.
2. **Ratified ADRs and accepted decisions** — [`docs/adr/`](docs/adr) records scoped decisions. McCarthy/Lisp names in historical ADRs describe provenance or Core1 compatibility; they do not create a second current function ontology.
3. **Reference implementation and substrates**
   - [`crates/sens`](crates/sens) — current Rust reference crate. Rust owns implementation mechanisms, not language meaning.
   - Independent substrates such as C, WASM, FPGA, GraalVM, Common Lisp, Prolog, Datalog, and CLIPS may execute or observe admitted behavior without becoming semantic authority.
4. **Active plans and standing doctrine** — [`AGENTS.md`](AGENTS.md), [`docs/agent-doctrine.md`](docs/agent-doctrine.md), [`PLAN.md`](PLAN.md), [`STATUS.md`](STATUS.md), [`ecosystem-status.md`](ecosystem-status.md), and the currently active scoped plans they reference.
5. **Tests and evidence** — `cargo test --workspace`, `--oracle-check`, focused witnesses, and CI prove what the implementation currently satisfies. A claim without executable or source evidence is a hypothesis, not a fact.
6. **Operational snapshot (2026-10-12)** — [`docs/project-reality-2026-10-12.uk.md`](docs/project-reality-2026-10-12.uk.md) tracks the benchmark-lab registry gap, measured Nano-SENS baseline and its open seed-closure gate, plus D10 runtime-admission boundaries. The pinned Nano-SENS Contract 11.8 run is not evidence of D10 execution under current Contract 11.9.

## Current identity rule

The language is **sens / СЕНС**.

```text
semantic object
=
exact binary word (0/1 digits)
+ exact domain
+ admitted / proved law
```

Current Core examples:

```text
D1  PredicateBit
D2  racana2 structure
D3  bīja3 foundation — 000 (), 001 QUOTE, 010 ATOM, 011 CDR, 100 CAR, 101 EQ, 110 COND, 111 CONS
D4  full compact bootstrap — 0000 APPLY, 0001 EVAL, 0010 LAMBDA, 0011 DEFINE, 0100 NOT, 0101 NULL, 0110 CDAR, 0111 CDDR, 1000 CAAR, 1001 CADR, 1010 LOOKUP, 1011 BIND, 1100 EVCON, 1101 EVLIS, 1110 LIST, 1111 APPEND
D5  full compact 32/32 — owner-ratified #3331 via #3305/#3330; canonical map in knowledge/d5-ratified.json
D6  full compact 64/64 — owner-ratified #3393; canonical map in knowledge/d6-ratified.json
D7  owner-ratified 126/128 — #3572; canonical map in knowledge/d7-ratified.json; 0100001 and 0101010 owner-reserved/pinned
D8  full compact 256/256 — owner-ratified #3960; canonical map in knowledge/d8-ratified.json — clean-room rebuild #3281
D9  full compact 512/512 — owner-ratified #4008; canonical map in knowledge/d9-ratified.json
D10  whole-domain owner-ratified 1024/1024 (2026-10-12), per-row F1/F2/F3 and T5 execution pending
D24+  owner-ratified numeric domain ladder D24/D48/D96/D192/..., separate from function domains
```

**Mathematical operand boundary (owner clarification 2026-10-12):** D1–D10 are domain-qualified binary words, not arithmetic operands. Only explicitly qualified D24/D48/D96/... values and lawful numeric compositions admit `+ - * /` and numeric `< > =`. An operator may have a D5/D6 function identity without making that function identity a number. D3 EQ and D1 predicates are separate non-mathematical laws; old unqualified Number/Rational/BinaryNumber no longer grants arithmetic admission.

**Migration evidence, not a green release claim:** Core checks now include `crates/sens/tests/math_domain_exclusivity.rs` and static admission checks in `scripts/check-numeric-domain-ratification.py`. Local Cargo execution has not yet been verified for these changes because the linked desktop runner is offline. Frozen Core4 still contains old numeric literals and arithmetic, e.g. `lib/core4.lisp:188,193` computes LENGTH by adding `1` to `acc` initialized as `0`; this is incompatible with D24+-only operands until an explicitly admitted domain-preserving migration is available. Do not silently re-enable legacy-number arithmetic to make the test green, and do not claim release pass before exact-SHA CI and Core4 evidence.

Owner foundation ratification #4008 extends the current chain through D9: D1 #1699, D2 #1702, D3 #3202, D4 #3272, D5 #3305/#3330, D6 #3393, D7 #3572, D8 #3960, D9 #4008. #3960 remains the historical D1–D8 foundation cut; D9 is owner-ratified 512/512 under #4008. Intermediate clean-room maps remain research provenance only. Any current implementation or fixture that still uses the superseded ordering `011=COND, 100=CONS, 101=CAR, 110=CDR, 111=EQ` is migration debt tracked by #3203/#2055/#3205/#3206, not an alternate language law.

D10 ratification source: `knowledge/d10-owner-whole-domain-ratification-20261012.json`; current codebook pointer: `knowledge/d10-current-inventory.json`. Domain ratification does not fabricate resident-level proofs. Numeric acts: `contracts/numeric-domains-ratification.lisp` and `knowledge/number-width-ratified.json`.

Equal packed bits in two domains do not imply equal identity. In particular owner-ratified Core.D8 is not historical Sens8 merely because both occupy eight physical bits. D7 Sound/Text residency is ratified under #3572, while LocalOrdinal remains a separate W7 role; neither inherits selector/callable law from width. Width alone does not mint meaning or callability. Ukrainian, English, Sanskrit, symbolic, and compatibility spellings remain source/UI projections only.

Owner direction (2026-10-12): remove active Sens8/SID8/Function8 runtime semantics across Rust, Lisp, scripts, tests, CLI and workflows; replace each call/data position with a width-qualified domain identity and explicit admitted mechanism. No new consumer may be added to the legacy carrier. Historical manifests and archived experiments remain provenance-only and must never be loaded as executable input.

**Виконаний полімовний зріз і залишкові блокери:** [`docs/migration/domain-ladder-cutover-2026-10-12.uk.md`](docs/migration/domain-ladder-cutover-2026-10-12.uk.md) фіксує видалений старий guard, новий Rust/Python/C/Lisp CI, явні D1–D10 координати в Python і ще не перенесені AST/evaluator/capability та Lisp-шляхи. На одному candidate SHA повний green ще **не доведений**; автоматично ототожнювати історичний W8:10101000 INVOKE із чинним D8:10101000 ROUND заборонено.

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
3. Read the relevant `lib/domains/dN.lisp` table and generated domain-owner registry for identity and law. Use `lib/surface/semantic-registry.lisp` only to migrate historical source spellings; never dispatch by an eight-bit row.
4. Inspect `crates/sens` for the current Rust reference mechanism and the relevant executable witnesses for the behavior being changed.
5. Run the focused tests for your slice and then the applicable repository gates before claiming the change works.
