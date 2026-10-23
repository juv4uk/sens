# Конкурс raw13 проти BE16 — фізичний експеримент

**IMPLEMENTED / UNVERIFIED.** Нативні тести очікують виконання центральним CI;
benchmark лишається ручним. p50/p95 не отримано й не вигадано.
Нормативний кодек, доменні таблиці, arithmetic admission та ратифікація не змінюються.

## Незалежний аудит D13

Перевірено `contracts/numeric-domains-ratification.lisp`,
blob `778965143ec9a86364f71a6e35fdbd74ecff39dd`: чинна schema
`numeric-d12-start-extension-1` задає **D(12×2^n)**, перші D12/D24/D48/D96/D192.
**D13 у цій numeric family немає.** `language-contract.lisp`, blob
`c719551e7d8ecab27aa486630dd9610c66bfe339`, повторює цей закон.
`lib/domains/d13.lisp` під час аудиту відсутній.
`numeric_domains.zig`, blob `b1d4b30e2e1125b613cab2f93b05d19705d57e36`,
містить лише legacy physical WIDE_WIDTHS=24/48/96/192; це не ратифікація D13.

Отже тут **raw13 — непрозорі 13 фізичних бітів**, а не новий числовий D13
SENS. Не приписуємо знаку, арифметики, дробу, float чи викличності. Формулювання
«D13 words» у конкурсному завданні перевіряється лише як raw width=13.

## Формати й чесна база

Обидва явно вибрані codec routes мають однакову рамку:
**BE32 word_count (4 B) + payload**. Magic/version/type не додаються;
codec route й width=13 відомі зовні. Це не самовизначальний універсальний формат.

- dense13: послідовні 13 бітів кожного u16 word MSB-first; low padding нульовий.
- BE16: ті самі слова, 2 B/word big-endian; high 3 біти кожного слова нульові.
- 0 слів, значення понад 0x1fff, недостатній output, зайві/відсутні байти,
  некоректний count і неканонічні padding/high bits відхиляються.
- encode/decode спочатку перевіряють усі умови; за помилки output не змінюється.
  Empty count заборонений однаково; переповнення розрахунку size — явна помилка.

Аналітична довжина: dense13=4+ceil(13N/8); BE16=4+2N.
Це **математичний size-факт, не native timing**:

| N | dense payload B | BE16 payload B | dense frame B | BE16 frame B |
|---:|---:|---:|---:|---:|
| 1 | 2 | 2 | 6 | 6 |
| 2 | 4 | 4 | 8 | 8 |
| 3 | 5 | 6 | 9 | 10 |
| 8 | 13 | 16 | 17 | 20 |
| 1024 | 1664 | 2048 | 1668 | 2052 |
| 4096 | 6656 | 8192 | 6660 | 8196 |

При N кратному 8 payload економія 18.75%; частка для повної рамки менша.
Це не прогноз швидкості: reference dense encoder тут свідомо простий bit-by-bit.

## Тести й точний корпус

`d13_raw_experiment.zig`: точні golden frames для
`[0,1,0x1fff,0x1000]`; exhaustive 8192 слів із complementary partner;
seeded pseudorandom + reencode byte parity; atomic negative controls.

Golden dense frame:
`00 00 00 04 00 00 00 7f ff 00 00`.
Golden BE16:
`00 00 00 04 00 00 00 01 1f ff 10 00`.

Точний `lcg13-v1`: u32 state=0x13c0ffee; перед кожним словом
state=(1664525×state+1013904223) mod 2^32; word=(state>>16)&0x1fff.
Тести counts=1,2,7,8,9,63,64,65,1023,1024,1025.
Benchmark додає 4096; extremes=0,1,0x0fff,0x1000,0x1ffe,0x1fff.
Це deterministic fixture, не твердження про випадковість чи типовий SENS corpus.

## Відтворення Zig 0.16.0

За pinned Guix запускайте наступні команди через `./guix/run dev --`:

```sh
zig test research/zig-codecs/d13_raw_experiment.zig
zig build-exe -lc -O ReleaseFast research/zig-codecs/d13_raw_bench.zig -femit-bin=/tmp/sens-raw13-bench
zig version
git rev-parse HEAD
sha256sum research/zig-codecs/d13_raw_experiment.zig research/zig-codecs/d13_raw_bench.zig /tmp/sens-raw13-bench
uname -a
lscpu
/tmp/sens-raw13-bench 2>&1
```

Єдиний import у вже наявному `tests.zig` підключає unit tests до existing
центрального CI. Нових automatic workflows немає; benchmark автоматично не запускається.

Benchmark вимірює лише preallocated frame API, включно з count header,
валідацією й packing, без alloc/free/startup/I/O/evaluator. До часу — strict
roundtrip. 1 warmup batch/op; 21 batch × 300 ops. p50=11-та й p95=20-та
відсортовані batch averages (nearest rank), не individual request latency.
Сирі elapsed_ns/reps друкуються; encode/decode порядок чергується, codec
порядок ротовано за count. Один процес не усуває hosted noise/drift.
До нативного запуску й перевірки сирих logs — **NOT_MEASURED**, не PASS.
