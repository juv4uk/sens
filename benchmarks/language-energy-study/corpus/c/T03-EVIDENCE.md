# ENERGY-02 / T03 C: незалежний фізичний паритет, не рейтинг

**Claim:** [#6287 comment 6472776684](https://github.com/juv4uk/sens/issues/6287#issuecomment-6472776684). **Зона:** тільки нові `corpus/c/t03_parse.c`, `test_t03_parse.py` і цей evidence. Заморожений `corpus/manifest.json` **не змінено**.

## Функціональна одиниця

T03 `T03-parsing-text`: згенерувати `N` рядків `k{(i*7919)%1000}=v{i}`; **розділити кожен рядок за першим `=`**; відсортувати отримані ключі у лексикографічному порядку зі збереженням дублікатів; вивести SHA-256 UTF-8 для `"\n".join(keys)`. Це фізична перевірка спільної постановки, **не семантичний закон SENS**.

- **VERIFY_SIZE:** `TASK_LINES=50`.
- **MEASURE_SIZE:** `TASK_LINES=5000` (заморожений manifest).
- Програма вимагає `TASK_ID=T03-parsing-text`; відмовляє на відсутніх, нульових, від'ємних та некоректних розмірах, на `>1000000` і переповненні. Результат — рівно один hex digest.
- C11 / `-O2 -Wall -Wextra -Werror`, OpenSSL EVP SHA-256 (`-lcrypto`). Компіляція **поза** процесом, якщо міряти холодний виконуваний файл; жодних даних про таке вимірювання поки немає.

## Локально виконані команди й сирі результати

Контрольна машина виконавця: Linux x86_64 kernel `6.18.55`; `cc (Debian 14.2.0-19) 14.2.0`; OpenSSL `3.5.5`; Python `3.13.5`. **Це не лабораторний фізичний стенд.**

```bash
cc -std=c11 -O2 -Wall -Wextra -Werror t03_parse.c -lcrypto -o t03_parse
TASK_ID=T03-parsing-text TASK_LINES=50 ./t03_parse
# 1aeafd4300d8543843748d3c2e7ba9621993a0f2abd015d0b6ba74795bab5589
TASK_ID=T03-parsing-text TASK_LINES=5000 ./t03_parse
# 3da92d0adfb229858ffb055f874961d3ca17e67f809ad5cab14550377e3af25d
TASK_ID=T03-parsing-text TASK_LINES=1001 ./t03_parse
# 7768247dffa30c5468dde7e27297d8acea6c501fc535ed8c8b03841d25104931
python3 -m unittest -v test_t03_parse.py
# Ran 6 tests in 0.295s
# OK
TASK_ID=T03-parsing-text TASK_LINES=0 ./t03_parse
# exit=2 ; stdout_bytes=0 ; stderr=T03_INPUT_INVALID ...
```

У тестах Python окремо обчислює frozen `parity_check.ref_T03` для `N=50/5000/1001/1` та перевіряє точний байтовий збіг. Негативні контролі: змінений генератор `7919→7920`, хибне видалення дублікатів, 10 некоректних input-випадків.

**Git blob SHA файлів локального тесту = GitHub blob SHA гілки:** C `ea9ae76087baff00cd546bd7ed662efdb6382795`; тест `dc3207c365d67debf3a835f2e9d9f92e7a66ebba`. Цим звірено *вміст*, а не саму наявність коміту.

## Негативний результат / блокер порівнянності

Станом на аудит `main`, `corpus/javascript/t03_parse.mjs` **не парсить** рядки `key=value`: робить `keys.push('k' + ((i * 7919) % 1000))` і сортує вже згенеровані ключі. Так отримується той самий SHA-256, **але інша функціональна робота** (без побудови й розбору рядка). Це **FUNCTIONAL_WORKLOAD_PARITY_BLOCKED** для остаточного T03 timing / energy ranking. Не редагую baseline іншого власника в цьому PR. Потрібне узгоджене виправлення окремою задачею до confirmatory вимірів.

### Методологічні підстави (перевірені джерела)

- [Pereira et al., SLE 2017](https://doi.org/10.1145/3136014.3136031): 27 мов / 10 задач, порівняльні енергія, час, пам'ять; час не замінює енергію. Тут спершу фіксуємо еквівалентну функціональну роботу.
- [Pereira et al., SCP 2021](https://doi.org/10.1016/j.scico.2021.102609): strict problem solutions і незалежна перевірка на Rosetta Code; результат одного checksum не гарантує тотожність реалізації.
- [Kalibera & Jones, ISMM 2013](https://doi.org/10.1145/2464157.2464160): рівні повторів і статистична невизначеність; 6 функціональних unit tests **не є** доказом різниці в швидкості.
- [Wilkinson et al., FAIR 2016](https://doi.org/10.1038/sdata.2016.18): машинна повторюваність потребує доступних вхідних даних, коду та provenance — зафіксовано команди, версії й SHA.
- [Green Software Foundation, SCI](https://greensoftware.foundation/standards/sci/): функціональна одиниця R й фізична енергія E; тут **ENERGY_NOT_MEASURED**, жодних J / CO₂e / рейтингу.

**Не доведено:** фізична енергія, час, peak RSS, реальна оптимізаційна однаковість C/JS/Python, придатність T03 для рейтингів, SENS-реалізація, незалежна реплікація на контрольованому залізі.
