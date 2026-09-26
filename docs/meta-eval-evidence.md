# Межа self-hosting для `lib/meta-eval.lisp`

> **GENERATED FILE — DO NOT EDIT BY HAND.**
> Джерело статусів і claim vocabulary: `knowledge/meta-eval-evidence.lisp`.
> Генератор: `scripts/generate-meta-eval-evidence.py`.

Цей Markdown є лише людською проєкцією machine-readable evidence matrix. Він не створює нової семантичної влади: змінювати статуси треба в `.lisp`, після чого перегенерувати цей файл.

**Стан на:** `2026-09-17`
**Required rows:** 34 · **confirmed:** 34 · **unresolved:** 0
**Усі статуси:** `confirmed`=34, `partial`=0, `broken`=0, `unknown`=0

**Нерозв'язані required rows:** немає.

## Evidence matrix

| Поведінка | Required | Статус | Reference evidence | Meta evidence | Розбіжність / межа | Найменший відсутній доказ |
|---|:---:|:---:|---|---|---|---|
| `canon-resolution-precedence` | yes | **confirmed** | `crates/sens/src/eval/canon.rs`<br>`crates/sens/tests/canon_immutability_meta.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/canon_immutability_meta.rs` | немає в аудитованому scope | немає |
| `canon-binding-rejection` | yes | **confirmed** | `crates/sens/tests/canon_immutability_meta.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/canon_immutability_meta.rs` | немає для lambda binder і top-level def | немає |
| `quote` | yes | **confirmed** | `crates/sens/tests/witness_authority.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/witness_authority.rs` | значення збігаються | немає |
| `cond-short-circuit` | yes | **confirmed** | `crates/sens/tests/witness_authority.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/witness_authority.rs` | значення збігаються на conformance fixtures | немає |
| `symbol-lookup-unknown-symbol` | yes | **confirmed** | `crates/sens/src/error.rs`<br>`crates/sens/tests/meta_eval_errors.rs`<br>`crates/sens/tests/meta_eval_evidence.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_errors.rs`<br>`crates/sens/tests/meta_eval_evidence.rs` | callable і bare unresolved names мають explicit UnknownSymbol ↔ unbound-symbol correspondence; quoted symbol data лишається data | немає |
| `noncallable-type-error` | yes | **confirmed** | `crates/sens/src/error.rs`<br>`crates/sens/tests/meta_eval_errors.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_errors.rs` | native Type явно відповідає data-level not-callable для non-callable operator values | немає |
| `lambda-construction` | yes | **confirmed** | `crates/sens/tests/meta_eval.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval.rs` | closure application parity підтверджена | немає |
| `fixed-arity` | yes | **confirmed** | `crates/sens/tests/meta_eval_errors.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_errors.rs` | successful binding і exact/minimum arity failure correspondence підтверджені | немає |
| `variadic-bare-symbol-lambda` | yes | **confirmed** | `crates/sens/tests/meta_eval.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval.rs` | значення збігаються | немає |
| `dotted-rest-lambda` | yes | **confirmed** | `crates/sens/tests/meta_eval.rs`<br>`crates/sens/tests/meta_eval_errors.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval.rs`<br>`crates/sens/tests/meta_eval_errors.rs` | rest binding і minimum-arity semantics збігаються | немає |
| `lexical-capture` | yes | **confirmed** | `crates/sens/tests/meta_eval.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval.rs` | captured free variable працює | немає |
| `ordinary-noncanon-shadowing` | yes | **confirmed** | `crates/sens/tests/canon_immutability_meta.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/canon_immutability_meta.rs` | звичайний + затінюється, Canon ні | немає |
| `function-application-order` | yes | **confirmed** | `crates/sens/src/eval/mod.rs`<br>`crates/sens/tests/meta_eval_evidence.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_evidence.rs`<br>`crates/sens/tests/meta_eval_error_provenance.rs` | operator evaluation precedes arguments; ordinary arguments evaluate left-to-right and stop at the first failure; private outcome-token identity preserves failure provenance without misclassifying quoted error/fail-shaped user data | немає |
| `primitive-identity-bridge` | yes | **confirmed** | `crates/sens/tests/witness_authority.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/witness_authority.rs` | Canon/list primitive values дають parity | немає |
| `arithmetic-comparison-bridge` | yes | **confirmed** | `crates/sens/tests/witness_authority.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/witness_authority.rs` | арифметичні й binary comparison substrate результати збігаються | немає |
| `chained-comparisons` | yes | **confirmed** | `crates/sens/tests/witness_authority.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/witness_authority.rs` | < = > chains збігаються на selected conformance fixtures | немає |
| `def-compatibility` | yes | **confirmed** | `crates/sens/tests/meta_eval.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval.rs` | top-level def threading і recursive def підтверджені | немає |
| `define-form` | yes | **confirmed** | `crates/sens/src/eval/necessary_forms.rs`<br>`tests/fixtures/meta-semantic-registry-witness.lisp` | `lib/generated/meta-semantic-registry.lisp`<br>`lib/meta-eval.lisp`<br>`tests/fixtures/meta-semantic-registry-witness.lisp` | 0011 define/визначити route through the same registry-derived semantic identity and reproduce native definition behavior; compatibility def remains identity 1000 | немає |
| `macro-recognition-expansion` | yes | **confirmed** | `crates/sens/tests/meta_eval.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval.rs` | raw argument forms expand then evaluate | немає |
| `macro-arity-error` | yes | **confirmed** | `crates/sens/tests/meta_eval_evidence.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_evidence.rs` | reference Arity ↔ meta arity; macro boundary rejects wrong arity before evaluating any expansion value | немає |
| `self-recursive-definitions` | yes | **confirmed** | `crates/sens/tests/meta_eval.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval.rs` | factorial/count-down parity підтверджена | немає |
| `finite-mutual-recursion` | yes | **confirmed** | `crates/sens/tests/meta_eval_mutual.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_mutual.rs` | two-member parity підтверджена | немає |
| `three-member-mutual-recursion` | yes | **confirmed** | `crates/sens/tests/meta_eval_mutual.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_mutual.rs` | >2-member parity підтверджена | немає |
| `recursive-group-forward-references` | yes | **confirmed** | `crates/sens/tests/meta_eval_mutual.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_mutual.rs` | earlier members call later members | немає |
| `recursive-group-member-shadowing` | yes | **confirmed** | `crates/sens/tests/meta_eval_evidence.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_evidence.rs` | local parameter beats same-named group member | немає |
| `recursive-group-captured-environment` | yes | **confirmed** | `crates/sens/tests/meta_eval_evidence.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_evidence.rs` | outer offset survives reconstructed group env | немає |
| `nested-closures-in-recursive-functions` | yes | **confirmed** | `crates/sens/tests/meta_eval_evidence.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_evidence.rs` | nested lambda captures outer offset through recursive call chain | немає |
| `adjacent-nonrecursive-defs-not-false-grouped` | yes | **confirmed** | `crates/sens/src/eval/mod.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_evidence.rs` | dependency-aware SCC recognition groups only mutually reachable lambda definitions; independent adjacent defs, quoted names, and parameter-shadowed names stay outside recursive groups | немає |
| `malformed-recursive-group` | yes | **confirmed** | `crates/sens/tests/meta_eval_evidence.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_evidence.rs` | InvalidForm correspondence survives malformed duplicate parameter in group | немає |
| `arbitrary-later-binding-visibility` | yes | **confirmed** | `docs/adr/ADR-009-SHARED-DEFINITION-FRAME.md`<br>`crates/sens/src/environment.rs`<br>`crates/sens/src/eval/closures.rs`<br>`crates/sens/src/eval/special_forms/core.rs`<br>`crates/sens/tests/meta_eval_later_binding.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_later_binding.rs`<br>`crates/sens/tests/meta_eval_evidence.rs` | ADR-009 shared-frame identity is reproduced with finite Lisp data: later binding and replacement are visible, one-way later lambda calls work without inventing an SCC, caller locals do not leak, and call-before-binding remains unresolved | немає |
| `error-kind-parity` | yes | **confirmed** | `crates/sens/src/error.rs`<br>`crates/sens/tests/meta_eval_errors.rs`<br>`crates/sens/tests/meta_eval_evidence.rs`<br>`crates/sens/tests/canon_immutability_meta.rs`<br>`crates/sens/tests/meta_eval_error_kind_parity.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_errors.rs`<br>`crates/sens/tests/meta_eval_evidence.rs`<br>`crates/sens/tests/canon_immutability_meta.rs`<br>`crates/sens/tests/meta_eval_error_kind_parity.rs` | current explicit meta-evaluator failure scope has paired UnknownSymbol↔unbound-symbol, Type↔not-callable, Arity↔arity, InvalidForm↔invalid-form witnesses across lookup, application, lambda, macro, top-level Canon definition, and malformed recursive-group boundaries; parse/resource/division failures remain outside this evaluator-owned scope | немає |
| `error-detail-parity` | yes | **confirmed** | `docs/language-core-axioms.md`<br>`crates/sens/src/error.rs`<br>`crates/sens/tests/meta_eval_error_detail_boundary.rs` | `docs/adr/ADR-011-ERROR-DETAIL-CONTRACT-BOUNDARY.md`<br>`lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval_error_detail_boundary.rs` | S2 contracts the named error category; Rust message/span and meta Lisp detail payload are diagnostic surfaces without a ratified shared cross-runtime schema; meta structured details remain regression-tested and are not erased by normalization | немає |
| `data-to-code-boundary` | yes | **confirmed** | `crates/sens/tests/meta_eval.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval.rs` | read/read-all data is executed through my-eval/my-eval-program | немає |
| `first-class-evaluation` | yes | **confirmed** | `crates/sens/tests/meta_eval.rs` | `lib/meta-eval.lisp`<br>`crates/sens/tests/meta_eval.rs` | my-eval is an ordinary Lisp binding invoked from Lisp | немає |

