# D7 human surfaces

Канонічна таблиця людських поверхонь D7 живе у `lib/domains/d7.lisp`.
D7 має 126 семантичних резидентів зі 128 можливих координат; зарезервовані власником
`0100001` і `0101010` навмисно відсутні. Усі 126 резидентів мають українські,
розширено-українські та санскритські пояснювальні поверхні. D7 — звуковий/текстовий
домен, тому Lisp-оператори не вигадуються: `LISP` лишається `()`.

Canonical D7 human table: `lib/domains/d7.lisp`.

Authority: `knowledge/d7-ratified.json` (#3572), Contract 11.7.

D7 has 126 semantic residents of 128 possible coordinates. Owner-reserved `0100001` and `0101010` are intentionally absent from the table.

Columns: `ук → укр → san → en → LISP → sym`.

All 126 residents have Ukrainian, expanded-Ukrainian, and Sanskrit explanatory surfaces. `sym` carries a concrete glyph or sound projection where one exists. D7 is a sound/text domain, so no Lisp operator names are invented: `LISP` stays `()`.
