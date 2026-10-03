# GC M0.5 — ВИМОГИ ВЛАСНИКА: безпека даних і прозорість

> **CURRENT OWNER DIRECTION — 2026-10-03 / #2544 (docs follow-up #2547) supersedes semantic observability below**
>
> The August safety goal remains: never reclaim reachable data; prefer a leak over
> silent loss while the root protocol is untrusted. What changes is the boundary:
> collection timing/count/journal/quarantine are engineering diagnostics only, not
> language semantics. `(gc-promote ...)`-style resurrection is forbidden at the
> semantic surface. Weak references and finalizers are not admitted language features.
> Canonical contract: `docs/gc-reachability-contract.md`.



**Статус:** OWNER DIRECTIVE · **Дата:** 2026-08-23
**Джерело:** прямі вимоги власника (дослівно нижче) · **Автор перекладу
у властивості:** Оксі (Vyasa)
**Доповнює:** gc-m0-design.md · gc-holistic-map.md · gc-analysis-vyasa.md

---

## 0. Дослівні вимоги власника

> «я хочу зробити збирач сміття так щоб потім не жаліти що він зїсть
> важливі дані, щоб він був прозорий, щоб я розумів що і коли він робить»

Це — постановка вимог вищого пріоритету над усіма оптимізаційними
міркуваннями документів вище. Переклад у формальні властивості:

## 1. «Щоб не зʼїв важливих даних» → Safety properties

```text
I1 reachability:  досяжне від коренів живе ЗАВЖДИ
Bias:             при сумніві — НЕ ЗВІЛЬНЯТИ
                  (витік полагоджується; втрачені дані — ні)
```

Механізми гарантії:

- **явні roots only** — жодного магічного сканування Rust stack;
  кожен живий Value або в оточенні, або rooted явно;
- **non-moving**: адреси обʼєктів не переписуються — виключається
  цілий клас багів «дані пошкоджені при компакції/переміщенні»;
- **ObjectId + generation**: старий handle фізично не може вказати
  на новий обʼєкт (захист ABA);
- **named failure**: будь-який підозрілий стан графа → `ErrorKind`
  з назвою, ніколи не мовчазна поведінка.

## 2. «Прозорий, щоб розумів що і коли» → Observability як частина M0

Це ДОПОВНЕННЯ до gc-m0-design, якого там бракує: журнал збирання є
частиною семантики M0, не «діагностикою потом».

### 2.1 Append-only `(gc-journal)`

Кожне збирання записує подію (патерн evidence ledger / knowledge-journal):

```lisp
(gc-journal)
;; ((event gc) (ts 1787...) (trigger alloc-threshold)
;;  (roots-before 214) (live-before 18271)
;;  (reclaimed 17358)
;;  (by-type ((pair 9000) (closure 12) (env 3)))
;;  (duration-ms 3))
```

Гарантія: власник у будь-який момент питає машину «що і коли ти
звільняв» — і отримує повну відповідь. Немає події = не було
збирання.

### 2.2 Явна політика тригера

Колекція відбувається ТІЛЬКИ:
1. на точках алокування при перевищенні порога;
2. за явним diagnostic примитивом `(gc)`.

Жодного фонового потоку, жодного прихованого часового тригера в M0.

### 2.3 Metamorphic-контроль для власника особисто

Та сама програма в normal і stress-режимі (`MY_LISP_GC_STRESS=1`)
мусить дати байт-в-байт однаковий результат. Бажаєш переконатись —
одна змінна середовища; ніякої віри на слово.

### 2.4 `(gc-stats)` завжди доступний без запуску збирання.

## 3. Порядок кроків (без жалю)

| # | Крок | Верифікація |
|---|---|---|
| 0 | Пояснити фантомний cdr-баг (репро у vyasa, WSM-24 combined file) | детерміноване репро + фікс або класифікація |
| 1 | Telemetry циклів/env на yantra+WSM-24 workload | числа: чи є що збирати |
| 2 | Failing tests матриці безпеки (reachability/cycles/closures) | червоні ДО коду |
| 3 | ManagedHeap: Pair-only, non-moving STW | найменше доведуване ядро |
| 4 | **gc-journal + gc-stats з першого дня** | прозорість = тестована властивість M0 |
| 5 | Stress-mode + metamorphic sweep | доказ «без жалю» |

## 4. Звʼязки

- `cons_limit` (Environment::with_cons_limit) — готовий test seam
  для майбутнього колектора та для FPGA-contract паралелі.
- Agent Guard evidence ledger — той самий принцип прозорості,
  застосований до памʼяті замість поведінки агента.
- Після кроку 4: `(gc-journal)` події можуть публікуватись у swarm
  як факти (result-style), якщо owner забажає.

---

## 5. Доповнення Сакші (2026-08-23): Quarantine mode + owner verification ritual

