# План повного рівноправ'я мов у my-lisp

**Стан:** активний план міграції  
**Мови першої хвилі:** українська (UK), англійська (EN), санскрит (SA)  
**Принцип:** значення первинне, мови рівноправні.

## 1. Мета

`my-lisp` не повинен мати привілейованої людської мови ні в семантичному
ядрі, ні в реєстрах, ні в bootstrap, ні в tooling, ні в тестах, ні в
діагностиці.

Повне рівноправ'я означає не однакову орфографію, а однаковий статус відносно
однієї мовно-нейтральної семантичної тотожності:

```text
                         0104
                           │
              ┌────────────┼────────────┐
              │            │            │
             UK           EN           SA
           додати          +           yoga
```

Жодна з гілок не проходить через іншу.

Заборонено:

```text
UK -> EN -> meaning
SA -> EN -> meaning
EN -> UK -> meaning
```

Потрібно:

```text
UK --\
EN ----> numeric semantic identity
SA --/
```

## 2. Непорушні інваріанти

1. **Семантичний ID містить тільки цифри.**
   Допустима форма: `[0-9]{4,}`. `m0104`, `id0104`, `meaning0104` та інші
   буквені префікси заборонені.
2. **ID не є словом.** Цифри — непрозорий машинний handle, а не скорочена назва
   операції.
3. **UK, EN і SA — peer surfaces.** Порядок рядків `(uk ...)`, `(en ...)`,
   `(sa ...)` у реєстрі не має семантичного значення.
4. **Одна тотожність — один numeric semantic ID, не один Rust-об'єкт.**
   Виправлено 2026-09-11: попередня редакція цього пункту вимагала "один
   `Value::Builtin`", і Gate B (нижче) вимагав `Rc::ptr_eq` як доказ —
   це саме той старий дизайн, від якого цей план мав відходити, а не
   зміцнювати. `Rc::ptr_eq` робить Rust-runtime-об'єкт частиною мовної
   тотожності; правильна залежність інша:

   ```text
   surface spelling (car / перше / ādi)
        ↓
   numeric semantic ID (0005)
        ↓
   semantic/callable value
        ↓
   implementation projection (Rust сьогодні; Lisp/CML/FPGA пізніше)
   ```

   `car`, `перше`, `ādi` та `0005` мають одну тотожність тому, що
   резолвляться до того самого numeric ID, а не тому, що випадково
   містять той самий `Rc<Builtin>`. `Value::Builtin`/`Rc<dyn Fn>` —
   сьогоднішня реалізаційна проекція semantic ID, не сама тотожність;
   план не повинен вимагати, щоб вона нею лишалась. Дослідницька карта
   залежностей: `docs/BUILTIN-IDENTITY-MIGRATION-MAP-2026-09-11.md`.
5. **Жодного cross-language alias як реалізації.** На кшталт
   `(define додати +)` або `(define yoga +)` не може бути способом побудови
   рівноправної поверхні.
6. **канон()+7 сильніший за ordinary API.** Його peer names незмінні; ordinary
   public names можуть лишатися лексично shadowable відповідно до Contract 6.
7. **Відсутність перекладу не приховується.** `missing` і `candidate` є чесними
   станами, а не приводом використовувати EN як мовчазний fallback.
8. **Tooling не має окремої англомовної істини.** Help, arity metadata,
   completion, hover, docs, diagnostics і surface inventory мають походити від
   semantic identity або явно surface-specific presentation data.

## 3. Визначення повного рівноправ'я

Для кожної вибраної публічної semantic identity мають одночасно виконуватися
всі умови:

- numeric-only ID;
- по одному запису для UK, EN і SA;
- усі три записи мають `stable`;
- кожне ім'я прямо резолвиться до тієї самої semantic identity;
- жодна людська назва не є внутрішнім ключем тотожності;
- однакове обчислювальне значення на всіх трьох поверхнях;
- однакові arity/type/error classes;
- acceptance program існує окремо для UK, EN і SA;
- help/hover/completion присутні для кожної поверхні;
- діагностика не змушує користувача іншої поверхні переходити на EN;
- тести перевіряють не лише результат, а й відсутність cross-language
  залежності.

Лише після цього `release parity` може бути `CONFIRMED`.

## 4. Етапи міграції

### Етап A — нейтральна authority

Мета: `lib/surface/semantic-registry.lisp` стає єдиним реєстром selected public
surface.

Роботи:

- перенести всі вибрані identities зі старого `uk-sa-coverage.lisp` у numeric
  registry;
- кожному рядку призначити opaque numeric ID;
- checker має читати neutral registry, а не EN-shaped legacy table;
- після повного переносу прибрати legacy registry з authority path;
- generated docs/inventories будувати лише з neutral registry.

**Gate A:** жоден authoritative surface registry не використовує EN spelling як
semantic key.

### Етап B — direct runtime peer bindings

Мета: усі runtime public names позначають значення прямо.

Роботи:

- мігрувати ordinary builtins за зразком `0104`;
- для кожної identity створювати callable/value один раз;
- встановлювати UK/EN/SA names як peer bindings цього самого value;
- видаляти surface definitions, які будують одну мову через іншу;
- окремо перевіряти незалежне lexical shadowing ordinary names.

