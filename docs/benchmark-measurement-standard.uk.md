# SENS: стандарт доказових бенчмарків — STAGED / HOLD

Дата 2026-10-09. Цей етап підготовлено для впровадження **після зеленого immutable L0** згідно з [вікном стабілізації #5224](https://github.com/juv4uk/sens/issues/5224).
**Це не семантична ратифікація й не дозвіл зливати perf-коміти в червоний main.**

## Два незалежні виміри

| Вимір | Інструмент | Що можна стверджувати |
|---|---|---|
| Instruction references, branching, memory accesses | Наявний Cachegrind, далі iai-callgrind для Rust-функцій | Лічильники однакового workload, не секунди та не універсальна швидкість |
| Wall-time, пропускна здатність, p50/p95 | Наявний paired Release/CLI; далі criterion (Rust), hyperfine (CLI) | Час на пінованій машині, з кількістю повторів і відомою дисперсією |

**Ніколи не змішувати I refs і наносекунди в одному performance-score.**
Менша кількість інструкцій не гарантує меншого wall-time.
Всі порівняння зберігають повний git SHA, input / fixture, доступні binary hashes,
toolchain, модель CPU, ОС, warmups, парний порядок, число повторів і доказ
семантичної тотожності до початку вимірювання.
За розбіжності oracle результат має бути BLOCKED_NO_TIMING.

## Перший інструмент статистики — без нових залежностей

Файл benchmarks/packed-vs-visible/paired_effect_ci.py читає **вже наявні**
packed-vs-visible.jsonl та packed-vs-visible-runtime.jsonl.
Він перевіряє заявлений AST/observable oracle, погодженість медіан,
парність batch-вибірок і числову коректність, а потім повідомляє
median(visible)/median(packed) і *дослідницький* 95% bootstrap CI,
ресемплюючи цілі paired batches, а не окремі внутрішні виклики.

Відтворення:

    python3 benchmarks/packed-vs-visible/paired_effect_ci.py \
      --input /tmp/sens-performance/packed-vs-visible-runtime.jsonl \
      --source-sha ВСТАВИТИ_ПОВНИЙ_40_СИМВОЛЬНИЙ_SHA \
      --out-dir /tmp/sens-performance/paired-effect \
      --seed 20261009 --resamples 5000

    python3 -m unittest discover -s tests -p 'test_paired_effect_ci.py' -v

Файли: paired-effect.json, paired-effect.md. Результати можуть бути
PACKED_FASTER_WITHIN_RUN, VISIBLE_FASTER_WITHIN_RUN або INCONCLUSIVE.
Ніякий із цих результатів не змінює семантичні CI-oracle й не стає
автоматичним перф-гейтом.

**Межа чесності:** це bootstrap окремих парних batch у межах **одного**
shared GitHub-hosted run. Вони можуть бути залежними. Це **не**
Kalibera–Jones CI для незалежних процесів/машин, і такого твердження
скрипт ніколи не робить. CI не використовувати для універсального
регресійного вердикту.

## Після зеленого L0 — Kalibera–Jones і Rust-інструменти

Для ієрархічної оцінки потрібно окремо зібрати незалежні зовнішні повтори
(процеси / різні CI runs) з вкладеними парними batch-вимірами, пінувати
workload, SHA та parity, оцінити різні рівні варіації і лише потім
обчислити ефект та довірчий інтервал, чітко назвавши незалежну одиницю.
Використовувати записаний seed для випадкового порядку A/B всередині
незалежних повторів. Чергування пар у поточному стенді корисне, але не
заміняє ієрархічну оцінку.

Окремо і малими PR, **лише після відновлення immutable L0**:
1. iai-callgrind: один ратифікований current-code Rust workload,
   зіставлення I refs на однаковому CI runner, з перевіреним output/byte parity.
2. criterion: той самий workload, із задокументованою warmup/sample конфігурацією;
   не змішувати інструкційні і часові результати.
3. Kalibera–Jones: незалежні зовнішні реплікації та effect size/CI
   з реальною ієрархічною схемою, інакше дослідницький вердикт INCONCLUSIVE.

Поточна .github/workflows/sens-performance.yml вже має GitHub-hosted
Cachegrind — це чинна інструкційна baseline-лінія; не замінювати її
навмання. Записати фактичний CPU governor, turbo та можливість affinity,
але **не змінювати системні налаштування shared GitHub-hosted машини сліпо**.
Якщо справжньої ізоляції немає, чесно зазначати noisy shared CPU.
Для мережевих/SDR графіків латентності окремо врахувати coordinated omission.

## Пенсія для бенчмарків

Стенд стає історичним, якщо він більше не виконує current-code, втратив
незалежний observable oracle, має застарілу fixture або його перекрив
краще документований стенд. Архівувати результати з SHA, не видаляти
immutable L0 / fail-closed negative admission gates разом з perf-історією.


## Performance-бюджети як ворота — рішення 13.10.2026

СЕМАНТИКА І ЦІНА — ДВОЄ НЕЗАЛЕЖНИХ ВОРІТ. Спочатку сам SENS у
фізичному двійковому коді доводить правильність, зокрема на негативному
мутанті. Тільки після цього механічний Cachegrind/Callgrind може
підтвердити ціну. Python/Rust не отримують семантичної authority.
Зелений тест без performance-доказу не означає бюджетного PASS.

Рівно один автоматичний workflow: .github/workflows/ci.yml. Не
створювати окремий benchmark push, PR, schedule або fan-out. Повний,
крос-мовний, wall-time та нічний набір — наявні ручні стенди;
автоматизувати їх тільки після окремого дозволу власника.

ВІДТВОРЮВАНА ЦІНА. Первинна метрика — Cachegrind Ir/op на одному
конкретному гарячому шляху. Результат цілого CLI, включно із startup,
не є Ir/op. Потрібен ідентичний бінарник і matched контрольний дослід,
точна кількість операцій, не менше трьох парних повторів, fixture
SHA, SENS output parity, валідне pinned CPU/Valgrind/toolchain середовище.
Valgrind дає вимір інструкцій, не CPU cycles або wall-clock. Не
змішувати різні CPU, версії, профілі чи різні алгоритми.

Новий механічний інструмент scripts/check_perf_budget.py допускає
реальний пінований baseline, порівнює медіану різниці I refs з
limit_ir_per_op та друкує PERF-BUDGET-EXCEEDED з id, шаром, fixture,
фактичним бюджетом, перевищенням і командою відтворення. Неповний
baseline, synthetic, відсутній самодоказ, інше середовище та
неконтрольований startup — PERF-EVIDENCE-BLOCKED, а не PASS або
регресія. Він не визначає семантику. --self-test використовує
ВИКЛЮЧНО синтетичні числа й не створює доказів SENS.

СТАН ВПРОВАДЖЕННЯ. Немає ратифікованого виміряного бюджету на
конкретну гарячу операцію. Тому числовий поріг НЕ вигадуємо й
НЕ вмикаємо його у єдиний ci.yml перед калібровкою. Після виміру,
SENS parity і ратифікації підключаємо як друге ворота У ТОМУ Ж
workflow. Це явний недоведений етап, не тихий skip та не green perf.

КАНАРЕЙКИ КОСТИЛІВ. Для доменної ідентичності вже існує вузький
source-аудит scripts/check-domain-ladder-identity.py --check:
нуль десяткових рядкових посередників, з дозволеним лише зовнішнім
людським відображенням D24+. Це структурна перевірка, не заміна Ir/op.
Далі окремо калібрувати allocations/call та scans/call там, де очікується
бітмапа: тільки з власними затвердженими свідками, без загальних regex.
Борговий підсумок — сума перевищень по фіксованому порівнюваному корпусу;
не змішувати несумірні одиниці.

WALL-CLOCK. Реальний регрес — лише виміряний effect size із
довірчим інтервалом за незалежними ієрархічними серіями; використати
чинні bench-methodology/paired_effect.py та measurement-triad/verdict.py
із чесною міткою K–J-inspired, не повний Kalibera–Jones.

RATCHET. Збільшення бюджету — окремий коміт із попереднім і новим
числом, SHA доказу, причиною, issue та дозволом власника. Не
послаблювати бюджет під червоний тест. Для кожного PERF-BUDGET-EXCEEDED
обов'язкові чинні RED-класифікація, власник, перший поганий SHA
(або чіткий UNRESOLVED, що блокує), команда відтворення. Мовчазний
skip та прихований карантин заборонені.

Першоджерела методики: Valgrind Cachegrind manual,
https://valgrind.org/docs/manual/cg-manual.html ;
Kalibera–Jones, Rigorous Benchmarking in Reasonable Time,
https://doi.org/10.1145/2464157.2464160 .
