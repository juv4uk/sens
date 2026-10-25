# Чекпоінт · F6 виробник записів, текст D7 на межі I/O · 25.10.2026

## Що було червоним, де й чому

GitHub Actions `40147741071`, SHA
`a9fdf0b31c5f02fb11925d1cdaf19b22107dba90`, job
`121032608773` (історичний, НЕ поточний SHA):

- `cargo test -p sens-cli --test wsm_fs_f6_pipeline`
- id `producer_records_are_reconstructed_by_the_physical_f6_consumer`
- actual: `wsm-fs-record-producer: F6_RECORD_TYPE expected=String actual=non-string`
- expected: рівно 2 однорядкові записи після виконання
  `tests/fixtures/wsm-fs-record-producer.sens` реальним SENS
  через Zig/T5M.
- `physical_f6_consumer_rejects_malformed_record_envelopes` уже PASS.
- До цього ж CI належали `SENS_CORE4_PHYSICAL_DRIFT` та
  8 semantic RED (7 D6, 1 D10) на історичному SHA; не стверджувати,
  що ці ж RED досі існують на новому main, оскільки кілька агентів
  внесли SENS-ремонти.

## Конкретний push

`c84a9c6fc64155fb9f74588a87a3862d9009f342`
`crates/sens-cli/src/bin/wsm-fs-record-producer.rs`.

F6 зовнішній транспорт тепер приймає **тільки** два типи
текстових значень:

1. `Value::String` — зовнішня рядкова оболонка (чинна).
2. `Value::Text7` — точні D7-клітинки, явно спроєктовані
   `sens::render_text7(..., Text7Layout::En)` для ASCII-оболонки
   F6/Lisp на межі stdout; жодної загальної D7→Unicode заміни
   всередині SENS.

Прямі `Value::Pair`, числа, символи й непридатні клітинки D7
відхиляються fail-closed. Обмеження 2 записи, ≤65536 байтів,
без LF/CR/NUL не послаблені. Два механічні тести:
`f6_accepts_exact_d7_text_projection_for_external_records`,
`f6_rejects_structural_values_instead_of_forging_text_records`.

Це **тільки Rust I/O-механізм**, а не мовний алгоритм,
додатковий виконавець SENS чи нова координата.
`SENS_SOURCE=N/A: тільки транспорт I/O`.
Нативна семантика записів лишається
`lib/lisp-fs.lisp`, `tests/fixtures/wsm-fs-record-producer.lisp`
і їхньою фізичною Zig/T5M парою.

## Межа доказовості

Старе `actual=non-string` не ідентифікує точний вид SENS-значення.
Отже, відповідність TEXT7 — **гіпотеза сумісності типів**, а не
вже доведена єдина першопричина старої регресії.
Новий I/O код дає чіткіші помилки `actual=Pair`,
`actual=non-text`, `F6_RECORD_TEXT7 unrenderable-en-layout`.
Якщо новий запуск знову падає, **не** додавати автоматичну
серіалізацію Pair хостом: це порушило б рішення власника,
за яким фс-серіалізатори і мовна істина належать SENS.

Стан після push:
- `NATIVE_SENS_POSITIVE=NOT_VERIFIED`.
- `NATIVE_SENS_NEGATIVE=NOT_VERIFIED`.
- `CI_SHA=c84a9c6fc64155fb9f74588a87a3862d9009f342`
- запуск `40150625379`: queued на момент перевірки;
- `RELEASE=NO-GO`.

## Наступний агент: точний порядок без дублювання

P0. Знайти результат `40150625379` і проаналізувати етап
`Rust — механізм без мовного оракула`, його actual stderr,
а також `wsm_fs_f6_pipeline`. Якщо F6 ще червоний,
зафіксувати саме `actual=Pair` / `actual=non-text`
або інший діагноз, не здогадуватися.

P0. Зіставити `tests/fixtures/wsm-fs-record-producer.lisp`
з канонічним `tests/fixtures/wsm-fs-record-producer.sens`,
а також фізичні бібліотеки `lib/lisp-fs.sens` і
`lib/content-store.sens` на тому самому SHA.
Побайтово перемайнити відхилену пару штатним Zig/T5M,
не ручним текстом і не host-оракулом.

P1. Простежити у реальному SENS значення двох викликів
`фс-серіалізувати-корінь` і `фс-серіалізувати-об'єкт`:
вони викликають чинний D8:11110100
`значення-у-текст` у `lib/lisp-fs.lisp`.
Обережно перевірити D6 `нехай-послідовно`, але не
переписувати мовну семантику в Rust.

P1. Далі перевірити оновлені колегами D6 LENGTH-ONTO,
NTH, REDUCE, MIN/MAX та D10 CLIPS тільки на свіжому
коміті після проходження всього реального Zig/T5M→SENS.
`SENS_CORE4_PHYSICAL_DRIFT` залишається самостійним
release NO-GO, доки фізична відповідність не доведена.

---
Deutsch: Nur die F6-I/O-Grenze akzeptiert nun die explizite
D7-Textprojektion. Der native Beweis ist noch offen.

English: F6 host I/O now accepts the explicitly rendered canonical
D7 text carrier, without synthesizing structured SENS values.
The exact root of the historical red test remains unconfirmed
until native execution on the new SHA.
