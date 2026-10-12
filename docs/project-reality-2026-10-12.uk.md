# SENS: операційна реальність і план лабораторії

**Станом на 12 жовтня 2026 року.** Цей документ зводить факти з `main` до однієї карти. Він не замінює контракт, машинні свідчення або raw benchmark artifacts.

## 1. Семантична влада: D10 ратифіковано, але не весь шлях виконання

- Поточний контракт — **Contract 11.9** (`../language-contract.lisp`).
- D1–D9 залишаються попереднім exact-domain фундаментом.
- **D10 ратифіковано як один цілісний каталог 1024/1024**: [каталог](../knowledge/d10-v18-semantic-inventory.json), [акт ратифікації](../knowledge/d10-owner-whole-domain-ratification-20261012.json).
- D24/D48/D96/… — окрема owner-ratified числова драбина.
- Цілісна ратифікація каталогу **не означає**, що індивідуальні F1/F2/F3 докази, незалежні позитивні/негативні witness-и, behavioral independence або physical T5 admission завершені. У самому акті ці межі зафіксовано явно.
- Перехід `language-contract.lisp` на повністю canonical visible-binary source ще триває (#4248). Документація не має називати цей cutover завершеним до landed evidence.

Канонічна identity лишається:

`(точні біти, точний домен, закон, який допускає інтерпретацію)`

Десяткові значення, host integer, byte, Rust type, backend opcode або назва поверхні — похідні подання, не джерело семантичної влади.

## 2. Nano-SENS: що виміряно і що ще заблоковано

Первинні джерела: [звіт seed-v0](research/nano-sens-seed-v0-20261012.uk.md), [звіт про frontier/варіанти розміру](research/nano-sens-size-frontier-20261011.uk.md), [канонічний evidence JSON](../evidence/nano-sens-seed-v0-2026-10-12.json), [K1 static-link evidence](../evidence/nano-sens-k1-static-link-2026-10-12.json).

### Доведено для конкретного pinned checkpoint

- Два чисті прогони; в кожному — **189/189 тестів**.
- C1/C2 executable побайтно тотожні; compiler-artifact output також збігається.
- Для dynamic C1/C2 зафіксовано: **92 248 Б файл**, **85 685 Б loadable PT_LOAD bytes**, **70 655 Б code sections**.
- Відомий partial operational-input subtotal найсвіжішого checkpoint: **36 033 737 Б** (runner + pinned SENS build-input subset + CML runtime-read contract + WSM nucleus source).
- Вимірювач має позитивні й негативні self-tests; це перевіряє інструмент, не створює нового compiler run.

**Версія семантичного джерела:** pinned Nano checkpoint використовує SENS source SHA `d0787a40fcea36501747732aa61b6de19fe29c70` і Contract 11.8 (`d10_dependency=false` у машинному звіті). Отже ці прогони не є виконанням D10 під поточним Contract 11.9; цей статус окремий від актуальної ратифікації D10 у `main`.

### Не доведено

**Повний seed-total, його мінімальність і самодостатність offline replay лишаються BLOCKED.** Найновіший успішний статичний аудит source edges на snapshot `main@a825e5d3d0afe615869117e0e2d22b926493a862`: 77 Rust-файлів / 111 ребер / 0 невирішених спостережень у межах аналізатора; pinned SENS `d0787a40fcea36501747732aa61b6de19fe29c70` — 71 / 90 / 0; pinned CML `ec4ba010cebd9fdc37b39224142dcac3ee907cfe` — 66 / 83 / 0. [CI run 38190527591](https://github.com/juv4uk/sens/actions/runs/38190527591) завершився SUCCESS, self-test аудитора — 7/7. Попередній snapshot `96ee15564d7a707d31664dca6e55b331d76ea6de` у [run 38190369519](https://github.com/juv4uk/sens/actions/runs/38190369519) дав ті самі лічильники. Це закриває інвентаризацію саме статичних Rust module/path/include ребер для цих трьох snapshot-ів, **не** повний seed closure. За межами лишаються build-script/proc-macro та environment inputs, повний Cargo dependency closure, vendor pruning, Git refs/objects, toolchain/OS/shared-library bytes і контрольований clean offline replay. Довготривалий receipt: [`evidence/nano-sens-static-source-edges-2026-10-12.json`](../evidence/nano-sens-static-source-edges-2026-10-12.json). Повні ліміти перелічені в [аудиторі](../scripts/audit-nano-sens-source-closure.py); [найновіший raw CI artifact 11721233152](https://github.com/juv4uk/sens/actions/runs/38190527591/artifacts/11721233152) зберігається до 11.11.2026 01:05:52 UTC.

Окремий K1 static-link/strip тест дав **792 544 Б** замість dynamic C1 **92 248 Б**. Він зберіг output parity, але збільшив on-disk footprint на 759.14%; рішення: **не приймати як size win**. Різні runner-source checkpoints не порівнювати як чисту оптимізацію.

Правило публікації: завжди називати розмір і метрику (*on-disk*, PT_LOAD, code sections, operational-input subtotal чи повний seed-total), pinned SHA і scope. Не називати subtotal «розміром Nano-SENS» без уточнення.

## 3. Бенчмарк-лабораторія: індекс — це не вся лабораторія

- В операційному обліку лабораторія вже має **100+ стендів/експериментальних напрямків**.
- Генерований [`benchmarks/README.md`](../benchmarks/README.md) на поточному стані перелічує **54 зареєстровані стенди** і окремо **7 source-backed support-exemptions**; винятки не додаються до кількості стендів.
- Census має **170 верхньорівневих каталогів**: 54 зареєстровані, 7 явних винятків, **109 досі некласифікованих**. Це реальний залишок #4172, а не завершене закриття лабораторії.
- Реєстр винятків [`../benchmarks/support-exemptions.json`](../benchmarks/support-exemptions.json) валідовується скриптом і має JSON Schema; свідок кожного винятку має існувати. Новий standalone-стенд вимагає `bench.json` за guard #4171, а support-каталог може бути винятком лише з явним поясненням і свідком.
- `benchmarks/README.md` генерується `scripts/benchmark_registry.py`: **не редагувати вручну**. Виправляти manifests і генератор, потім запускати перевірку/генерацію.

### Повний sweep зареєстрованих стендів і follow-up

[Перший повний sweep, run 38190345552](https://github.com/juv4uk/sens/actions/runs/38190345552) на SHA `d57d55f7f50f157d672bb283d31f9a427690596f` охопив **54/54** стенди без дублікатів, пропусків чи зайвих результатів: **50 PASS / 4 FAIL / 0 BLOCKED / 0 TIMEOUT**. Його чотири первинні відмови розібрано в історичній частині receipt.

Після виправлення CLI-контракту `d6-parity-duality` [follow-up run 38190822493](https://github.com/juv4uk/sens/actions/runs/38190822493) на SHA `411312eab71a7c31cd9d71e52ebd34c031881c58` знову охопив **54/54**, цього разу **51 PASS / 3 FAIL / 0 BLOCKED / 0 TIMEOUT**. Це реальний приріст на один PASS, не просто зміна опису. Довготривалий receipt з історією обох прогонів: [`evidence/benchmark-sweep-2026-10-12.json`](../evidence/benchmark-sweep-2026-10-12.json).

Після другого sweep виправлено класифікацію двох відомих generation/environment blockers:
- `cross-language` тепер друкує явний `SENS_BENCHMARK_STATUS=BLOCKED`, коли немає pinned Guix environment; без Guix це не результат порівняння мов.
- `store-air-load` тепер класифікує Contract 11.8 проти поточного 11.9 як `BLOCKED` для current replay, а маніфест прямо зветься історичним до окремого replay.

Обидві зміни й нові рядки generated index потрапили в останні коміти, але exact-head sweep для них іще не завершився. Третя проблема — `physical-binary-performance` — виникла тому, що runner намагався передати старий Lisp AST `(00000001 ())` до canonical exact-width reader. Parser не послаблюємо. Runner тепер формує тимчасову ASCII word-projection безпосередньо з committed `.sens` через незалежний Python T5-декодер, а потім вимагає від Rust `sens-trit encode` побайтної тотожності. Додано окрему функцію проєкції, п'ять unit-тестів її позитивних/негативних меж і перевірку всіх восьми фізичних файлів у smoke workflow. Це доводить транспортний round-trip, не компіляцію історичного AST і не семантичну ратифікацію. [Physical smoke](https://github.com/juv4uk/sens/actions/runs/38192076757) та [registry sweep](https://github.com/juv4uk/sens/actions/runs/38192066930) для цієї зміни ще в черзі; до їхнього завершення не оголошувати physical benchmark або всю лабораторію PASS.

## 4. Пріоритети — у порядку доказової цінності

1. **Закрити реєстр лабораторії:** провести census усіх наявних стендів, відрізнити активні від архівних, зробити backfill `bench.json` для реальних активних стендів і закрити #4172 без дублювання manifests.
2. **Довести Nano-SENS seed closure:** завершити module/cfg/include census, закріпити повний набір runtime opens, окремо врахувати Git/toolchain/OS/shared-library bytes, зробити clean offline replay, і лише тоді оголошувати total/minimum.
3. **Закрити D10 admission шляхом окремих доказів:** не змінюючи ратифікованого каталогу, додати й перевірити domain laws/witnesses/negative cases та фізичні T5 ворота.
4. **Зробити current cross-language replay:** ті самі workloads, oracle та точні SHA для Python і інших мов; відокремити startup, load, compile, setup, steady-state та one-shot. Історичні Function8/Sens8 результати залишити historical, не перейменовувати на current.
5. **Інтегрувати, не розмножувати:** корисні скрипти, witness-и й документацію з попередніх досліджень переносити в `main`, зберігаючи provenance та явні negative results.

## 5. Джерела поточної влади

- [README](../README.md)
- [Contract 11.9](../language-contract.lisp)
- [D10 whole-domain ratification](../knowledge/d10-owner-whole-domain-ratification-20261012.json)
- [D10 inventory, 1024 coordinates](../knowledge/d10-v18-semantic-inventory.json)
- [Benchmark registry generator](../scripts/benchmark_registry.py)
- [Generated registered-stand index](../benchmarks/README.md)
- [Nano-SENS seed-v0 evidence](../evidence/nano-sens-seed-v0-2026-10-12.json)
- [Nano-SENS K1 static-link evidence](../evidence/nano-sens-k1-static-link-2026-10-12.json)
- [Historical occupancy benchmark with corrected D10 interpretation](benchmarks/2026-10-09-domain-occupancy-bitmask.uk.md)
