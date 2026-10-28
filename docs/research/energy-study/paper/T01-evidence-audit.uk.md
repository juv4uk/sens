# ENERGY-07 · T01: незалежний аудит допуску доказів (28.10.2026)

**Висновок: EVIDENCE_BLOCKED. Це не FASTER і не REPRODUCED.** Жодного виміру або закону SENS тут не змінено.

## Що перевірено в GitHub raw

- Шлях: benchmarks/language-energy-study/raw/T01-python-vs-javascript-8x4.json
- Git blob: **38f1a0e583c5960eafb304a5cb5b22862f36ccca**.
- Schema: sens-energy-study-raw/v1, T01-symbolic-recursion; **32 записані пари, 8 process_id, одна session_id** (session-5227). Мітка процесу — не доказ фізичної незалежності.
- Provenance: git_sha = not-a-git-checkout; OS = Linux 4.19.0-gvisor; governor = unknown; affinity = not-pinned.
- Parity: passed=true, але oracle_id = parity_check.py --selftest. Виміряні stdout кожного A/B запуску й reference-output SHA не записані. Самотест не посвідчує фактичний паритет запусків.
- У всіх 32 парах energy_not_measured=true; реальних джоулів немає.

**Сім об'єктивних блокерів:** SOURCE_SHA_UNPINNED_OR_MISMATCHED; PARITY_SELFTEST_IS_NOT_MEASURED_OUTPUT_PROOF; MEASURED_INPUT_NOT_PINNED; REFERENCE_OUTPUT_NOT_PINNED; MEASURED_OUTPUTS_MISSING; SESSION_TIMESTAMP_MISSING; INSUFFICIENT_INDEPENDENT_SESSION_EVIDENCE.

Це не доказ, що часові виміри були неправильні. Це доказ, що набору бракує provenance, перевірки виміряних виходів і незалежних сесій для confirmatory висновку. Старі секунди зберігаються як exploratory, а не як мовний рейтинг.

## Локальне відтворення без дорогих runners

    python3 -m unittest discover -s docs/research/energy-study/paper -p 'test_audit_corpus_evidence.py' -v
    python3 docs/research/energy-study/paper/audit_corpus_evidence.py \
      benchmarks/language-energy-study/raw/T01-python-vs-javascript-8x4.json \
      --source-sha "$(git rev-parse HEAD)"

Очікувано: status=BLOCKED, exit 2; energy=ENERGY_NOT_MEASURED, independent_reproduction=NOT_REPRODUCED. Git SHA checkout не можна підставляти за відсутній SHA реально виміряної програми.

Позитивна *синтетична* структура дає лише STRUCTURE_ONLY, навіть якщо заявлено 4 сесії, 2 дні, 8 process_id та ідентичні stdout. Валідація записів **не доводить**, що процеси дійсно запускались, що сесії фізично незалежні, що p-value/CI коректні, що сенсор калібрований або що робота реплікована.

## Методологія: прочитані джерела й конкретні наслідки

- [Pereira et al. 2017, SLE, §2](https://doi.org/10.1145/3136014.3136031): міжмовні порівняння вимагають реалізацій порівнюваних задач. Результати фактичних запусків треба верифікувати, а не посилатись тільки на selftest.
- [Pereira et al. 2021, SCP, вступ](https://doi.org/10.1016/j.scico.2021.102609): точно визначені задачі, алгоритми й незалежна перевірка на Rosetta Code; наш T01 — exploratory single-task, не універсальний рейтинг.
- [Kalibera & Jones 2013, ISMM, §3](https://doi.org/10.1145/2464157.2464160): різні рівні експериментальної варіації; 8 process_id в одній сесії не замінюють незалежні сесії.
- [Wilkinson et al., FAIR 2016](https://doi.org/10.1038/sdata.2016.18): машинна перевірність і повторне використання потребують provenance, алгоритмів і workflow поряд із raw.
- [Green Software Foundation, SCI](https://greensoftware.foundation/standards/sci/): визначена функціональна одиниця R; без реальної енергії E та необхідних I/M не розраховувати SCI або CO₂e.

**Наступна залежність:** #6287 — у **нових** прогонах зберігати фактичні stdout A/B, exact source SHA, input SHA, session timestamps і негативні результати; #6290 — окрема статистична перевірка; #6291/#131 — незалежна реплікація. Старий raw заднім числом не виправляти.
