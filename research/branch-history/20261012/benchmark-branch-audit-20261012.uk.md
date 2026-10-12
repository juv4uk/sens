# Аудит злиття гілок бенчмарків і документації — 12.10.2026

**База порівняння main на початку аудиту:** `0d12ba37e0e3927433835d17caffea0d3196598a`. Звіт і source-only архів зафіксовано наступними комітами на main; вони не змінюють активний runtime чи benchmark-поверхню.

## Висновок

**Ні, не всі branch histories злиті в Git ancestry main.** Але частина розбіжних refs має лише застарілі знімки, а її актуальний скрипт/тест уже збігається з main. Інші гілки мають унікальні історичні джерела, які не можна безпечно повернути в активний код, тому їх збережено точно й неактивно. Примусове злиття старого дерева могло б відкотити новіший README, benchmark registry, T5 inventory або канонічну бінарну поверхню.

## Обсяг перевірки

- GitHub branch search за `bench` дав **208 refs**; кожен із них порівняний з main.
- Search за `benchmark` дав ще **22 refs** (із перетинами попереднього списку); усі порівняні з main.
- Search за `docs` дав **64 refs**; усі порівняні з main.
- Додатково перевірені README-, performance- й measurement-related refs, зокрема `fix/4250-readme-current-triple-and-reference-20261009` та `fix/5520-measurement-triad-repro-20261010`.
- Історичний all-time census від 11.10.2026 фіксував **4 133 live refs / 4 034 distinct heads**: 1 256 у ancestry тодішнього main і 2 877 із tree, що потребував content review. Це знімок на 11.10, не актуальний лічильник і не доказ повної консолідації всіх гілок репозиторію.

## Що вже зведено за вмістом

- `research/bench-triad-replay-20261010`: Cargo/bench-код, verdict-тести й workflow побайтно збігаються з main. У гілці старі `bench.json` і generated `benchmarks/README.md`.
- `research/bench-paired-wall-replay-20261010`: README, manifest, paired-wall runner, тести й workflow збігаються з main; registry snapshot і T5 inventory старі.
- `research/t22-benchmark-main-replay-20261011`: T22-скрипт, README та manifest збігаються з main; старі копії registry workflow, generated index і T5 inventory не слід повертати поверх актуальних.
- `research/benchmark-effect-ci-20261009`: paired-effect runner/тести/документація вже є на main; старими лишилися workflow та generated index.
- `research/archive-bench-1995-20261011-gpt6`: identity-carrier README та TSV є в `research/domain-archive/20261011/pr1995`; metadata extension на main новіша.
- `perf/packed-vs-visible-hosted-bench-20261009` і rebased-варіант: активні runner/docs/manifest є в `benchmarks/packed-vs-visible`; попередні джерела зафіксовані в `docs/research/benchmark-history-20261011/pr5192`.
- `staging/benchmark-paired-effect-ci-after-l0-20261009`: статистичний код, документація та тестовий оракул уже є на main; workflow архівовано як неактивний source під `research/domain-archive/20261011/pr5229-bench`.
- `fix/5520-measurement-triad-repro-20261010`: triad manifest збігається з main; відрізняється старий generated benchmark index.
- README-гілки `refresh-readme-docs-d1-d8` та `fix/4250-readme-current-triple-and-reference-20261009` — старіші дерева документації. У другій гілці contract test і workflow побайтно збігаються з main; її README/API коротші й застаріліші. Не зливати ці snapshots поверх новіших документів.

## Розбіжні branch histories, знайдені в benchmark-кластері

У refs нижче є коміти поза ancestry перевіреного main, але це **не є автоматичною командою робити merge**:

- `perf/packed-vs-visible-hosted-bench-20261009`, `perf/packed-vs-visible-hosted-bench-rebased-20261009`
- `perf/74-readfile-benchmark-harness-replay`, `perf/74-real-readfile-benchmark-harness`, `perf/74-real-readfile-benchmark-harness-current`
- `research/archive-bench-1995-20261011-gpt6`, `research/bench-paired-wall-replay-20261010`, `research/bench-triad-replay-20261010`, `research/benchmark-effect-ci-20261009`, `research/encoder-same-input-bench-20261010`, `research/t22-benchmark-main-replay-20261011`
- `staging/benchmark-paired-effect-ci-after-l0-20261009`
- `verify/362-fused-utf8-benchmark`, `verify/362-production-readfile-benchmark`, `verify/362-readfile-current-main-benchmark`, `verify/596-readfile-benchmark`

Критично: більшість основного вмісту з цього списку вже є на main або в історичному архіві. Для трьох груп нижче виявлено унікальні source blobs, які не було знайдено за активними оригінальними шляхами на main.

## Унікальні source gaps: збережено й перевірено

Одинадцять source blobs із чотирьох груп збережено під суфіксом `.source.txt` у [source recovery archive](benchmark-unique-source-recovery/README.uk.md); маніфест: [manifest.json](benchmark-unique-source-recovery/manifest.json). **11/11 архівованих файлів підтверджені побайтним збігом вихідного й архівного Git blob SHA.**

- `research/encoder-same-input-bench-20261010`: історичний `.github/workflows/encoder-same-input-bench.yml`, SHA `10e8972cf277eccb10a8f1065bf8f16e56970dd5`.
- `verify/362-fused-utf8-benchmark`: workflow `64f7bbcfc7e8a87d97fd4b1caf427d743e9529fa`, стара `lib/utf8.lisp` `c1c5e5fa3e52f9d02aeb946615937c2055607cfa`, profiler `df491da7e517126b46a8426ab1fec32587d838c4`, shell helper `0e56a24af1c1a49875c7acb9d58e4eff71861b1d` та witness `8d31811d36843c411bab41647eceac44bb695590`.
- `verify/362-production-readfile-benchmark`: workflow `80c04bb1f4059af2e5b80cbc48bf73c2debd22fe`, стара `lib/fs.lisp` `11dcc2ce97c03252f694dfe80e2581c65dd5ad11` і profiler `6f6aa9fc02abc1bcf0eac4e02f289d28d934931d`. Refs `verify/362-readfile-current-main-benchmark` і `verify/596-readfile-benchmark` мають ті самі вихідні SHA; дублікати не зберігали вдруге.
- `perf/74-readfile-benchmark-harness-replay`: стара workflow-версія `bf642a5830c427118206661e0a17521cd13bb922` і Lisp-скрипт `9e1606b65d795e4f095a31518e29b696615809e4`. Refs `perf/74-real-readfile-benchmark-harness` та `perf/74-real-readfile-benchmark-harness-current` мають ті самі два blob SHA.

Архівні гілки використовували старі назви `my-lisp`/старі API. Копії збережено лише для доказового відновлення; жоден старий workflow не активовано, старі `lib/utf8.lisp` та `lib/fs.lisp` не записувалися поверх нових main-файлів.

## Політика

1. Працювати тільки в main; нових гілок не створювати.
2. Не переносити старий generated index чи inventory поверх актуальних.
3. Історичний код зберігати як source-only із точним SHA та origin ref, якщо він не проходить чинну перевірку.
4. Щоб відновити archived benchmark як активний, потрібні адаптація до чинного контракту, перевірка byte/parity, незалежний oracle, відтворювані raw samples і успішний актуальний CI.
5. **Архів не робить коміти гілки ancestor main.** Отже, чесний статус зараз: значний benchmark-вміст консолідовано на main, унікальні історичні джерела збережені; твердження «всі гілки всього репозиторію злиті» не підтверджене.
