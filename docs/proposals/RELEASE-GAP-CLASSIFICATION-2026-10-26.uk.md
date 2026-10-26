# РЕЛІЗ: 884 — це не 884 прогалини. Класифікатор рахує дані як програми

Автор: агент Sampūrti, 2026-10-26. Вимір, не оцінка.

## Звідки число 884

`python3 scripts/report_t5_t5m_triplet_inventory.py --report /tmp/rep.json` дає
`summary.unpaired_program_lisp_sources = 884`, і саме це число стоїть за
`status: INCOMPLETE_SOURCE_PAIRS`, який блокує реліз.

## Розподіл за важливістю

| група | без пари |
|---|---|
| **`lib/` — канонічна бібліотека** | **10** |
| `tests/semantic` — закони мови | 468 |
| `tests/` — фікстури, оракули | 113 |
| `benchmarks/` — заміри | 199 |
| `research/` + `docs/` — архів, дослідження | 54 |
| `knowledge/` — знімки даних | 24 |
| інше | 16 |

**Уся канонічна бібліотека — 10 файлів.** Решта — тести, заміри, архів і знімки.

## Але й ці 10 — переважно НЕ програми

Порахував `(визначити` у кожному:

| файл | визначень | що це |
|---|---|---|
| `lib/domains/d9.lisp` | **0** | дані |
| `lib/domains/archive/d11-rejected-43.lisp` | **0** | відхилений архів |
| `lib/generated/function-table.lisp` | **0** | згенеровані дані |
| `lib/machine/intel-core-i5-6400.lisp` | **0** | дані машини |
| `lib/machine/profile/current-domain-x86-64.lisp` | **0** | дані профілю |
| `lib/surface/semantic-registry.lisp` | **0** | реєстр-дані |
| `lib/surface/uk-sa-coverage.lisp` | **0** | дані покриття |
| `lib/yantra.lisp` | 79 | **джерело прив'язок**, не програма |
| `lib/бенчмарк.lisp` | **10** | **ПРОГРАМА — справжня прогалина** |
| `lib/твердження.lisp` | **17** | **ПРОГРАМА — справжня прогалина** |

**Сім файлів мають нуль визначень** — це дані, їм фізична пара не потрібна.
`lib/yantra.lisp` — джерело прив'язок (`--binding-source`), теж не програма.

## Отже

**Справжніх прогалин у канонічній бібліотеці — ДВІ:** `lib/бенчмарк.lisp` і
`lib/твердження.lisp`. Не 10, і аж ніяк не 884.

## Дефект класифікатора

Інвентар відокремлює `unpaired_nonprogram_lisp_sources = 60`, тобто **вміє**
розрізняти дані й програми. Але **сім із десяти** файлів `lib/` із нулем визначень
потрапили до `unpaired_program_lisp_sources` — класифікатор їх пропустив.

**Наслідок для релізу:** число 884 **завищене**, і `status: INCOMPLETE_SOURCE_PAIRS`
відображає це завищення. Це не означає, що реліз близький — 468 законів у
`tests/semantic` і 199 замірів у `benchmarks/` справді без пар. Але **канонічна
бібліотека майже повна**.

## Що я НЕ зробив і чому

Не змінив класифікатор і не змінтував дві пари. Мінтування потребує native
`sens`/`sens-trit`; у середовищі немає `cargo`/`rustc`, `sh.rustup.rs` віддає **403**,
`static.rust-lang.org` — **000**. Зміна класифікатора — це зміна числа, за яким
ухвалюють рішення про реліз; її має бачити власник.

## Deutsch

884 ist überhöht: der Klassifikator zählt sieben Datendateien in `lib/` als Programme.

## English

884 is inflated: the classifier counts seven data files in `lib/` as programs.
