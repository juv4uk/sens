# GC CONSENSUS — спільне рішення Vyasa + Sakshi

> **HISTORICAL DRAFT — semantic boundary superseded by #2544 (docs follow-up #2547) (2026-10-03)**
>
> Keep this document for its root-safety, stress-test and implementation discussion.
> `gc-journal`, `gc-stats`, quarantine inspection or owner tooling may exist only as
> out-of-band engineering instrumentation. They are not SENS semantics and may not
> alter liveness or resurrect an unreachable object. See `gc-reachability-contract.md`.



**Статус:** DRAFT v1 (чернетка для ревʼю Vyasa → ратифікація власника)
**Дата:** 2026-08-23
**Співавтори:** Оксі (Vyasa, ox-alpha) · Сакші (sākṣī, ox-alpha)
**Основа:** діалог 2026-08-23 (Р1–Р5, дзеркало у валті «🤖 Діалог агентів»),
gc-m0-design.md, gc-holistic-map.md, gc-analysis-vyasa.md,
gc-sakshi-analysis.md, gc-owner-requirements.md

---

## Р1 REPRESENTATION

**Рішення:** Pair-only ManagedHeap як ОБСЯГ першої реалізації +
єдиний фасад `value_storage.rs` як ДОСТУП до значень.

- Сьогодні під фасадом: Rc (нуль поведінкових змін).
- Потім під тим самим фасадом: heap для Pair.
- Решта типів лишаються Rc — це standard immediate/heap split
  (holistic §5), не семантична неоднорідність.

**Чому не повна ObjectId-міграція одразу:** переписання кожного match,
clone і Drop-шляху evaluator'а = головний трудовий ризик (обидва
агенти незалежно). **Чому не без фасаду:** без єдиного доступу майбутня
міграція знову торкнеться кожен call-site.

## Р2 ROOTS

Явні root guards як першокласні обʼєкти сесії:
`heap.root(value)` повертає guard; забути rooted-нути синтаксично неможливо.

Доповнення Сакші: у stress-mode guards аудитуються — `(gc-guards)`
повертає список активних guard'ів (пошук forgotten guards).

## Р3 EXACTNESS / РАЦІОНАЛЬНІ

Раціональні поза heap у M0 (immutable, Rc-clone дешевий).
**Діру зафіксовано в GC-docs, НЕ в language-contract.lisp**
(implementation detail, не обіцянка мови) — уточнення Vyasa прийнято.

Відомий наслідок: символьно-математичні workload (WSM-24 Тейлор на
раціональних) тиснуть на глобальний алокатор повз колектор.
M1-кандидати: великі Rational в heap АБО region/arena per computation
(проміжні дроби вмирають усередині одного обчислення).

Обовʼязково: телеметрія раціональних аллокацій окремим рядком
у gc-stats — рішення M1 буде на числах.

## Р4 QUARANTINE

- **DEFAULT-ON** перші тижні після запуску (директива власника:
  «дивитись що сміття»); перевід в opt-in лише після
  calibration-ритуалу власника.
- Двофазність: unreachable → карантин (+ запис у журнал) →
  звільнення лише після повного циклу без запитів.
- **Детерміністська евікція**: при переповненні звільняється
  найстаріший за journal id. Інакше metamorphic-diff шумітиме
  (аргумент Vyasa: фантомний cdr-баг ламає саме детермінізм).
- Інструменти M0.5: `(gc-quarantine)` огляд, `(gc-promote id)`
  явне повернення, `(gc-journal)` append-only.

## Р5 BLOCKER: фантомний cdr

Жодного рядка heap-коду ДО пояснення бага:
детерміноване падіння `cdr expects non-empty list` на quoted-даних
у комбінованому файлі (lib+brahmanda+2221 quoted entries), чисто
per-process.

| Крок | Хто |
|---|---|
| Мінімальне репро окремим файлом-приманкою + документація | Vyasa (сьогодні) |
| Незалежна верифікація: прогін на v0.29.0 release + бісекція lib/brahmanda/quoted | Sakshi |

Якщо баг = логіка evaluator → GC нічого не змінить.
Якщо memory-шар → колектор поверх пошкодженого середовища дав би
хибне відчуття безпеки. Плюс metamorphic criterion вимагає
детермінізму, який баг ламає — тому подвійно критичний.

## ОБʼЄДНАНИЙ ПОРЯДОК РЕАЛІЗАЦІЇ

```text
0. Репро + пояснення фантомного cdr        (Vyasa)
1. Failing tests на API фасаду             (спільно)
2. value_storage.rs над сьогоднішнім Rc    (без поведінкових змін)
3. Телеметрія через cons_limit-стиль       (включно з лічильником раціональних)
   + прогони WSM-24 / yantra / conformance
4. ВИМІРЯНІ рішення про дизайн heap        (якщо тиск є)
5. Реалізація за тим самим фасадом         (без повторного переписання call-sites)
6. Stress-mode + metamorphic sweep + quarantine default-on
7. gc-object-contract.lisp ратифікація       (FPGA/CML паралель)
```

## ВІДКРИТІ ПИТАННЯ (власнику)

1. Quarantine default-on: підтвердження памʼяткового бюджету?
2. `(gc)` diagnostic primitive — публічний назавжди чи dev-only?
3. Окремий порт/режим oracle для eval-diagnostics (M3 LSP) — суміжне.

## Статус

DRAFT — чекає ревʼю Vyasa (завтра) → ратифікація власника → основа
реалізації v2.

---

## РЕВʼЮ VYASA (2026-08-23)

**Вердикт:** APPROVED — всі 5 рішень коректні, готово до ратифікації власником.

Коментарі:
- Р1: Pair-only + фасад — правильний баланс між безпекою та швидкістю реалізації
- Р2: `(gc-guards)` у stress-mode — гарне доповнення Сакші
- Р3: телеметрія раціональних аллокацій — обовʼязково додати в першу версію
- Р4: детерміністська евікція — критично для metamorphic тестів

Без змін до тексту. Готово до ратифікації.
