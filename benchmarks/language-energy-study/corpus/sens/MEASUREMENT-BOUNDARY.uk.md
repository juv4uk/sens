# Межа вимірювання нативного SENS · #6287

**Статус:** exploratory only. Це НЕ доказ переваги SENS і НЕ заміна позитивних/негативних SENS-свідків.

## Відтворена проблема до цього патча

- [Actions run 40718541814, job 122922781437](https://github.com/juv4uk/sens/actions/runs/40718541814/job/122922781437), `main@821df8da1e5c78f3fd35aa7edb69dbe5a5fe864c`: SENS 0.42.3 збирається, T01 карбується у 124-байтовий файл, але нативний паритет **RED** (`PARITY_FAILED exit=1`, `Dn comparison requires exactly two same-domain numeric values`). Немає допустимої для ранжування T01-проби.
- [Manual SENS D6 job 122922468383](https://github.com/juv4uk/sens/actions/runs/40718451952/job/122922468383): `/usr/bin/time -v` показав wall 1.11/1.09/1.10 секунди, maximum RSS 46668/48668/48168 KiB. Ця вже існуюча команда `ci.yml` приховувала stdout програми через `grep` і не публікувала перевірку результату, тому час/RSS лише діагностичні. Ці дані не є «виміром T01».

## Що робить новий незалежний інструмент

`measure_verified.py` запускає **вже зібраний** нативний SENS із **вже закарбованим** .sens файлом як окремий процес; компіляція/карбування не входять у виміряну часову межу, cold startup входить. Він вимагає рівно одного stdout-рядка, byte-exact збігу з наперед перевіреним очікуванням, exit code 0, скінченний додатний wall time із GNU time та додатний kernel-reported peak RSS. Кожен незалежний запуск записує raw; перша помилка зупиняє прийняття, повертає exit 1 і стан `BLOCKED_PARITY_OR_MEASUREMENT`. Таймаут завершує цілу групу процесів, без безмежних повторів (1–5, не більше 120 секунд на пробу).

Не записує 0 J, не робить TDP→J, ніколи не приписує енергію процесу RAPL package: `energy_status=ENERGY_NOT_MEASURED` та `energy_joules=null`. Навіть `EXPLORATORY_OUTPUT_VERIFIED` стверджує лише відповідність stdout/exit на заявленому вході, **не** доводить фактичне число внутрішніх операцій або семантику SENS.

Метадані raw JSON: Git HEAD full SHA, SHA-256 бінарника і програми, команда, hostname-free OS/arch, таймер, expected output, межа timeout, кожен wall_s/RSS/exit/stdout, відмови, незмінні метрологічні обмеження. Немає вимоги запускати Python як SENS-семантичний оракул.

## Запуск після підтвердження SENS-свідка та frozen output

У GitHub-hosted Linux із `/usr/bin/time` і зібраним нативним `target/release/sens`:

```bash
python3 -m unittest discover -s benchmarks/language-energy-study/corpus/sens -p 'test_measure_verified.py' -v
python3 benchmarks/language-energy-study/corpus/sens/measure_verified.py \
  --binary "$PWD/target/release/sens" \
  --program "$PWD/path/to/verified-program.sens" \
  --expected '10' --task-id 'D6-existing-verified-workload' \
  --repo-root "$PWD" --runs 3 --timeout-s 30 \
  --output "$RUNNER_TEMP/sens-native-raw.json"
```

**Число `10` у прикладі не є доведеним еталоном!** Спочатку запуск на справжньому SENS має дати саме такий вихід та окреме позитивне/негативне нативне свідчення. Не підставляти очікування з Python для встановлення законів мови. T01 із наведеного Actions логу **зараз BLOCKED** — до виправлення T01 іншою робочою групою цей інструмент не створить з нього допустимих проб.

## Обмеження

Пік RSS GNU time стосується timed child, не гарантовано всього дерева підпроцесів. Точність секундного поля GNU time — 0.01 с: 0.00 s відхиляємо; коротші завдання потребують більшої функціональної одиниці. Shared runner, кеш, governor, фонове навантаження і відсутність незалежних сесій не дозволяють confirmatory inferential rating. Для рейтингу потрібен preregistered корпус T01–T09, підтвердження рівної фактичної роботи на MEASURE_SIZE, парні блоки AB/BA, статистика між сесіями, інший фізичний стенд та RAPL/калібрований wattmeter для енергії.

## Джерела та обґрунтування

- Pereira et al., 2017, *Energy Efficiency across Programming Languages* — енергія, час і пам'ять є різними показниками, порівнювати треба коректну однакову роботу: https://doi.org/10.1145/3136014.3136031
- Pereira et al., 2021, *Ranking programming languages by energy efficiency* — обережність узагальнення від реалізацій/набору задач до рейтингу мов: https://doi.org/10.1016/j.scico.2021.102609
- Kalibera & Jones, 2013, *Rigorous Benchmarking in Reasonable Time* — багаторівнева мінливість, незалежні запуски/сесії, ДІ: https://doi.org/10.1145/2464157.2464160
- Wilkinson et al., 2016, FAIR — сталі ідентифікатори, походження raw й машинне відтворення: https://doi.org/10.1038/sdata.2016.18
- Green Software Foundation, SCI — лише явна функціональна одиниця та визначена системна межа, без вигаданих вуглецевих/енергетичних значень: https://greensoftware.foundation/standards/sci/
