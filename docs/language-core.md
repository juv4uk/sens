# my-lisp language core · Ядро мови my-lisp · my-lisp-Sprachkern

> **A small language that grows itself. · Маленька мова, що вирощує себе. · Eine kleine Sprache, die sich selbst wachsen lässt.**

This document is the compact human explanation of the current core architecture. It is **not** the highest semantic authority. For conflicts, follow [`semantic-authority-map.md`](semantic-authority-map.md): `language-contract.lisp` and ratified ADRs outrank explanatory prose.

## Identity

The language/project name is **`my-lisp`**.

The current canonical source extension is **`.lisp`** (per [my-lisp#81](https://github.com/juv4uk/my-lisp/issues/81) — extension is never semantics). **`.wsm`** and **`.my`** remain fully supported legacy aliases. The separate repository named `wsm` is not this language project.

`crates/my-lisp` is the **reference Rust implementation**. It is the mature software oracle used to check behavior, but it does not gain semantic authority merely by being the reference implementation.

```text
semantic authority        = contract + ratified decisions + executable evidence
reference implementation  = crates/my-lisp (Rust)
independent implementations = fpga-lisp, c-runtime, other declared substrates
```

## Reader invariant

At the start of an expression, apostrophe `'` is reader sugar for canonical
quotation. Inside a symbol it remains an ordinary Unicode character, so natural
Ukrainian words are not split.

На початку виразу апостроф `'` є синтаксичним цукром канонічного цитування.
Усередині символу він лишається звичайним знаком, тому українські слова не
розриваються.

These forms are equivalent:

```lisp
(quote expression)
'expression
```

For example, `об'єкт` is one symbol, while `'об'єкт` means
`(quote об'єкт)`.

## Canon 0 + McCarthy-7 as stable historical root

Canon 0 + McCarthy-7 remain a stable historical/minimal root. Permanent closure of the primitive set is superseded by [`adr/ADR-005-OPEN-PRIMITIVE-ARCHIPELAGO.md`](adr/ADR-005-OPEN-PRIMITIVE-ARCHIPELAGO.md):

```text
quote · atom · eq · cons · car · cdr · cond
```

No later capability acquires primitive status merely because it is useful or implemented in Rust. A new primitive identity requires the evidence-based admission discipline of ADR-005.

### Canon 0

The concrete empty proper list is:

```lisp
()
```

It is Canon 0: a concrete value/syntax identity and the inductive base of proper lists. It is **not an eighth operation** and has no canonical lexical alias.

The intended structural laws include:

```text
ATOM(CONS(x,y)) = false
CAR(CONS(x,y))  = x
CDR(CONS(x,y))  = y

(a b c) = (a . (b . (c . ())))
```

Pair projections are pair operations, not dotted-pair-only special cases.

## Surface names are not semantic identity

A symbol spelling does not become the primitive itself.

```text
"car"    != primitive identity CAR
"перше"  != primitive identity CAR
"ādi"    != primitive identity CAR
```

Different surfaces may denote the same semantic identity. Ordinary lexical bindings may still shadow names according to the current contract; that does not mutate the underlying identity.

The current canonical teaching/research surfaces are documented separately from the core identity. This document therefore avoids treating any natural-language spelling as the essence of a primitive.

## Bootstrap boundary

The closed seven-operation set and the implementation bootstrap are different things.

The evaluator still needs mechanisms for such things as:

- lexical environments and symbol lookup;
- closures and application;
- definition/binding;
- controlled evaluation for forms such as quotation/conditionals;
- exact numeric representation;
- structured errors;
- a capability boundary to the external world.

Those mechanisms do not automatically become new semantic primitive identities.

### Necessary forms and derived forms

Current implementation work distinguishes evaluator-controlled necessary-form identities from forms the language can derive after bootstrapping.

`define` and `lambda` have explicit necessary-form identities in the evaluator. Historical `def` compatibility remains. `lib/macro.lisp` owns the normal `defmacro` binding, and the Rust evaluator no longer has a `defmacro` fallback. A bare `Environment::root()` remains the smaller Rust kernel, while standard `Session` construction evaluates the macro layer before user code.

This is an **implementation ownership migration**, not an automatic semantic-contract rewrite. `language-contract.lisp` remains authoritative for observable Level 1/2 guarantees until deliberately revised.

Bootstrap order matters:

```text
minimal Rust mechanisms
        ↓
macro layer
        ↓
core library
        ↓
semantic libraries
        ↓
natural-language / application surfaces
```

The architectural rule is:

> If a construct can be expressed by the language itself, do not embed it in the host without a concrete reason.

## Exact arithmetic

Exact arithmetic is a kernel-level semantic commitment. Integer/rational operations must not silently become floating point.

The Rust reference runtime currently supplies low-level arbitrary-precision integer/rational machinery. That is an implementation mechanism supporting the exactness contract; it does not mean high-level arithmetic policy belongs in Rust by default.

Performance costs caused by stronger exactness are measured rather than hidden. Correctness and observable semantics take precedence over pretending exact arithmetic is free.

## Host capability boundary

The core distinction is not “Rust versus Lisp”. It is **mechanism versus meaning**.

```text
external world
    ↓
host observation / capability
    ↓
my-lisp data
    ↓
Lisp interpretation / policy
```

A host operation should remain host-owned when it provides an external fact/effect the language cannot derive from values it already has.

A deterministic transformation of an existing fact is a candidate for Lisp ownership.

### Time as the current example

Current direction:

```text
Rust: mono-ns
Lisp: mono-ms, elapsed/deadline semantics

Rust: unix-time-now
Lisp: civil-from-days, utc-from-unix, utc-now

Rust: raw NTP/network observation
Lisp: accepted timestamp interpretation and calendar meaning
```

This is tracked in [`host-semantic-surface.md`](host-semantic-surface.md).

The rule is intentionally conservative: first implement the language-owned equivalent, then add deterministic tests, then prove ownership, then migrate consumers, and only then remove the host duplicate.

## Runtime and capability crates

`crates/my-lisp` owns language-runtime mechanisms such as values, parsing, evaluation, lexical environments, exact arithmetic, and structured diagnostics.

OS-facing filesystem/process/TCP capabilities belong behind explicit host boundaries rather than leaking into language semantics. `crates/my-lisp-host` exists for this purpose.

Some compatibility mechanisms may still live in the core implementation during migration. Their presence is not proof that their policy belongs there permanently; each one is auditable against the Host Semantic Surface test.

## Conformance

A claim of language compatibility is about observable behavior, not internal architecture.

The main evidence chain is:

```text
language-contract.lisp
        +
ratified ADRs
        +
tests/fixtures/conformance.lisp
        +
executable language-owned laws such as lib/canon.lisp
        ↓
implementation conformance claim
```

Independent substrates matter because a second implementation can expose assumptions that a single implementation cannot falsify.

Rust, C/assembly, and FPGA do **not** need the same internal representation. They need the same contract-level behavior within documented resource limits.

## Error semantics

Error categories covered by `language-contract.lisp` are observable semantics. Implementation refactors must therefore preserve contract-level error classification rather than collapsing distinct failures into a convenient generic error.

For the current exact version and ratified invariants, read `language-contract.lisp` directly rather than copying a version number from prose.

## Derived language systems

Large parts of the repository deliberately live above the language core:

```text
lib/core.lisp          standard language
lib/macro.lisp         macro bootstrap layer
lib/time.lisp          time/calendar semantics
lib/meta-eval.lisp     metacircular experiments
lib/unify.lisp         unification
lib/reason.lisp        backward chaining
lib/forward.lisp       forward chaining
lib/knowledge.lisp     knowledge modules
lib/world.lisp         immutable history/world semantics
lib/epistemic.lisp     epistemic layer
lib/understand.lisp    controlled-language ingestion
lib/narrate.lisp       controlled-language rendering
```

Their existence demonstrates the language growing itself, but they do not silently become primitive semantics.

## Architecture levels

A useful current map is:

```text
L0  runtime/substrate mechanisms
L1  closed semantic core (Canon 0 + seven operations)
L2  bootstrap / standard language
L3  semantic libraries
L4  reasoning
L5  knowledge/history/epistemic systems
L6  explicit host capabilities
L7  applications and ecosystem experiments
```

Dependencies and authority should generally point downward. A high-level subsystem must not redefine a lower-level semantic fact by convenience.

## Documentation discipline

Detailed builtin/function inventory belongs in generated or specialized documentation such as [`FUNCTIONS.md`](FUNCTIONS.md), not duplicated manually here.

Historical decisions belong in dated ADRs/audits/versioning notes. They should not remain mixed into the current contract explanation after being superseded.

When current prose and executable evidence disagree, fix the prose or explicitly open a contract change. Do not let ambiguity become a third semantic state.

## Further reading

- [`../language-contract.lisp`](../language-contract.lisp) — machine-readable current Level 1/2 contract version;
- [`semantic-authority-map.md`](semantic-authority-map.md) — authority hierarchy;
- [`host-semantic-surface.md`](host-semantic-surface.md) — host/Lisp ownership audit;
- [`adr/ADR-004-CLOSED-MCCARTHY7-CORE.md`](adr/ADR-004-CLOSED-MCCARTHY7-CORE.md) — historical closed-set decision, partially superseded;
- [`adr/ADR-005-OPEN-PRIMITIVE-ARCHIPELAGO.md`](adr/ADR-005-OPEN-PRIMITIVE-ARCHIPELAGO.md) — current primitive-admission and kernel-archipelago decision;
- [`language-core-axioms.md`](language-core-axioms.md) — broader draft axioms and project principles;
- [`../tests/fixtures/conformance.lisp`](../tests/fixtures/conformance.lisp) — executable fixtures;
- [`../lib/canon.lisp`](../lib/canon.lisp) — language-owned Canon laws;
- [`FUNCTIONS.md`](FUNCTIONS.md) — current generated reference.

---

## Українське резюме

Семантична істина належить не Rust-файлу, а контракту та виконуваним доказам. Rust — референсна реалізація й host-механізм. Lisp має забирати собі все значення й політику, які може вивести з уже наданих фактів.

```text
Rust дає світові двері.
Lisp вирішує, що означає те, що через них приходить.
```

Сім примітивних операцій замкнені назавжди. `()` — Canon 0, а не восьмий примітив. Поверхневі назви не є семантичними identity. Нові можливості мають виростати над ядром, не розширювати його без доказу.

---

## Deutsche Zusammenfassung

Semantische Autorität liegt beim Vertrag und ausführbarer Evidenz, nicht bei einer einzelnen Rust-Datei. Rust ist die Referenzimplementierung und stellt Mechanismen bereit; ableitbare Bedeutung und Policy sollen in der Sprache leben.

Die sieben klassischen McCarthy-Operationen bleiben ein stabiler historischer/minimaler Ursprung. `()` ist Canon 0. Neue primitive Identitäten sind nach ADR-005 evidenzbasiert zulässig; Oberflächennamen sind weiterhin nicht mit semantischer Identität gleichzusetzen.
