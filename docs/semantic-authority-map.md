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

Current Core domains include D1 PredicateBit, D2 structure, D3 foundation, D4 bootstrap, owner-ratified D5/D6, D7 126/128 under #3572, D8 256/256 under #3960, D9 512/512 under #4008, and peer numeric D24/D48/D96/D192/... ratified 2026-10-11. Equal packed numeric payloads in two domains do not imply equal semantic identity, and width alone does not grant occupancy or callability.

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

- **D24, D48, D96, D192, … є справжніми числовими доменами SENS,
  рівноправними з D1–D9** за семантичним статусом. Їхня драбина:
  `D(24·2^n)`, `n≥0`. Вони не просто фізичні `Number24`-місткості,
  не псевдоніми функцій та не GPU-регістри. Акти:
  `contracts/numeric-domains-ratification.lisp` і
  `knowledge/number-width-ratified.json`. Цифри `Text7` не замінюють D24.
- Арифметичний виклик має явний двійковий код операції та домен; обидва
  операнди й результат є точними двійковими об'єктами. Числове порівняння
  повертає окремий D1 `PredicateBit`, не числове 0/1.
- Математика над функціональними координатами (XOR, добуток, композиція,
  квадрат/корінь тощо) є законною *операцією над бітами*, але не автоматичним
  доказом нового значення або нового функціонального резидента.
- Жодне ядро не може мовчки округлити значення, замінити `Number` на host
  `f64`, втратити провідні нулі точного функціонального слова або вивести
  знакове/раціональне кодування з особливостей свого процесора.
- Ратифіковані числові домени, **однодоменне натуральне додавання з
  переносом до наступного домену**, а також **математичні композиції
  NEG і скороченого RATIO всередині D24+**. Ці композиції не є окремими
  атомами Dn. Двійкове кодування композицій, callable-механізми, повна
  арифметика зі знаком та дробами, автоматична змішанодоменна конверсія
  й політика переповнення інших операцій **ще не реалізовані/не допущені**.
  Не підтримувану дію відхиляти fail-closed.

**Перевірка завершення:** для кожного ядра — той самий набір допущених
операцій/входів, точні очікувані біти, D1 результати, негативні тести,
читання/запис/повторне читання, незалежне підтвердження семантики й фактичний
CI на тому самому SHA. `UNKNOWN`, `UNSUPPORTED`, `BLOCKED` та `FAIL`
не перетворюються на `PASS`. Відсутній механізм — відкрита робота цього
ядра, **не** привід створювати нове математичне ядро чи гілку.

## Ратифіковані числові домени D24/D48/D96/…

Пряме рішення власника від 11.10.2026: **D24, D48, D96, D192, … — повноцінні
домени SENS, рівноправні D1–D9**, а не просто ступені місткості
бездоменного Number. Рівність статусу не означає рівність змісту.
Новим уточненням власника **не створено D24Z/D48Q**: від'ємні цілі
та дроби мають канонічні **закони композиції над числовими атомами
D24+**. Для базових натуральних атомів жоден біт не відбирається
під знак або дробовість. Фізичне кодування NEG/RATIO, callable-механізм
та загальні неявні переходи **ще не допущені**. Доменні значення не потребують
текстових літералів; саму належність до домену не можна
вивести лише з довжини невизначеного бітового слова.

## Закони знака та дробів у наявних D24+ (11.10.2026)

**Вказівка власника:** змінити числове сімейство D24 → D48 → D96 → …,
**не** створювати окремих знакових чи дробових доменів. Із фіксованих
n бітів отримуємо рівно `2^n` різних натуральних атомів. Тому
до цих самих атомів **неможливо** додати всі від'ємні цілі й дроби
без окремої однозначної композиції або зміни попередніх значень.
Природний носій кожного базового Dn лишається повнорозрядним.

**Ратифікована математична семантика (ще не physical opcode/wire):**

