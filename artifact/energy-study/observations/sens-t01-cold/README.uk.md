# SENS T01: реальне process-cold спостереження з GitHub-hosted runner

Дані з **дійсного** [GitHub Actions run 40724311685 / job 122943309505](https://github.com/juv4uk/sens/actions/runs/40724311685/job/122943309505), а не симуляція. Окремий архів зберігає п'ять рядків із журналу до завершення триденного терміну зберігання GitHub artifact `sens-t01-cold-raw` (artifact ID `12832740473`). Файл JSON не має права називатися незалежною реплікацією або результатом порівняння мов.

- Точний SHA checkout: `1a4635d8fc812bb889e09a01dbb79ebdcdb274f5`; SENS **0.42.3**.
- Джерело MEASURE: Git blob `ecaead4c0f7ffa881b936396bdececbd4f5b2153` (`t01_fib_measure.lisp`, fetched during job); VERIFY blob `93d82a343bd90b13fb61dd9188110578e99821ef`.
- Функціональна одиниця: **один процес SENS** з наївним Fibonacci(24) → точне stdout `46368`.
- Linux 6.17.0-1022-azure x86_64, AMD EPYC 7763; Zig 0.16.0, Rust 1.99.0.
- Вимір: GNU `/usr/bin/time` wall seconds і peak child RSS KiB, **5 запусків в одній сесії**. Програма стартувала як новий процес кожен раз, але CPU/cache уже прогрілися попередньою верифікацією.
- Фізичних джоулів немає: `ENERGY_NOT_MEASURED`; без RAPL і без PUE/TDP-оцінки. Медіана (дескриптивна) 0.52 с і 22076 KiB; **95% ДІ не обчислювати як для п'яти незалежних сесій**.
- Важливий негативний результат: у **тому самому** job `run_study.py` позначив 32/32 T01 pairs як `PARITY_FAILED`, `pairs=0`. Це **інша гілка вимірювання**, її статус не можна підмінити цими п'ятьма прямими вимірами й оголосити comparative PASS.

## Перевірка (offline, без GitHub runners)

```sh
cd artifact/energy-study/observations/sens-t01-cold
python3 verify.py
python3 -m unittest -v test_verify.py
```

`verify.py` перевіряє заморожені raw, SHA, функціональну одиницю, відсутність енергії/CI/переможця та одну незалежну сесію. Це тест **походження фізичних даних**, не нова реалізація семантики SENS. Для реальної незалежної реплікації треба інші сесії/машини, валідний SENS-output parity і пари інших мов; не трактувати цей snapshot як final estimate.

## Наукові підстави

- Kalibera & Jones (ISMM 2013), DOI `10.1145/2464157.2464160`: досліди з недетермінованими системами потребують повторів на різних рівнях; п'ять процесів в одному контексті не означають п'ять незалежних машин/сесій.
- Pereira et al. (SLE 2017), DOI `10.1145/3136014.3136031`: енергія, час і пам'ять — окремі результати; час **не** є виміром Дж.
- Green Software Foundation SCI (ISO/IEC 21031:2024): https://greensoftware.foundation/standards/sci/ — чітка функціональна одиниця та межа системи. Тут одиниця одна SENS-програма, але SCI **не обчислюється**.
- FAIR, Wilkinson et al. (2016), DOI `10.1038/sdata.2016.18`: позначений provenance (SHA, апаратний профіль, маршрут) для повторного використання.
