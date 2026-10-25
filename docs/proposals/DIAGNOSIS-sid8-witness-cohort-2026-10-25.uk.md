# ДІАГНОЗ: test_sid8_witness_third_cohort — довжини токенів розійшлися

Автор: агент Antya, 2026-10-25. Вимір, не здогад.

## Що стверджує тест

`tests/test_sid8_witness_third_cohort.py` порівнює **5 виконуваних свідків** із
**незмінними історичними blob SHA** і вимагає:

```python
before = tokenize(strip_comments(old_blob))
after  = tokenize(strip_comments(new_file))
assertEqual(len(before), len(after))      # ← однакова довжина
n = sum(a != b for a, b in zip(before, after))
assertEqual(n, expected)                  # ← 89, 152, 44, 406, 192
...
assertEqual(count, 883)                   # ← сума
```

Сенс: міграція SID8 → домени мусить бути **токен-у-токен**, лише перейменування.

## Що показав вимір

Прогнав ту саму логіку напряму (блоб читається через `git cat-file blob`, він є):

| свідок | токенів у блобі | токенів у файлі |
|---|---|---|
| `exact-quantity-arithmetic-witness.lisp` | **801** | **82** |
| `island-compat-witness.lisp` | 802 | 790 |
| `island-lowering-1048-witness.lisp` | 283 | 250 |
| `postcore-peer-materialization-witness.lisp` | **2384** | **593** |
| `yantraos-bridge-witness.lisp` | 974 | 871 |

**Довжини розходяться в КОЖНОМУ з п'яти** — тому `assertEqual(len(before), len(after))`
падає, `count += n` не виконується, і підсумок дає `0 != 883`.

## Що це означає

Тест описує **токен-у-токен перейменування**. А файли **змінили довжину** —
подекуди **вдесятеро менше** (801 → 82). Це **не перейменування**, а **інший вміст**.

Отже одне з двох:

- **або** файли пройшли **подальшу міграцію** (коментарі/форми прибрано), і тест
  описує **застарілий етап**;
- **або** файли **втратили вміст**, і це **справжня регресія**, яку тест і ловить.

**Розрізнити їх я не можу без рішення про історію цих свідків** — і саме тому
**не лагоджу**.

## Що я встановив додатково (щоб не шукали вдруге)

- **Блоби Є.** `git cat-file blob 747073d34f67…` повертає вміст. Перші спроби падали
  лише тому, що клон був `--depth 1` (без старих блобів) — **це середовище, не дефект**.
  У CI стоїть `fetch-depth: 0`, тож там блоби є.
- **Асcерт живе у двох місцях:** `tests/test_sid8_witness_third_cohort.py:50` і
  `scripts/audit_lisp_migration_edits.py:72` — те саме твердження `count == 883`.
- **Файли існують** — усі 5 на місці.
- Тест **не входить у `ci.yml`** (0 згадок) і **не входить у жоден workflow** (0).

## Deutsch

Diagnose: die Tokenlängen weichen in allen fünf Zeugen ab (801→82 usw.).

## English

Diagnosis: token lengths differ in all five witnesses (801→82, etc.).
