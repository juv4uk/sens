# my-lisp semantic authority map

Status: CURRENT ARCHITECTURE MAP. This file does not create new language semantics. It defines where an existing claim must be checked before prose is trusted.

## One rule

> The language defines its semantics; runtimes prove conformance to it.
>
> Rust knows mechanisms. Lisp knows the language.

No implementation file, README paragraph, agent note, benchmark, or historical plan may silently outrank the semantic contract.

## Authority order

When two sources disagree, use this order:

1. **`language-contract.lisp`** — machine-readable Level 1/2 contract version and ratified observable invariants.
2. **Ratified ADRs under `docs/adr/`** — closed decisions whose scope is explicitly stated, especially `ADR-004-CLOSED-MCCARTHY7-CORE.md`.
3. **Executable conformance evidence** — `tests/fixtures/conformance.lisp`, `tests/fixtures/macro-conformance.lisp`, `lib/canon.lisp`, and the tests that execute those contracts.
4. **Reference implementation** — `crates/my-lisp`. It is the mature software oracle used to test behavior, not the owner of semantics merely because it is Rust.
5. **Independent implementations** — `fpga-lisp`, `c-runtime/`, and other declared substrates. Their value is that they can falsify implementation-specific assumptions.
6. **Generated reference** — for example `docs/FUNCTIONS.md`. Generated output describes the current implementation surface but does not redefine the contract.
7. **Human explanatory prose** — `README.md`, `docs/language-core.md`, tutorials, architecture notes.
8. **Historical/process material** — `PLAN.md`, dated audits, agent notes, superseded decisions. These are evidence of history, not current semantic authority.

If a lower item conflicts with a higher item, the lower item is stale until reconciled.

## Semantic identity vs surface spelling

A spelling is not a primitive identity. Canon 0 + McCarthy-7 remain the stable historical/minimal root:

```text
quote · atom · eq · cons · car · cdr · cond
```

The project also treats the concrete empty proper list `()` as Canon 0: a value/syntax identity, not an eighth operation and not a lexical alias.

Natural-language and historical surfaces map onto semantic identities; changing a surface name does not create a new primitive.

## Bootstrap forms

Do not collapse three different questions:

- **semantic primitives** — evidence-admitted identities under Contract 7.0 / ADR-005, with Canon 0 + McCarthy-7 retained as the stable historical root;
- **evaluator-controlled bootstrap forms** — machinery needed to create language behavior;
- **derived language forms** — behavior expressible by the language once the bootstrap substrate exists.

The current implementation is actively reducing host-owned bootstrap behavior. `lib/macro.lisp` owns the normal `defmacro` binding, and the Rust evaluator no longer has a `defmacro` fallback. Standard `Session` construction evaluates the macro layer before user code; a bare `Environment::root()` intentionally remains the smaller Rust kernel. `define`/`lambda` have explicit necessary-form identities in the evaluator, while historical `def` compatibility remains. These are implementation facts and do not silently rewrite `language-contract.lisp`; observable-contract changes still require the contract process.

## Project identity and source extensions

The project/repository name is **`my-lisp`**.

The current canonical source extension is **`.lisp`** (per [my-lisp#81](https://github.com/juv4uk/my-lisp/issues/81) — extension is never semantics). **`.lisp`** and **`.lisp`** remain fully supported legacy aliases. The separate repository named `wsm` is unrelated foundational research; the shared letters do not rename this language project.

## Reference implementation terminology

Use these terms consistently:

```text
semantic authority       = contract + ratified decisions + executable conformance
reference implementation = crates/my-lisp (Rust)
independent substrate     = fpga-lisp / c-runtime / other conformance target
```

Avoid “canonical Rust implementation” when the intended meaning is “reference implementation”. A canonical implementation would imply that Rust itself defines semantics, which contradicts the conformance architecture.

## Host boundary

A host operation earns its place by providing information/effects unavailable inside pure language semantics or by enforcing an embedding security boundary that untrusted language code must not be able to self-grant.

Two different meanings of “policy” must not be collapsed:

1. **semantic/application policy** — what an observation means, how bytes become text, which default bind address a language API chooses, how a Guard finding is reasoned about. Move this into Lisp when it is derivable and doing so reduces duplicate semantic authority;
2. **embedding authorization policy** — which filesystem roots, process names, connect targets, or listen targets a partially-trusted session is permitted to touch. This belongs to the host boundary because the program being constrained must not be able to redefine or self-grant the check.

A useful split is:

```text
mono-ns                       -> host observation
mono-ms                       -> Lisp derivation
unix-time-now                 -> host observation
UTC/Gregorian                 -> Lisp interpretation
raw process/TCP/filesystem I/O -> host mechanism
UTF-8/result/default API policy -> Lisp when derivable
Guard decision semantics      -> Lisp
Guard protocol validation     -> trusted boundary adapter
filesystem/TCP authorization  -> host embedding policy
```

Thus “shrink Rust, grow Lisp” is not a security rule. It concerns semantic ownership. A tiny host-side authorization check can be architecturally correct even when the corresponding language-level meaning is Lisp-owned.

Current per-session host scopes are documented in `docs/host-capability-scoping-adr-2026-08-27.md`; the living host semantic inventory is `docs/host-semantic-surface.md`.

## Documentation rule

New prose that states a contract-level fact should link to the authoritative source instead of re-specifying the fact in a new independent wording. If repetition is necessary for teaching, phrase it as a summary and keep a drift test for facts that are easy to contradict mechanically.

Dated reviews such as `docs/capabilities.md` snapshots may remain valuable evidence even after implementation advances; their date/status must not be mistaken for current authority. Current implementation claims should be rechecked against PLAN, current ADR status, source, and executable evidence.

The goal is not fewer documents at any cost. The goal is one authority for each kind of claim.


Current primitive-admission authority: [`adr/ADR-005-OPEN-PRIMITIVE-ARCHIPELAGO.md`](adr/ADR-005-OPEN-PRIMITIVE-ARCHIPELAGO.md).
