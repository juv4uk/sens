# Архів PR #1038 — Lisp-authored CML bootstrap envelope

**Статус: ARCHIVE-ONLY / НЕ АКТИВОВАНО В SENS.**

П'ять файлів збережено точно з branch head `feat/1036-cml-bootstrap-envelope` (`c5bf3888bad91ac427f9d15e8e995766d563bd7e`). Цей дизайн описує вузький frontend envelope для вже прочитаного `(+ 1 2)), з fail-closed відмовами на невідомі shape-и; він не повинен переносити семантичний авторитет у CML.

Однак Rust observer у PR використовує `crates/my-lisp`, а тестові authority inventory шляхи теж посилаються на старий crate. Перш ніж активувати перевірку, потрібні: current `crates/sens` execution path, точний CML consumer у його власному репозиторії/гілці та parity позитивного/негативного witness. Архів зберігає унікальну Lisp-форму як джерело; не трактувати це як чинний compiler contract. Нову гілку не створено.
