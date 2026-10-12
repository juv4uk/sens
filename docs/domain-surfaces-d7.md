# D7 human surfaces

Канонічна таблиця людських поверхонь D7 живе у `lib/domains/d7.lisp`.
D7 має 126 семантичних резидентів зі 128 координат; `0100001` і `0101010`
зарезервовані. **Кожна поверхня містить символ саме її писемності**, а не
фонетичний опис. Якщо символ не засвідчено, поле має `()` (відсутня лише
проєкція, а не семибітний резидент). `LISP` завжди `()`.

Canonical D7 human table: `lib/domains/d7.lisp`.

Authority: `knowledge/d7-ratified.json` (#3572), Contract 11.8.

D7 has 126 semantic residents of 128 possible coordinates. Owner-reserved `0100001` and `0101010` are intentionally absent from the table.

Columns: `ук → укр → san → en → LISP → sym`.

The 126 ratified codes are independent of their script-specific glyphs.
`ук/укр` contain Ukrainian graphemes, `san` Devanagari, `en` IAST,
and `sym` the IAST symbol view. Missing spellings are represented by `()`.
Explanatory phonetic names remain only in the owner evidence JSON. `LISP`
never grants execution.

## Механічне введення D7 в Rust

Джерело розміщення: `knowledge/d7-ratified.json` (#3572); людиночитна таблиця
`lib/domains/d7.lisp` тепер має справжні гліфи, а не описи. Команда
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

## D7 у чинному виконанні

Вхід — **точні сім бітів та явно названа роль**, а не вільний символ чи
число. Авторитет резидентів: `knowledge/d7-ratified.json` (рішення #3572);
`lib/domains/d7.lisp` — лише читабельна проєкція.

```sh
python3 scripts/d7_source_projection.py --check
python3 scripts/d7_source_projection.py --coordinate 0000000 --role sound-text --namespace ук
python3 scripts/d7_source_projection.py --coordinate 0000001 --role local-ordinal
python3 scripts/d7_source_projection.py --coordinate 0011111 --role sound-text --namespace sym
```

Два зарезервовані `0100001` та `0101010` ніколи не допускаються як
Sound/Text. LocalOrdinal — окрема роль: джерело
`contracts/d7-local-ordinal.lock` і 14 підтверджених порядкових номерів
Śiva-sūtras; довільна W7-координата не набуває цього статусу автоматично.
Зокрема гліф `1` у D7 — текст, **не** арифметичне число й **не** функція.

`scripts/d7_source_projection.py` нічого не ратифікує; повертає
`surface` = символ обраної писемності, `report_name` = службова
фонетична мітка. `scripts/d7_symbol_codec.py` — реальний двосторонній
кодек, порт механізму `juv4uk/shiva-sutras/prototype/upc7_layouts.py`,
який читає **тільки** координати чинного #3572. Rust зберігає механічну
координату W7 без мовної семантичної таблиці. Тестові докази:
`tests/test_d7_source_projection.py`, `scripts/check-d7-current-authority.py`,
`crates/sens/tests/d7_w7_pack.rs`. Обов'язкова перевірка D7 включена
у `.github/workflows/triple-projection-gate.yml` для кожного push у main.

## Фактичний кодек / тест

```sh
python3 scripts/d7_symbol_codec.py --surface ук --text 'кіт' --target en
python3 scripts/d7_symbol_codec.py --surface san --code 0000000
python3 scripts/d7_symbol_codec.py --surface ук --code 0000001
python3 -m unittest discover -s tests -p 'test_d7_symbol_codec.py' -v
python3 scripts/check-d7-runtime-projection.py
```

Багатосимвольні відповідники (напр. `kh`) потребують збереження границь
кодів: `encode_tokens/render_tokens` працюють із точними семибітними словами;
`render_text` відхиляє неоднозначне склеювання. У D7:1100101 старий
ратифікований запис помилково містить TAB замість glyph подвійних лапок;
до виправлення джерела проєкцію не вигадано. Немає зміни законів чи зайвих
бітів у виконуваній мові.
