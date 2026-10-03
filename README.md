<div align="center">

<img src="docs/assets/wsm-lisp-hero.svg" alt="sens — experimental exact-width language · multi-substrate" width="100%">

# sens (СЕНС)

**Експериментальна мова програмування з exact-width двійковими доменами**

*An experimental programming language exploring exact-width binary domains*

*SENS досліджує domain-derived semantics, точну ширину двійкової identity, щільне packed-представлення, виконувані закони та різні execution substrates. Lisp був початковим синтаксичним носієм і середовищем прототипування.*

> **Поточний фундамент:** ратифіковані D1→D4 exact-width domains. Історичні SENS8 / Function8 механізми лишаються compatibility/research provenance під час міграції, але більше не є описом поточної онтології мови.

<p><a href="https://github.com/juv4uk/sens/releases/latest/download/sens-cli-web.html"><strong>▶ Спробувати sens у вебі</strong></a></p>
<sub>Один автономний portable-файл <code>.html</code> · без встановлення · працює локально у браузері</sub>

[![CI](https://github.com/juv4uk/sens/actions/workflows/ci.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/ci.yml)
[![WASM](https://github.com/juv4uk/sens/actions/workflows/wasm-browser-test.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/wasm-browser-test.yml)
[![Surface drift](https://github.com/juv4uk/sens/actions/workflows/surface-drift-check.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/surface-drift-check.yml)

**Українська — перша мова проєкту.** Англійська й німецька — допоміжні.

</div>

---

## Що таке `sens` (СЕНС)

`sens` (СЕНС) — експериментальна мова програмування й дослідницька платформа для exact-width двійкової identity, domain-derived semantics, точної арифметики, компактного packed-представлення та незалежних execution kernels.

Історично проєкт розвивався під робочою назвою `my-lisp`. Lisp слугував початковим синтаксичним носієм і середовищем прототипування; пізніше проєкт пройшов через flat SENS8 / Function8 фазу. Поточний ратифікований фундамент інший: ширина є частиною identity, а D1, D2, D3 і D4 є різними exact-width доменами. Людські назви лишаються проєкціями й не визначають машинну identity.

Головний архітектурний принцип:

> **Мова володіє значенням та ідентичністю. Ядра володіють своїм способом обчислення. Жоден механізм не має права вигадувати семантику за мову.**

Rust лишається важливим механічним substrate/reference implementation, але не джерелом семантичної істини. Так само Prolog, Datalog, CLIPS і Common Lisp не стають глобальною semantic authority лише тому, що вони краще виконують свій клас задач.

```text
                     sens
       exact-width domains / laws / data
                      |
        +-------------+-------------+
        |             |             |
    local sens      routing       observation
        |             |             |
        +------+------+------+------+
               |      |      |
           Common   Prolog  Datalog  CLIPS
            Lisp
```

Нова дисципліна проста: `sens` має вміти **висловити, адресувати, передати, прийняти й композиційно використати** результат, але не зобов'язаний повторно реалізовувати всередині себе найкращий алгоритм кожного острова.

Поточний машинний семантичний контракт — [`language-contract.lisp`](language-contract.lisp), версія **10.1** (domain-authority cutover; Contract 10.0 flat-Function8 збережений як NON-NORMATIVE provenance у `contracts/history/`).


### Одна мова, різні субстрати

Поточний напрям substrate switch фіксує ще жорсткішу межу:

> **`sens` лишається семантичною владою; субстрат змінюється без міграції значення.**

Тобто перенесення виконання на GraalVM, WASM, C, FPGA чи інший host не повинно породжувати другу реалізацію мови. Новий субстрат має виконувати той самий pinned sens source і доводити це незалежним witness-шаром.

```text
pinned sens source
        ↓
semantic contract + executable laws
        ↓
      substrate
   ↙      ↓      ↘
 Rust   GraalVM   WASM / C / FPGA
```

Особливо це стосується bootstrap: `lib/macro.lisp` і поточний профіль `lib/core4.lisp` є Lisp/sens-owned behavior. `lib/core.lisp` лишається bounded compatibility donor/entry point під час міграції чотирьох Core. Інший субстрат або Rust-host може мати власну локальну семантику, таблиці, lowering, dispatch і fallback. Межа асиметрична: ця implementation semantics не має ставати джерелом мовної істини для СЕНС або замінювати exact-width identity словесною чи host-owned identity.

D3-слово `011` (`COND`) має двочленний закон `(test expression)`: тест повертає рівно PredicateBit `1` або `0`; `1` вибирає гілку, `0` переходить до наступної, а вичерпання повертає структурне `()`.

---

## Що вже доведено

Для evidence layer достатньо простої межі:

- width є частиною identity: `1 != 01 != 001 != 0001`;
- ратифікований фундамент D1→D4 використовує точні ширини 1, 2, 3 і 4 біти;
- packed payload переносить біти щільно, але сам payload не вигадує межі слів;
- surface — лише необов'язкова людська проєкція;
- witness — виконуваний доказ конкретного обмеженого твердження.

На сьогодні README може чесно показати такі результати:

- **Exact-width carriers працюють механічно.** `Bits<N>`, `BinarySourceWord`, `BitPacker` і `PackedBitstream` зберігають width + bits без zero-padding identity.
- **D1→D4 ратифіковані як різні домени.** D1 — PredicateBit, D2 — структура, D3 — фундаментальні операції, D4 — bootstrap-шар.
- **Packed source має явну boundary-межу.** Однаковий payload може мати різні valid width schedules; standalone framing досліджується окремо.
- **Міграція одностороння.** Новий exact-width код не повинен створювати нову залежність від legacy SENS8 / Function8 identity.
- **Vertical Day — історичний bounded machine-path доказ.** Зріз [`2026-09-14`](docs/research/2026-09-14-vertical-day.md) передує поточній D1→D4 моделі й зберігається як provenance, а не як доказ сучасної identity-схеми.
- **Machine path fail-closed.** Raw/malformed/unadmitted requests відхиляються до входу в host.

**Ще не доведено:** complete native GC/general heap, first-class escaping native pairs, automatic GPU/FPGA scheduler, complete Lisp machine або OS. Повний список меж твердження й exact evidence ledger лежить у датованому [`Vertical Day record`](docs/research/2026-09-14-vertical-day.md).

README лише показує вже зароблені докази; він не є новим джерелом семантичної влади.

---

## Exact-width фундамент

Поточний ратифікований фундамент не є flat 256-slot function space. Width входить у identity:

```text
D1: 1 bit
D2: 2 bits
D3: 3 bits
D4: 4 bits
```

Тому однакове числове значення з різною шириною не є однією identity:

```text
1 != 01 != 001 != 0001
0 != 00 != 000 != 0000
```

Поточні доменні ролі:

- **D1 / PredicateBit** — рівно `0` або `1`;
- **D2 / racanā2** — структурні слова;
- **D3 / bīja3** — ратифіковані фундаментальні операції;
- **D4** — bootstrap-рівень, включно з LAMBDA/DEFINE та породженими/похідними residents.

Packed transport не надає слову семантики: він переносить точні біти й ширину/межі, отримані від граматики або envelope. Семантичне значення належить домену вище transport layer.

Історичний `Sens8` / Function8 простір лишається compatibility/research donor під час міграції. Він не є поточною онтологічною моделлю нового exact-width коду.

### Compatibility reader/UI examples

Наступні приклади документують чинні reader/surface compatibility paths під час міграції. Вони не перевизначають exact-width D1→D4 identity.

### Апостроф

Контракт 4.0 фіксує просте правило:

```lisp
'кіт        ; те саме, що (quote кіт)

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

## Українською можна програмувати

Українська — не лише мова README. Людські слова є source/UI-проєкціями, а не machine identity. Чинний [`lib/surface/semantic-registry.lisp`](lib/surface/semantic-registry.lisp) ще містить compatibility SID8 routing під час міграції; exact-width D1→D4 фундамент від цього registry не залежить.

У проєкті розрізняються **дві українські поверхні**:

- `ук` — коротка, інтуїтивно зрозуміла українська поверхня для щоденного програмування;
- `укр` — повна українська поверхня, де ім'я максимально явно описує операцію.

Обидві належать **тому самому semantic ID**. Якщо чинне `ук`-ім'я вже коротке й ясне, `ук` і `укр` можуть бути однаковими. Якщо повна назва краще пояснює дію, `укр` може бути довшою:

| byte SID | `ук` | `укр` |
|---:|---|---|
| `00000010` | `атом?` | `атом?` |
| `00001001` | `визначити` | `визначити` |
| `00111100` | `текст-порожній?` | `порожній-текст?` |
| `01011010` | `монотонний-нс` | `монотонний-час-у-наносекундах` |
| `01011110` | `поточний-всч` | `поточний-всесвітній-координований-час` |

У чинній моделі surface status-категорій немає. Кожен namespace slot містить або spelling, або `()`:

```lisp
("00001100"
  (en ())
  (ук додати)
  (укр додати)
  (sa yoga)
  (sym +))
```

Тобто немає прихованої третьої категорії між «ім'я є» і «імені немає». Якщо ім'я існує в реєстрі — воно маршрутизується до відповідного SID.

Повна жива таблиця `ук | укр | English | Sanskrit` генерується з authority: [`docs/generated/function-table.md`](docs/generated/function-table.md). Детальні пояснення поведінки: [`docs/ukrainian-api.md`](docs/ukrainian-api.md). Репрезентативний executable witness без перемикання на латинську розкладку: [`lib/surface/ukr-acceptance.lisp`](lib/surface/ukr-acceptance.lisp).

Окремо [`docs/generated/public-api-discovery.md`](docs/generated/public-api-discovery.md) рекурсивно показує всі знайдені top-level `def`/`defmacro` у живому `lib/**/*.lisp`. Його рядки поки мають статус `unreviewed`: discovery не оголошує функцію публічною і не створює semantic ID.

Поточний код через `ук` може виглядати так:

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

Раніше центральним дослідницьким питанням було: скільки поведінки можна повернути всередину самого evaluator.

Цей напрям дав важливі результати, але тепер проєкт рухається далі: **не все корисне повинно жити всередині одного evaluator**.

```text
sens
  ├─ exact-width domains / surfaces / laws
  ├─ локальна sens-поведінка
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

Попередня пірамідальна модель була корисною як спосіб вийти з замкненої бульбашки й перестати зводити всі відповіді до одного наперед заданого truth model.

Тепер її роль спрощується.

Вона може лишатися як:
- опційна view/projection над evidence;
- інструмент для incomplete/conflicting evidence;
- compatibility/research layer.

Але Prolog, Datalog і CLIPS отримують право лишатися собою. `sens` не має перетворювати їхні native результати на одну універсальну логічну шкалу.

Принцип:

> **Не змушувати реальність ставати зручною для однієї внутрішньої моделі.**

Якщо Prolog повертає багато substitutions — зберігаємо множинність.  
Якщо Datalog не вивів факту — не домальовуємо його.  
Якщо два kernels суперечать один одному — зберігаємо обидва результати та provenance.  
Якщо bridge неповний — неповнота є допустимим результатом.

### Король і свита

Історична метафора проєкту тепер отримує точніший зміст:

```text
             sens
       identity / Canon
          /   |   \
         /    |    \
   Prolog  Datalog  CLIPS  Common Lisp
```

`sens` є центральною мовою не тому, що виконує все сам, а тому, що зберігає **цілісність identity, Canon, композицію й прямий контакт із різними execution models**.

Кожен острів говорить із мовою прямо й повертає власний результат без обов'язкового переписування під одну універсальну семантику.

---

## Хост не є семантикою

`sens` не ставить собі за мету механічно «переписати Rust на Lisp». Межа інша:

```text
OS / hardware
      ↓
спостереження та capability-механізми
      ↓
значення sens
      ↓
Lisp/sens-визначена інтерпретація / політика / протокол
```

Тому низькорівнева операція може чесно лишатися в Rust, C або FPGA, якщо вона є механізмом. Але semantic policy не повинна випадково ставати властивістю конкретного хоста.

Живий аудит цієї межі: [`docs/host-semantic-surface.md`](docs/host-semantic-surface.md).

---

## Незалежні субстрати

Різні реалізації потрібні не для того, щоб копіювати одну архітектуру, а щоб **ламати приховані припущення одна одної**.

- [`crates/sens`](crates/sens) — референсний Rust crate: exact-width carriers/packing плюс bounded compatibility API (зокрема історичний Sens8);
- [`crates/sens`](crates/sens) — референсний Rust runtime (перехідний сумісний шар);
- [`crates/sens-cli`](crates/sens-cli) — CLI, REPL і semantic oracle (sens-oracle);
- [`crates/sens-wasm`](crates/sens-wasm) — WebAssembly;
- [`crates/sens-lsp`](crates/sens-lsp) — LSP;
- [`crates/sens-host`](crates/sens-host) — явна межа OS capabilities;
- [`c-runtime/`](c-runtime/) — C + x86_64 substrate;
- [`racket/`](racket/) — `#lang sens` для Racket/DrRacket;
- [`juv4uk/cml`](https://github.com/juv4uk/cml) — AOT / heterogeneous compiler напрям;
- [`juv4uk/fpga-lisp`](https://github.com/juv4uk/fpga-lisp) — фізично інша Lisp/sens-машина на FPGA.

Сумісність визначається контрактами, а не тим, наскільки схожий код реалізацій.

---

## Локальний запуск

Потрібні Rust toolchain і залежності workspace. У репозиторії також є Guix manifest для відтворюваного середовища.

```bash
# REPL (через sens або sens-cli)
cargo run -p sens --example repl # або: cargo run -p sens-cli

# виконати файл
cargo run -p sens-cli -- path/to/file.lisp

# повний workspace
cargo test --workspace
cargo build --workspace
cargo clippy --workspace --all-targets -- -D warnings
```

Канонічне розширення вихідного коду — **`.lisp`** (згідно з [sens#81](https://github.com/juv4uk/sens/issues/81)). **`.wsm`** і **`.my`** лишаються повністю підтримуваними legacy aliases.

---

## З чого читати проєкт

Якщо відкриваєте `sens` уперше, цей порядок дає найменше плутанини:

1. [`language-contract.lisp`](language-contract.lisp) — що саме обіцяє мова;
2. [`docs/semantic-authority-map.md`](docs/semantic-authority-map.md) — хто має право визначати істину;
3. [`docs/language-core.md`](docs/language-core.md) — історична SID8-only архітектура; читати як migration/provenance donor, не як поточний exact-width фундамент;
4. [`lib/canon.lisp`](lib/canon.lisp) — legacy law witness під міграцією #1325;
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

`sens` (СЕНС) is an experimental programming language and research platform exploring exact-width binary identities, domain-derived semantics, compact packed representation, executable laws, and multiple execution substrates. Its current ratified foundation is D1→D4, where width is part of identity. The earlier flat SENS8 / Function8 model remains compatibility and research provenance during migration, not the current ontology. Human names (Ukrainian, English, Sanskrit, symbols) are non-authoritative source/UI projections.

Ukrainian is the project's primary human language. English and German are auxiliary. The Rust runtime is the reference implementation, not semantic authority; start with [`language-contract.lisp`](language-contract.lisp) and [`docs/semantic-authority-map.md`](docs/semantic-authority-map.md).

The central research question is now: **how simple can the language remain while directly composing independent execution models without surrendering semantic identity to any of them?**

## Deutsch · ergänzend

`sens` (СЕНС) ist eine experimentelle Programmiersprache und Forschungsplattform für exakt breite binäre Identitäten, domänenabgeleitete Semantik, kompakte gepackte Darstellung, ausführbare Gesetze und mehrere Ausführungssubstrate. Das aktuell ratifizierte Fundament ist D1→D4; die Bitbreite ist Teil der Identität. Das frühere flache SENS8-/Function8-Modell bleibt während der Migration nur Kompatibilitäts- und Forschungsprovenienz. Menschliche Namen (Ukrainisch, Englisch, Sanskrit, Symbole) sind nicht-autoritative Source-/UI-Projektionen.

Ukrainisch ist die primäre menschliche Sprache des Projekts; Englisch und Deutsch sind Hilfssprachen. Rust ist die Referenzimplementierung, aber nicht die semantische Autorität. Maßgeblich sind [`language-contract.lisp`](language-contract.lisp), ratifizierte Entscheidungen und ausführbare Konformitätsbelege.

Die zentrale Forschungsfrage lautet: **Wie einfach kann die Sprache bleiben, während sie unabhängige Ausführungsmodelle direkt komponiert, ohne ihnen die semantische Identität zu überlassen?**


---

## Ліцензія

[ВОЛЬНІСТЬ](LICENSE)
