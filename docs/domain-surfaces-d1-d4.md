# D1–D4 human surfaces

Канонічні таблиці поверхонь доменів D1–D4 зберігаються по одному файлу на домен.
Ці файли містять повні колонки в канонічному порядку; документ навмисно не повторює
самі таблиці — точна семантична тотожність залишається точністю ширини, бітів і
ратифікованого закону домену.

Canonical tables are stored one domain per file:

- `lib/domains/d1.lisp`
- `lib/domains/d2.lisp`
- `lib/domains/d3.lisp`
- `lib/domains/d4.lisp`

The files themselves contain the complete columns in canonical order:

`ук → укр → san → en → LISP → sym`

This document intentionally does **not** repeat the tables. Exact semantic identity remains exact width + exact bits + the ratified domain law.

Runtime projection guard: `scripts/check-domain-surfaces-d1-d4.py`.
Human translator: `scripts/translate-domain-program.py`.
