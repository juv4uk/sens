
<div align="center">

<img src="docs/assets/wsm-lisp-hero.svg" alt="sens — exact-width domain language" width="100%">

# SENS (СЕНС)

**Експериментальна мова програмування, у якій двійкова координата є частиною семантики.**

<p><a href="https://github.com/juv4uk/sens/releases/latest/download/sens-cli-web.html"><strong>▶ Спробувати SENS у вебі</strong></a></p>
<sub>Один автономний portable-файл <code>.html</code> · без встановлення · працює локально у браузері</sub>

[![CI](https://github.com/juv4uk/sens/actions/workflows/ci.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/ci.yml)
[![WASM](https://github.com/juv4uk/sens/actions/workflows/wasm-browser-test.yml/badge.svg)](https://github.com/juv4uk/sens/actions/workflows/wasm-browser-test.yml)

**Українська — перша мова проєкту.**

</div>

---

## SENS у двох словах

SENS — це не «звичайна мова з бітовими opcode».

У SENS **точна двійкова послідовність + точна ширина + закон домену** утворюють semantic identity.

~~~text
D1 1  ≠  D2 01  ≠  D3 001  ≠  D4 0001
~~~

Число, яке можна отримати з бітів, — лише похідне представлення. 168 не стає семантичним значенням замість 10101000.

І так само байт, u8, FPGA-комірка чи інший carrier не визначає meaning.

Поточна нормативна база — **Contract 11.8, D1–D9**. Перехід самого `language-contract.lisp` до canonical visible-binary source ще триває в **#4248**; цей README описує цільову binary-source модель, а не оголошує незавершений cutover завершеним.

### Файлова та виконавча влада

Канонічне розширення вихідного коду — **`.lisp`**. У поточній українській проєкції це людський запис `ук`; семантичну тотожність задають точні двійкові слова, ширини та ратифіковані домени, а не назви функцій.

**`.wsm`** і **`.my`** — історичні псевдоніми розширення (*legacy aliases*) для сумісності. Вони не створюють інших семантичних законів.

**Rust — референсна реалізація** (*reference implementation*) для перевірюваного виконання, кодера/декодера й тестових оракулів. Rust, компілятор і жоден backend **не** визначають семантику SENS: її влада походить від ратифікованих законів і виконуваних свідчень; див. [карту семантичної влади](docs/semantic-authority-map.md).



---

## `.sens`: трійкова межа всередині, звичайний пробіл назовні

**Мова залишається строго двійковою.** Для файлового кодера `.sens` обрано T5 (транспортні трити 0/1/2, п'ять тритів на фізичний байт). `2` означає лише внутрішню межу доменних слів: коли файл відкритий через декодер, бачимо **звичайні пробіли**. **Окремого завершувача `22` немає:** кінець визначає сам файл, у фінальному байті можуть бути лише 0–4 трити `2` для доповнення.

~~~text
Двійкові слова:  10 | 001 | 00 | 000 | 01
Перегляд .sens:  10 001 00 000 01
~~~

~~~shell
cargo run -q -p sens-cli --bin sens-trit -- encode path/program.lisp
cargo run -q -p sens-cli --bin sens-trit -- open path/program.sens

# Фізична двійкова програма виконується без текстового Lisp-парсера:
cargo run -q -p sens-cli --bin sens -- tests/fixtures/migration-quote-cohort-main/quote-legacy.sens

# Еквівалентний явно викликаний чистий evaluator:
cargo run -q -p sens-cli --bin sens-trit -- eval tests/fixtures/migration-quote-cohort-main/quote-legacy.sens
~~~


**Поточна виконавча межа:** `sens file.sens` читає фізичні T5-байти, перевіряє канонічну D2-структуру й передає точні доменні слова чинному SENS-виконавцю **без** текстового Lisp-reader, неявного Core4-bootstrap або host capabilities. `sens-trit open file.sens` тільки показує бітовий перегляд, не виконує його. `sens-trit eval-core4 file.sens` є окремим *явним* запитом завантажити Core4, а не наслідком відкриття файлу. Недопущені закони чи дефектне T5 викликають відмову; чистий CLI-запуск сам по собі не є доказом історичної/української semantic-oracle parity. Перевірка механіки — [Physical binary SENS CLI smoke](.github/workflows/physical-binary-sens-cli.yml).

**Правило міграції репозиторіїв:** існуючий `каталог/назва.lisp` має відповідник `каталог/назва.sens`, який містить справжні T5-байти з транспортною `2` лише між точними двійковими словами. Створювати **третій однойменний файл `каталог/назва` без розширення** як похідний перевірюваний перегляд точних бітових слів `0/1`, розділених **одним ASCII-пробілом**, із одним завершальним LF. Не зберігати текст `0/1/2` у `.sens` і не підміняти фізичні T5-байти видимим бітовим записом. `.lisp`, `.sens` і файл-view мають проходити спільний перевірений roundtrip; сам лише транспортний view **не підтверджує семантичного допуску**. [Міграція `.lisp → .sens`](docs/SENS-LISP-TO-T5-MIGRATION-2026-10-08.uk.md), [координація агентів #4449](https://github.com/juv4uk/sens/issues/4449).

Файл `.sens` **фізично двійковий**, не ASCII. `open/view` декодує його у текст для людини; звичайному редактору потрібен окремий codec provider або file association. Деталі й обмеження: [T5 `.sens` — відображення пробілів](docs/sens-t5-space-view.uk.md). Формальна ратифікація всього wire-v1, зокрема EOS, лишається окремою задачею #4444.

---
## Подивімося на саму мову

Ось маленька програма, у якій **весь executable source можна побачити як точні двійкові слова**.

Людська форма:

~~~lisp
(CAR (CONS () ()))
~~~

Це означає:

> взяти CAR від пари, у якій обидва елементи — порожня структура.

Канонічна видима двійкова форма:

~~~text
10 100 00 10 111 00 000 00 000 01 01
~~~

Тут немає ні #b..., ні рядків "101", ні десяткових semantic IDs.

Розбираємо послідовність:

~~~text
10    D2 open
100   D3 CAR
00    D2 separator

10    D2 open
111   D3 CONS
00    D2 separator
000   D3 empty
00    D2 separator
000   D3 empty
01    D2 close

01    D2 close
~~~

Тобто структура програми видно прямо з бітів:

~~~text
10 [100 00 10 [111 00 000 00 000] 01] 01
~~~

А semantic words мають **різну ширину там, де цього вимагає домен**:

~~~text
D2 = 2 біти
D3 = 3 біти
~~~

Результат цієї програми — D3 000, тобто порожня структура.

### Те саме іншою surface-мовою

Людські surface names — лише проекції. Наприклад, current Ukrainian surface може записати ту саму операцію як:

~~~lisp
(перше (сполучити () ()))
~~~

Семантична програма при цьому не стає іншою. Після canonical lowering вона приходить до тієї самої двійкової identity.

---

## Чотири фундаментальні речі

### 1. D2 задає форму

D2 не містить Core-функцій. Він описує структуру source:

~~~text
00  separator
01  close
10  open
11  dot
~~~

Наприклад:

~~~text
10 100 00 000 01
~~~

має відкрити форму, покласти туди D3-word 100 і закрити її.

11 — саме D2 dot. Воно не є «ще одним opcode».

### 2. D3 задає фундамент мови

Поточний D3:

| Біти | Meaning | Surface |
|---|---|---|
| 000 | порожня структура | `()` |
| 001 | QUOTE | як-є |
| 010 | ATOM | атом? |
| 011 | CDR | решта |
| 100 | CAR | перше |
| 101 | EQ | тотожне? |
| 110 | COND | за-умовою |
| 111 | CONS | сполучити |

Ці координати — **current authority**, а не старі prefix-tree експерименти.

### 3. Ширина є частиною identity

Не можна зробити так:

~~~text
001 → 1 → byte 1
~~~

і потім забути, що це був D3.

Правильно:

~~~text
(D1, 1)
(D2, 01)
(D3, 001)
(D4, 0001)
~~~

— чотири різні exact-width identities.

### 4. Carrier не є семантикою

У пам'яті D3 може фізично лежати в u8.

На FPGA D3 може потрапити у ширшу BRAM word.

У WASM воно може пройти через integer type.

Це нічого не змінює:

~~~text
semantic width  ≠  physical carrier width
~~~

---

## D1–D9

SENS будує не одну плоску таблицю opcode, а **драбину доменів**.

| Домен | Ширина | Роль |
|---|---:|---|
| D1 | 1 | точний PredicateBit |
| D2 | 2 | структура source |
| D3 | 3 | фундамент Core |
| D4 | 4 | bootstrap |
| D5 | 5 | наступний exact-width semantic domain |
| D6 | 6 | наступний exact-width semantic domain |
| D7 | 7 | Sound7/Text7 та окремі role laws |
| D8 | 8 | повний owner-ratified domain |
| D9 | 9 | повний owner-ratified domain |

Поточна owner-ratified картина:

~~~text
D7 = 126/128 admitted; 2 координати reserved
D8 = 256/256
D9 = 512/512
~~~

D9 має окремий runtime-carrier ланцюг. Це механізм розміщення, а не привід звести D9 назад до D8/SID8.

---

## Як виглядає справжня binary source

Канонічний source має містити **лише видимі біти та синтаксичні розділення**.

Добре:

~~~text
10 100 00 10 111 00 000 00 000 01 01
~~~

Не є канонічним semantic source:

~~~text
#b100
"100"
4
168
Sid8(168)
Function8(...)
~~~

Останні форми можуть існувати як compatibility, tooling або host representation, але вони не повинні ставати authority для current SENS source.

---

## Чому 00, 01, 10, 11 не плутаються з D3

Двобітні слова належать **D2**.

Трибітні слова належать **D3**.

Тому:

~~~text
10  ≠  010
01  ≠  001
11  ≠  111
~~~

10 — D2 open.

010 — D3 ATOM.

11 — D2 dot.

111 — D3 CONS.

Саме тому SENS не намагається вирівняти все до одного 8-бітного поля.

---

## Як мова росте

SENS не хоче вручну роздати meaning кожному вільному бітовому шаблону.

Потрібен закон:

~~~text
корінь
  ↓
закон
  ↓
породження
  ↓
witness
  ↓
falsifier / negative cases
  ↓
ratification
~~~

Для selector-family це особливо наочно. У current D3:

~~~text
100 = CAR
011 = CDR
~~~

Але подальший selector не можна призначати тільки через «схожість бітів». Кожна family-law має бути окремо доведена або ратифікована.

Отже:

> **геометрія допомагає знайти закон; вона не замінює закон.**

---

## Канонічний pipeline

~~~text
human / symbolic surface
        ↓
domain-aware parser
        ↓
exact-width semantic objects
        ↓
domain laws / evaluator
        ↓
IR / lowering
        ↓
Rust / WASM / C / FPGA / other substrate
~~~

Назва CAR, перше, aṇu або інша surface-форма не є semantic authority.

Так само backend не має права сказати:

> «у мене opcode 100, отже це CAR».

Правильний напрямок інший:

> «семантика вже визначила exact D3:100; backend лише обирає механізм виконання».

---

## Українська surface

Українська — основна surface-мова SENS.

Поточні короткі програмні імена:

~~~text
порожнє
як-є
атом?
решта
перше
тотожне?
за-умовою
сполучити
~~~

Повні назви та інші поверхні зберігаються окремо:

~~~text
ук → укр → san → en → LISP → sym
~~~

Surface можна повністю перейменувати без зміни semantic identity.

---

## Інструменти для двійкової мови

У репозиторії вже є корисне tooling-ядро.

### Єдина команда для міграції `.lisp` → фізичний `.sens`

**Запускайте з кореня репозиторію:** `scripts/migrate.py` — перевірений
маршрутизатор до вже реалізованих трьохпрохідного мігратора, T5-кодека,
Git-атестації й справжнього SENS Rust-оракула. Він не додає нових функцій
мови, не конвертує непідтверджені символи за схожістю назв і не пише в
`main` автоматично.

~~~bash
# 1. Назви конкретних ще не допущених файлів та причини, БЕЗ запису
python3 scripts/migrate.py candidates --report /tmp/sens-candidates.json

# 2. Пробний запуск справжнього мігратора на ОДНОМУ старому файлі
python3 scripts/migrate.py preview benchmarks/lists.lisp \
  --mirror /tmp/sens-preview --report /tmp/sens-preview.json
# Якщо повернуло BLOCKED — потрібний доказ/закон, а НЕ вимкнення захисту

# 3. Збірка чинного Rust D2 рідера
cargo build -p sens-cli --bin sens-trit

# 4. Допуск тільки після незалежно доведеного source→T5→oracle
python3 scripts/migrate.py admit \
  --manifest /tmp/approved-original-proof.json \
  --mirror /tmp/sens-approved \
  --reader target/debug/sens-trit \
  --report /tmp/sens-admission.json

# 5. Лише якщо попередній звіт VERIFIED_NOT_WRITTEN
python3 scripts/migrate.py admit \
  --manifest /tmp/approved-original-proof.json \
  --mirror /tmp/sens-approved \
  --reader target/debug/sens-trit \
  --report /tmp/sens-written.json --write
~~~

`preview` ніколи не має `--write`. Публікація доступна **тільки**
через `admit --write`: маніфест фіксує вихідний Git blob,
фізичний SHA256, typed-word SHA256 і команди незалежного оракула.
Запис — лише нового файла `name.sens` у зовнішньому mirror; старий
`name.lisp` зберігається, перезапис заборонено. Результат
`BLOCKED` не вважати міграцією. Нові контрольні приклади не рахувати
як перенесення старих файлів.

Для агентів обов'язкові три окремі класи доказів: **правильні T5-байти,
валідна D2-структура, семантична еквівалентність у незалежному оракулі**.
Деталі маніфесту: [допуск міграції](docs/ADMIT-T5-MIGRATION.uk.md);
[координація #4449](https://github.com/juv4uk/sens/issues/4449).

### Exact-width witness-и

Корисні дослідницькі скрипти:

~~~text
scripts/research-2077-binary-word-law.py
scripts/research-2092-word-algebra.py
~~~

Вони досліджують exact binary words, width-preserving identity, prefix-vs-equality та зовнішнє framing.

Старі research witness-и в research-1962-*, research-2023-*, research-2034-* можуть містити історичні координати. Їхні алгоритми корисні, але їхні старі бітові карти не є current authority.

---

## Запуск

Потрібен Rust toolchain.

~~~bash
# REPL
cargo run -p sens-cli

# або приклад REPL
cargo run -p sens --example repl

# файл
cargo run -p sens-cli -- path/to/file.lisp

# тести
cargo test --workspace

# build
cargo build --workspace

# clippy
cargo clippy --workspace --all-targets -- -D warnings
~~~

Канонічне розширення source-файлів — **.lisp**.

.wsm та .my залишаються legacy aliases для старих матеріалів.

---

## Де дивитися далі

**Семантика:**

- [language-contract.lisp](language-contract.lisp)
- [docs/domain-paradigm.uk.md](docs/domain-paradigm.uk.md)
- [docs/language-core.md](docs/language-core.md)
- [docs/semantic-authority-map.md](docs/semantic-authority-map.md)

**Домени:**

- [lib/domains/](lib/domains)

**Conformance:**

- [tests/fixtures/conformance.lisp](tests/fixtures/conformance.lisp)

**Binary tooling:**

- [scripts/migrate-to-sens-codes.py](scripts/migrate-to-sens-codes.py)
- [scripts/research-2077-binary-word-law.py](scripts/research-2077-binary-word-law.py)
- [scripts/research-2092-word-algebra.py](scripts/research-2092-word-algebra.py)

**Правила для агентів:**

- [AGENTS.md](AGENTS.md)

---

## Що SENS намагається зробити

Не:

~~~text
зробити стару мову трохи компактнішою
~~~

і не:

~~~text
покласти всі функції у 8-бітну таблицю
~~~

А:

~~~text
визначити точні домени
        ↓
знайти закони між ними
        ↓
отримувати semantic objects з цих законів
        ↓
переносити одну семантику між різними substrates
~~~

Тому головний об'єкт SENS — не opcode.

**Головний об'єкт SENS — точна семантична identity, яку можна перенести з мови в мову, з backend у backend і з carrier у carrier, не змінюючи того, чим вона є.**

---

## English

SENS is an experimental programming language built around **exact-width binary domains**.

A semantic object is:

~~~text
exact bits + exact domain + proved/ratified law
~~~

Width is part of identity. A byte or u8 carrier is only storage.

Current Contract 11.8 ratifies D1–D9. D2 owns source structure; D3 and higher domains own semantic residents according to their own laws.

Canonical binary source is visible binary, not decimal IDs, #b..., quoted binary strings, or host opcode wrappers.

The project is designed so that the same semantic identity can be executed by different substrates without making any backend the owner of language meaning.

---

## License

[ВОЛЬНІСТЬ](LICENSE)
