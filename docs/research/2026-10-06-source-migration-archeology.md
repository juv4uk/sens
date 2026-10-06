# Археологія форматів SENS і вимоги до мігратора

Дата: 2026-10-06  
Статус: робочий звіт для нового мігратора source → canonical binary SENS  
Гілка дослідження: `codex/sens-code-migration-tools`

## Мета

Поточний мігратор не можна будувати як простий replace-all.

Репозиторій пройшов кілька різних епох представлення функцій і програм. Один і той самий семантичний виклик міг бути записаний:

1. старим точним 8-бітним SID8/Sens8;
2. звичайним my-lisp написанням;
3. історичним LISP I / LISP 1.5 написанням, часто великими літерами;
4. новим exact-width domain-qualified кодом.

Тому правильний мігратор спочатку **класифікує вхід**, потім розбирає структуру, і лише після цього переводить семантичні вузли у чинні координати.

## Історичні переходи, підтверджені комітами

### Епоха A — LISP I / LISP 1.5 як історичний корінь

Ключові сліди:

- `cdc959c7720216dd495ddcd6c43c0bc9f17e2e1d` — McCarthy/LISP 1.5 зафіксовано як явний історичний корінь Core1.
- `85cca8b1eb1b44325e2b46f2a37534cc7d0fadea` — closures прив'язано до LISP 1.5 FUNCTION/FUNARG.
- `24493175a20547538ef60b19ffec47230fe837af` — у function table додано McCarthy 1960 / Lisp 1.5 column.
- дослідницький corpus Lisp I/Lisp 1.5 пізніше використовував `CAR/CDR/CONS/ATOM/EQ/COND/LAMBDA/DEFINE` як історичний словник.

Цей шар треба розпізнавати окремо від сучасного surface syntax. Великі імена на кшталт `CAR`, `COND`, `LAMBDA`, `DEFINE`, `PLUS`, `DIFFERENCE`, `TIMES`, `QUOTIENT` є **історичними написаннями**, а не D7-текстом за замовчуванням.

### Епоха B — my-lisp / named surface

my-lisp довго допускав виклики через людські назви, а lowering переводив частину незатінюваних імен у внутрішні функціональні ідентичності.

Важливий перехід:

- `92f18aa27c155effa3f9a0fed82e31562ca6f4cc` — `ExprKind::Call(Sens8, args)`: після розбору named forms на кшталт `atom`, `eq`, `cons`, `car`, `cdr`, `cond`, `lambda`, `define` зводилися до 8-бітної функціональної коробки.
- цей же коміт прямо фіксує великий інвентар коду, який ще залишався записаний іменами.

Отже другий прохід мігратора повинен знати **my-lisp surface spelling**, shadowing і позицію list head. Не кожен текстовий символ у файлі є Text7-даними.

### Епоха C — SID8 / Sens8

Ключові переходи:

- `383954059191c513b073f681622bf27913f03eac` — canonicalize Sens8/sens! із backward-compatible Sid8 alias.
- `747c01a0c8e979afd2cbf401d71253dbf294b940` — власник фіксує одну 1-byte коробку `Sens8`; Sid8 лишається deprecated compatibility alias.
- `4abb15f2cec953a74f63bd9ca8ea59b1b9bb1bb1` — historical exact SID8 self-load.
- `320a389d005433938358c15eca39b850eb952e8a` — current authority переходить від flat Sens8/Sid8/Function8 до exact domains.
- `e113bcd6b9dd5d844c2e2e7808b053ab649aec7c` — semantic Sens8/Sid8 debt ratchet.
- `0b10b28fe9a4c8321af3fe80a212b72e27c7f634` — W3–W6 source/domain bridge як prerequisite для Sens8/Sid8 exit.

Отже перший прохід нового мігратора має знаходити старі **8-бітні функціональні слова** і переводити їх через історичну semantic mapping, а не трактувати як сучасний D8 чи як Text7.

### Епоха D — exact-width domains

Ключові переходи:

- `804a938e2c5acdb3a805b2e8d13a8e6cdd1c4cc2` — ratification D3 / bīja3 A.
- `6b4d8a908cc21879928766af1bf51373e16492d4` та `fae6ac755acdf299ae5d600b7ca9692f10ca2d79` — runtime/compiler cutover на ratified D3.
- `e02e3cf657dde36dd90771cbf4f385c8e396325e` — D1–D5 current foundation.
- пізніший exact-domain compiler explicitly забороняє Sid8/Sens8 fallback.

Тут ширина слова є частиною identity. `001`, `0001` і `00000001` не можна зводити до одного numeric payload.

## Наслідок для нового мігратора

Мігратор повинен працювати мінімум у три семантичні проходи.

### Pass 1 — legacy SID8 / Sens8

Мета: визначити старі 8-бітні function identities.

Алгоритм:

- знайти 8-бітні binary tokens у **call-head / executable position**;
- перевірити їх через historical SID8/Sens8 ledger;
- якщо historical meaning відомий — перевести meaning у поточний exact-domain coordinate;
- якщо meaning неоднозначний або ledger не дає однозначної відповіді — файл блокувати;
- не трактувати старий 8-bit function code як сучасний D8 автоматично.

### Pass 2 — my-lisp surface

Мета: знайти сучасні/перехідні named calls.

Алгоритм:

