<div align="center">

<img src="docs/assets/wsm-lisp-hero.svg" alt="my-lisp — SID8 · CORE PROFILES · MULTI-SUBSTRATE" width="100%">

# my-lisp

**Проста Lisp-мова, що координує різні способи обчислення**

*Дослідження мови з одним функціональним простором: рівно 256 восьмибітних функцій `00000000..11111111`, поверх яких Core-профілі задають закони, а незалежні ядра дають механізми виконання.*

<p><a href="https://github.com/juv4uk/my-lisp/releases/latest/download/my-lisp-cli-web.html"><strong>▶ Спробувати my-lisp у вебі</strong></a></p>
<sub>Один автономний portable-файл <code>.html</code> · без встановлення · працює локально у браузері</sub>

[![CI](https://github.com/juv4uk/my-lisp/actions/workflows/ci.yml/badge.svg)](https://github.com/juv4uk/my-lisp/actions/workflows/ci.yml)
[![WASM](https://github.com/juv4uk/my-lisp/actions/workflows/wasm-browser-test.yml/badge.svg)](https://github.com/juv4uk/my-lisp/actions/workflows/wasm-browser-test.yml)
[![Surface drift](https://github.com/juv4uk/my-lisp/actions/workflows/surface-drift-check.yml/badge.svg)](https://github.com/juv4uk/my-lisp/actions/workflows/surface-drift-check.yml)

**Українська — перша мова проєкту.** Англійська й німецька — допоміжні.

</div>

---

## Що таке `my-lisp`

`my-lisp` — дослідницька Lisp-мова з єдиним функціональним простором `00000000..11111111`, точною арифметикою, виконуваними Core-законами та архіпелагом незалежних execution kernels.

Головний архітектурний принцип:

> **Мова володіє значенням та ідентичністю. Ядра володіють своїм способом обчислення. Жоден механізм не має права вигадувати семантику за мову.**

Rust лишається важливим механічним substrate/reference implementation, але не джерелом семантичної істини. Так само Prolog, Datalog, CLIPS і Common Lisp не стають глобальною semantic authority лише тому, що вони краще виконують свій клас задач.

```text
                  my-lisp
        00000000..11111111 / Core laws / data
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

Поточний машинний семантичний контракт — [`language-contract.lisp`](language-contract.lisp), версія **9.0**.


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

Особливо це стосується bootstrap: `lib/macro.lisp` і поточний профіль `lib/core4.lisp` є Lisp-owned behavior. `lib/core.lisp` лишається bounded compatibility donor/entry point під час міграції чотирьох Core. Якщо іншому субстрату потрібен host-механізм, він має бути вузьким і semantics-blind; backend не має права замінювати 8-бітний function SID словесною або власною identity.

Для Core4 функція SID `00000111` має тричленний закон `(query expected-result expression)`: спостережений результат порівнюється з явним expected datum, а вичерпання дає `UnsatisfiedConditional`. Інші Core можуть мати інший ратифікований закон для того самого SID. Contract 9.0 не створює для цього жодної словесної identity.

---

## Що вже доведено

Три терміни, на яких тримається evidence layer:

- **SID8** — сама 8-бітна function identity;
- **surface** — необов'язковий source/UI routing до SID8, але не функція і не meaning;
- **witness** — виконуваний доказ конкретного обмеженого твердження.

На сьогодні README може чесно показати такі результати:

- **Є один function-ID space:** `00000000..11111111`.
- **Surface не є функцією.** Українські, англійські, санскритські й символьні підказки можуть лише механічно маршрутизувати до SID8.
- **Vertical Day — bounded фізичний доказ.** Ратифікований зріз [`2026-09-14`](docs/research/2026-09-14-vertical-day.md) проводить `(00000101 (00000100 2 3))` через structured machine forms → closed admission → Lisp-owned x86-64 encoding → semantics-blind host → physical CPU і отримує `2`.
- **Machine path fail-closed.** Raw/malformed/unadmitted requests відхиляються до входу в host.

```text
(00000101 (00000100 2 3))
        ↓
Sid8
        ↓
Core-owned law / mechanism selection
        ↓
structured machine forms
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

## Єдиний функціональний простір

Поточний закон мови простий:

```text
00000000
...
11111111
```

Це рівно 256 **функціональних** SID. Жодного другого набору іменованих
функцій немає. Слова, символи, enum-мітки, opcode-и та backend-назви не
можуть бути identity функції.

Core1–Core4 — це профілі законів над тими самими SID, а не чотири набори
названих функцій.

`()` є структурним значенням поза функціональним простором. Усі 256
восьмибітних комбінацій `00000000..11111111` належать виключно функціям.

### Апостроф

Контракт 4.0 фіксує просте правило:

```lisp
'кіт        ; reader безпосередньо створює (00000001 кіт)

об'єкт      ; один ідентифікатор
п'ять       ; один ідентифікатор
зв'язок     ; один ідентифікатор
```

Апостроф на початку виразу — reader syntax, що ставить SID `00000001` без проміжної словесної identity; апостроф усередині слова — звичайна частина ідентифікатора.

### Десяткова кома

На українській розкладці десятковий роздільник можна набирати комою. Крапка й кома є двома написаннями **того самого точного числового значення**:

```lisp
(00000011 12,455 12.455)   ; t
(00001100 1,5 2,5)          ; 4
(00000011 -0,25 -0.25)     ; t
(00000011 1,5e3 1500)      ; t
```

Кома отримує числовий сенс лише тоді, коли весь токен є коректним числом. Тому `а,б` і `версія1,2` лишаються звичайними символами.

---

## Людський інтерфейс не створює функцій

Людські слова, локалізовані підказки, IDE-підписи та інші UI-представлення можуть існувати лише як зовнішня навігація до восьми бітів. Вони **не є функціями**, не мають власної семантичної тотожності й не входять до мови як другий набір операцій.

У поточній архітектурі функцію в контрактах, Core-законах, compiler IR та backend boundary позначають її точні 8 бітів:

```text
00000000
...
11111111
```

Будь-який людський інтерфейс повинен залишатися механічною проєкцією поза функціональною онтологією.

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
  ├─ 00000000..11111111 / Core laws
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

`my-lisp` є центральною мовою не тому, що виконує все сам, а тому, що зберігає **цілісність восьмибітного функціонального простору, Core-законів, композиції й прямий контакт із різними execution models**.

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
3. [`docs/language-core.md`](docs/language-core.md) — SID8-only архітектура ядра;
5. [`lib/surface/uk-acceptance.lisp`](lib/surface/uk-acceptance.lisp) — українська мова як виконуваний програмний інтерфейс;
6. [`lib/meta-eval.lisp`](lib/meta-eval.lisp) — як мова починає обчислювати саму себе;
7. [`lib/reason.lisp`](lib/reason.lisp) — reasoning-напрям;
8. [`tests/fixtures/conformance.lisp`](tests/fixtures/conformance.lisp) — спостережувані факти, які мають пережити зміну реалізації.

Додатково:

- [`docs/testing.md`](docs/testing.md) — карта тестів;
- [`docs/benchmarks.md`](docs/benchmarks.md) — методика вимірювань;
- [`docs/adr/ADR-004-CLOSED-MCCARTHY7-CORE.md`](docs/adr/ADR-004-CLOSED-MCCARTHY7-CORE.md) — історичний, не-нормативний документ;
- [`docs/mccarthy-vision.md`](docs/mccarthy-vision.md) — історичний контекст і свідомі відхилення;
- [`AGENTS.md`](AGENTS.md) — правила роботи агентів у репозиторії;
- [`knowledge/guard-reference.lisp`](knowledge/guard-reference.lisp) — машинно-читане довідкове бюро Guard.

---

## English · auxiliary

`my-lisp` is a Lisp research language with one exact 8-bit function-identity space (`00000000..11111111`), Core-specific laws, executable conformance, and multiple execution substrates. Human names are routing/UI metadata only, never function identities.

Ukrainian is the project's primary human language. English and German are auxiliary. The Rust runtime is the reference implementation, not semantic authority; start with [`language-contract.lisp`](language-contract.lisp) and [`docs/semantic-authority-map.md`](docs/semantic-authority-map.md).

The central research question is now: **how simple can the language remain while directly composing independent execution models without surrendering semantic identity to any of them?**

## Deutsch · ergänzend

`my-lisp` ist eine Lisp-Forschungssprache mit genau einem 8-Bit-Funktionsidentitätsraum (`00000000..11111111`), Core-spezifischen Gesetzen, ausführbarer Konformität und mehreren Ausführungssubstraten. Menschliche Namen sind nur Routing/UI-Metadaten.

Ukrainisch ist die primäre menschliche Sprache des Projekts; Englisch und Deutsch sind Hilfssprachen. Rust ist die Referenzimplementierung, aber nicht die semantische Autorität. Maßgeblich sind [`language-contract.lisp`](language-contract.lisp), ratifizierte Entscheidungen und ausführbare Konformitätsbelege.

Die zentrale Forschungsfrage lautet: **Wie einfach kann die Sprache bleiben, während sie unabhängige Ausführungsmodelle direkt komponiert, ohne ihnen die semantische Identität zu überlassen?**


---

## Ліцензія

[ВОЛЬНІСТЬ](LICENSE)
