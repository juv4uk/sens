# Червоний CI: маршрутизація причин (операційне правило)

Це **операційний шар**, не другий контракт семантики SENS. Мову визначають точні біти, домен та ратифікований закон; Python тільки транспортує й перевіряє метадані.

## Два незалежні виміри

| Причина | Відповідальний | Умова закриття |
|---|---|---|
| OWNER_UNCLEAR | власник `juv4uk` лише один раз | точне письмове ратифіковане правило (`ratified_rule`), а також доказ CI |
| AGENT_DEFECT | рій | атомарне виправлення та CI-доказ |
| TEST_DEFECT | рій | виправлення тесту без заміни SENS-семантики, CI-доказ |
| LEGACY_BINDING | рій; власник тільки для нормативного вердикту | `legacy_marker` (SID8/десятковий посередник/спадковий синтаксис), `provenance`, міграція або доведений історичний статус |

Окремий статус **REGRESSION / TRANSITIONAL / FLAKE** регулюється чинним `scripts/ci_failure_contract.py` та `knowledge/red-test-quarantine.json`. Цей механізм його не замінює. Не підмінювати недоведені регресії штампом REGRESSION. Відсутність причини/статусу: UNCLASSIFIED і блокувальна відмова негайно; після 24 годин — ESCALATE_24H. Іменований чинний карантин не означає некласифікованість.

## Запис у журналі

Кожний `cases[]` з `knowledge/red-cause-ledger.json`: `run_id`, точний `run_url`, `first_seen_at` (з поясом часу), `cause`, `stamp`, `owner`, `state: open|resolved`. Для FLAKE і TRANSITIONAL: `ticket: #N`, `since`, `expires`, `investigation`. Для LEGACY_BINDING: `legacy_marker`, `provenance`. Для доведеного розв'язання: `proof_run_url`, `proof_sha` (40 hex), `resolved_by: swarm|owner`. Для OWNER_UNCLEAR: `ratified_rule` (посилання на чинну доктрину, не новий паралельний авторитет). 

Жодний агент не створює ратифікацію самостійно; лише додає перевірений запис до чинної доктрини після рішення власника. Відсутній доказ CI не можна рахувати як виправлення.

## Запуск

- `python3 -m unittest discover -s tests -p 'test_red_cause_router.py' -v` — 8 негативних/позитивних механічних перевірок.
- `python3 scripts/red_cause_router.py audit` — аудит журналу й частки підтверджених виправлень без власника.
- `GITHUB_TOKEN=... python3 scripts/red_cause_router.py live` — перелік падінь GitHub Actions за останні 48 годин (за замовчуванням), включно з workflow-level failures із `jobs=[]`.

Обмеження пілота: live-інвентар перевіряє **workflow conclusion=failure** і обмежене вікно, не всі види `cancelled`/`timed_out`; після межі сторінок виводить INCOMPLETE_INVENTORY і завершується червоним. Він не збирає приватні job logs, не створює GitHub issues і не привласнює причину на підставі назви тесту. Автоматичне створення задач/assignments та історичне покриття всіх 600 workflow — окремий етап із доказом, не заявлена готовність.

Метрика: verified_swarm / verified_total по унікальних записах `state=resolved` із `proof_sha` та `proof_run_url`. Це міра документованих доказів, не автоматичний висновок про справність SENS.

Першоджерела: GitHub Actions workflow commands (офіційна документація); CI-договір #5741; координація #5029. TECH-SCAN проведений 2026-10-13.
