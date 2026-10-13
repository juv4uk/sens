# SENS l0.42.0 — готовність до релізу (виміряний стан)

**Ревізія заміру:** `6b980ca78ba3893fc16c6b3b8c91565567173a8c` (main)
**Метод:** свіжий знімок дерева + запуск релізних перевірок із самого репо.
Rust/cargo у пісочниці немає, тому tag-time smoke (`release.yml`) не ганяв —
нижче те, що вимірюється Python-інструментами репо.

## 1. Як влаштований реліз (перевірено)

- Тригер: `release.yml` на `push: tags: ['l*']`.
- Версія тегу мусить дорівнювати `version` з `crates/sens-cli/Cargo.toml`:
  assert `RELEASE_TAG == "l" + package.version`.
- Ланцюг джоб: `test` (smoke + triple-gate) → `create-release` (створює реліз
  ОДИН раз) → `build-cli` (4 матриці), `build-msi`, `build-web`,
  `publish-island-manifest`.
- Останній реліз: **l0.41.0** (2026-09-21). Отже наступний — **l0.42.0**.
- Координація вже є: **#4196** (l0.42.0 freeze/cut) і **#5604**
  (release-publish, draft-first).

## 2. Головний hard-gate: triple inventory — **BLOCKED**

```
python3 scripts/report_t5_triplet_inventory.py . --strict --report /tmp/relinv.json
→ status: BLOCKED
```

| показник | значення |
|---|---:|
| physical_pairs_seen | 23 |
| physical_blocked | 0 |
| view_present_valid | 13 |
| **view_missing** | **10** |
| view_invalid_or_unsafe | 0 |
| **uk_oracle_verified** | **0** |
| **release_admitted** | **0** |
| original_executable_migrations_certified | 0 |

`release.yml` fail-closed блокує тег, якщо `view_missing != 0` **АБО**
`uk_oracle_verified != physical` **АБО** `release_admitted != physical`.
Тобто **три незалежні блокери**, не один.

## 3. Точний перелік 10 відсутніх view-файлів

Усі — у legacy `*-cohort` теках (їхні `*-cohort-main` аналоги вже мають view і
проходять):

1. `tests/fixtures/migration-atom-cohort/atom-empty`
2. `tests/fixtures/migration-eq-cohort/eq-legacy-sid`
3. `tests/fixtures/migration-eq-cohort/eq-lisp15`
4. `tests/fixtures/migration-eq-cond-cohort/eq-cond-select`
5. `tests/fixtures/migration-eq-cond-cohort/eq-cond-skip`
6. `tests/fixtures/migration-pair-cohort/pair-car-cdr`
7. `tests/fixtures/migration-pair-cohort/pair-cons`
8. `tests/fixtures/migration-quote-cohort/quote-legacy`
9. `tests/fixtures/migration-quote-cohort/quote-lisp15`
10. `tests/fixtures/migration-quote-cohort/quote-mylisp`

**Важливо (перевірено):** ці view механічно виводяться з `.sens` за законом репо
(`" ".join(decode_bytes(sens)) + "\n"`, ASCII). Я їх згенерував і прогнав
`verify_uk_t5_triplet.py` — але трійка **все одно BLOCKED**, тепер на семантиці:
7 файлів «noncanonical українська ук source or wrong T5 semantics», 3 —
«D3 QUOTE structured/Text7 data not proven».

**Висновок:** відсутні view — це *не* справжній блокер релізу. Їх генерація
знімає лише `view_missing`, а `uk_oracle_verified`/`release_admitted` лишаються
0. Справжній блокер — **незалежний український oracle і ратифікований
admission-ledger**, а не 10 текстових файлів.

## 4. Другий блокер: race публікації (за #5604)

`create-release` створює реліз **без draft** до завершення asset-джоб; якщо одна
matrix/asset впаде, ззовні вже може існувати неповний публічний реліз. Фікс
(атомарний): реліз створюється **draft**, оприлюднюється окремим фінальним
кроком після success усіх asset-джоб; SHA-256 manifest; rejection-тести
(fail matrix / missing MSI / wrong checksum → no public release).

## 5. Preflight-чекліст l0.42.0

- [ ] version-bump 0.41.0 → 0.42.0 у всіх релізних crate/Guix/install/asset
      (без семантичних змін), `Cargo.lock` узгоджено.
- [ ] triple inventory: `view_missing=0`, `uk_oracle_verified=physical`,
      `release_admitted=physical` → status PASS (зараз BLOCKED).
- [ ] `release.yml` → draft-first + SHA-256 manifest + rejection-тести (#5604).
- [ ] зафіксувати один exact candidate SHA; preflight (#975) зелений саме на ньому.
- [ ] усі asset-джоби (linux/mac x64/arm64, win exe/msi, web html,
      islands-manifest) зібрались на тому ж SHA.
- [ ] не вимикати жоден fail-closed T5/oracle gate заради зеленого.

## 6. Межі

- Замір — на точному SHA вище; дерево рухається швидко, числа перезаміряти
  перед кожним merge/тегом.
- Я не змінював ратифікованих артефактів і не тегував.
- Обидва релізні issue вже існують (#4196, #5604) — цей документ не створює
  паралельної влади, лише дає виміряні числа.
