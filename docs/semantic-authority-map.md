# sens (СЕНС) semantic authority map

Status: CURRENT ARCHITECTURE MAP. This file does not create language semantics. It tells agents where a current claim must be checked before prose is trusted.

## One rule

> The language owns function identity and semantics; runtimes own mechanisms and prove conformance.

No implementation file, README paragraph, agent note, benchmark, generated table, surface spelling, or historical plan may silently outrank the ratified SENS contract.

## Authority order

When current sources disagree, use this order:

1. **`language-contract.lisp`** — Contract 9.0 and later ratified contract revisions. The complete function-identity space is exactly the 256 eight-bit SENS values `00000000..11111111`.
2. **Ratified contract/ADR artifacts in their stated scope** — only decisions explicitly marked current/ratified. Historical ADRs remain historical evidence and do not override a later language contract.
3. **Executable SENS-owned laws and conformance evidence** — current contract/witness files and tests that execute them.
4. **Reference implementation** — `crates/sens` plus its current consumers such as `crates/sens-cli`, `crates/sens-host`, and `crates/sens-wasm`. Rust is implementation/mechanism evidence, not semantic authority merely because it executes the language.
5. **Independent substrates/kernels** — FPGA, C/WASM, GraalVM, Common Lisp, Prolog, Datalog, CLIPS and other declared executors. They may own native mechanisms and producer-native observations, never SENS meaning.
6. **Generated projections/reference** — generated tables and documentation describe a projection of current authority; they do not mint identities or laws.
7. **Human explanatory prose** — `README.md`, `docs/language-core.md`, tutorials and architecture notes.
8. **Historical/process material** — archived plans, dated audits, superseded reviews and old implementation names. They are provenance, not current specification.

If a lower item conflicts with a higher item, the lower item is stale until reconciled.

## Function identity and surfaces

There is one function ontology:

```text
00000000
...
11111111
```

Each function identity is the eight bits themselves (`Sens8`). A word, string, symbol, enum label, historical primitive name, opcode or backend selector is not a second function identity.

`lib/surface/semantic-registry.lisp` may provide optional human/source spellings that route mechanically to an already-existing exact `Sens8`. Those spellings are UI/source metadata only. They do not own meaning and must not become a `name -> meaning -> SENS` or `SENS -> named identity -> law` layer.

The structural empty value `()` is outside the 256-function space.

## Core profiles

Core1, Core2, Core3 and Core4 are law profiles over the same 256 SENS identities. Selecting a profile may change the admitted law, result domain or mechanism for a SENS function, but never its eight-bit identity and never the global function space.

Historical McCarthy/Lisp material remains important provenance, especially for Core1, but it is not the current global function ontology.

## Bootstrap and evaluator mechanisms

Do not confuse identity with mechanism.

The evaluator may contain local mechanism classes or temporary implementation labels needed to execute an already-selected exact SENS function. Such labels are not language identities and cannot define meaning. Remaining named-mechanism debt such as `NecessaryFormIdentity` is explicitly tracked by #1328 and must not be described as current semantic identity.

Likewise, `crates/sens/src/eval/canon.rs`, generated dispatch tables, IR roles and host registries are mechanisms/projections. They are valid only insofar as they conform to SENS-owned authority.

## Project identity and source extensions

The project and repository are **`sens`** (СЕНС). The historical repository/project name `my-lisp` may appear in preserved history and compatibility evidence, but is not the current product identity.

The canonical source extension remains **`.lisp`**. Supported aliases such as **`.sens`** and **`.сенс`** are source/UI conveniences, not semantics.

## Reference implementation terminology

Use these terms consistently:

```text
semantic authority       = ratified SENS contract + SENS-owned executable laws
function identity        = exact Sens8 only
surface                  = optional source/UI routing metadata
mechanism                = executor-local way to execute an already-selected Sens8
reference implementation = crates/sens and current sens-* consumers
independent executor     = another substrate/kernel proving bounded conformance
```

Avoid phrases that imply Rust, a surface name, a kernel operator, or a historical Lisp primitive defines SENS meaning.

## Host and kernel boundary

A host or island may provide effects, observations, lifecycle and native computation unavailable inside pure language semantics. It may not gain semantic authority from being registered or available.

The required direction is:

```text
exact Sens8
    ↓
selected Core law / admitted mechanism
    ↓
executor or host mechanism
    ↓
producer-native observation
```

Host registration is availability, not ordinary SENS admission. Kernel names/opcodes remain mechanism data, not function identities.

## Documentation rule

Current prose that states a contract-level fact should point to the authoritative source instead of re-specifying an independent truth. Historical documents may retain old names and old models when clearly historical; current-authority documents must use current SENS terminology and current paths.

For the current entry point, read `CURRENT.md` first. Archived material under `docs/archive/**` is non-normative by construction.
