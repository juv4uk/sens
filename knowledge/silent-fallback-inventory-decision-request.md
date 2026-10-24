# Запит на рішення власника — `.sens`-компаньйон у `knowledge/silent-fallback-inventory.lisp`

- Дата: 2026-10-24
- Репозиторій: `juv4uk/sens`, гілка `main`
- Тип: **артефакт для рішення власника**. Жодного рішення тут не ухвалено; `.lisp`, `.sens` і безрозширений носій **не змінювались**.

## 1. Стан

На `main` падає захисний тест:

```
tests/test_migration_nonprogram_knowledge_records.py
::KnowledgeRecordSources.test_all_pinned_originals_are_data_not_executable_programs
AssertionError: True is not false : knowledge/silent-fallback-inventory.lisp
```

Рядок 65 тесту:

```python
self.assertFalse(src.with_suffix(".sens").exists(), path)
```

Тобто pinned-оригінал даних не повинен мати одноіменного `.sens`-компаньйона. Причина падіння: у `knowledge/silent-fallback-inventory.lisp` з'явився одноіменний `.sens` (а також безрозширений SENS-носій з тим самим базовим іменем).

> **Важливе уточнення до вихідної постановки.** Завдання описує «1 фейл» як останній кодовий залишок. Під час дослідження виявлено, що **той самий механізм зачепив не лише цей файл**: на tip падають 5 тестів родини `test_migration_nonprogram_*` (knowledge, isa, schema, evidence, print). Деталі — розділ 2.4. Імовірно, «1 фейл» стосується окремого workflow `migration-nonprogram-knowledge-records.yml`, який запускає лише один тестовий файл.

## 2. Докази

### 2.1. `knowledge/silent-fallback-inventory.lisp` — це дані, а не програма

