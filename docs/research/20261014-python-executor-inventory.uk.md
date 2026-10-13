# Інвентар Python у єдиному автоматичному SENS CI · 14.10.2026

**Обсяг:** лише workflow `.github/workflows/ci.yml`, який автоматично виконується
на push. Інші ручні/карантинні workflow не вважаються виконаними. Перевірено
на SHA `a365b7fd37326a9f62491439dc6971b9d1d668a7`, CI
[38473596437](https://github.com/juv4uk/sens/actions/runs/38473596437):
`SUCCESS`, три `NATIVE_SENS_ORACLE` квитанції,
`NATIVE_EXECUTOR_RATCHET_PASS verified=3`.

Хеші в таблиці — **Git blob SHA-1 джерела**, не SHA-256 виконуваного файлу:
SHA-256 бінарника, входів, expected/actual беруться з **реального логу**
цього CI запуску; не підставляти хеші з таблиці замість runtime-доказу.

| Шлях виклику | Git blob SHA-1 | Стан | Семантичні ворота? |
|---|---|---|---|
| `scripts/ci_one_focused_workflow.py` | `d7036ff365227f0a0c5f20cff01ce53bf077a59a` | CI_GLUE_NO_SEMANTICS: перевірка рівно одного workflow | Ні |
| `scripts/check-domain-ladder-identity.py` | `357b0504a4447ad3c95e4e9b636e2feb16e64f00` | CI_GLUE_NO_SEMANTICS: структурна інвентаризація, не evaluator | Ні |
| `scripts/ci_failure_contract.py` | `2f7fe6259e2dbb943afdd70a4161f16f1a6759bf` | CI_GLUE_NO_SEMANTICS: виклик native, хешування, аудиторія; `eval` без `target/debug/sens` відхиляється | Лише **фактичний** дочірній native SENS |
| `tests/test_migrate_exact_domain.py` | `1a2ce22eeaa7157e656c097384f0d4ee90abe2d8` | Python unittest переписування точних голів; `encode` | Ні, лише механічна міграція |
| `tests/test_sens_quoted_datum_law.py` | `dacaafecb4efa795adae32ba74a8520bc31ab0aa` | Python unittest для quote/Text7-проєкції; назва `law` не робить його SENS оракулом | **Ні**; перенести semantic proof у фізичний `.sens` |
| `tests/test_slp1_d7_v2_quote_boundary.py` | `4cbe1e31c854cd3815174ac0f82764ca9bc99a06` | Python unittest механічного D7/SLP1-мосту; перевірка регістру й відмов читача | **Ні**; native parity ще не доведено |
| `tests/test_migrate_resolver_failclosed.py` | `1088e3d287f0b71a7995bae3996cb0079fcd813f` | Python `-O` негативна механічна перевірка мігратора; `encode` | Ні |

## Перелік чинних нативних семантичних свідків

- `sens-time-d1-predicate-law`: `target/debug/sens tests/semantic/time-d1-predicate-law.sens`.
- `sens-domain-logic-2040-mutant`: `target/debug/sens tests/semantic/domain-logic-2040/mutant.sens`, очікувана SENS-відмова `not callable`.
- `knowledge-exact-arity-structure`: `target/debug/sens tests/semantic/knowledge-exact-arity-structure.sens`.

Вони на `main` пишуть `TEST_EXECUTOR_START`, `TEST_EXECUTOR_RECEIPT`,
`NATIVE_EXECUTOR_END` і перевіряються командою
`python3 scripts/ci_failure_contract.py scan-executors`. Сам scanner **не є**
семантичним оракулом, а лише звіряє записані нативні виклики з файлами/SHA.
`TCP` (cargo integration) явно перейменовано на транспортно-інтеграційний,
а не самостійний SENS CLI verdict.

## Монотонна міграція / іменований борг

**Owner:** swarm / інтегратор SENS. **Облік:** issue
[#5741](https://github.com/juv4uk/sens/issues/5741). **Стан:**
`NATIVE-SEMANTIC-NOT-YET-ATTESTED` для двох Python-only quote/D7 законів.
Не трактувати їхній Python `PASS` як binary SENS `PASS`; зберегти як
**механічні** перевірки до реального фізичного свідка. Їх не прибирали,
не підмінили очікування і не видали за зелені semantic ворота.

Ця відомість не претендує на інвентар **всіх історичних** workflow:
архівні й ручні тести потребують окремого перебирання в #5741.
Нормативне правило — `AGENTS.md` `OWNER-ANTI-THEATER-20261014`.
