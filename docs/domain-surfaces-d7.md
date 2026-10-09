# D7 human surfaces

Канонічна таблиця людських поверхонь D7 живе у `lib/domains/d7.lisp`.
D7 має 126 семантичних резидентів зі 128 можливих координат; зарезервовані власником
`0100001` і `0101010` навмисно відсутні. Усі 126 резидентів мають українські,
розширено-українські та санскритські пояснювальні поверхні. D7 — звуковий/текстовий
домен, тому Lisp-оператори не вигадуються: `LISP` лишається `()`.

Canonical D7 human table: `lib/domains/d7.lisp`.

Authority: `knowledge/d7-ratified.json` (#3572), Contract 11.8.

D7 has 126 semantic residents of 128 possible coordinates. Owner-reserved `0100001` and `0101010` are intentionally absent from the table.

Columns: `ук → укр → san → en → LISP → sym`.

All 126 residents have Ukrainian, expanded-Ukrainian, and Sanskrit explanatory surfaces. `sym` carries a concrete glyph or sound projection where one exists. D7 is a sound/text domain, so no Lisp operator names are invented: `LISP` stays `()`.

## Механічне введення D7 в Rust

Джерело розміщення: `knowledge/d7-ratified.json` (#3572); людиночитна таблиця
`lib/domains/d7.lisp` не змінюється. Команда
`python3 scripts/generate-domain-owner-registry.py` матеріалізує тільки
координати з нормативного джерела, без назв, фонемних законів, старих SID8 чи
виконуваних примітивів. `--check` відхиляє будь-яке розходження генератора
і Rust-проєкції.

`DomainCoordinate::new(7, bits)` відповідає лише за форму слова.
`DomainCoordinate::owner_residency()` для D3–D7 повертає
`Some(true)` для admitted, `Some(false)` для не зайнятих координат
та `None` за межами охоплення проєкції. У D7 маємо рівно 126 admitted
і лише дві зарезервовані координати `0100001` та `0101010`.

D7 identity залишається `DomainIdentity::D7(SoundD7)`, а
`core_operation()` для нього повертає `None`. Отже, навіть admitted
Sound7/Text7/LocalOrdinal **не стає** Lisp-функцією за фактом ширини
або місця у таблиці. Гліфи, українські та санскритські написання — тільки
проєкції. Аріфметичні Number-значення, Text7 та локальний порядковий
індекс не ототожнюються автоматично.
