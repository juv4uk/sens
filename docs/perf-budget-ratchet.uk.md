# SENS: performance-бюджети поряд із семантичними тестами

**13.10.2026. Статус:** числовий baseline не ратифікований, автоматичні performance-ворота ще НЕ активні. Діє один автоматичний workflow `ci.yml` для двійкових SENS-законів; цей контракт його не замінює, не створює іншого workflow та не запускає червоних Actions.

## Доказовий механізм

Перший профіль — наявний `benchmarks/domain12345678/run.py`, котрий вимірює Cachegrind `Ir` кожного `d1..d9, mixed, width-roundtrip` при фіксованих ітераціях і `empty` baseline. Це історичний замір обмеженого source-word fast path, не вся драбина D1–24+, не семантика, не викличність доменів і не універсальна швидкість SENS. T5M переносить точні слова різної ширини, але не визначає їхні домени. `scripts/perf_budget_gate.py` перевіряє `results.tsv` і `environment.json` проти **окремо ратифікованих** бюджетів.

Висновок для кожного кейса: `PERF-BUDGET-EXCEEDED` або `PASS` із назвою, шаром `parse/eval/encode/transport`, порогом і спостереженим `Ir/op`, різницею, commit SHA й SHA256 результату. У JSON-звіті — сумарний ліміт, витрачений бюджет і **сума додатних перевищень**. Це обсяг відомого performance-боргу, не абстрактна оцінка якості коду.

## Встановлення перевіреного baseline

1. Зібрати виробничий приклад тим самим toolchain: `cargo build --locked --release -p sens --example domain12345678_bench`.
2. Виміряти: `python3 benchmarks/domain12345678/run.py --binary target/release/examples/domain12345678_bench --out-dir /tmp/sens-irefs --iterations 100000 --reps 3`. Зберегти raw-відліки, `results.tsv`, `environment.json`, commit SHA, версію Valgrind/Rust, архітектуру, digest і issue ратифікації.
3. Окремим review-комітом замінити `baseline: null`, `environment: null` та порожні `budgets: []` у `knowledge/perf-budget-ratchet.json`. Потрібен об'єкт `baseline` з `source_sha` (40 hex), `evidence_sha256` (64 hex), `ratification_issue` (`#N`), `environment` з `rustc`, `valgrind`, `machine`, `iterations`, `reps`, `contract_version`, `semantic_generation`, і всі **11** бюджетів `{case,layer,source_location,max_net_irefs_per_iteration}`, із додатним числовим лімітом. Не використовувати вимір поточного регресійного коміту як автоматичну нову норму.
4. Вимірявши новий SHA на співставному середовищі, виконати: `python3 scripts/perf_budget_gate.py --evidence-dir /tmp/sens-irefs --json-report /tmp/sens-perf-verdict.json`. Exit 0: доведені бюджетні межі; exit 1: перевищення; exit 2: `PERF-BUDGET-UNCALIBRATED` / `PERF-ENVIRONMENT-MISMATCH` / некоректні докази. Поки baseline порожній, це **не зелені ворота**.
5. Лише після такого виміру і ratchet-review приєднати дешевий бюджет до **існуючого** одного CI job. Нічний/релізний повний набір лишити в ручних workflow, без другого `schedule`.

## Відомі канарейки й обмеження

- Гарячі `parse→decimal text→format` посередники, лінійні сканування замість бітмап, алокації на операцію — **кандидати** для профілювання, не оголошені автоматично спійманими. Щоб вважати канарейку чинною, потрібен точний виклик та ліміт `Ir/op` або доведена кількість алокацій. Ніякого regex-based semantic-оракула.
- Старий runner застосовував `max(0, raw-empty)`, приховуючи від'ємний шум; після цього виправлення зберігає підписану різницю, а gate відхиляє від'ємний net як неінформативний доказ.
- Cachegrind `Ir` в основному детермінований на тих самих бітах і бінарнику, але розкладка машинного коду та версія компілятора впливають на нього. Для wall-clock використовувати парні повтори й effect-size із інтервалами за Kalibera–Jones, а не FAIL за будь-який 0.1% шум. Інструкційний ліміт не ловить усі структурні костилі.

Джерела: Valgrind 3.27.1 Cachegrind manual (https://valgrind.org/docs/manual/cg-manual.html); Kalibera–Jones (https://arxiv.org/abs/2007.10899). Наявні донори: `benchmarks/physical-sens-runtime/irefs.py`, `benchmarks/bench-methodology/paired_effect.py`, `benchmarks/domain12345678/run.py`.

Контракт бюджетів — **метадані продуктивності**, не нова ратифікація доменів чи логіки двійкового SENS. Зміна лімітів — окремий коміт із причиною та review ([#5748](https://github.com/juv4uk/sens/issues/5748)), не тихе збільшення.