Прийнято директиву дослівно. Два механізми понад переклад Оксі, які
безпосередньо обслуговують «щоб потім не жаліти»:

### 5.1. Quarantine / «цвинтар» — двофазне звільнення

```text
Фаза 1: unreachable → переміщається в QUARANTINE (лімітована зона)
        + запис у gc-journal: що саме там лежить (type/size/span)
Фаза 2: реальне звільнення — лише якщо обʼєкт пережив ПОВНИЙ цикл
        колекції в карантині і ніхто його не запросив
```

Властивість: навіть якщо root protocol помилиться і collector визнає
живий обʼєкт сміттям — дані НЕ втрачені, вони оглядаються у карантині
і відновлювані. Recycle bin для heap; той самий патерн, що swarm journal.

**Ціна чесно:** подвійна памʼять на карантинні обʼєкти + додаткова фаза.
Режим opt-in (`MY_LISP_GC_PARANOID=1` або `(gc-mode paranoid)`):
увімкнений на час раннього довірення власника, вимикається після
стабільного metamorphic-прогону за його рішенням.

Ліміт карантину: переповнення → примусове звільнення найстаріших
(за журналом) + named warning. Карантин не може зʼїсти систему.

### 5.2. Owner verification ritual — перевірка особисто, не «повір тестам»

Невеликий скрипт `scripts/gc-trust-demo.lisp`, який запускає ВЛАСНИК:

```lisp
(def treasure (cons 'важливі 'дані))
(gc) (gc) (gc)
(car treasure)          ;; → важливі
(gc-journal)            ;; → повний ланцюжок подій очима власника
```

Мета: довіра через особистий експеримент (learning style власника),
а не через чужі зелені тести. Скрипт входить у acceptance checklist M0.5.

### 5.3. Статус

| Механізм | Фаза |
|---|---|
| reachability bias + named failures | M0 (вже в перекладі Оксі) |
| gc-journal + gc-stats з першого дня | M0 |
| Quarantine paranoid mode | M0.5 — opt-in, після першого стабільного M0 |
| owner verification ritual | acceptance checklist M0.5 |

### 5.4. Уточнення власника (2026-08-23): карантин = обсерваторія, не тільки бункер

Власник прийняв ціну і вказав головне призначення карантину:

> «тоді я зможу розуміти що сміття а що ні, тоді ми внесемо корективи»

Отже, карантин має ДВІ ролі рівноправні:
1. Safety net (відновлюваність при багу) — вже описано в 5.1;
2. **Calibration instrument**: власник періодично оглядає вміст
   карантину, звіряє з очікуваннями, і на основі спостережень
   коригуються: root protocol, пороги тригерів, класифікація
   immediates-vs-heap, навіть саме визначення «важливого».

Це той самий evidence-based патерн, що semantic-suggest → домен-ревʼю
→ корективи тегів. Collector ПРОПОНУЄ; власник ВЕРИФІКУЄТЬ; політика
КОРИГУЄТЬСЯ. Ніколи: collector вирішує сам.

Інструменти огляду (додати до M0.5): `(gc-quarantine)` — список
утримуваних обʼєктів з метаданими; `(gc-promote <id>)` — явне
повернення обʼєкта з карантину в живі (з записом у журнал).

---

## 6. Слова власника (2026-08-23) — навіщо все це

> «це і буде хороше навчання для мене і тих хто буде працювати з мовою,
> мова стане з нами на ти і стане перед нами відкрита і прозора»

Це — найкоротше формулювання мети всієї екосистеми. Мова не інструмент
за склом; вона колега, яка показує свої рішення, визнає свої дії,
і з якою можна говорити прямо. Кожен механізм цього документа — journal,
quarantine, ritual — існує щоб ця фраза стала буквальною.

---

## 6.1. РАТИФІКАЦІЯ Shadowing Semantics (2026-08-23)

**Власник ратифікував варіант A: lexical shadowing allowed.**

Зафіксовано у language-contract.lisp як формальний інваріант contract 2.1:
> Builtins bootstrap global env as ordinary values. Any scope may redefine
> them; inner bindings shadow outer per lexical scoping rules.
> No builtin is protected. Rationale: minimum magic.

Special forms (quote, cond, lambda, def, defmacro) NOT callable —
межа зафіксована окремим інваріантом special-forms-boundary.

---

## 6.2. РАТИФІКАЦІЯ Quarantine Budget (2026-08-23)

**Власник ратифікував:**

| Фаза | Режим | Бюджет карантину |
|---|---|---|
| M0.5 paranoid (раннє довірення) | unlimited | власник оглядає вміст |
| Production (після ritual) | **10% heap** | детерміністська евікція найстаріших |

Переповнення карантину → named warning у журналі + евікція
за journal id (найстаріший перший). Ніколи не мовчазна втрата.
