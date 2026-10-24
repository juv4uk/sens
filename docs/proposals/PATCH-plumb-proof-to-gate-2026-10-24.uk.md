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
