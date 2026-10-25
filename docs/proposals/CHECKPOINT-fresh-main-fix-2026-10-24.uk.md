# ЧЕКПОІНТ: три правки, готові до перенесення на свіжий main

Автор: агент Sthāpaka, 2026-10-24.

## Стан системи

| факт | значення |
|---|---|
| гілка `feat/semantic-backlog-measurement` | відстає від `main` на **449** комітів, випереджає на **82** |
| три правки | **закомічено на гілці** (звіт, `_proof_counts`, `release.yml`) |
| спроба створити свіжу гілку | **не вдалась** — коміти створюються, гілка ні (`Branch not found`) |
| `main` | **чистий** (перевірено: `report=` 0, `record_case` 0, `_proof_counts` 0) |

## Три файли, які треба перенести на свіжий `main`

Усі три лежать у робочій копії свіжого `main` (`/scratch/work/mainfresh/`).
Джерело істини — **свіжий `main`**, не стара гілка.

### 1. `scripts/prove-lisp-language-laws.sh`

Другий аргумент — звіт виконання. Звіт **лише друкує**; вердикт він не змінює.

```sh
if (( $# > 2 )); then
  echo 'usage: bash scripts/prove-lisp-language-laws.sh [native-sens-path] [report.json]' >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
report="${2:-}"
if [[ -n "$report" ]]; then
  printf '{"schema":"sens-language-law-proof/v1","cases":[' > "$report"
fi
case_records=0
record_case() {
  [[ -n "$report" ]] || return 0
  if (( case_records > 0 )); then printf ',' >> "$report"; fi
  printf '{"test_id":"%s","kind":"%s","expected":"%s","actual":"%s"}' \
    "$1" "$2" "$3" "$4" >> "$report"
  case_records=$((case_records + 1))
}
```

Плюс виклик `record_case` перед `cmp -s "$tmp/expected" "$tmp/actual"` і закриття
JSON перед `NATIVE_SENS_SUITE_PASS`.

### 2. `scripts/report_t5_t5m_triplet_inventory.py`

`--proof-report` в `argparse`, хелпер `_proof_counts()` (відсутній/порожній/
**невалідний** звіт → `(0, 0)`), і після `inspect(...)`:

```python
        uk_oracle, certified = _proof_counts(args.proof_report)
        report["summary"]["uk_oracle_verified"] = uk_oracle
        report["summary"]["original_executable_migrations_certified"] = certified
        report["summary"]["release_admitted"] = 1 if certified > 0 else 0
```

`status` **не** перераховується — це семантика гейта й рішення власника.

### 3. `.github/workflows/release.yml`

Перед кроком «BLOCK tag publishing…» — **збірка** і **доказ**; у виклик
інвентаря — `--proof-report`:

```yaml
      - name: Build native SENS executor for language-law proof
        run: cargo build --locked -p sens-cli --bin sens --bin sens-trit
      - name: Prove language laws by EXECUTION (same tagged SHA)
        run: |
          set -euo pipefail
          bash scripts/prove-lisp-language-laws.sh "$PWD/target/debug/sens" "$RUNNER_TEMP/proof.json"
```

Причина, чому це потрібно: крок «BLOCK tag publishing…» у job `test:`, а `sens`
збирався в **іншому** job (`build-cli:`). Тому доказ виходив із `actual=missing`.

## Червоні: дві природи

1. **Тіні застарілої бази.** CI звітує про `d11-clojure-juxt-constructor-improper-tail`
   і `d11-clojure-juxt-positive`, але на свіжому `main` фікстура
   `…-constructor-improper-tail-negative.lisp` **існує** (409 Б), `lib/core4.sens`
   **пере-карбовано** (213834 Б), а скрипт доказу **утріч більший** (212967 Б).
   **Ці червоні не можна лагодити на старій гілці.**
2. **Ті, що лишаться після освіження** — `lib/core4.sens` (фізичний дрейф) і пара
   `d11-clojure-juxt-*`. Перевіряти **на `main`**.

## Deutsch

Prüfpunkt: drei Korrekturen bereit zur Übernahme auf frischem main.

## English

Checkpoint: three corrections ready to move onto fresh main.