- розібрати S-expression structure;
- визначити list head;
- перевірити shadowing / local definitions;
- зіставити admitted surface spelling з current semantic identity;
- лише після успішного semantic lookup замінити head на exact-width code;
- аргументи, binder names, strings і quoted data не перетворювати на function codes.

### Pass 3 — historical LISP I / LISP 1.5 spelling

Мета: розпізнати historical uppercase forms.

Типові кандидати:

`CAR CDR CONS ATOM EQ COND QUOTE LAMBDA DEFINE LIST NOT APPEND LOOKUP BIND EVLIS EVCON APPLY EVAL PLUS DIFFERENCE TIMES QUOTIENT ...`

Алгоритм:

- historical spelling → historical semantic operation;
- semantic operation → **current** ratified coordinate;
- old coordinate, якщо він існував, не має placement authority;
- historical uppercase form не можна автоматично знижувати до D7 Text7 до завершення цього проходу.

## Структура source: D2 і EMPTY

Критична owner-корекція:

```text
() → 000
```

Тобто порожній список/порожня форма має бути розпізнана **до** механічного кодування двох дужок.

Для непорожніх форм D2 лишається structural grammar:

```text
10 → open
01 → close
00 → separator
11 → dot
```

Отже:

```text
()            → 000
(CAR x)       → 10 100 00 <x> 01
(a . b)       → 10 <a> 00 11 00 <b> 01
```

Точне правило separator placement повинно бути підтверджене canonical reader tests; мігратор не має вставляти `00` евристично без parser state.

## D7 / Text7: тільки після semantic passes

Головна помилка попередньої версії скрипта: невідомий token одразу падав у Text7.

Правильний порядок:

```text
token
  ↓
legacy SID8/Sens8?
  ↓ no
current exact-domain word?
  ↓ no
my-lisp callable spelling?
  ↓ no
historical Lisp 1/1.5 callable spelling?
  ↓ no
structure / number / binder / quoted-data classification
  ↓
Text7 only if grammar says this node is text/spelling
```

**Text7 не повинен бути fallback для нерозпізнаної функції.**

Якщо token стоїть у executable head position і semantic mapping не знайдено — файл треба блокувати, а не кодувати назву як D7.

## Коментарі

Коментарі не входять у canonical output.

Треба видаляти:

- `; ... end-of-line`
- nested `#| ... |#`, якщо цей вид коментаря присутній у historical source

але не чіпати comment markers усередині string literals.

Обов'язковий тест:

```text
program_with_comments
program_without_comments
```

після migration мають давати **ідентичний canonical binary output**.

## Імена вихідних файлів

Власник окремо вказав: у `master` binary-result files **не повинні мати розширення**.

Приклад:

```text
lib/core.lisp
→ master: lib/core
```

Не:

```text
lib/core.lisp.wire.bits
lib/core.bits
lib/core.lisp
```

Сам вміст output file:

- тільки `0` і `1`;
- whitespace дозволений лише як physical presentation separator;
- кожне visible word має зберігати exact width;
- жодних коментарів;
- жодних human names;
- жодного generic SW/FASL byte-container dump.

## Master policy

`master` — це не development branch і не копія `main`.

У `master` потрапляє тільки файл, для якого:

1. source parser пройшов;
2. історична форма класифікована;
3. всі executable heads мають однозначний current semantic identity;
4. структура розпізнана, включно з `() → 000`;
5. comments removed;
6. output contains only exact-width binary SENS words;
7. validator може повторно прочитати output без human fallback.

Якщо хоча б одна умова не виконана — файл залишається поза `master`.

## Що було помилковим у попередньому експерименті

Попередній exporter робив:

```text
parse → lower → SW/FASL-like bytes → 8-bit textual binary
```

Це не є canonical SENS source.

Він серіалізував **контейнерні байти**, тому втрачав саму ідею exact-width D1/D2/D3/... words. Такий output був відкочений із `master` і не повинен повертатися.

Друга помилка: function name, який не був розпізнаний, міг перетворитися на D7 spelling. Це семантично неправильно.

Третя помилка: `()` механічно бачилося як open+close замість canonical `000 EMPTY`.

## Рекомендована архітектура скриптів

Краще не один монолітний regex-мiгратор, а pipeline:

```text
scan-source
    ↓
classify-era
    ├─ legacy-sid8/sens8
    ├─ my-lisp
    ├─ historical-lisp-1-1.5
    └─ current-exact-width
    ↓
parse-structure
    ↓
resolve-semantics
    ↓
emit-current-exact-width
    ↓
validate-roundtrip
    ↓
strip-extension
    ↓
publish-to-master
```

Практично це можуть бути три classifier passes над одним AST, а не три незалежні text-replacement scripts.

## Stop conditions

Міграція має fail closed, якщо:

- executable head лишився нерозпізнаним;
- old SID8 має більше одного можливого current meaning;
- historical name shadowed локальним definition;
- parser не може визначити structure;
- `()` не нормалізувалося в `000`;
- token було відправлено в Text7 лише тому, що function lookup провалився;
- output містить слово > 8 bits у current bounded source;
- output містить будь-який небінарний символ, крім whitespace;
- source file мав parse ambiguity.

## Висновок

Історія репозиторію показує, що проблема міграції — не “замінити назви кодами”. Це **semantic archaeology**.

Надійний мігратор повинен знати, з якої епохи походить конкретне написання, відновити meaning, а потім уже поставити current exact-width coordinate.

Головний принцип:

> **meaning first → current coordinate second → Text7 only for actual text.**
