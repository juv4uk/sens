# Аудит злиття гілок бенчмарків і документації — 12.10.2026

**Перевірений main:** `0d12ba37e0e3927433835d17caffea0d3196598a` (SHA на момент порівняння).

## Висновок

Історія Git не повністю зведена в main. Це не тотожне втраті всіх змін: кілька гілок мають власні старі коміти, хоча їхні поточні скрипти й документація вже збігаються з main; інші джерела збережені в неактивних історичних архівах. Не можна зливати такі гілки цілком: це могло б відкотити актуальні README, реєстр бенчмарків, інвентар T5 або канонічну бінарну поверхню.

## Обсяг перевірки

- GitHub пошук гілок за `bench` повернув **208 refs**. Кожен ref порівняно з main через commit comparison; більшість — лише застарілі гілки без комітів попереду main.
- Повний all-time branch census від 11.10.2026 раніше фіксував **4 133 live refs / 4 034 distinct heads**: 1 256 були в ancestry main, а 2 877 потребували content review. Це історичний знімок, не актуальний лічильник і не доказ того, що всі зміни інтегровані.
- Перевірка Git-ancestry відповідає на питання, чи досяжні коміти, а порівняння файлів — чи залишився корисний вміст поза main. Обидва критерії потрібно вести окремо.

## Вміст уже на main або в архіві

- `research/bench-triad-replay-20261010`: Cargo/bench-код, verdict-тести й workflow збігаються з main; `bench.json` та згенерований `benchmarks/README.md` у гілці — старі знімки.
- `research/bench-paired-wall-replay-20261010`: методологічний README, manifest, paired-wall runner, тести й workflow побайтно збігаються з main; branch registry та T5 inventory старі.
- `research/t22-benchmark-main-replay-20261011`: T22-скрипт, README та manifest збігаються з main; старі копії registry workflow, згенерованого індексу й migration inventory не слід повертати поверх актуальних.
- `research/benchmark-effect-ci-20261009`: paired-effect runner, тести й документація вже є на main; відрізняються старі workflow/index snapshots.
- `research/archive-bench-1995-20261011-gpt6`: identity-carrier README і TSV є в `research/domain-archive/20261011/pr1995`; extension metadata на main новіша.
- `perf/packed-vs-visible-hosted-bench-20261009` і rebased-варіант: поточні runner/docs/manifest є в активному `benchmarks/packed-vs-visible`; старі SHA джерел зафіксовані в `docs/research/benchmark-history-20261011/pr5192`. Не замінювати поточні файли старими копіями.
- `perf/74-*`: branch script використовує стару Lisp-поверхню та назви пакунків. Поточний `scripts/benchmark-semantic-registry-read.lisp` на main вже переведений у канонічну бінарну форму; не переносити стару реалізацію назад.
- workflow парної статистики `staging/benchmark-paired-effect-ci-after-l0-20261009` неактивний; її джерело збережено як `.source.txt` у `research/domain-archive/20261011/pr5229-bench`. Реальний код оцінки й тестові оракули вже на main.

## Знайдені source gaps, що потребують збереження

Окремі benchmark-refs мають історичні джерела, яких не знайдено за початковим шляхом на main:

- `research/encoder-same-input-bench-20261010`: `.github/workflows/encoder-same-input-bench.yml`, blob SHA `10e8972cf277eccb10a8f1065bf8f16e56970dd5`.
- `verify/362-fused-utf8-benchmark`: workflow blob `64f7bbcfc7e8a87d97fd4b1caf427d743e9529fa`; стара `lib/utf8.lisp` — `c1c5e5fa3e52f9d02aeb946615937c2055607cfa`; profiler — `df491da7e517126b46a8426ab1fec32587d838c4`; witness — `8d31811d36843c411bab41647eceac44bb695590`; current-semantic-slice shell helper — `0e56a24af1c1a49875c7acb9d58e4eff71861b1d`.
- `verify/362-production-readfile-benchmark`: workflow blob `80c04bb1f4059af2e5b80cbc48bf73c2debd22fe`; стара `lib/fs.lisp` — `11dcc2ce97c03252f694dfe80e2581c65dd5ad11`; profiler — `6f6aa9fc02abc1bcf0eac4e02f289d28d934931d`. Суміжні refs `verify/362-readfile-current-main-benchmark` і `verify/596-readfile-benchmark` є близькими варіантами цього ж історичного експерименту.

Ці SHA — походження історичних джерел, а не свідчення, що старий код досі правильний. Ці експерименти використовували назви `my-lisp` і старі API. Їх не можна повертати в активний CI без адаптації до поточного main, незалежного оракула та повторного запуску.

## Політика інтеграції

1. Працюємо лише в main; нових гілок не створюємо.
2. Поточний код, тести та README залишаємо як є, якщо вони вже новіші за donor.
3. Унікальні історичні експерименти зберігаємо source-only з точними blob SHA, origin ref і шляхом; файли мають суфікс `.source.txt`, щоб не запускатися автоматично.
4. Для відновлення в активний benchmark спочатку потрібні адаптація до чинного контракту, byte/parity gate, correct-workload oracle, відтворювані raw samples і перевірений workflow.
5. Не можна оголошувати «всі гілки злиті» за самим фактом наявності архіву. Архів зберігає знання, але не робить старий commit ancestor main і не означає, що експеримент зараз runnable.

