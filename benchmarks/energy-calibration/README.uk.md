# #6289 · ENERGY-04 — протокол фізичної калібровки RAPL (дослідницький кандидат)

> **Не є результатом калібрування, сертифікатом вимірювача, статистичним висновком або релізним гейтом.** Новий скрипт перевіряє **лише структуру отриманих сирих записів**. Він **не звертається до датчика**, не запускає SENS та не обчислює рейтинг мов. Синтетичні unit-тести не означають, що фізична енергія виміряна.

## Межі та залежності

- **#6275** володіє реалізацією RAPL-збирача. Не дублювати reader/collector із `energy_uj` або його unit-тести.
- **#6276** володіє фізичною роботою hot SENS. Не замінювати її пустими циклами чи зовнішнім SENS semantic oracle.
- **#6286** визначає майбутню пререгістрацію; поки вона не заморожена, ця схема є *exploratory*. **#6290** відповідає за статистичні ДІ й гіпотези.
- Для AB/BA потрібні дві бінарні реалізації **тієї самої функціональної одиниці** й незалежний результат `output_sha256`; рівність дайджестів є тільки **технічним контролем**, не доказом семантики SENS. Справжні закони SENS доводяться SENS-позитивними й SENS-негативними свідками через Zig/T5M.
- RAPL CPU **package** включає системну активність і не є джоулями конкретного процесу, окремого виклику або всієї стіни/розетки. Не додавати PP0/DRAM до package.

## Збирання на Linux bare metal (не виконано цим PR)

1. Прочитати `/sys/class/powercap/intel-rapl:*/name`; обрати **один** `package-*` (а не дочірній `core`/`dram`/`psys`). Перевірити доступ до `energy_uj` і `max_energy_range_uj`, записати справжній абсолютний шлях і діапазон. За браку файлу/прав доступу — **`ENERGY_NOT_MEASURED`**, без жодних J/системного рейтингу.
2. Зафіксувати точний 40-hex `source_sha` та `collector_sha`, `binary_sha` A і B, `input_sha`, хеш **фактичного виходу**, функціональну одиницю й кількість одиниць за запуск; `CPU`, `kernel`, `OS`, governor, температура, ідентифікатор фізичної машини, час UTC, афініті/турбо/BIOS у лабораторному журналі. Створити окремі сесії в різні години або дні; **два різні `session_id` не доводять незалежність**.
3. Виміряти накладні витрати читання датчика `read_overhead_ns` з повторів **тим самим API** і контроль idle у кожній сесії. Зберігати **сирі** `start_uj`, `end_uj`, `elapsed_ns`, `peak_rss_bytes`, `exit_code` кожного запуску; ніяких TDP-апроксимацій енергії. Idle package J записуються окремо; різницю із зайнятим пакетом не називати безпосередньою енергією програми.
4. Для кожної сесії виконати два блоки `AB` і `BA`, по два самостійні запуски в кожному; фіксувати порядок **до** запуску, а не підбирати за отриманим результатом. Реальна рандомізація/баланс між сесіями має бути зафіксована в пререгістрації. Сам цей валідатор перевіряє лише формальні назви/послідовність.
5. Для можливості виключити два або більше переповнень лічильника вкажіть **консервативну незалежно документовану верхню межу фізичної потужності пакета**, `documented_max_package_power_w`, та `power_ceiling_reference`. Це **не** оцінка енергії із TDP. За відсутності доведеної межі/документа — відмовитися від валідації енергії; **структурний валідатор не може перевірити правдивість посилання**. Безпечна умова для інтервалу `elapsed_ns`: `upper_W × elapsed_ns < max_energy_range_uj × 1000`. Додатково дельта має бути додатною й не перевищувати фізичну верхню межу. Не припускати, що один `end >= start` означає нуль переповнень. Якщо інтервал завеликий — зменшити розмір пакета або використати валідовану частішу вибірку #6275.
6. Якщо доступний **окремо відкалібрований зовнішній ватметр**, зібрати незалежні raw samples і відокремити socket/package від wall-power; цей валідатор їх **не корелює** й не видає статусу `WATTMETER_CALIBRATED`.
7. Оцінювати шум/дрейф, температури/гоvernor, фон, повтори сесій та інтервали невизначеності в #6290. **Не** звітувати «достовірна перевага» на основі `STRUCTURAL_PASS`.

## Формат та запуск

