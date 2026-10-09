# D10 — звірка старої гілки Lisp 1.5 з канонічними D1–D9

Дата аудиту: 2026-10-09. Статус: **дослідження, без нових residents**.

Стара гілка `research/d8-lisp15-appendix-ledger` (#3947) містить корисний каталог 30 історичних родин із Lisp 1.5, але її карта координат належить до давнього стану до ратифікації D8. Її не можна зливати механічно: D1–D9 наразі owner-ratified, а канонічні D8 координати визначає актуальна `knowledge/d1-d9-foundation.json`, не старий `knowledge/d8-recovery-candidate-map.json`.

Цей replay переносить **докази та класифікацію**, а не старі коди. Він звіряє кожне з 30 сімейств за точними іменами проти актуального фундаменту та всіх 625 вибраних D10-кандидатів. Там, де ім'я вже існує, це не дає дозволу на повторний resident; де ім'я відсутнє, результат лише HOLD/перевірка закону.

## Висновки

- Усі 30 родин збережено з первинним/історичним походженням і окремою поточною класифікацією.
- Знайдені збіги включають D8 `RPLACA/RPLACD`, `ERRORSET/ERROR`, `READ`, `VECTOR`, `VECTOR-REF`, `VECTOR-SET!`, `SPECIAL`, `GET`, `GETPROP/PUTPROP`; а в дослідницькому D10 уже є `INTERN`, `REMOB`, `REMPROP`, `SASSOC`, `SEARCH`. Тому історичні назви не слід подавати повторно як незалежні пропозиції.
- Найближча додаткова **питальна гіпотеза** — `MAPATOMS/OBARRAY`: MacLisp описує множинні symbol tables, символи з однаковим print-name у різних tables і операцію обходу таблиці без залежності клієнта від її hash-bucket layout. Треба перевірити, чи це незалежний portable law, чи лише спосіб огляду реалізаційного symbol registry. Це HOLD, не selected.
- `APVAL/CSET/CSETQ/FLAG/REMPROP` слід мінімізувати до вже наявних property-list/value-cell семантик; `SPECIAL` вже є в канонічному D8; `MAP`, `MAPLIST`, `EQUAL`, `GENSYM`, `READ` та vector/array family вже мають lower-domain/selected matches або derivation hypotheses. Debugging, I/O, compiler and memory controls — не Core resident автоматично.

## Первинні джерела

1. [LISP 1.5 Programmer's Manual, 17 Aug 1962](https://softwarepreservation.computerhistory.org/LISP/book/LISP%201.5%20Programmers%20Manual.pdf): §7.3 *Property Lists*, друковані pp. 39–40 (PDF viewer page range around 46–48); атом має property list, `APVAL` задає постійне значення символу, а `GET`, `REMPROP`, `DEFLIST` та flags мають визначені властивості. Джерело підтверджує історичну поведінку, але не надає сучасних D10 координат.
2. [MacLisp Reference Manual, 17 Dec 1975](https://softwarepreservation.computerhistory.org/LISP/MIT/MACLISP_Reference_Manual-Dec_17_1975.pdf): §5.4 *Interning of Symbols*, printed pp. 2-53–2-54 — `OBARRAY` може бути декілька; interning відбувається за print-name; різні обarrays можуть містити різні, не-EQ символи з однаковим print-name; існують uninterned symbols.
3. Там же, §9 *Mapping Functions*, printed p. 2-95: `MAPATOMS` застосовує callback до символів указаного/current obarray і приховує від користувача її фізичне представлення.
4. [Interlisp-D Reference Manual](https://interlisp.org/documentation/IRM.pdf), §11.15–11.16 printed pp. 11-15–11-16, підтверджує окрему сім'ю можливостей/generatorів, але `POSSIBILITIES/TRYNEXT/AU-REVOIR` лишаються питанням D2 control: різниця між відсутнім значенням і явно виданим NIL сама по собі не доводить потребу у D10 opcode.

## Єдина пропозиція, яку варто дослідити далі

`MAPATOMS/OBARRAY`: дві позитивні проби та один falsifier записані в JSON. До будь-якого оформлення через єдиний D10 proposal workflow потрібні точні callback return/error/early-exit умови, adversarial oracle проти `INTERN/REMOB/COPYSYMBOL/NEW-SYMBOL/READTABLE`, і висновок owner щодо Core-власності. Немає порядку обходу, координати, resident, ratification чи T5-авторизації.

## Лічильники

Цей replay додає **0** D10 selected, **0** координат і **0** ратифікацій. Машинний стан D10 знімка: 625/1024 вибраних, 369 без координат, 399 невибраних, 0 ратифікованих.
