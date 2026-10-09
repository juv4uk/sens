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
