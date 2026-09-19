<div align="center">

<img src="docs/assets/wsm-lisp-hero.svg" alt="my-lisp — CANON 0+7 · META-EVAL · WASM" width="100%">

# my-lisp

**Проста Lisp-мова, що координує різні способи обчислення**

*Дослідження мови, яка зберігає власний Canon та semantic identities, але не намагається підмінити собою Prolog, Datalog, CLIPS, Common Lisp чи інші незалежні ядра.*

<p><a href="https://github.com/juv4uk/my-lisp/releases/latest/download/my-lisp-cli-web.html"><strong>▶ Спробувати my-lisp у вебі</strong></a></p>
<sub>Один автономний portable-файл <code>.html</code> · без встановлення · працює локально у браузері</sub>

[![CI](https://github.com/juv4uk/my-lisp/actions/workflows/ci.yml/badge.svg)](https://github.com/juv4uk/my-lisp/actions/workflows/ci.yml)
[![WASM](https://github.com/juv4uk/my-lisp/actions/workflows/wasm-browser-test.yml/badge.svg)](https://github.com/juv4uk/my-lisp/actions/workflows/wasm-browser-test.yml)
[![Surface drift](https://github.com/juv4uk/my-lisp/actions/workflows/surface-drift-check.yml/badge.svg)](https://github.com/juv4uk/my-lisp/actions/workflows/surface-drift-check.yml)

**Українська — перша мова проєкту.** Англійська й німецька — допоміжні.

</div>

---

## Що таке `my-lisp`

`my-lisp` — дослідницька Lisp-мова з власним Canon, 8-бітним простором semantic identities, точною арифметикою, виконуваними законами та архіпелагом незалежних execution kernels.

Головний архітектурний принцип:

> **Мова володіє значенням та ідентичністю. Ядра володіють своїм способом обчислення. Жоден механізм не має права вигадувати семантику за мову.**

Rust лишається важливим механічним substrate/reference implementation, але не джерелом семантичної істини. Так само Prolog, Datalog, CLIPS і Common Lisp не стають глобальною semantic authority лише тому, що вони краще виконують свій клас задач.

```text
                  my-lisp
        Canon / SID / laws / data
                     |
       +-------------+-------------+
       |             |             |
   local Lisp      routing       observation
       |             |             |
       +------+------+------+------+
              |      |      |
          Common   Prolog  Datalog  CLIPS
           Lisp
```

Нова дисципліна проста: `my-lisp` має вміти **висловити, адресувати, передати, прийняти й композиційно використати** результат, але не зобов'язаний повторно реалізовувати всередині себе найкращий алгоритм кожного острова.

Поточний машинний семантичний контракт — [`language-contract.lisp`](language-contract.lisp), версія **7.0**.


### Один Lisp, різні субстрати

Поточний напрям substrate switch фіксує ще жорсткішу межу:

> **`my-lisp` лишається семантичною владою; субстрат змінюється без міграції значення.**

Тобто перенесення виконання на GraalVM, WASM, C, FPGA чи інший host не повинно породжувати другу реалізацію мови. Новий субстрат має виконувати той самий pinned Lisp source і доводити це незалежним witness-шаром.

```text
pinned my-lisp source
        ↓
semantic contract + executable laws
        ↓
      substrate
   ↙      ↓      ↘
 Rust   GraalVM   WASM / C / FPGA
```

Особливо це стосується bootstrap: `lib/macro.lisp` і `lib/core.lisp` є Lisp-owned behavior. Якщо для запуску на іншому субстраті потрібен новий host-механізм, він має бути вузьким, незвідним і semantics-blind; переписування `COND`, `defmacro`, `let`, `equal?` чи іншої Lisp-поведінки в Java/Rust не є еквівалентним substrate switch.

Поточний bootstrap рухається до канонічного **тричленного `COND`** — `(query expected-result expression)`: структурні та identity-рішення порівнюються з явним результатом, а не через загальну truthiness. Перший upstream-крок для `lib/macro.lisp` проходить через PR [`#615`](https://github.com/juv4uk/my-lisp/pull/615); це ще не є оголошенням зеленого CI.

---

## Що вже доведено

Три терміни, на яких тримається evidence layer:

- **semantic ID** — стабільна числова тотожність значення, незалежна від написання імені;
- **surface** — шар написань/проєкцій, який відображає імена на semantic IDs;
- **witness** — виконуваний доказ, що перевіряє конкретне обмежене семантичне твердження.

На сьогодні README може чесно показати такі вже ратифіковані результати:

- **Canon 0+7 має executable witnesses.** Закони стабільного історичного кореня не лише описані прозою: вони виконуються в [`lib/canon.lisp`](lib/canon.lisp) і перевіряються conformance/Canon-тестами.
- **Українська поверхня є peer projection тих самих numeric semantic identities.** `uk`, `en`, `sa` та інші admitted spellings не створюють окремих значень і не перекладають «привілейовану англійську семантику»; authority лежить у numeric-only registry [`lib/surface/semantic-registry.lisp`](lib/surface/semantic-registry.lisp).
- **Vertical Day — bounded фізичний доказ.** Ратифікований зріз [`2026-09-14`](docs/research/2026-09-14-vertical-day.md) проводить `(перше (сполучити 2 3))` через structured machine forms → closed admission → Lisp-owned x86-64 encoding → semantics-blind host → physical CPU і отримує `2`. Це доказ конкретного bounded шляху, не твердження про повну native Lisp-машину.
- **Canonical machine path fail-closed.** Ill-typed semantic input та raw/malformed/unadmitted, зокрема truncated, machine requests відхиляються до входу в host; негативні witnesses фіксують `HOST CALL COUNT = 0`, а не використовують crash як oracle.

```text
(перше (сполучити 2 3))
        ↓
semantic identity
        ↓
structured machine forms
        ↓
closed admission
        ↓
Lisp-owned x86-64 encoding
        ↓
semantics-blind host
        ↓
physical CPU
        ↓
2
```

**Ще не доведено:** complete native GC/general heap, first-class escaping native pairs, automatic GPU/FPGA scheduler, complete Lisp machine або OS. Повний список меж твердження й exact evidence ledger лежить у датованому [`Vertical Day record`](docs/research/2026-09-14-vertical-day.md).

README лише показує вже зароблені докази; він не є новим джерелом семантичної влади.

---

## Canon 0 і історичний корінь Маккарті

`()` лишається **Canon 0** — первинним порожнім правильним списком і базою індукції для спискової структури.

Сім класичних операцій Маккарті лишаються важливим історичним і мінімальним коренем:

| Канонічна тотожність | Українська поверхня | Символ | Історичне ім'я |
|---|---|---:|---|
| Canon 0 | `()` | `()` | `()` |
| QUOTE | `як-є` | `'` | `quote` |
| ATOM | `атом?` | `.?` | `atom` |
| EQ | `тотожне?` | `=?` | `eq` |
| CONS | `сполучити` | `:` | `cons` |
| CAR | `перше` | `:п` | `car` |
| CDR | `решта` | `:р` | `cdr` |
| COND | `за-умовою` | `?:` | `cond` |

Але проєкт **більше не обмежує мову сімома примітивами**.

Новий критерій інший:

> **Примітив має заслужити окрему identity тим, що він є реально окремою базовою операцією системи.**

Тому нові first-class identities допустимі, якщо вони потрібні для чесної композиції мови, островів, даних або спостережень. Водночас ми не додаємо окремий SID лише тому, що якийсь kernel має багату внутрішню онтологію.

Кількість примітивів не задається наперед як 7, 20 чи 40. Вона визначається експериментально всередині одного 8-бітного простору semantic identities.

### Апостроф

Контракт 4.0 фіксує просте правило:

```lisp
'кіт        ; те саме, що (quote кіт)

об'єкт      ; один ідентифікатор
п'ять       ; один ідентифікатор
зв'язок     ; один ідентифікатор
```

Апостроф на початку виразу — reader syntax для `QUOTE`; апостроф усередині слова — звичайна частина ідентифікатора.

### Десяткова кома

На українській розкладці десятковий роздільник можна набирати комою. Крапка й кома є двома написаннями **того самого точного числового значення**:

```lisp
(eq 12,455 12.455)   ; t
(+ 1,5 2,5)          ; 4
(eq -0,25 -0.25)     ; t
(eq 1,5e3 1500)      ; t
```

Кома отримує числовий сенс лише тоді, коли весь токен є коректним числом. Тому `а,б` і `версія1,2` лишаються звичайними символами.

---

## Українською можна програмувати

Українська — не лише мова README. Українські імена є peer-проєкціями тих самих numeric semantic IDs у [`lib/surface/semantic-registry.lisp`](lib/surface/semantic-registry.lisp); вони не створюють окремої реалізації функцій.

У проєкті розрізняються **дві українські поверхні**:

- `uk` — коротка, інтуїтивно зрозуміла українська поверхня для щоденного програмування;
- `ukr` — повна українська поверхня, де ім'я максимально явно описує операцію.

Обидві належать **тому самому semantic ID**. Якщо чинне `uk`-ім'я вже коротке й ясне, `uk` і `ukr` можуть бути однаковими. Якщо повна назва краще пояснює дію, `ukr` може бути довшою:

| semantic ID | `uk` | `ukr` |
|---:|---|---|
| `00000010` | `атом?` | `атом?` |
| `00001001` | `визначити` | `визначити` |

У чинній моделі surface status-категорій немає. Кожен namespace slot містить або spelling, або `()`:

```lisp
("00001100"
  (en ())
  (uk додати)
  (ukr додати)
  (sa yoga)
  (sym +))
```

Тобто немає прихованої третьої категорії між «ім'я є» і «імені немає».

Повна жива таблиця `uk | ukr | English | Sanskrit` генерується з authority: [`docs/generated/function-table.md`](docs/generated/function-table.md). Детальні пояснення поведінки: [`docs/ukrainian-api.md`](docs/ukrainian-api.md). Репрезентативний executable witness без перемикання на латинську розкладку: [`lib/surface/ukr-acceptance.lisp`](lib/surface/ukr-acceptance.lisp).

Окремо [`docs/generated/public-api-discovery.md`](docs/generated/public-api-discovery.md) рекурсивно показує всі знайдені top-level `def`/`defmacro` у живому `lib/**/*.lisp`. Його рядки поки мають статус `unreviewed`: discovery не оголошує функцію публічною і не створює semantic ID.

Поточний код через stable `uk` може виглядати так:

```lisp
(визначити квадрат
  (функція (число)
    (помножити число число)))
```

### Предикати читаються як питання

Українська назва предиката закінчується `?`. На своїй припустимій області предикат повертає тільки канонічне `t` або `()`:

```lisp
(атом? 'кіт)                         ; t
(менше? 2 5)                         ; t
(значення-у-списку? 'пес (список 'кіт 'пес))   ; t
```

`?` — частина ідентифікатора, а не окремий оператор. Функції, що можуть повернути дані або `()` (наприклад `отримати-з-карти`), предикатами не є й `?` не мають.

Повна самоперевірна українська програма є в [`lib/surface/uk-acceptance.lisp`](lib/surface/uk-acceptance.lisp).

Українська, англійська та санскритська **програмні поверхні не розмножують семантику**. Вони відображають різні імена на ті самі визначення й канонічні тотожності. Єдина машинна таблиця відповідності лежить у [`lib/surface/semantic-registry.lisp`](lib/surface/semantic-registry.lisp): semantic identity там numeric-only, а спільна пунктуація винесена в окрему `sym`-поверхню.

Є й програмний перекладач поверхонь:

```bash
python3 scripts/translate-program.py --from en --to uk input.lisp
python3 scripts/translate-program.py --from uk --to sa input.lisp
```

Він підтримує всі шість напрямків між `en`, `uk` і `sa`, зберігаючи форматування, коментарі, рядки та невідомі користувацькі символи. Деталі: [`docs/program-surface-translator.md`](docs/program-surface-translator.md).

---

## Мовна політика репозиторію

Людська комунікація проєкту має окрему ратифіковану політику: [`knowledge/language-policy.lisp`](knowledge/language-policy.lisp).

```text
1. Українська — перша і головна.
2. Англійська й німецька — допоміжні.
3. Текстові файли репозиторію — UTF-8.
4. Нові коментарі в коді — українською кирилицею.
5. Точні API, protocol literals, identifiers, filenames і upstream-назви не перекладаються довільно.
```

[`scripts/uk-latynka.py`](scripts/uk-latynka.py) лишається оборотним ASCII-інструментом для спеціальних зовнішніх меж без Unicode. Це **не** штатний стиль коментарів у репозиторії.

---

## Семантична влада

README пояснює проєкт, але не визначає його семантику.

```text
language-contract.lisp
        ↓
ратифіковані ADR
        ↓
виконувані закони та conformance fixtures
        ↓
референсна реалізація Rust
        ↓
незалежні реалізації
        ↓
згенерована документація
        ↓
README / tutorials / історичні плани
```

Якщо нижчий рівень суперечить вищому — нижчий рівень застарів. Повна карта: [`docs/semantic-authority-map.md`](docs/semantic-authority-map.md).

Це одна з головних дисциплін проєкту:

> **Назва явища не може бути сильнішою за найсильніший експеримент, який його підтримує.**

---

## Мова і архіпелаг ядер

Раніше центральним дослідницьким питанням було: скільки поведінки можна повернути всередину самого Lisp.

Цей напрям дав важливі результати, але тепер проєкт рухається далі: **не все корисне повинно жити всередині одного Lisp evaluator**.

```text
my-lisp
  ├─ Canon / SID / surfaces / laws
  ├─ локальна Lisp-поведінка
  ├─ ordinary data
  ├─ композиція
  └─ kernel boundary
       ├─ Common Lisp — Lisp runtime/execution
       ├─ Prolog      — unification/backtracking/0..N answers
       ├─ Datalog     — relational closure/fixpoint
       └─ CLIPS       — production rules/working memory/agenda
```

Старі Lisp-owned реалізації `unify.lisp`, `reason.lisp`, `forward.lisp` та інші не оголошуються помилкою і не видаляються автоматично. Вони можуть залишатися:
- reference implementations;
- простими локальними механізмами;
- compatibility paths;
- експериментальними шарами;
- witnesses для порівняння з незалежними kernels.

Але вони більше не зобов'язані бути фундаментом усієї reasoning-архітектури.

### Пірамідальна та множинна логіка

Попередня пірамідальна модель була корисною як спосіб вийти з замкненої Lisp-бульбашки й перестати зводити всі відповіді до одного наперед заданого truth model.

Тепер її роль спрощується.

Вона може лишатися як:
- опційна view/projection над evidence;
- інструмент для incomplete/conflicting evidence;
- compatibility/research layer.

Але Prolog, Datalog і CLIPS отримують право лишатися собою. `my-lisp` не має перетворювати їхні native результати на одну універсальну логічну шкалу.

Принцип:

> **Не змушувати реальність ставати зручною для однієї внутрішньої моделі.**

Якщо Prolog повертає багато substitutions — зберігаємо множинність.  
Якщо Datalog не вивів факту — не домальовуємо його.  
Якщо два kernels суперечать один одному — зберігаємо обидва результати та provenance.  
Якщо bridge неповний — неповнота є допустимим результатом.

### Король і свита

Історична метафора проєкту тепер отримує точніший зміст:

```text
            my-lisp
       identity / Canon
          /   |   \
         /    |    \
   Prolog  Datalog  CLIPS  Common Lisp
```

`my-lisp` є центральною мовою не тому, що виконує все сам, а тому, що зберігає **цілісність identity, Canon, композицію й прямий контакт із різними execution models**.

Кожен острів говорить із мовою прямо й повертає власний результат без обов'язкового переписування під одну універсальну семантику.

---

## Хост не є семантикою

`my-lisp` не ставить собі за мету механічно «переписати Rust на Lisp». Межа інша:

```text
OS / hardware
      ↓
спостереження та capability-механізми
      ↓
значення my-lisp
      ↓
Lisp-визначена інтерпретація / політика / протокол
```

Тому низькорівнева операція може чесно лишатися в Rust, C або FPGA, якщо вона є механізмом. Але semantic policy не повинна випадково ставати властивістю конкретного хоста.

Живий аудит цієї межі: [`docs/host-semantic-surface.md`](docs/host-semantic-surface.md).

---

## Незалежні субстрати

Різні реалізації потрібні не для того, щоб копіювати одну архітектуру, а щоб **ламати приховані припущення одна одної**.

- [`crates/my-lisp`](crates/my-lisp) — референсний Rust runtime;
- [`crates/my-lisp-cli`](crates/my-lisp-cli) — CLI, REPL і semantic oracle;
- [`crates/my-lisp-wasm`](crates/my-lisp-wasm) — WebAssembly;
- [`crates/my-lisp-lsp`](crates/my-lisp-lsp) — LSP;
- [`crates/my-lisp-host`](crates/my-lisp-host) — явна межа OS capabilities;
- [`c-runtime/`](c-runtime/) — C + x86_64 substrate;
- [`racket/`](racket/) — `#lang my-lisp` для Racket/DrRacket;
- [`juv4uk/cml`](https://github.com/juv4uk/cml) — AOT / heterogeneous compiler напрям;
- [`juv4uk/fpga-lisp`](https://github.com/juv4uk/fpga-lisp) — фізично інша Lisp-машина на FPGA.

Сумісність визначається контрактами, а не тим, наскільки схожий код реалізацій.

---

## Локальний запуск

Потрібні Rust toolchain і залежності workspace. У репозиторії також є Guix manifest для відтворюваного середовища.

```bash
# REPL
cargo run -p my-lisp-cli

# виконати файл
cargo run -p my-lisp-cli -- path/to/file.lisp

# повний workspace
cargo test --workspace
cargo build --workspace
cargo clippy --workspace --all-targets -- -D warnings
```

Канонічне розширення вихідного коду — **`.lisp`** (згідно з [my-lisp#81](https://github.com/juv4uk/my-lisp/issues/81)). **`.wsm`** і **`.my`** лишаються повністю підтримуваними legacy aliases.

---

## З чого читати проєкт

Якщо відкриваєте `my-lisp` уперше, цей порядок дає найменше плутанини:

1. [`language-contract.lisp`](language-contract.lisp) — що саме обіцяє мова;
2. [`docs/semantic-authority-map.md`](docs/semantic-authority-map.md) — хто має право визначати істину;
3. [`lib/canon.lisp`](lib/canon.lisp) — виконуваний Canon 0+7;
4. [`docs/language-core.md`](docs/language-core.md) — компактна архітектура ядра;
5. [`lib/surface/uk-acceptance.lisp`](lib/surface/uk-acceptance.lisp) — українська мова як виконуваний програмний інтерфейс;
6. [`lib/meta-eval.lisp`](lib/meta-eval.lisp) — як мова починає обчислювати саму себе;
7. [`lib/reason.lisp`](lib/reason.lisp) — reasoning-напрям;
8. [`tests/fixtures/conformance.lisp`](tests/fixtures/conformance.lisp) — спостережувані факти, які мають пережити зміну реалізації.

Додатково:

- [`docs/testing.md`](docs/testing.md) — карта тестів;
- [`docs/benchmarks.md`](docs/benchmarks.md) — методика вимірювань;
- [`docs/adr/ADR-004-CLOSED-MCCARTHY7-CORE.md`](docs/adr/ADR-004-CLOSED-MCCARTHY7-CORE.md) — чому ядро 0+7 замкнене;
- [`docs/mccarthy-vision.md`](docs/mccarthy-vision.md) — історичний контекст і свідомі відхилення;
- [`AGENTS.md`](AGENTS.md) — правила роботи агентів у репозиторії;
- [`knowledge/guard-reference.lisp`](knowledge/guard-reference.lisp) — машинно-читане довідкове бюро Guard.

---

## English · auxiliary

`my-lisp` is a Lisp research language built around Canon 0, an experimental 8-bit semantic identity space, exact arithmetic, executable conformance, and an archipelago of autonomous execution kernels. The classical McCarthy primitives remain a historical/minimal root, but no longer form a permanent limit on what may become a primitive.

Ukrainian is the project's primary human language. English and German are auxiliary. The Rust runtime is the reference implementation, not semantic authority; start with [`language-contract.lisp`](language-contract.lisp) and [`docs/semantic-authority-map.md`](docs/semantic-authority-map.md).

The central research question is now: **how simple can the language remain while directly composing independent execution models without surrendering semantic identity to any of them?**

## Deutsch · ergänzend

`my-lisp` ist eine Lisp-Forschungssprache mit Canon 0, einem experimentellen 8-Bit-Raum semantischer Identitäten, exakter Arithmetik, ausführbarer Konformität und einem Archipel autonomer Ausführungskerne. Die klassischen McCarthy-Primitive bleiben ein historischer/minimaler Ursprung, sind aber keine dauerhafte Obergrenze mehr.

Ukrainisch ist die primäre menschliche Sprache des Projekts; Englisch und Deutsch sind Hilfssprachen. Rust ist die Referenzimplementierung, aber nicht die semantische Autorität. Maßgeblich sind [`language-contract.lisp`](language-contract.lisp), ratifizierte Entscheidungen und ausführbare Konformitätsbelege.

Die zentrale Forschungsfrage lautet: **Wie einfach kann die Sprache bleiben, während sie unabhängige Ausführungsmodelle direkt komponiert, ohne ihnen die semantische Identität zu überlassen?**


---

## Ліцензія

[ВОЛЬНІСТЬ](LICENSE)