## Claim vocabulary

| Твердження | Стан | Правило |
|---|:---:|---|
| `metacircular-evaluator-exists` | **allowed** | allowed while representative programs execute through lib/meta-eval.lisp |
| `self-hosting-witness` | **allowed** | allowed only for the explicitly confirmed/qualified subset in this matrix |
| `partial-self-hosting` | **allowed** | allowed while known gaps remain explicit and executable |
| `complete-self-hosting` | **forbidden** | must remain forbidden while any required row is partial, broken, or unknown |

## Named errors: correspondence, а не текстова тотожність

У paired proofs reference-side `ErrorKind` перевіряється як контрактна категорія, а Lisp meta-evaluator повертає data-level observation. Поточні mappings у covered corpus:

```text
UnknownSymbol ↔ unbound-symbol
Type          ↔ not-callable
Arity         ↔ arity
InvalidForm   ↔ invalid-form
```

ADR-011 фіксує межу detail parity: Rust `message`/`span` і meta Lisp `detail` є діагностичними поверхнями, доки окремий майбутній контракт не ратифікує спільну structured-detail schema. Їх не можна мовчки нормалізувати в удавану семантичну рівність і не треба видаляти лише заради зовнішньої схожості.

## Правило інтерпретації

Differential mismatch — це **finding**, а не автоматично «meta-eval неправильний». Якщо reference runtime суперечить `language-contract.lisp` або ратифікованому ADR, під підозрою reference implementation. Сила self-hosting тверджень обмежується machine matrix і окремим claim vocabulary вище.

Після редагування `knowledge/meta-eval-evidence.lisp` запустіть:

```bash
python3 scripts/generate-meta-eval-evidence.py
python3 scripts/generate-meta-eval-evidence.py --check
```
