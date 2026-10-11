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

Current Core examples are exact-width D1 PredicateBit, D2 structure, D3 foundation, D4 bootstrap, owner-ratified D5/D6, D7 126/128 under #3572, D8 256/256 under #3960, and D9 512/512 under #4008. Equal packed numeric payloads in two domains do not imply equal semantic identity, and width alone does not grant occupancy or callability.

Historical exact-eight-bit Sens8/Sid8/Function8 values remain bounded compatibility, transport, backend, and provenance projections while #2817 migrates runtime consumers. They are not the universal current ontology.

Human spellings in Ukrainian, English, Sanskrit, symbolic notation, and compatibility surfaces are **source/UI routing metadata**. Current canonical human-readable projections for D1–D9 live one domain per file in `lib/domains/d1.lisp` … `lib/domains/d9.lisp`; D9's normative machine-readable identity map remains `knowledge/d9-ratified.json`. D1–D9 columns: `ук → укр → san → en → LISP → sym`. The D9 human table does not imply W9 runtime support or Core ownership; those remain separate implementation/ownership axes. A surface may route to an already-admitted domain-qualified semantic object; it does not own identity or meaning. Historical `lib/surface/semantic-registry.lisp` remains compatibility/provenance only.

The concrete empty proper list `()` is Core.D3 `000`. It is distinct from historical exact-eight-bit `00000000`, PredicateBit `0`, and Number zero even though their packed numeric payloads may look related.

## Historical Lisp and Core1 provenance

Lisp was the original syntactic carrier and experimental substrate from which SENS developed. McCarthy's 1960 evaluator remains important historical evidence and is intentionally preserved in **Core1** compatibility/bootstrap research.

Names such as historical Lisp operations may therefore appear in Core1 material, archived research, provenance notes, old ADR context, and compatibility witnesses. Such names are historical descriptions or surfaces; they are not the active function ontology of SENS.

Current Core profiles may select mechanisms and separately ratified profile behavior, but they do not mint or renumber domain residents and may not override the shared D1/D3 predicate-control foundation.

## Математика є спільною для всіх ядер

**Нормативне джерело:** `language-contract.lisp`, інваріанти
`mathematics-all-kernels`, `number-ladder-all-kernels` і `math-parity-proof`.
`contracts/core-profile-contract.lisp` не дозволяє профілю змінювати математичну семантику.

Математика **не належить лише Core-Math**. Core-Math є напрямом відкриття та
доведення законів; **Core1, Core2, Core3, Core4, interpreter/oracle, bytecode,
AOT/compiler та CPU/GPU/FPGA/GraalVM/Futhark й інші ядра** споживають
**ті самі допущені закони SENS**. Ядро може бути ще не готовим до їх виконання;
це `UNSUPPORTED/BLOCKED`, а не інша арифметика.

- `Number` є одним окремим семантичним простором із власними ратифікованими
  місткостями **24→48→96→192→…**, визначеними
  `knowledge/number-width-ratified.json`. Це не D24/D48 функціональні домени
  і не вибір GPU-регістра. `Text7`-цифри не можуть замінити `Number`.
- Арифметичний виклик має явний двійковий код операції та домен; обидва
  операнди й результат є точними двійковими об'єктами. Числове порівняння
  повертає окремий D1 `PredicateBit`, не числове 0/1.
- Математика над функціональними координатами (XOR, добуток, композиція,
  квадрат/корінь тощо) є законною *операцією над бітами*, але не автоматичним
  доказом нового значення або нового функціонального резидента.
- Жодне ядро не може мовчки округлити значення, замінити `Number` на host
  `f64`, втратити провідні нулі точного функціонального слова або вивести
  знакове/раціональне кодування з особливостей свого процесора.
- Ратифіковані **лише числові ширини**; двійковий знак, дробовий layout,
  переповнення/авторозширення і правило читання десяткових літералів
  залишаються нератифікованими. Ядра мають fail-closed замість самостійного
  вигадування представлення.

**Перевірка завершення:** для кожного ядра — той самий набір допущених
операцій/входів, точні очікувані біти, D1 результати, негативні тести,
читання/запис/повторне читання, незалежне підтвердження семантики й фактичний
CI на тому самому SHA. `UNKNOWN`, `UNSUPPORTED`, `BLOCKED` та `FAIL`
не перетворюються на `PASS`. Відсутній механізм — відкрита робота цього
ядра, **не** привід створювати нове математичне ядро чи гілку.

## Number-домени без обов'язкових літералів

**Пріоритет Core, уточнений власником 11.10.2026:** для мови
існує домен-кваліфіковане двійкове значення, а не необхідність
писати число як `#b...`, `#d...` чи десяткову строку.
Вихідний текстовий токен — лише факультативна проєкція читача.

- Семантичний об'єкт = точні біти + **його домен** + допущений закон.
  Арифметичні числа належать окремому простору `Number`, де
  ратифіковані `Number24 → Number48 → Number96 → Number192 → …`.
  Функціональні D1–D9, PredicateBit, D2 і Text7 залишаються іншими
  просторами навіть для однакових бітових payload.
- Не планувати нову роботу над синтаксисом числових літералів.
  Існуючі reader-нотації можуть залишатися для спадкової сумісності
  та введення/виведення, але **не визначають числової семантики**.
- Стан виконання: `crates/sens/src/binary_number.rs` має натуральну
  точну бітову арифметику та перевірку деяких числових місткостей;
  `Value::BinaryNumber` ще не включає явного Number-домену у власну
  ідентичність. Його нормалізовані біти **не доводять** завершеності
  ратифікованого доменного представлення.
- Схема знака, дробів, автоматичного розширення й десяткового
  перетворення не ратифікована; відсутній закон має давати явний
  `BLOCKED/UNSUPPORTED`, а не нову довільну семантику.
- Core-Math, Core1–Core4 та зовнішні ядра зараз **заморожені**.
  Уточнення пріоритету доменів не є дозволом поновлювати їхню
  розробку, Actions або бенчмарки.

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
surface                   = source/UI routing metadata; current human tables are lib/domains/dN.lisp
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
