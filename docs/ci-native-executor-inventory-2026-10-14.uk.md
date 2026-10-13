# Інвентар активних Python-виконавців CI — 14.10.2026

**Обсяг перевірки:** автоматичний `.github/workflows/ci.yml` в `juv4uk/sens`.
**SHA нижче — Git blob SHA-1 файлів на час інвентаризації**, а не SHA-256
виконаних програм. Фізичні SHA-256 зобов'язаний друкувати Actions.
Це не претензія на завершений аудит усіх ручних workflow/архівних тестів.

| Файл | Git blob SHA | Фактична роль | Семантичне свідчення? |
|---|---|---|---|
| `tests/test_migrate_exact_domain.py` | `1a2ce22eeaa7157e656c097384f0d4ee90abe2d8` | механічна міграція D3/D4 | ні |
| `tests/test_migrate_resolver_failclosed.py` | `1088e3d287f0b71a7995bae3996cb0079fcd813f` | перевірка механічного resolver під `python3 -O` | ні |
| `tests/test_sens_quoted_datum_law.py` | `dacaafecb4efa795adae32ba74a8520bc31ab0aa` | тест Python-мігратора цитування | **ні**, попередній напис `semantic_authority=binary-SENS` хибний |
| `tests/test_slp1_d7_v2_quote_boundary.py` | `4cbe1e31c854cd3815174ac0f82764ca9bc99a06` | Python-мігратор D7/SLP1 | **ні**, інструментальна межа |
| `scripts/check-domain-ladder-identity.py` | `357b0504a4447ad3c95e4e9b636e2feb16e64f00` | інвентар доменних координат | ні |
| `scripts/ci_one_focused_workflow.py` | `d7036ff365227f0a0c5f20cff01ce53bf077a59a` | структурний CI guard | ні |
| `scripts/ci_failure_contract.py` | `482168a0490023e8ec6bd1478df3f4f7cf362623` | CI glue/запуск процесів, хешування, RED-діагностика | сам по собі — ні |

## Реальне виконання, окреме від інструментального

Семантичні фізичні свідки в одному автоматичному workflow:

- `sens-time-d1-predicate-law` → `target/debug/sens tests/semantic/time-d1-predicate-law.sens`.
- `knowledge-exact-arity-structure` → `target/debug/sens tests/semantic/knowledge-exact-arity-structure.sens`.
- `sens-domain-logic-2040-mutant` → `target/debug/sens tests/semantic/domain-logic-2040/mutant.sens`, очікуване відхилення non-callable.

Це **реальні ELF-процеси SENS** під механічним Python CI-клеєм, а не
Python-інтерпретація семантики. Лог містить команду, версію ELF,
SHA-256 виконавця та фікстури, очікуваний/фактичний SHA-256 результату,
exit/status, verdict і точну команду replay. `scan-executors` не дає
показати PASS без трьох записів.

`cargo test` із викликом SENS evaluator усередині Rust-бінарника
є **in-process parity**: корисний окремий доказ, але це не CLI-процес
`sens`. Не позначати його `NATIVE_SENS_ORACLE` без реального запуску.

## Незакрита частина аудиту

Ручні workflow, історичні скрипти, а також повний корпус `tests/` ще
потребують класифікації `PARITY`, `CI_GLUE_NO_SEMANTICS`,
`RESEARCH_NON_GATE` або `NATIVE_SENS_ORACLE`. До завершення такого
аудиту **не заявляти повного покриття**, не плутати механічні зелені
тести із семантичним PASS та не приховувати застарілий тест карантином.
