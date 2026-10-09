# D10 — із захоплень до перевірюваних семантичних законів (2026-10-09)

**Статус:** RESEARCH / UNRATIFIED; **це не зміна канонічного інвентарю**. Авторитет: #4012, #4013, #4162, #4182, #4301, #4463. Машиночитаний матеріал: `knowledge/d10-hobbies-source-laws-v1.json`.

## Мотивація

Донори охоплюють астрономію та астрономічний час, механіку, маятники/хронометрію, дискретні та аналогові обчислення, радіо, FPGA, музику та акустику. Уже відібрані D10 закони Паніні/сандгі й алгебра розмірностей зберігаються: дублювати `RESOLVE-PRATYAHARA`, `APPLY-SANDHI` або `SCIENCE-ADD-DIMENSION` не потрібно. Тому цей пакет не пропонує жодного нового бітового коду.

## Реальні джерела — source-pinned

| Напрям | Донор і точний blob SHA | Нова постановка |
|---|---|---|
| Астрономія/час | `juv4uk/maitreya8/src/swe/swedate.c` — `cf2c83a7bc38c086d2fae14cc80b382a05a35c84` | календар ↔ JD, опівдні цілочисельний JD; явна календарна шкала |
| Орбітальна механіка | `juv4uk/vsop2013/CelestialObjects.pas` — `811c574c7a3de7873951de8db7eebd8960b4e27a` | синхронний leapfrog-крок стану, не конкретні масиви планет |
| Акустика/музика | `juv4uk/xva-trainer/python/xvapitch/stft.py` — `297af5efb10f5f8211fda7cd352b09a1d91c4738` | windowed frame → амплітуди/фази без залежності від Torch/CUDA |
| Радіо/DSP | `juv4uk/radio-log/src/lib/sens-radio/bpsk.ts` — `5c1b9f838686800bc049b34f4aecf6c8a8e74a04` | кореляція → біт/впевненість/невизначеність |
| Радіо/музика/FPGA | `juv4uk/radio-log/src/lib/sens-radio/bfsk-tx.ts` — `5ca28e0cf64737c7a0ad6421e2ad91a2fcb1c896` | неперервна фаза між змінами частоти |
| Вимірювання маятника | `juv4uk/esp32-pendulum/components/physics/period_estimator.c` — `062d7889bff31c58d17cfee1c0dfdcfb62ad0c29` | потрібен напрямлений zero crossing; джерело **TODO**, не готове |
| Радіо/логіка | `juv4uk/radio-log/src/lib/sens-radio/frame-sync.ts` — `5d3be712b417379b7c8d68bb83cd95f00acbff90` | інваріант унікальної прийнятої рамки: 0/1/>1 |

## Шість дослідницьких кандидатів (ще не SELECTED)

**CALENDAR-TO-JULIAN-DAY** — UTC/цивільну дату не плутати з JD: календарна модель і день, що починається опівдні, мають бути в аргументах. Позитив: Gregorian 2000-01-01 12:00 = 2451545.0, 00:00 = 2451544.5. Фальсифікатор: 2000-02-30 не можна мовчки прийняти як коректний день.

**JULIAN-DAY-TO-CALENDAR** — оборотність за заданого календаря, окремо від функцій `UTC-FROM-UNIX` D9. Позитив: 2451545.0 за Gregorian → 2000-01-01 12:00; фальсифікатор: повернути північ замість полудня.

**LEAPFROG-SNAPSHOT-STEP** — зафіксований попередній стан та одночасне оновлення всіх частин. Позитив: x=0, v_half=1, a=2, dt=2 → x'=2, v_half'=5. Фальсифікатор: перестановка порядку тіл змінює результат.

**WINDOWED-SPECTRAL-FRAME** — задане вікно, DFT та виражені magnitude/phase; нульова амплітуда не дає виміряної фази. Позитив: [1,0,0,0] з прямокутним вікном → magnitude [1,1,1]. Фальсифікатор: непарні довжини зразків і вікна мовчки обрізаються.

**COHERENT-PHASE-BIT-DECISION** — додатна/від'ємна кореляція з еталоном та явно відхилена нульова впевненість. У донорі low-level decoder повертає bit=1 при correlation=0 разом з confidence=0; **пропонований вищорівневий закон** не має стверджувати, що такий біт надійно виміряно. Це поки не source/runtime parity.

**PHASE-CONTINUOUS-TONE-SEQUENCE** — tone0/tone1 і безперервний phase accumulator, з sample-rate та Nyquist-обмеженнями. Позитив: 16 samples, rate 16, 2 symbols/s, tones 1.5/2.5 Hz, bits `01` → sample[8] ≈ -1. Фальсифікатор: скидати фазу на межі символів (вийшов би 0).

## Три HOLD, не число відібраних

- **PENDULUM-PERIOD-FROM-DIRECTIONAL-CROSSINGS**: source лише TODO, потрібна справжня реалізація, гістерезис і докази напрямку.
- **RADIO-FRAME-UNIQUE-ACQUISITION**: може бути композицією `RESULT-COUNT`, рівності та існуючих outcome/ambiguity законів.
- **JULIAN-CENTURIES-FROM-JD**: ймовірно звичайна арифметична похідна `(JD-2451545)/36525`.

## Безпечна процедура допуску

1. Повний behavior-level dedup D1–D9 та всіх актуальних D10; перевірка назв проти **D9 + D10** — лише первинний фільтр.
2. Незалежна реалізація-оракул для позитивних прикладів, фальсифікаторів, границь, відсутніх даних, цілочисельного/раціонального і float-узгодження; запуск реального pinned source та порівняння. Тести пакета — лише **independent model**, не source-runtime parity.
3. Для кожного кореня записати `unblock_fanout`, `expressibility_gap`, чи редукується він до існуючих композицій; лише після цього пропонувати SELECTED.
4. Якщо результат підтверджено, окремий append-only transition PR до канонічних `knowledge/d10-v1-semantic-inventory.json` та `knowledge/d10-fill-v1-state.json`, із актуальним CI-growth gate #4867.
5. Не призначати координат, не ратифікувати, не привласнювати D2 керування, D7 текст або фізичний T5-кодек. Жодних FPGA/GPU opcode чи radio frame offsets як D10 meaning.

## Виконувана перевірка метаданих / незалежної моделі

```bash
python3 -m unittest discover -s tests -p 'test_d10_hobbies_source_laws_v1.py' -v
```

**Межі:** жоден source float/host framework/частота пристрою/код сторонньої ліцензії не скопійований як реалізація SENS. Пакет — саме specification і вузький позитивно-негативний independent oracle, а не runnable `.sens` програма чи новий реліз.
