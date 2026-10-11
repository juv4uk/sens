# Рамка-3: GitHub Actions Rust-бенчмарки (11.10.2026)

**Пін вихідного коду:** `b46ea15c3b134e3de2a148d47af5d63ac1616adc`.
**GitHub Actions:** https://github.com/juv4uk/sens/actions/runs/38160531210
**Первинний артефакт** (TSV summary, raw paired samples, env; retention 21 days):
https://github.com/juv4uk/sens/actions/runs/38160531210/artifacts/11710790384

Два jobs на цьому SHA: `rust-proof` — SUCCESS,
`Frame3 paired CPU and full-file bytes` — SUCCESS.
Перед timing: 13/13 focused `universal_frame3` Rust unit tests PASS.

**Середовище:** GitHub-hosted `ubuntu-24.04`;
AMD EPYC 7763 64-Core Processor;
Linux 6.17.0-1022-azure x86_64; rustc 1.99.0;
Release mode.
Це **час теплого in-process кодека**, НЕ виконання програм SENS
і НЕ cold start. Час — медіана p50 у нс/виклик. Т5 і F3 мають
різні вимоги до integrity/CRC32: ці розміри — фізичні, а не
еквівалентна надійність.

## Важливе розмежування авторства та результатів

**Оригінальна Рамка-3 (F3) ≠ S3/v1, S3/v2 або S3/v3.**
S3/v1–v3 — окремі альтернативні фізичні реалізації/експерименти,
які не можна видавати за оригінальну математичну конструкцію F3.
Їхні overhead, CRC32, заголовки, DP/REPEAT та заміри швидкості
**не є характеристиками оригінальної F3**.

Зокрема, **1025 Б → 41 Б (25×)** для 512 однакових W9 —
результат S3/v2 з режимом REPEAT; **не** доказ стискання F3.
Оригінальна F3 виміряна лише на відповідних їй формах:
наприклад, `single-d3-quote` = 3 Б і
`nested-quote-data` = 5 Б, а F3 декодер нині відхиляє
частину старих фікстур як `NotCanonical`. Ці обмеження
потрібно виправляти/аналізувати незалежно, не підміняти S3.

Для дослідження ефективності Рамки-3 первинними є
математичні правила F3 та код її авторизованої Rust-реалізації;
S3/v1–v3 залишаються лише сторонніми контрольними конкурентами.

## Фізичний повний файл (байти)

| Корпус | T5 | S3/v1 | S3/v2 | S3/v3 | F3 |
|---|---:|---:|---:|---:|---:|
| empty-list | 1 | 12 | 11 | 11 | REJECTED_NONCANONICAL |
| single-d3-quote | 3 | 14 | 13 | 13 | 3 |
| nested-quote-data | 5 | 17 | 15 | 15 | 5 |
| dotted-pair | 3 | 14 | 12 | 12 | REJECTED_NONCANONICAL |
| separator-exact | 4 | 15 | 13 | 13 | 3 |
| mixed-width | 6 | 17 | 16 | 16 | REJECTED_NONCANONICAL |
| repeated-w9-80 | 161 | 21 | 21 | 21 | NA (F3 profile) |
| w9-repeat-512 (paired corpus) | 1025 | 41 | 41 | not measured | not measured |
| w9-mixed-512 (paired corpus) | 1025 | 853 | 853 | not measured | not measured |
| d24-run-80 (numeric only) | not supported | not supported | not supported | 15 | not supported |

`REJECTED_NONCANONICAL` позначає фактичну відмову
`senc::decode_senc` на відповідній старій фікстурі.
Це НЕ нульовий розмір F3; фізична довжина неприпустимого носія
не рахується як успішне стискання.

## Час кодування/декодування, нс/виклик (p50, один набір F3-vs-all)

| Корпус/формат | Encode p50, нс | Decode p50, нс |
|---|---:|---:|
| single-d3-quote / T5 | 68 | 167 |
| single-d3-quote / S3v1 | 603 | 1070 |
| single-d3-quote / S3v2 | 2711 | 4107 |
| single-d3-quote / S3v3 | 3360 | 4790 |
| single-d3-quote / F3 | 16853 | 63847 |
| repeated-w9-80 / T5 | 2516 | 5705 |
| repeated-w9-80 / S3v1 | 40427 | 43172 |
| repeated-w9-80 / S3v2 | 43260 | 46471 |
| repeated-w9-80 / S3v3 | 237836 | 241360 |

Для тієї ж F3-vs-all програми: 11 серій × 12 повторів
кожної фази, часові вимірювання послідовні, не randomized paired.

## Рандомізований paired A/B (окремий набір v2-paired)

21 серія × 12 повторів; детерміновано перемішано порядок
6 режимів (T5/S3v1/S3v2 encode/decode); повний файл, без
підміни «grammar-only body» фізичним розміром.

| Корпус | T5 encode p50, нс | S3v2 encode p50, нс | T5 decode p50, нс | S3v2 decode p50, нс |
|---|---:|---:|---:|---:|
| w9-repeat-512 | 12646 | 679807 | 31688 | 696687 |
| w9-mixed-512 | 12643 | 692415 | 31529 | 725298 |

При 512 однакових W9 S3v2 має 41 Б замість 1025 Б
(**25× менше байтів**), однак на цьому самому хості
кодується близько **53.8× повільніше** (679807 / 12646).
Це ефект від repeat у специфічному корпусі, а не
глобальна перевага алгоритму.

## Методологічні обмеження

- Порівняння p50 між окремими експериментами не є paired A/B:
  F3-vs-all і v2-paired мають різні корпуси/порядок проб.
- Не вимірювалися runtime execution, CLI cold startup, GPU або FPGA.
- Глобальна byte-optimality поза наявними RAW/REPEAT/обмеженим
  GRAMMAR набором НЕ доведена.
- Повні сирі paired-семпли та вихідні таблиці в artifact за посиланням вище.
- При наступній зміні коду/середовища потрібна нова SHA-pinned серія.