- `NEG(x)`: `x` — явно допущене **ненульове** натуральне Dn.
  Єдина математична протилежність, жодного окремого `NEG(0)`.
  Знак не займає біт із Dn, і не створено D24Z/D48Z.
- `RATIO(p,q)`: `q>0`, `gcd(abs(p),q)=1`.
  `p` — натуральний Dn або канонічно заперечений `NEG(x)`.
  `RATIO(0,q)` приводиться до наявного нуля відповідного домену.
  `RATIO(p,1)` приводиться до цілого числа. В інших випадках `q>1`.
  Немає округлення, нескорочених дублювань і знаменника нуль.
- Входові атоми **зберігають точні домени кожного компонента**.
  Математичне значення `D24(1)/D48(2)` не дає права стерти
  різницю доменів або призначити один flat D24-word усьому дробу.
- `NEG` та `RATIO` тут — **пояснювальні назви законів**, не
  англомовні функціональні коди canonical SENS.
  Для їх виконання потрібні admitted binary-opcodes/позиційне
  обрамлення, окремі конформанс-тести та Core evaluator.

У Core є вузький бітовий доказ `BinaryNumber::reduce_numeric_domain_ratio_parts`:
точно обчислює НСД і повертає скорочені **ті самі Dn-носії**
чисельника й знаменника; `can_be_negated_in_numeric_domain`
перевіряє допустимість ненульової величини. Це механізми
нормалізації, **не повне виконання signed/rational об'єктів**.
Заморозка Core1–4/Core-Math/інших підкладок і правило лише `main`
зберігаються.

## Числові домени у двійкових форматах Core (11.10.2026)

Механічні відображення **не створюють нових семантичних доменів**.
`BinaryNumber` уже несе `numeric_domain_width` і цілісні
біти D24/D48/…; правила цих доменів залишаються у мовному
контракті та ратифікації.

- У `BinaryFrame::BinaryNumber` збережено старий `EXT_BINARY_NUMBER`
  із `gamma0(length>0)` та нормалізованим payload для
  **некваліфікованого** історичного числа.
- Раніше недопустима довжина `gamma0(0)` в цьому самому
  обрамленні відділяє **явно доменне** значення:
  `gamma0(0) + gamma0(Dn.width) + exactly n binary bits`.
  Це метадані обрамлення, не D2-код, не людський літерал і
  не нова мова. Відкидаємо неретифіковані ширини та неповні payload.
- AST FASL / program wire отримали **адитивні, окремі** теги:
  FASL `13` + `u32 LE width` + повне Dn-слово;
  wire `0x5B` + `varint(width)` + повне Dn-слово.
  Старі теги `12` і `0x5A` лишилися сумісними та
  не несуть доменної ідентичності.
- `OuterRecord::N` у ще не ратифікованому зовнішньому
  конверті **відмовляє** для Dn, бо інакше губив би домен.
  `Value::to_canonical_wire_string()` теж не є маршрутом
  передавання доменних чисел. Розв'язання канонічного
  **фізичного .sens / reader** належить окремому акту #2189/#3134,
  тому не називати механічні FASL/wire обрамлення ратифікацією
  фізичного формату.

## Точне додавання й перенесення до вищого числового домену

Уточнення власника від 11.10.2026: два **повнорозрядні значення D24**
під час додавання можуть утворити суму шириною 25 біт. Така сума
**не може лишитися в D24**; наступний домен **D48** приймає повне
значення без втрати переносу. Узагальнено для однодоменних невід'ємних
операндів Dn, де `n=24·2^k`:

- `a+b < 2^n` → результат лишається Dn.
- `a+b ≥ 2^n` → результат переходить до D(2n), із повними
  `2n` бітами доменного слова. Останні `n+1` або менше біт
  представляють суму, старші біти нового домену доповнюються нулями.
