# План аудиту базису ATOM

> **Для агентних виконавців:** обов’язковий допоміжний процес — `superpowers:subagent-driven-development` (рекомендовано) або `superpowers:executing-plans`. Кроки позначені прапорцями `- [ ]`.

**Мета:** фальсифікувати або підтримати строго слабше виведення поточної тристанової семантики `PRIM_ATOM`, не змінюючи production-семантику.

**Архітектура:** робота живе лише в `docs/research/470/**` та у verification-only дочірніх гілках. Спостереження дає живий evaluator; тимчасові Rust integration-тести можуть лише спостерігати названі результати й не стають новим семантичним oracle. Висновок залишається відносним до явно оголошеного базису.

**Стек:** my-lisp evaluator, Lisp-owned structural contracts, GitHub Actions, тимчасові Rust integration observers.

**Специфікація:** GitHub issue #470 — `[P1][#419/#218] Falsify ATOM structural-kind as irreducible three-way observation`.

## Глобальні обмеження

- Не змінювати production evaluator, Canon registry, `language-contract.lisp`, semantic fixtures, machine layer або Rust semantic producers.
- #305 володіє видаленням stale Rust-шляху `atom`; цей план не редагує `crates/my-lisp/src/eval/builtins.rs`.
- #218 залишається джерелом істини для чинного тристанового result contract.
- Цільові результати рівно: `(structural-kind empty-list|pair|atom)`.
- Generic truth coercion заборонений.
- Host representation tags, `Value::is_atom`, peer-surface recursion, прихований `pair?` або shape oracle не вважаються нижчим базисом.
- На поточному мовному рівні немає try/catch; error recovery не можна припускати.
- Усе, що сильніше за виконаний експеримент, лишається `insufficient-evidence`.

---

### Завдання 1: Зафіксувати obstruction нижнього базису до запуску

**Файл:** `docs/research/470/atom-basis-obstruction.lisp`.

Оголосити:

```text
B470 = {Canon 0, quote, eq, cons, car, cdr, cond, lambda/application, define}
excluded = {atom, aliases, host shape tags, pair?, error catch/recovery, registry round-trip}
```

Перевіряються два часткові маршрути:

- **E:** `eq(x, ())` відділяє Canon 0 від звичайного атома;
- **P:** успішний `car(x)`, значення якого відкидається, розпізнає pair.

Прогноз до запуску:

```text
E(empty) -> identity-relation same
E(atom)  -> identity-relation distinct
E(pair)  -> Type

P(pair)  -> structural-kind pair
P(atom)  -> Type
P(empty) -> Type
```

Без error recovery порядок E→P має обриватися на pair, а P→E — на двох non-pair класах.

### Завдання 2: Виконати probes на NEVER-MERGE child

Verification workflow тимчасово створює `crates/my-lisp/tests/verify_470_atom_basis.rs`, запускає живий `eval_program` і перевіряє:

- чинний ATOM тотально розрізняє empty-list / atom / pair;
- EQ-zero має саме передбачену partial domain boundary;
- projection-success має комплементарну partial domain boundary;
- EQ-first не доходить до COND fallback на pair;
- projection-first не доходить до fallback на non-pair.

Команда:

```bash
cargo test -p my-lisp --test verify_470_atom_basis -- --nocapture
```

Після запуску тимчасовий Rust-файл видаляється, потім виконується `git diff --check`. Verification PR ніколи не merge-иться.

### Завдання 3: Класифікувати лише виконаний маршрут

У research record записати точний PR/run/SHA і кількість тестів.

Якщо прогноз підтвердився, дозволений висновок:

```text
eq-zero + projection-success:
route-falsified-as-total-classifier
```

Причина: комплементарні часткові домени плюс відсутність admitted error recovery.

Не дозволено робити глобальний висновок `ATOM irreducible`.

Відкритими лишаються:

- справді слабший total pair/shape observer, якщо його незалежно обґрунтовано;
- generic shape-case eliminator — це basis exchange, доки не показані слабші observable laws;
- майбутній error-as-data механізм — він змінить нижній базис і потребуватиме нового експерименту.

Фінальний research PR має пройти власний exact-head CI; лише після цього bounded result передається в #470/#419.