**Gate B (виправлено 2026-09-11):** усі builtin peer spellings резолвляться до
того самого numeric semantic ID, і ця тотожність спостережувана мовою через
семантику `eq` — **не** через `Rc::ptr_eq` чи інший Rust-рівневий identity
proof як самоціль. `Rc::ptr_eq` може лишатись сьогоднішнім internal
механізмом реалізації (доки `Value::Builtin` є єдиною runtime-проекцією), але
gate перевіряє semantic-ID equality, а не pointer equality — щоб майбутня
заміна реалізаційної проекції (CML/FPGA/чиста Lisp-машина) не ламала сам gate.
Дослідницька знахідка й обґрунтування: `docs/BUILTIN-IDENTITY-MIGRATION-MAP-2026-09-11.md`.

### Етап C — syntax і necessary forms

Мета: `lambda`, `define`, `defmacro` та інші necessary forms не мають EN як
прихованого canonical surface.

Роботи:

- завершити SA spellings там, де зараз `missing`;
- dispatch виконувати через semantic form identity;
- parser/evaluator не повинен спочатку перетворювати UK/SA на EN spelling;
- arity/error classification має бути однаковим для трьох surfaces.

**Gate C:** три окремі програми UK/EN/SA проходять однаковий набір syntax/error
випробувань.

### Етап D — Lisp-defined public library

Мета: функції та макроси, визначені у Lisp, теж мають peer topology.

Роботи:

- відділити створення semantic value від встановлення surface names;
- створювати public closure/macro один раз;
- після створення прив'язувати до нього всі stable peer spellings;
- заборонити шаблон `UK define -> EN function` і `SA define -> EN function` як
  механізм реалізації surface parity;
- зберегти можливість surface-specific presentation без дублювання semantics.

**Gate D:** для кожної migrated Lisp-defined identity усі stable spellings
посилаються на один runtime value.

### Етап E — tooling і presentation

Мета: рівноправ'я видно не лише evaluator-у, а й людині.

Роботи:

- REPL help за semantic identity;
- completion по активній surface без EN-first ranking;
- hover/signature з surface-local spelling;
- діагностика з surface-local operation name;
- документація для UK/EN/SA з однаковим semantic coverage;
- жодного silent EN fallback, якщо surface row позначений `missing`.

**Gate E:** однаковий tooling corpus виконується на трьох surfaces.

### Етап F — acceptance і release gate

Мета: заяву "три повністю рівноправні мови" робить не README, а executable
evidence.

Потрібно:

- 100% selected identities: UK stable;
- 100% selected identities: EN stable;
- 100% selected identities: SA stable;
- 100% identities мають direct-resolution proof;
- 0 cross-language alias definitions у production surface files;
- 0 alphabetic semantic IDs;
- окремі UK/EN/SA acceptance programs;
- neutral registry є єдиною authority;
- legacy EN-shaped inventory не є gate для нових peer identities;
- `--require-complete` перевіряє саме neutral registry.

**Gate F:** тільки тут `release parity: CONFIRMED`.

## 5. Україномовний test layer

Українські тести потрібні не як декорація, а як антиупереджувальний інструмент.
Якщо весь test vocabulary англійський, приховану EN-first модель легше не
помітити.

Перший файл: `crates/my-lisp/tests/rivnopravnist_mov.rs`.

Активні тести повинні перевіряти:

1. semantic IDs складаються тільки з цифр;
2. кожна identity у neutral registry має рівно по одному UK/EN/SA row;
3. жодне human spelling не збігається з numeric ID;
4. `0104` має один runtime builtin для `додати`, `+`, `yoga`;
5. shadowing одного ordinary peer name не переналаштовує інші;
6. UK і SA surface files не визначають `0104` через EN.

Окремий фінальний тест визначає **Definition of Done**: усі UK/EN/SA rows
`stable`. Поки міграція не завершена, він має бути `#[ignore]` з явною
причиною. Його не можна видаляти або послаблювати; наприкінці міграції
`#[ignore]` прибирається, і він стає release gate.

Наступні test modules теж бажано називати й описувати українською:

```text
rivnopravnist_mov.rs
rivnopravnist_syntaksysu.rs
rivnopravnist_biblioteky.rs
rivnopravnist_diahnostyky.rs
rivnopravnist_instrumentiv.rs
```

Це не означає перевагу української. Це навмисний pressure test проти вже
наявної історичної переваги EN: сама система повинна однаково добре витримати
тести, сформульовані не англійською.

## 6. Порядок роботи для кожної semantic identity

Для кожного наступного ID:

```text
1. вибрати meaning
2. призначити numeric ID
3. записати UK / EN / SA у neutral registry
4. створити value один раз
5. прив'язати peer spellings прямо
6. видалити cross-language aliases
7. додати UK-named identity test
8. додати behavioral parity test
9. додати shadowing/immutability test за політикою identity
10. прогнати workspace + surface drift + WASM
11. лише після green evidence позначити rows stable
```

## 7. Принцип завершення

Ми не рахуємо кількість перекладів. Ми доводимо топологію:

```text
semantic identity
      │
      ├── UK
      ├── EN
      └── SA
```

Якщо хоча б одна surface реалізована через іншу, рівноправ'я ще не досягнуте.
Якщо machine identity містить слово або мовний префікс, рівноправ'я ще не
досягнуте.
Якщо одна surface має іншу семантику помилок, tooling або acceptance coverage,
рівноправ'я ще не досягнуте.

Кінцева вимога проста:

> **Жодна людська мова не є мостом до значення для іншої людської мови.**
