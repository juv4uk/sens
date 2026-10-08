# D10 CLIPS library harvest v1

**RESEARCH / UNRATIFIED**, #4013 / #4162 / #4463. Донор `lib/clips-import.lisp`, blob `7fd5a01f86fc33e7651de7880a8fda434629354a`.

Додано **12** окремих мовно-видимих значень існуючого CLIPS-імпортера: нормалізація імен модуля, slot lookup, позиційні аргументи, поділ умов і дій, перевірка assert/printout, збір фактових висновків, відсікання преамбули та printout.

**D10: 546 → 558/1024; selector placed 256; unplaced 302; remaining 466; ratified 0.**

`CLIPS-DROP-PRINTOUTS` навмисно прибирає тільки операції друку — це **не** повна еквівалентність із CLIPS side effects. Усі 12 без координат, з line + SHA provenance і запропонованими, але не ратифікованими поверхнями. Ті CLIPS-функції, що вже в D9, не дубльовані. Перевірка: `python3 scripts/check-d10-clips-library-harvest-v1.py`.
