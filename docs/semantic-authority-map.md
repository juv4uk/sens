# sens (СЕНС) semantic authority map

Status: CURRENT ARCHITECTURE MAP. This file does not create new language semantics. It records where a current claim must be checked before prose is trusted.

## One rule

> The language owns meaning and domain-qualified semantic identity; runtimes provide mechanisms and conformance evidence.

No implementation file, README paragraph, agent note, benchmark, or historical plan may silently outrank the current language contract.

## Authority order

When two sources disagree, use this order:

1. **`language-contract.lisp`** — the current machine-readable contract and ratified observable invariants.
2. **Ratified ADRs under `docs/adr/`** — scoped decision records. A historical ADR can preserve McCarthy/Lisp provenance without turning historical names into current function identities.
3. **Executable conformance evidence** — admitted fixtures such as `tests/fixtures/conformance.lisp`, `tests/fixtures/macro-conformance.lisp`, and focused executable witnesses.
4. **Reference implementation** — `crates/sens` (Rust). It is the current reference mechanism, not the owner of semantics merely because it is Rust.
5. **Independent implementations and execution substrates** — C, WASM, FPGA, GraalVM, Common Lisp, Prolog, Datalog, CLIPS, and other declared executors. They can falsify implementation-specific assumptions and provide mechanisms without creating a second language.
6. **Generated reference** — for example `docs/generated/function-table.md` and other generated inventories. Generated output describes an admitted projection; it does not redefine the contract.
7. **Human explanatory prose** — `README.md`, `CURRENT.md`, tutorials, and architecture notes.
8. **Historical/process material** — archived plans, dated audits, old agent notes, and superseded decisions. These remain evidence of history, not current semantic authority.

If a lower item conflicts with a higher item, the lower item is stale until reconciled.

## Current SENS semantic identity

Canonical semantic identity is domain-qualified:

```text
semantic object
=
exact binary number
+ exact domain
+ admitted / proved law
```

Current Core examples are exact-width D1 PredicateBit, D2 structure, D3 foundation, D4 bootstrap, and owner-ratified D5/D6 domains. Equal packed numeric payloads in two domains do not imply equal semantic identity, and width alone does not grant occupancy or callability.

Historical exact-eight-bit Sens8/Sid8/Function8 values remain bounded compatibility, transport, backend, and provenance projections while #2817 migrates runtime consumers. They are not the universal current ontology.

Human spellings in Ukrainian, English, Sanskrit, symbolic notation, and compatibility surfaces are **source/UI routing metadata**. A surface may route to an already-admitted domain-qualified semantic object; it does not own identity or meaning.

The concrete empty proper list `()` is Core.D3 `000`. It is distinct from historical exact-eight-bit `00000000`, PredicateBit `0`, and Number zero even though their packed numeric payloads may look related.

## Historical Lisp and Core1 provenance

Lisp was the original syntactic carrier and experimental substrate from which SENS developed. McCarthy's 1960 evaluator remains important historical evidence and is intentionally preserved in **Core1** compatibility/bootstrap research.

Names such as historical Lisp operations may therefore appear in Core1 material, archived research, provenance notes, old ADR context, and compatibility witnesses. Such names are historical descriptions or surfaces; they are not the active function ontology of SENS.

Current Core profiles may select mechanisms and separately ratified profile behavior, but they do not mint or renumber domain residents and may not override the shared D1/D3 predicate-control foundation.

## Bootstrap and implementation mechanisms

Do not collapse three different questions:

- **language identity and laws** — owned by SENS contract and admitted executable evidence;
- **bootstrap/evaluator mechanisms** — implementation machinery needed to realize admitted behavior;
- **derived language behavior** — behavior defined by SENS programs once the bootstrap substrate exists.

Rust may contain parser, evaluator, closure, macro, lowering, host-boundary, or other mechanisms. Those implementation structures do not become function identities. Likewise, a language-defined closure or macro can become the execution mechanism for an admitted domain resident without making its human spelling authoritative.

## Project identity and source extensions

The project/repository name is **`sens`**. Historical project provenance includes the former working name **`my-lisp`**.

The current canonical source extension is **`.lisp`** (see [sens#81](https://github.com/juv4uk/sens/issues/81): extension is never semantics). **`.wsm`** and **`.my`** remain supported legacy aliases. Ukrainian filename spellings supported by the tooling are likewise source-surface choices, not semantic identities.

## Reference implementation terminology

Use these terms consistently:

```text
semantic authority        = language-contract + ratified decisions + executable conformance
SENS semantic object      = exact bits + exact domain + admitted/proved law
surface                   = source/UI routing metadata
reference implementation  = crates/sens (Rust)
independent substrate      = another conformance/execution target
```

Avoid wording that makes Rust, a surface spelling, a historical Lisp name, or an execution island the canonical owner of language meaning.

## Host boundary

A host operation earns its place by providing information/effects unavailable inside pure language semantics or by enforcing an embedding security boundary that untrusted language code must not be able to self-grant.

Two different meanings of policy must not be collapsed:

1. **semantic/application policy** — what an observation means, how bytes become text, how a result is classified; keep this language-owned when it is derivable there;
2. **embedding authorization policy** — which filesystem roots, process names, connect targets, or listen targets a partially trusted session may touch; this belongs at the trusted host boundary.

A useful split is:

```text
host observation/effect       -> mechanism
SENS law/result interpretation -> language
authorization                 -> trusted host boundary
```

Rust/host code may grow as needed. The architectural prohibition is the reverse semantic flow: a host mechanism must not become the source of SENS meaning.

## Documentation rule

New prose that states a contract-level fact should point to the authoritative source instead of inventing an independent restatement. If repetition is useful for teaching, phrase it explicitly as a summary and keep executable drift checks for facts that can be verified mechanically.

Archived and dated documents may preserve old names, paths, ontologies, and conclusions. They are not rewritten merely to resemble current terminology. Current implementation claims must be checked against current contract, source, and executable evidence.

The goal is not fewer documents. The goal is one authority for each kind of claim.