- 18 рядків: заголовковий коментар + один верхньорівневий s-вираз.
- `record_head` (перший верхньорівневий запис) = `silent-fallback-inventory`.
- Структура: `(silent-fallback-inventory (site (class …) (file …) (key …) (line …)) …)` — 9 записів `site`.
- Виконуваних форм немає: **0** збігів на `(define`, `(lambda`, `(print`, `(defmacro`, `(call`.
- Заголовок прямо описує призначення: «Інвентар тихих відкатів (#2134). Базис для `scripts/check-silent-fallback-classes.py`: відомий сайт проходить, НОВИЙ неіменований сайт не проходить.»

Вміст (скорочено; повністю — 9 `site`-записів):

```lisp
;; Інвентар тихих відкатів (#2134).
;; Базис для scripts/check-silent-fallback-classes.py ...
(silent-fallback-inventory
  (site (class "fail-fast-hides-suites") (file ".github/workflows/ci.yml") (key "...") (line "278"))
  (site (class "fail-fast-hides-suites") (file ".github/workflows/full-nightly.yml") (key "...") (line "34"))
  (site (class "implicit-default-flag") (file "crates/sens/src/environment.rs") (key "...") (line "174"))
  (site (class "implicit-default-flag") (file "crates/sens/src/environment.rs") (key "...") (line "183"))
  (site (class "implicit-default-flag") (file "crates/sens/tests/semantic_authority.rs") (key "...") (line "103"))
  (site (class "implicit-default-flag") (file "crates/sens/tests/witness_authority.rs") (key "...") (line "58"))
  (site (class "total-serializer-fallback") (file "crates/sens/src/value.rs") (key "...") (line "852"))
  (site (class "total-serializer-fallback") (file "crates/sens/src/presentation.rs") (key "...") (line "53"))
  (site (class "total-serializer-fallback") (file "crates/sens/src/value.rs") (key "...") (line "780"))
)
```

### 2.2. Коли і яким комітом з'явився `.sens`

```
git log --follow knowledge/silent-fallback-inventory.sens
d50666b60fdfa783dcdafbb61f20a09cafda4403 | 2026-10-21 17:15:50 +0300 |
  оборотність(руками): +206 пар — повне правило даних (записи даних, не виклики)
```

Це **єдиний** коміт, що торкався `.sens`. Той самий коміт:

- додав **206 пар** `<path>` + `<path>.sens` (у статистиці: 412 файлів, 206 insertions);
- для нашого випадку додав рівно два файли:
  - `A knowledge/silent-fallback-inventory` — безрозширений SENS-носій (103792 B);
  - `A knowledge/silent-fallback-inventory.sens` — бінарний (20759 B);
- сам `knowledge/silent-fallback-inventory.lisp` **не змінював**.

`git log --follow knowledge/silent-fallback-inventory.lisp` (окремо) показує останню зміну `.lisp` у коміті `742b66ce` (2026-10-23), а поточний blob `4f93ff14b51be11d595b2b40164553ce2adc39dc` **точно збігається** з піном у манифесті. Отже `.lisp` недоторканий — новизна полягає лише в `.sens` і безрозширеному носії.

**Що саме лежить у `.sens`.** Декодування `scripts/sens_t5_t5m_codec.decode_t5m_bytes` дає той самий бітовий потік (`10 10 1110011 00 1101001 …`), що й у безрозширеному носії, і цей потік кодує **ті самі дані**, що й `.lisp` (перевірено: декодований `.sens` == безрозширений носій, 103791 токен; потік читається як `silent-fallback-inventory site class fail-fast-hides-suites …`). Тобто `.sens` — фізичний носій того самого запису даних, а не скомпільована програма.

### 2.3. Правило/манифест, який мав би виключити цей файл

`knowledge/migration-nonprogram-knowledge-records-2026-10-08.json`:

```json
{
  "schema": "sens-migration-nonprogram-manifest-1",
  "issue": 4460,
  "classification": "lisp-data-nonprogram",
  "authority": "research/classification; not executable SENS or domain law",
  "automatic_sens_companion": false,
  "admitted_as_executable": 0,
  "entries": [ ..., {
    "path": "knowledge/silent-fallback-inventory.lisp",
    "git_blob_sha1": "4f93ff14b51be11d595b2b40164553ce2adc39dc",
    "record_head": "silent-fallback-inventory"
  }, ... ]
}
```

Отже файл явно pinned як **непрограмні дані** (`admitted_as_executable: 0`) з `automatic_sens_companion: false`.

Захисний тест `tests/test_migration_nonprogram_knowledge_records.py` додано **2026-10-08** (коміт `88ffff1029` «audit(4460): SHA-classify 14 knowledge records…»), і вже тоді він містив `assertFalse(src.with_suffix(".sens").exists())`. Sweep `d50666b60` — **2026-10-21**, тобто на 13 днів пізніше за guard. Sweep не оновлював жодного `migration-nonprogram-*.json`.

### 2.4. Інші файли-дані з `.sens` — і як із ними чинять

Серед **12** pinned knowledge-записів `.sens` має **лише** `silent-fallback-inventory.lisp`; решта 11 — ні (жоден із них не має також безрозширеного носія).

Але sweep виявився системним. Той самий `d50666b60` (і пізніший `a5ed993a`) дав `.sens` pinned-записам і в інших манифестах:

| Манифест | Записів | З `.sens` |
|---|---|---|
| knowledge-records | 12 | 1 (`silent-fallback-inventory.lisp`) |
| isa-manifest | 25 | 25 |
| schema-manifest | 19 | 9 |
| evidence-manifest | 8 | 8 |
| print-manifest | 75 | 5 (коміт `a5ed993a`, 2026-10-22) |
| domain-tables | 11 | 0 |
| expr-records | 13 | 0 |
| comment-only-loaders | 2 | 0 |

Кожен із відповідних тестів має **той самий** guard `assertFalse(source.with_suffix(".sens").exists())`. На tip падають 5 тестів родини `test_migration_nonprogram_*`:

- `knowledge_records` — `.sens`-guard (наш випадок);
- `isa_manifest` — `.sens`-guard (`lib/machine/isa/adx.lisp` …);
- `schema_manifest` — `.sens`-guard (`contracts/compiler-program-data-v1.lisp` …);
- `evidence_manifest` — `.sens`-guard (`evidence/G5/my-lisp/196d7f2.lisp` …);
- `print_manifest` — окрема причина: розбіжність SHA-піна (`closures-sens.lisp`), не `.sens`-guard.

Тобто `.sens`-на-pinned-даних **не є** послідовною практикою: вони з'явилися саме в тих манифестах, які зачепив масовий sweep.

## 3. Три гіпотези

### Г1. `.sens` законний (тоді узгодити тест/манифест)

**За:** поле манифесту названо `automatic_sens_companion` («автоматичний»), а sweep описано як «руками» (manual). Якщо манифест забороняє лише *автоматичний* компаньйон, ручний носій міг бути свідомим.
**Проти:** sweep не оновив жодного манифесту; `admitted_as_executable: 0`; 11 із 12 knowledge-записів залишені без `.sens`; guard-тест прямо забороняє **будь-який** `.sens`, не лише автоматичний.

### Г2. `.sens` — артефакт масового sweep (тоді прибрати) — найкраще підкріплена доказами

- З'явився єдиним комітом `d50666b60`, який обробляв 206 джерел наскрізно (дані й програми разом), не розрізняючи клас.
- Guard-тест і манифест (обидва 2026-10-08) **передували** sweep; sweep їх порушив, не узгодивши манифест.
- `silent-fallback-inventory` — єдиний pinned knowledge-запис, який sweep зачепив; решта 11 чисті.
- Той самий sweep зламав ще 4 тести родини (isa/schema/evidence/print) → це системна помилка sweep, а не однофайлове рішення.
- Вміст `.sens` — ті самі дані (не програма): sweep не вигадав семантичної програми, лише помилково видав фізичний носій для запису даних.

### Г3. Це нормальна практика для даних-носіїв

**Спростовується:** pinned-записи в механізмі guard'ів послідовно утримуються **без** `.sens`; присутність `.sens` збігається саме з манифестами, які зачепив sweep, і з падінням відповідних guard'ів. Немає жодного манифесту чи тесту, який би очікував `.sens` у pinned-даних.

## 4. Явне питання до власника

**Чи повинен `knowledge/silent-fallback-inventory.lisp` (pinned як `lisp-data-nonprogram`, `automatic_sens_companion: false`, `admitted_as_executable: 0`) нести одноіменний `.sens`-носій?**

Можливі рішення (жодне не ухвалено тут):

1. **Ні → прибрати артефакт.** Видалити `knowledge/silent-fallback-inventory.sens` і безрозширений `knowledge/silent-fallback-inventory`; `.lisp` лишити як є (його blob уже збігається з піном). Тоді ж вирішити долю ще 4 манифестів (isa/schema/evidence/print), бо той самий sweep зламав і їх.
2. **Так → узгодити правило.** Дозволити ручні `.sens`-носії для pinned-даних: переосмислити/перейменувати поле `automatic_sens_companion`, послабити guard-тести, оновити SHA/pin там, де треба. Тоді слід явно зафіксувати, чим носій даних відрізняється від носія програми.
3. **Гібрид.** Прибрати лише там, де запис — чиста таблиця/інвентар без жодної виконуваної форми (як `silent-fallback-inventory`), і лишити носії для тих, де є хоч якась кодоподібна структура. Це вимагає окремого критерію від власника.

**Рекомендація (не рішення):** докази схиляються до варіанта 1 / гіпотези Г2 — `.sens` тут є побічним продуктом масового sweep `d50666b60`, а не свідомим рішенням: його поява порушила guard, старший за нього, і не супроводжувалась оновленням манифесту. Проте поле названо `automatic_sens_companion`, що лишає місце для тлумачення Г1, — **остаточне рішення за власником**.

## 5. Що свідомо НЕ зроблено

- `.sens`, безрозширений носій і `.lisp` **не змінювались** і не видалялись.
- Жодного манифесту чи тесту не змінено.
- Рішення не ухвалено — це запит до власника.