Файл JSON — **raw запис**, не новий центральний реєстр. Не комітити машинні приватні дані без перевірки. Схема `sens-energy-calibration/v1` (обов'язкові поля у `check_calibration.py`). Нижче **синтетичний фрагмент**; це *не* приклад фізичних показань, він свідомо не містить справжніх SHA чи датчика.

```json
{
  "schema": "sens-energy-calibration/v1",
  "mode": "SYNTHETIC",
  "provenance": {
    "source_sha": "<40 lowercase hex>",
    "collector_sha": "<40 lowercase hex>",
    "input_sha": "<40 lowercase hex>",
    "machine_id": "<study pseudonym>",
    "cpu_model": "<recorded CPU>",
    "os_release": "Linux", "kernel": "<uname -r>", "governor": "<recorded governor>",
    "sensor_name": "package-0", "sensor_path": "/sys/class/powercap/intel-rapl:0",
    "energy_unit": "microjoule", "clock": "monotonic_ns",
    "functional_unit": "<verified units of identical work>",
    "recorded_at_utc": "2026-10-28T12:00:00Z",
    "power_ceiling_reference": "<independent physical bound source>",
    "documented_max_package_power_w": 75,
    "max_energy_range_uj": 100000000,
    "sensor_access_confirmed": false
  },
  "sessions": []
}
```

Повний **вигаданий позитивний** формат із двома сесіями генерується функцією `record()` у `test_check_calibration.py`; **НЕ** публікувати його як спостереження. Справжній запис без доступу до датчика з `sensor_access_confirmed=false` повертає тільки `ENERGY_NOT_MEASURED`, exit 2.

```bash
(cd benchmarks/energy-calibration && python3 -m unittest -v test_check_calibration.py)
python3 benchmarks/energy-calibration/check_calibration.py --help
python3 benchmarks/energy-calibration/check_calibration.py /path/to/calibration-raw.json
```

Результат `STRUCTURAL_PASS` означає лише, що необхідні **метадані присутні**, локальний паритет дайджестів узгоджений, одне переповнення математично припустиме під **задекларованою** верхньою межею та AB/BA записані. Він завжди супроводжується **`PHYSICAL_CALIBRATION_NOT_VERIFIED`**; навіть `mode=PHYSICAL` — неперевірене твердження джерела, а не автоматично фізичне свідчення. Валідатор **не** перевіряє незалежність датчиків, компіляторний DCE, автентичність SHA, реальні показання, фізичну верхню межу чи природу хешованого виходу. Відмови — JSON, `status=CALIBRATION_REJECTED` або `ENERGY_NOT_MEASURED`, exit 2. Справжні підсумки енергії / SCI тут взагалі не обчислюються.

## Методологічні джерела та межі застосування

| Вивчене джерело | Що саме використано тут |
| --- | --- |
| [Linux kernel Power Capping Framework](https://cdn.kernel.org/doc/html/latest/power/powercap/powercap.html) | Ієрархія package/subzone і точні `name`, `energy_uj`, `max_energy_range_uj`; не виводити process J із package. |
| Pereira et al. [SLE 2017](https://doi.org/10.1145/3136014.3136031), [конференційна анотація](https://conf.researchr.org/details/sle-2017/sle-2017-papers/30/Energy-Efficiency-across-Programming-Languages-How-do-Energy-Time-and-Memory-Relat) | Структура порівняння енергія/час/пам'ять на кількох задачах; **не** переносити їхній рейтинг на SENS. |
| Pereira et al. [Science of Computer Programming 2021](https://doi.org/10.1016/j.scico.2021.102609), [авторський препринт](https://haslab.github.io/SAFER/scp21.pdf) | Паритет задач/контрактів між реалізаціями та відокремлення енергії, часу й пам'яті; наш checker — тільки фізична підготовка. |
| Kalibera & Jones [ISMM 2013](https://kar.kent.ac.uk/33611/) | Повторні сесії, кілька джерел варіації, перевірка ефекту з невизначеністю; **цей скрипт не є K–J оцінювачем**. |
| Wilkinson et al. [FAIR 2016](https://pubmed.ncbi.nlm.nih.gov/26978244/) | Збереження машинозчитуваних raw даних, SHA, метаданих і походження для незалежного повтору; у цьому PR **немає** депозиту/DOI. |
| [Green Software Foundation SCI](https://greensoftware.foundation/standards/sci/) | Функціональна одиниця й системна межа; **SCI/CO₂e не обчислювати**, поки немає окремих E, I, M та R. |

**Стан фізичного стенда для цього артефакту:** `ENERGY_NOT_MEASURED`; `PHYSICAL_CALIBRATION_NOT_VERIFIED`; незалежного ватметра та реальних RAPL-проб немає. Результати синтетичних unit-тестів не замінюють цей статус.