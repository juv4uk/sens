# План реалізації Lisp-owned інвентаря tooling

> **Для agentic workers:** ОБОВ’ЯЗКОВИЙ SUB-SKILL: використовуйте `superpowers:subagent-driven-development` (рекомендовано) або `superpowers:executing-plans`, виконуючи задачі по черзі. Кроки мають checkbox (`- [ ]`) для відстеження.

**Мета:** Реалізувати #382 як Lisp-owned fail-closed інвентар immediate `scripts/*` tooling з executable negative witnesses, Guard-навігацією та CI enforcement без додавання Rust.

**Архітектура:** `knowledge/repo-tooling-inventory.lisp` є єдиним machine-readable registry. `scripts/check-repo-tooling-inventory.lisp` володіє schema/policy validation і спостерігає реальний immediate `scripts/` через уже наявні CLI filesystem capabilities. Постійний gate живе в існуючому `.github/workflows/ci.yml`; окремий RED-probe workflow допускається лише тимчасово і має бути видалений до готовності PR.

**Tech Stack:** my-lisp (`.lisp`), `read-dir`/`read-file` через `my-lisp-cli`, GitHub Actions YAML, Guard navigation data.

**Spec:** `docs/superpowers/specs/2026-09-17-repo-tooling-inventory-design.md`

## Глобальні обмеження

- #299: **нуль доданих Rust-рядків і нуль нових `.rs` файлів**.
- #76 володіє Python→Lisp migration; #382 лише індексує `migration-issue`.
- `lifecycle` першого зрізу: `active | transitional | legacy | generated-helper | archive-candidate`.
- Не записувати `parity-green`, `switched-to-lisp`, `removable` чи `bootstrap-exception` у `lifecycle`; це migration dimension #76.
- Якщо реально знадобляться обидва виміри одночасно — окремо еволюціонувати schema до `lifecycle + migration-state`.
- Coverage першого зрізу: всі immediate entries з `read-dir("scripts")`, крім literal directory entry `tests`.
- `scripts/tests/*` поза scope цього slice.
- Не переносити й не видаляти scripts у #382.
- Не залишати нового постійного GitHub Actions workflow; фінальний gate використовує `ci.yml`.
- Новий Lisp control flow використовує explicit result equality (`structural-kind`, `identity-relation`, `structural-relation`), а не generic `t/()` truth authority.
- RED зараховується тільки коли failure походить від очікуваної відсутньої поведінки; parser/stale-baseline failures не рахуються.

---

### Задача 1: Отримати чесний focused RED для duplicate path

**Файли:**
- Modify: `scripts/check-repo-tooling-inventory.lisp`
- Temporary: `.github/workflows/382-red-probe.yml`

**Інтерфейс:**
- Вхід: pure rows + observed immediate names.
- Вихід: `(repo-tooling-ok)` або `(repo-tooling-violation KIND DETAIL)`.

- [ ] **Крок 1: Зберегти вже GREEN witness для unregistered tool**

Має лишатися точний expected result:

```lisp
(repo-tooling-violation unregistered-tool "scripts/b.lisp")
```

- [ ] **Крок 2: Додати duplicate-path witness до реалізації duplicate validation**

Fixture:

```lisp
(repo-tooling-verdict
  (list repo-tooling-sample-row-a repo-tooling-sample-row-a)
  (quote ("a.lisp")))
```

Expected:

```lisp
(repo-tooling-violation duplicate-path "scripts/a.lisp")
```

- [ ] **Крок 3: Запустити через CI/RED probe і перевірити причину**

Команда gate:

```sh
./target/debug/my-lisp scripts/check-repo-tooling-inventory.lisp
```

Expected RED: checker парситься, unregistered witness GREEN, duplicate witness показує actual `(repo-tooling-ok)` і завершується non-zero через mismatch. Parser error або сторонній authority failure не зараховувати.

- [ ] **Крок 4: Зафіксувати CI run/commit SHA у PR evidence**

Після валідного RED більше не використовувати RED probe як постійний workflow.

---

### Задача 2: Реалізувати duplicate validation і наступні pure negative witnesses

**Файли:**
- Modify: `scripts/check-repo-tooling-inventory.lisp`

**Produces:** pure validator, який перевіряє schema/policy без filesystem mutation.

- [ ] **Крок 1: Реалізувати мінімальний duplicate-path pass**

Додати функцію на кшталт:

```text
repo-tooling-duplicate-path-verdict
```

Вона рекурсивно порівнює `path` поточного row з наступними rows через `equal?` + `(structural-relation same|distinct)` і повертає перший duplicate як explicit violation.

- [ ] **Крок 2: Запустити duplicate witness GREEN**

Expected: обидва selftests (`unregistered-tool`, `duplicate-path`) проходять.

- [ ] **Крок 3: RED→GREEN окремо для stale registered path**

Fixture має містити registered `scripts/a.lisp`, але observations без `a.lisp`.

Expected:

```lisp
(repo-tooling-violation stale-registered-path "scripts/a.lisp")
```

Спочатку побачити RED, потім додати мінімальний stale-row validator.

- [ ] **Крок 4: RED→GREEN окремо для invalid enum**

Приклад:

```lisp
(kind semantic-oracle)
```

Expected violation:

```lisp
(repo-tooling-violation invalid-kind semantic-oracle)
```

Закриті словники:

