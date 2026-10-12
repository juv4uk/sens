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

**Повний seed-total, його мінімальність і самодостатність offline replay лишаються BLOCKED.** У підсумок не закрито весь граф `mod`/`cfg`/`include`, залежності toolchain/OS/shared libraries, Git refs/objects та повний мінімізований набір зовнішніх vendor inputs. Спостережені vendor-файли — subset runtime traces, не доказ мінімального набору.

Окремий K1 static-link/strip тест дав **792 544 Б** замість dynamic C1 **92 248 Б**. Він зберіг output parity, але збільшив on-disk footprint на 759.14%; рішення: **не приймати як size win**. Різні runner-source checkpoints не порівнювати як чисту оптимізацію.

Правило публікації: завжди називати розмір і метрику (*on-disk*, PT_LOAD, code sections, operational-input subtotal чи повний seed-total), pinned SHA і scope. Не називати subtotal «розміром Nano-SENS» без уточнення.

## 3. Бенчмарк-лабораторія: індекс — це не вся лабораторія

- В операційному обліку лабораторія вже має **100+ стендів/експериментальних напрямків**.
- Генерований [`benchmarks/README.md`](../benchmarks/README.md) на поточному стані перелічує **47 зареєстрованих стендів**. Це кількість рядків індексу, а не доказ, що інших стендів не існує.
- Незареєстровані вже наявні стенди — backfill debt #4172. Новий стенд від самого початку має мати `bench.json` за guard #4171.
- `benchmarks/README.md` генерується `scripts/benchmark_registry.py`: **не редагувати вручну**. Виправляти manifests і генератор, потім запускати перевірку/генерацію.
- Не заводити паралельний benchmark framework лише для того, щоб описати існуючий результат. Звести наявні виміри до одного індексу, не викидаючи raw results і історичний provenance.
- Для історичних гілок: не називати їх код «інтегрованим», доки свідок/тест і корисна реалізація не присутні в `main`. Існуючі дослідження переносити та перевіряти у `main`; не створювати нові гілки для чергової паралельної копії.

### Мінімальна картка для кожного стенда

Кожен `bench.json` повинен давати змогу відповісти: яке питання перевіряємо; яку семантичну генерацію/Contract вимірюємо; які саме encode/decode/compile/setup/execute шари включено; який oracle й corpus; як відтворити прогін; де raw JSON/TSV/stdout; які `git_sha`, `corpus_sha`, artifact SHA та toolchain/host provenance; що саме результат **не** доводить.

Мітки на кшталт `CURRENT`, `RESEARCH-ONLY`, `HISTORICAL`, `BLOCKED` та `COMPLEMENTARY-BOUNDED` мають зберігатися. Наявність у каталозі не надає семантичної влади; зелений benchmark не підміняє oracle parity.

### Вже опубліковані виміри й межі

- **T5 streaming, 09.10:** 1 D3 QUOTE — 109 → 70 нс/виклик; 1024 форми — 48 896 → 47 852 нс/виклик у парному same-run контролі, з перевіркою побайтової тотожності.
- **D3/D7 occupancy bitmask:** наведені виграші порівнюють різні hosted прогони. Це історичні механічні заміри lookup, не контрольований A/B на тому самому фізичному runner і не швидкість усієї мови.
- **Frame-3:** на обмеженому корпусі з 5000 валідних D2-програм отримано 37 837 Б проти 46 327 Б T5 (−18.3%). Це окремий явний кодек F3 (`.senc`), не заміна канонічного T5 `.sens`, і не дає права на автоматичний format-sniffing/fallback.
- **Однобайтовий `.f3m`:** незалежний вичерпний свідок приймає 45 програм із 256 кодів у вузькому мікропрофілі. Це не означає, що довільна SENS-програма або універсальний `.senc` вміщується в один байт.

Принцип: **encode/correctness перед timing; raw evidence перед висновком; порівнювати лише тотожний workload/semantic generation з належною provenance.** Один benchmark, один host або один шар не визначає переможця для всієї мови.

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
