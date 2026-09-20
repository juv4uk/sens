# 216-V3-COMPARISON-GATES-GREP-CHECKLIST-2026-09-21

Статус: **step 1 artifact** — повний grep-чеклист усіх `(< …)`, `(> …)`, `(= …)`,
`(<= …)`, `(>= …)` у query-позиції в `lib/`, `scripts/`, `tests/`. Коду не
торкаємось. Ratification: **(Б) підтверджено** (власник, 2026-09-21);
Contract 8.0 ратифіковано (`f665f541`), цей cutover входить у ту саму смугу.

## 0. Рішення про payload (амендує попередній `same|distinct`-варіант)

```text
exact YES  -> (exact-comparison так)      ; 1 виправлено на "так"
exact NO   -> (exact-comparison ні)       ; 0 виправлено на "ні"
inexact    -> Canon ()
```
Канонічні payload-символи — українські `так`/`ні` як author-data (мовна політика #38);
«різними нашими мовами» — лише прочитання у prose/surface-списках, НЕ різні символи
записах (інакше `equal?` відповідей ламається між surfaces).
Наслідок для matching: three-part expected-літерал = сам запис `(exact-comparison так)`;
query-значення порівнюється через `equal?` — працює без змін семантики cond.

## 1. Метод і повний список сайтів

grep-патерн: `\(\(\s*(<|>|=|<=|>=)` (не-generated). Знайдено: **93 sites** в `lib/` +
**3** в `scripts/` + **16** в `tests/` fixtures. Категорії:

- **(L)** three-part expected-літерал `1` → `(exact-comparison так)` або `0` →
  `(exact-comparison ні)`; body — **значення** (не змінюється).
- **(B)** two-part clause — ремонтується Правкою 2 у мості/`truthy?`; expected/body не міняються.
- **(X)** false-positive / поза класом.

### lib/core.lisp — 26
**(L)** query-position expected: 576·577·603·604·622·624·626·632·634·636·764·765·772·773·780·781·786·787·788·821·822·860·861·874·875.
- **`791` — особливий випадок (баг-ремонт):** `((= (* r r) x) t r)` — expected `t`
  замість exact-Q `1` → гілка **мертва** (`sqrt` баг сесії). Міграція ставить expected
  `(exact-comparison так)` → гілка оживає: `(sqrt 9)` стає `3`, не дріб.
- **answer-type (Правка 2 власника, не механічний swap):** `nondecreasing-from?`/`nonincreasing-from?`
  (618–644): базовий випадок `621` body `1` → `(exact-comparison так)`; `626`/`636` body `0` →
  `(exact-comparison ні)`; expected-літерали рекурсійних клауз теж у записи. ЛОГІКА комбінування
  змінюється: результат `<=`/`>=` стає записом (окремий підпункт step 2, власні fixtures).
- **expression-position (лишаються числами — значення, не відповіді):**
  `quotient` 605 `(+ (cdr chunk+mult) …)`, 603·604 bodies `0`/`(let …)`;
  `abs` 821·822 bodies `(- x)`/`x`; `min-list`/`max-list` 860·861·874·875 bodies — дані;
  `isqrt` 764·765·772·773·780·781 bodies (`guess`, `n`, recursion) — числа;
  `sqrt` 786·787·788 bodies `()`/`0`/recursion (значення). Міняються ТІЛЬКИ expected.

### lib/utf8.lisp — 22
**(L)** 20·21·23·24·37·38·59·61·63·65·71·73·75·77·101·103·262·264·266·271·273·280.
Body — числові значення (кодування байтів), не змінюються.

### lib/persistent-vector.lisp — 7
**(L)** 92·94·98·100·115·131 (expected `1` → так).
**(B)** `65` `(cond ((< a b) b) (t a))` — `max`, **LIVE broken** (a≥b → повертає b).

### lib/persistent-map.lisp — 5
**(L)** 109·111·115·117.
**(B)** `70` — `max`, **LIVE broken** (той самий патерн).

### lib/linter.lisp — 6
**(L)** 7·153·156·159·162·164 (expected `1` → так).

### lib/world.lisp — 5
**(L)** 413·414·423·479·498 (expected `1` → так; body `world`/`World-not-found`/depths).

### lib/time.lisp — 3
**(B)** 22 (month), 23 (year), 75 (NTP gate) — **LIVE broken** (підтверджено probes).

### lib/quantity.lisp — 3
**(L)** 119·127 (expected `1` → так), **233** (expected `0` → ні: `((= (length x) 7) 0 (quote ()))`).

### lib/narrate.lisp — 3
**(L)** 63·64·142 (expected `1` → так; body 142 returns `t` як ДАНИХ — лишається).

### lib/forward.lisp — 3
**(L)** 205·373·1197 (expected `1` → так).

### lib/yantra.lisp — 2
**(B)** 454 `((>= turn max-turns) …)`, 505 `((= (http-transport-exit r) 0) …)` —
**LIVE broken** (exit==0 check міс-бранч).

### lib/meta-eval.lisp — 2
**(L)** 433 (expected `1` → так), 434 (expected `0` → ні); body `()`/`t` — дані.

### lib/knowledge.lisp — 2 · lib/result-status.lisp — 1
**(B)** knowledge 287·301, result-status 88 — shape-check, **LIVE broken**.

### lib/reason.lisp — 1
**(B)** 100 — bound-guard, **LIVE broken** (рекурсія на межі).

### lib/machine/encoding/x86-64.lisp — 1
**(B)** 563 `((> code 3) …)`.

### lib/canon.lisp — 1 · **(X) EXCLUDED**
`196` `((=? (:п …) 'ліве)` — це `=?` (семантична рівність), НЕ числовий `=`.
False-positive grepu (`=` matched inside `=?`). Поза класом (Б); вердикт `=?` не змінюється.

### scripts/program-symbol-table.lisp — 3
**(B)** 18·20·22 (string-length/pos gates; body — рядки-значення).

### tests/fixtures — 16
- `postcore-peer-materialization-witness.lisp` — **12 (L)**: 47·49·176·180·196·198·218·220·255·257·350·360
  (helper-код свідка; expected 1/0 → записи).
- `persistent-vector-balance-witness.lisp` — **1 (B)**: 13.
- `properties-helpers.lisp` — **1 (B)**: 18.
- `linter.lisp` — **1 (X)**: 42 — input-sample рядок для лінта, не наш вислів.
- `conformance.lisp` — окрема секція ↓.

## 2. Conformance.lisp та superseded-механізм (Правка 3)

- **Механізм ІСНУЄ** (не потрібне розширення схеми): header файлу (рядки 7–10) прямо каже —
  «a ratified semantic cutover MAY update an existing fact key when the old result has been
  explicitly superseded»; git зберігає історію.
- **Прецедент**: `067b6bef` «make conformance structural expectations current (#307)» — той самий
  рух для #218; у message явно відкладено «mathematical comparison domains for their own migration
  lane» — це наша смуга. Другий прецедент vocabulary: `b16c545b` (supersede через Lisp witness).
- **Конфліктні entries**: 110–116 (`< 1 2 3`→`t`, `< 1 3 2`→`()`, `> 3 2 1`→`t`, `= 1 1 1`→`t`,
  `= 1/2 0.5`→`t`, `<= 1 1 2`→`t`, `>= 2 2 1`→`t`), 172 (`< 5`→`t`), 185 (`= 3 3.0`→`t`).
- **Oracle-доказ (live)**: `(< 1 2 3)` → `1`, `(< 1 3 2)` → `0` — тобто ці entries вже **не
  відповідають** точній відповіді 1/0 (vestigial з до-exact-Q епохи). **Open verification item:**
  підтвердити у запускачі conformance, чи ці рядки зараз проходять (нормалізація?), чи вже червоні —
  не залежить від обсягу зміни, але фіксує стартовий стан «першого коміту».
- Cutover оновлює ці expected на `(exact-comparison так/ні)` за правилом header + прецедент, у тому ж
  (dedicated) коміті, з позначкою superseded у decision-нотатці.

## 3. Послідовність (після цього чеклиста)

1. **Fixtures RED (step 2)**: нові/оновлені entries у conformance (answer-records), witnesses
   Правки 2 (`(and (= 2 2) 'так)` → `так`, `(or (= 2 3) 'ні)` → `ні`), ремонт-кейси (`max`-family,
   month/year, NTP gate, knowledge shape-check, `(sqrt 9)` → 3). CI падає — очікувано.
2. **Правка 2**: `truthy?` (Lisp) + `migration_only_cond_truthy` (Rust, `core.rs:46-63`) — гілка
   `exact-comparison` (same→true/distinct→false); пара-данные без тегів не торкаються.
3. **Canon `= < >`** у ядрі → повертають записи (форма), включно з `791`-ремонтом.
4. **Derived `<= >=`** (nondecreasing/nonincreasing) — логіка комбінування (окремий підпункт, свій CF).
5. **Механічний sweep (L)**: expected-літерали всіх секцій таблиці → записи.
6. **two-part (B)**: без змін — після кроку 2 зелений сам; verify witnesses.
7. **Green**: повний локальний прогон + контрольні witnesses; CI.

## 4. Non-blockers (після зеленої CI)

- `fpga-lisp` та `cml`: їх comparison-ops теж повертають 1/0 — завести issue/запис у обох,
  не синхронізувати зараз.
- `docs/` answer-taxonomy mini-map (4 теги: structural-kind, identity-relation, structural-relation,
  exact-comparison; спільний словник) — щоб п'ятий тег не народився випадково.