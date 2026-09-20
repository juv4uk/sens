# Ukrainian Surface Coverage Plan

> Повний змістовний український відповідник: [`ukrainian-surface-plan.uk.md`](ukrainian-surface-plan.uk.md). Український текст є первинним відповідно до ратифікованої мовної політики репозиторію.

Status: active implementation plan. This document does not redefine language semantics; it describes how the Ukrainian human-facing surface catches up with already existing public my-lisp functionality.

## Goal

A user should be able to write an ordinary my-lisp program through the Ukrainian surface without knowing the English names of public builtins, necessary forms, or standard-library functions.

The project does **not** create a second Ukrainian implementation of the standard library. There remains one semantic implementation and multiple surface names.

```text
semantic identity / existing implementation
                ↓
        public surface mapping
          ↙             ↘
      English        Ukrainian
```

Principle:

> A word is not the semantics. A surface name maps to an existing semantic identity or existing public definition.

This follows the same separation already used by canon()+7: canonical identity is distinct from spelling.

## Non-goals

- Do not fork or duplicate `lib/core.lisp` merely to translate function names.
- Do not put Ukrainian semantic policy into Rust.
- Do not rename neutral internal Rust identifiers to Ukrainian.
- Do not change the meaning of existing English names.
- Do not treat natural-language understanding/NLP as part of this task. This plan is about the programming-language surface.

## Source of truth

The coverage inventory must be generated or checked against live public names rather than maintained as an isolated hand-written list.

Public names come from these classes:

1. canon()+7 surfaces.
2. Necessary evaluator forms.
3. Root builtins exposed through `language_items()` / the live root environment.
4. Public definitions in `lib/core.lisp`.
5. Public functions of other user-facing `lib/*.lisp` libraries when those libraries are intentionally included in Ukrainian coverage.

The Ukrainian map records, for each public English-facing name:

```text
category | semantic/public identity | English | Ukrainian | status
```

Suggested status values:

- `stable` — Ukrainian name selected and tested.
- `candidate` — proposed name, not ratified.
- `missing` — public English name has no Ukrainian mapping yet.
- `compatibility-only` — English/historical spelling intentionally has no separate Ukrainian public equivalent.

## First authoritative table

The initial table should start with the already ratified or established mappings rather than inventing new names immediately.

| Category | Identity / role | English | Ukrainian | Status |
|---|---|---|---|---|
| Canon | QUOTE | `quote` | `як-є` | stable |
| Canon | ATOM | `atom` | `атом?` | stable |
| Canon | EQ | `eq` | `тотожне?` | stable |
| Canon | CONS | `cons` | `сполучити` | stable |
| Canon | CAR | `car` | `перше` | stable |
| Canon | CDR | `cdr` | `решта` | stable |
| Canon | COND | `cond` | `за-умовою` | stable |
| Necessary form | LAMBDA | `lambda` | `функція` | stable |
| Necessary form | DEFINE | `define` / `def` compatibility | `визначити` | stable |

Everything else begins from live inventory and is reviewed in batches.

## Coverage metric

Define **Ukrainian Surface Coverage (USC)** as:

```text
USC = stable Ukrainian public mappings / eligible public names
```

Report it by layer, not only as one total number:

```text
canon()+7
Necessary forms
Root builtins
Core library
Strings
Collections
Time
Host capabilities
Reasoning / knowledge libraries
Overall
```

The metric is descriptive, not a semantic quality score. A higher percentage means less English vocabulary is required to use the selected public surface; it does not imply better semantics.

## Implementation stages

### Stage 1 — inventory

Generate the live eligible public-name inventory. Compare it with existing `lib/surface/uk.lisp` and Canon surface mappings. Produce a machine-checkable list of `stable`, `candidate`, and `missing` entries.

Exit condition: every eligible public name is classified; there are no invisible gaps.

### Stage 2 — core programming vocabulary

Fill Ukrainian mappings for the names needed to write ordinary programs:

- arithmetic and comparisons;
- predicates;
- lists and collections;
- strings;
- `map` / `filter` / `reduce` family;
- basic I/O where appropriate.

Names are reviewed semantically, not translated mechanically. Prefer short Ukrainian words that reveal the operation.

Exit condition: a nontrivial program using only core facilities can be written without English public operators.

### Stage 3 — library domains

Extend mappings to selected public libraries: time, persistent structures, knowledge/reasoning, and other user-facing modules. Do not require every internal helper to have a Ukrainian alias; eligibility must distinguish public API from implementation helpers.

Exit condition: each selected library has an explicit coverage percentage and no accidental omissions.

### Stage 4 — drift prevention

Add CI checks so new eligible English public names cannot silently appear without being classified in the Ukrainian coverage table.

A new English public symbol may legitimately be marked `missing` or `candidate`, but it must not be invisible.

Exit condition: surface drift is mechanically observable.

### Stage 5 — Ukrainian-only acceptance program

Add one or more acceptance programs that intentionally use only Ukrainian public vocabulary (numeric literals, strings and punctuation are naturally exempt).

The acceptance test should exercise at least:

- definition and lambda;
- conditionals;
- arithmetic/comparison;
- list processing;
- higher-order operation;
- strings;
- one library outside `core.lisp`.

Exit condition: CI executes the program successfully and a reviewer can follow it without knowing English builtin names.

## Naming discipline

For every new Ukrainian candidate ask:

1. What operation does the existing function actually perform?
2. Does the Ukrainian word describe that operation for proper lists, dotted pairs, edge cases and higher-order use?
3. Is the word confused with a stronger claim than the implementation supports?
4. Does it compose naturally with neighbouring names?
5. Can a new user predict behaviour from the name before reading documentation?

This is the same standard used for `перше`, `решта`, `сполучити`, `як-є`, and the other Canon surfaces.

## Architecture constraint

Do not turn the Ukrainian surface into a parallel implementation tree.

Preferred shape:

```text
existing definition / canonical identity
              ↓
       surface binding table
              ↓
   English / Ukrainian / Sanskrit / compatibility
```

For ordinary library functions where there is no immutable Canon identity, the mapping may target the existing public binding/definition rather than inventing a fake canonical primitive identity.

## Immediate work queue

1. Inventory all live public English names.
2. Define eligibility rules: public API vs internal helper.
3. Create the first machine-readable English↔Ukrainian coverage table.
4. Seed it with canon()+7 and `функція` / `визначити` as `stable`.
5. Generate the first USC report by layer.
6. Review the first batch: arithmetic, comparisons, lists, strings, higher-order core functions.
7. Implement aliases/mappings only after names are reviewed.
8. Add tests proving Ukrainian aliases reach the same existing semantics, including shadowing/canonical-identity invariants where relevant.
9. Add CI drift detection.
10. Finish with a Ukrainian-only acceptance program.

## Definition of done

The Ukrainian programming surface is considered caught up for a selected release when:

- every eligible public English name is classified;
- all names in the release's target layers have `stable` Ukrainian mappings;
- no duplicate Ukrainian implementation of the underlying semantics exists;
- mapping tests are green;
- CI detects future coverage drift;
- the Ukrainian-only acceptance program passes.

At that point English remains a supported surface, not a prerequisite for programming in my-lisp.
