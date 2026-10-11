# Архів PR #1943 — XED binary count migration

**Статус: ALREADY-IN-MAIN-NEWER; не повертати старі generated outputs.**

Основний задум PR — записувати метадані кількості у XED evidence як явні двійкові числові літерали — уже наявний у чинному `crates/xtask/src/xed_import.rs`: поточні рядки генератора формують `(form-count #b...)`. Поточний `encoder_coverage.rs` і дві numeric inventory data-файли byte-identical до гілки.

Три файли відрізнялися: старий генератор XED та дві generated Lisp-вивідні таблиці. Вони збережені побайтно як `.source.txt` під `source/` з оригінальними blob SHA. Стара гілка має top-level coverage count 1175, а поточний main — 1176; також змінився source digest, тому ці generated файли не можна переписати поверх main.

Маніфест фіксує всі шість початкових шляхів та їхній статус. Потрібний semantic/production change вже на main; старі output blobs залишено лише як історичний доказ. Нову гілку не створено.