- Жодного обрізання carry, wraparound або неявного `mod 2^n`.
- Натуральні **MUL, невід’ємне SUB та точне ціле DIV** теж тепер
  реалізовані у Core для двох операндів **одного Dn**.
  MUL лишає Dn, якщо добуток поміщається, і бере D(2n), коли ні;
  адже добуток двох n-бітних натуральних чисел має щонайбільше
  2n бітів. SUB із від’ємною різницею та DIV з ненульовою
  остачею fail-closed — їм потрібні компоновані NEG/RATIO Value.
  Змішанодоменна арифметика не допущена.

Механізм `BinaryNumber::add_admitted_numeric` і Core evaluator
вже повертають точне `Value::BinaryNumber` із конкретним Dn
за законом переносу, перевірено Core-only CI. 
`reduce_numeric_domain_ratio_parts` лише **механічно**
скорочує чисельник і знаменник бінарним НСД; не створює
новий семантичний дріб чи callable-механізм.
Core1–Core4, Core-Math та зовнішні виконавці залишаються замороженими.

## Наступні працюючі натуральні операції Core D24+ (11.10.2026)

Додатково до ADD тепер допущено **два явно доменні операнди одного Dn**:

- `MUL(a,b)`: без втрати значущих бітів; точний добуток із
  місткістю до 2n бітів; Dn, якщо результат помістився, і D(2n)
  інакше (наприклад, `D24(max) × D24(max)` дає D48).
- `SUB(a,b)`: якщо `a≥b` — точний натуральний Dn.
  Якщо `a<b`, механізм може повернути ознаку NEG і
  `Dn(b−a)`, але канонічне від'ємне `Value` ще не реалізоване.
- `DIV(a,b)`: при `b>0` точні частка `q` та
  остача `r` у Dn, `a=b·q+r`, `0≤r<b`.
  Якщо `r=0`, Core повертає цілочисельну частку Dn.
  Якщо `r>0`, повинен створюватися RATIO за ратифікованим
  законом, але відповідного `Value` ще немає — явний блок,
  **не** округлення до `q`. Ділення на нуль — помилка.

Перевірено властивостями через незалежний `u32` oracle
для малих входів і повними D24/D48/D96/D192/D384 крайовими
свідками. Математика одна на весь SENS; зупинені ядра не
перевірялися й не розморожувалися. Немає нових доменів,
числових літералів, неявної конверсії D24↔D48 або вигаданого
opcode для композицій NEG/RATIO.

## Number-домени без обов'язкових літералів

**Пріоритет Core, уточнений власником 11.10.2026:** для мови
існує домен-кваліфіковане двійкове значення, а не необхідність
писати число як `#b...`, `#d...` чи десяткову строку.
Вихідний текстовий токен — лише факультативна проєкція читача.

- Семантичний об'єкт = точні біти + **його домен** + допущений закон.
  Числові об'єкти належать **D24 → D48 → D96 → D192 → …**,
  які мають той самий онтологічний рівень, що й D1–D9, але
  власні закони та ідентичності. D1 PredicateBit, D2 структура,
  D7 Text7 і функціональні домени з ними не ототожнюються.
- Не планувати нову роботу над синтаксисом числових літералів.
  Існуючі reader-нотації можуть залишатися для спадкової сумісності
  та введення/виведення, але **не визначають числової семантики**.
- Стан виконання: `crates/sens/src/binary_number.rs` має натуральну
  точну бітову арифметику та перевірку деяких числових місткостей;
  `Value::BinaryNumber` уже зберігає явний `numeric_domain_width` для
  D24/D48/... у своїй ідентичності, а FASL/wire та Core binary frame
  підтримують їхній точний round-trip. Це **не** означає завершення
  фізичного T5 reader чи композицій NEG/RATIO.
- Математичні закони зміни знака та скороченого дробу допущені
  як композиції існуючих D24+ атомів, але **синтаксис/бінарний
  opcode/physical wire та повний signed/rational runtime** ще не
  допущені. Відсутній механізм має відповідати
  `BLOCKED/UNSUPPORTED`, без втрати точності чи домену.
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