```lisp
(def repo-tooling-kinds
  (quote (check generator migration benchmark deploy release helper other)))

(def repo-tooling-languages
  (quote (lisp python shell javascript powershell other)))

(def repo-tooling-lifecycles
  (quote (active transitional legacy generated-helper archive-candidate)))
```

- [ ] **Крок 5: RED→GREEN для Python без migration ownership**

`language python` + `lifecycle active|transitional` + empty `migration-issue` має дати:

```lisp
(repo-tooling-violation python-migration-unowned "scripts/example.py")
```

Не вводити `migration-state` у цьому slice.

- [ ] **Крок 6: Зберегти всі pure witnesses GREEN одним focused запуском**

```sh
cargo run -p my-lisp-cli --bin my-lisp -- scripts/check-repo-tooling-inventory.lisp
```

До filesystem-backed enforcement script може завершуватися named selftest verdict, але не має ще заявляти повний repo coverage.

---

### Задача 3: Додати реальний machine-readable inventory і filesystem enforcement

**Файли:**
- Create: `knowledge/repo-tooling-inventory.lisp`
- Modify: `scripts/check-repo-tooling-inventory.lisp`

**Registry header:**

```lisp
(about
  (schema repo-tooling-inventory/1)
  (issue 382)
  (scope immediate-scripts-entries-except-tests)
  (authority governance-metadata-not-language-semantics)
  (python-migration-authority 76)
  (rust-retirement-valve 299))
```

- [ ] **Крок 1: Додати по одному `(tool ...)` row на кожний immediate script file**

Поточний baseline містить 41 existing top-level file; після checker — 42 rows. `scripts/tests` виключається правилом scope, а не маскується tool row.

Language mapping:

```text
.lisp -> lisp
.py -> python
.sh та check-bilingual-docs -> shell
.mjs -> javascript
.ps1 -> powershell
```

- [ ] **Крок 2: Python rows позначити тільки artifact lifecycle + migration issue**

Усі repo-owned Python rows мають `lifecycle transitional`.

Відомі вузькі owners:

```text
scripts/generate-meta-semantic-registry.lisp -> migration-issue 76 (completed by current replay)
scripts/generate-meta-eval-evidence.py     -> migration-issue 351
```

Для інших активних Python tools тимчасово використовувати parent `migration-issue 76`, доки не існує вужчого child issue. Не вигадувати replacement path.

- [ ] **Крок 3: Невідомі facts залишати `unknown`/`()`, а не домислювати**

Кожен row усе одно мусить мати всі required fields.

- [ ] **Крок 4: Додати real-tree runner**

Checker читає:

```lisp
(read-all (read-file "knowledge/repo-tooling-inventory.lisp"))
(read-dir "scripts")
```

і виключає тільки exact `"tests"` через structural equality.

- [ ] **Крок 5: Реальний current inventory має стати GREEN**

Expected final verdict:

```lisp
(repo-tooling-ok)
```

- [ ] **Крок 6: Доказ fail-closed без committed mutation**

Використати pure fixtures як основний negative proof. Якщо потрібен real-tree smoke, тимчасова мутація має бути повністю прибрана перед commit.

---

### Задача 4: Додати Guard navigation і прибрати temporary workflow

**Файли:**
- Modify: `knowledge/guard-reference.lisp`
- Delete: `.github/workflows/382-red-probe.yml`

- [ ] **Крок 1: Додати лише navigation topic `repo-tooling`**

Вона вказує на:

```text
knowledge/repo-tooling-inventory.lisp
scripts/check-repo-tooling-inventory.lisp
docs/superpowers/specs/2026-09-17-repo-tooling-inventory-design.md
#382
```

Не копіювати individual rows у Guard.

- [ ] **Крок 2: Видалити `.github/workflows/382-red-probe.yml`**

Його роль завершується після доказу RED. Постійне існування суперечить design і перетинається з #384.

- [ ] **Крок 3: Переконатися, що `.github/workflows/ci.yml` лишився єдиним steady-state gate для #382**

CI step виконує:

```sh
./target/debug/my-lisp scripts/check-repo-tooling-inventory.lisp
```

після доступності canonical CLI.

---

### Задача 5: Exact-head verification перед merge

**Файли:** без нових production changes, крім виправлень, які реально випливають із verification.

- [ ] **Крок 1: Focused tooling checker**

```sh
cargo build -p my-lisp-cli --bin my-lisp
./target/debug/my-lisp scripts/check-repo-tooling-inventory.lisp
```

Expected: `(repo-tooling-ok)`, exit 0.

- [ ] **Крок 2: Rust one-way valve**

```sh
bash scripts/test-rust-one-way-valve.sh
```

та PR diff має показати Rust additions = 0.

- [ ] **Крок 3: Bilingual/Ukrainian-first docs gate**

Changed design/plan docs мусять пройти `scripts/check-bilingual-docs`.

- [ ] **Крок 4: CI exact head**

Перевірити, що `CI` на exact PR head GREEN і що немає `.github/workflows/382-red-probe.yml` у фінальному diff.

- [ ] **Крок 5: Acceptance audit**

Підтвердити одночасно:

```text
all immediate scripts covered exactly once
stale/unregistered/duplicate/invalid-enum mechanically caught
Python migration ownership points to #76/#317/#351
no invented replacements
Guard navigation only
Rust additions = 0
no script moves/deletions for gaming
no permanent new workflow
```

Лише після цього переводити PR з draft/merge-ready за звичайною дисципліною репозиторію.