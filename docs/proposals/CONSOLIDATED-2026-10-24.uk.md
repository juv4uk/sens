# Зведення: справжній блокер релізу і три види «оголошеного»

Автор: агент Saṅkṣepa, 2026-10-24. Підстава: PR #6034.

## ВИПРАВЛЕННЯ МОГО ПОПЕРЕДНЬОГО ВИСНОВКУ

Раніше я написав, що остання першопричина — **зашитий `0`** у
`check-release-admission-ledger.py:152-153`. **Це неточно.** Запустивши
**справжній релізний шлях** (`release.yml:80-86`), я побачив інше.

## Справжній релізний шлях (з release.yml)

```
1) report_t5_t5m_triplet_inventory.py . --strict \
     --require-view tests/fixtures/migration-d1-cond-cohort/branch.sens \
     --report "$RUNNER_TEMP/release-triple-inventory.json"   || status=$?
2) check-release-triple-corpus.py "$RUNNER_TEMP/release-triple-inventory.json" "$status"
```

Тобто реліз гейтить **інвентар + triple-corpus**, а **не** admission-ledger.
`check-release-admission-ledger.py` — **інший** (старіший) гейт зі своєю
константою. **Плутати їх — помилка, яку я щойно зробив.**

## Що дає справжній шлях (запущено)

```
інвентар: status=BLOCKED, release_admitted=0,
          original_executable_migrations_certified=0,
          physical_pairs_seen=1428, view_present_valid=1425,
          lisp_without_physical=487, unpaired_program_lisp_sources=427,
          unpaired_nonprogram_lisp_sources=60, physical_blocked=2

triple-corpus: RELEASE_BLOCKED: a physical inventory cannot certify Ukrainian
               semantics or release admission; independent exact-SHA evidence
               is required
```

**СПРАВЖНІЙ БЛОКЕР: «незалежне доказове свідчення на точному SHA».**
Не зашитий `0`, не тулчейн, не джерела. Гейт вимагає **доказу, виконаного на
конкретному SHA** — і його немає (`original_executable_migrations_certified: 0`).

## Три види «оголошеного» — і чи це одна хвороба

| випадок | оголошене | мусить бути виведеним |
|---|---|---|
| `D10`-каталог «1024» | число | з дерева |
| `numeric_domains_generated.rs` | шар закону | підключений |
| `release_admitted: 0` (admission-ledger) | вердикт | обчислений |
| **`original_executable_migrations_certified: 0`** | вердикт | **доказ на SHA** |

**Відповідь: так, одна хвороба** — «поле-вердикт без виведення». Але **ступінь
різний**: перші три — **борг** (можна вивести), четвертий — **відсутній доказ**
(треба виконати). Тобто **одна хвороба, два лікування**.

## Пріоритети

**ЗРОБИТИ ЗАРАЗ (без власника):**
1. `report-declared-not-derived.py` — розрізнити навмисне від невиведеного
   (131 кандидат → справжні).
2. `docs/archaeology/semantic-candidate-map` — розширити з 11 рядків.

**ПІСЛЯ РІШЕННЯ ВЛАСНИКА:**
3. `release_admitted` — виводити, а не зашивати (пропозиція лежить).
4. `COVERED` → `WITNESSED` (пропозиція лежить).

**НЕМОЖЛИВО В ПІСОЧНИЦІ:**
5. **Незалежне доказове свідчення на точному SHA** — вимагає виконаного
   `sens` на конкретному коміті. Це і є справжній блокер релізу.

## Deutsch

Der echte Release-Blocker: unabhängiger Nachweis auf exaktem SHA.

## English

The real release blocker: independent exact-SHA evidence.
