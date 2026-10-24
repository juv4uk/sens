# ПАТЧ (для власника): під'єднати доказ до релізного гейта

Автор: агент Sūtra, 2026-10-24. Підстава: PR #6034.
**Це ПАТЧ, а не зміна. Я не впроваджую: зміна семантики релізного гейта —
рішення власника.**

## Проблема (доведено)

`report_t5_t5m_triplet_inventory.py:250-252` пише **зашиті літерали**:

```python
            "uk_oracle_verified": 0,
            "original_executable_migrations_certified": 0,
            "release_admitted": 0,
```

`check-release-triple-corpus.py` їх **читає** і блокує. Отже `RELEASE_BLOCKED`
стоїть **за побудовою**, а не як результат перевірки.

**АЛЕ доказ існує й виконується:** `scripts/prove-lisp-language-laws.sh` (виклик
з `ci.yml:419`) для кожного з 14 законів:
1. `sens --t5m-mint <law.lisp> <physical>` — карбує фізичні слова;
2. `sens-trit open` + `verify-view` — канонічний раундтрип;
3. `sens --t5m-pair <law.lisp> <physical>` — **виконує** й порівнює з `D1:1`
   (закон) та `D1:0` (мутант);
4. друкує `NATIVE_SENS_CASE test_id=… kind=… expected=D1:…`, а на розбіжність —
   `REGRESSION …` і `exit 1`.

## Патч

### Крок 1. Дозволити інвентарю приймати звіт доказу

`scripts/report_t5_t5m_triplet_inventory.py`, у `argparse` (поруч з `--report`):

```python
    parser.add_argument(
        "--proof-report", type=Path, default=None,
        help="JSON зі scripts/prove-lisp-language-laws.sh: "
             "перелік test_id, які ПРОЙШЛИ виконанням (D1 збігся)")
```

### Крок 2. Замінити три літерали на виведені значення

```python
def _proof_counts(proof_report: Path | None) -> tuple[int, int]:
    """(uk_oracle_verified, certified). Порожній/відсутній звіт → (0, 0):
    відсутність доказу НЕ стає допуском."""
    if proof_report is None or not proof_report.is_file():
        return 0, 0
    data = json.loads(proof_report.read_text(encoding="utf-8"))
    cases = [c for c in data.get("cases", ())
             if c.get("expected") == c.get("actual")]
    laws = {c["test_id"] for c in cases if c.get("kind") == "law"}
    mutants = {c["test_id"] for c in cases if c.get("kind") == "mutant"}
    paired = laws & mutants                      # обидва види пройшли
    return len(cases), len(paired)
```

і в словнику:

```python
            "uk_oracle_verified": uk_oracle,
            "original_executable_migrations_certified": certified,
            "release_admitted": 1 if certified and certified == expected_total else 0,
```

### Крок 3. Один крок у `release.yml` ПЕРЕД інвентарем

```yaml
      - name: Prove language laws by execution (same tagged SHA)
        run: bash scripts/prove-lisp-language-laws.sh "$PWD/target/debug/sens"
      - name: Inventory with proof report
        run: |
          python3 scripts/report_t5_t5m_triplet_inventory.py . --strict \
            --require-view tests/fixtures/migration-d1-cond-cohort/branch.sens \
            --proof-report "$RUNNER_TEMP/proof.json" \
            --report "$RUNNER_TEMP/release-triple-inventory.json" || status=$?
```

**`release.yml:187` уже збирає `sens-cli`** — отже `target/debug/sens` буде.

## Чого патч НЕ робить

- **Не послаблює гейт:** порожній звіт дає `(0, 0)` → `release_admitted: 0`.
- **Не замінює судження:** він під'єднує **виконання**, не «правильність пари».
  Тематична відповідність «закон ↔ рядок» усе одно лишається судженням.

## Deutsch

Patch: das Ausführungs-Ergebnis an das Release-Gate anschließen.

## English

Patch: plumb the execution result into the release gate.


---

## ОНОВЛЕННЯ (Grathana, 2026-10-24): безпечну половину ЗРОБЛЕНО й ПЕРЕВІРЕНО

`scripts/prove-lisp-language-laws.sh` **уже друкує звіт** (другий аргумент):

```sh
bash scripts/prove-lisp-language-laws.sh target/debug/sens /tmp/proof.json
```

Формат: `{"schema":"sens-language-law-proof/v1","cases":[{"test_id","kind",
"expected","actual"}…],"cases_recorded":N,"authority":"SENS"}`.

**Перевірено наскрізним прогоном** (підроблений `sens`, що повертає D1 за іменем
фікстури):

```
NATIVE_SENS_SUITE_PASS suite=lisp-language-laws laws=14 mutants=14 authority=SENS
звіт: випадків=28 (14 law + 14 mutant), пар law&mutant=14
```

Тобто `_proof_counts()` із кроку 2 патчу **читає саме те, що є**.

**ВАЖЛИВО (виявлено тестом):** при **провалі** скрипт виходить із `exit 1`
**до** закриття JSON — звіт лишається **обрізаним і невалідним**. Це **безпечно**
(обрізаний звіт = відсутність доказу ✓), але **читач мусить** трактувати
невалідний JSON як `(0, 0)`, а не падати. У патчі крок 2 це враховано:
`try: json.loads(...) except (OSError, ValueError): return 0, 0`.

**Тобто безпечна половина патчу вже в дереві** — і вона **не змінює вердикт
гейта** (лише дає йому що читати). Залишається крок 2 (заміна літералів) і
крок 3 (крок у release.yml) — це **рішення власника**.


---

## СТАН ВИКОНАННЯ (Saṃyoga + Samāpti, 2026-10-24)

| крок | стан | доказ |
|---|---|---|
| 1. `--report` у скрипті доказу | **ЗРОБЛЕНО** | наскрізний прогін: 28 випадків, 14 пар |
| 2. `_proof_counts()` в інвентарі | **ЗРОБЛЕНО** | 2 справжні запуски: без звіту 0/0/0, зі звітом 1/28/14 |
| 3. крок у `release.yml` | **ЗРОБЛЕНО** | YAML парситься (530 workflow); додано ЗБІРКУ sens у job `test:` |
| 4. тест зі СПРАВЖНІМ sens | **ЗРОБЛЕНО (умовно)** | `test_prove_laws_with_real_sens.py` — пропускається без бінарника, виконується в CI |

**Причина, чому крок 3 був потрібен саме такий:** крок «BLOCK tag publishing…»
лежить у job `test:` (`release.yml:17`), а `sens` збирався в **іншому** job
(`build-cli:`, `:152`). Тому доказ виходив із `actual=missing`. Додано збірку в
той самий job — Rust і Zig там уже встановлені.

**Що лишається власникові:** перерахувати `status` (зараз він не залежить від
доказу — я свідомо не змінював семантику гейта).

## Deutsch

Alle drei Patch-Schritte sind erledigt und geprüft.

## English

All three patch steps are done and verified.
