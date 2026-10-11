# Архів PR #1044 — механічний міст CLIPS ↔ Datalog

**Статус: ARCHIVE-ONLY / ПАРИТЕТ НЕ ДОВЕДЕНО ДЛЯ ЧИННОГО SENS.**

Усі п'ять змінених файлів із head feat/718-clips-datalog-bridge (1981c7acf6fb9003dc66332a6755da4bfb716a3e) збережено побайтно. Пропозиція обмежувала міст простими decoded fact/tuple observations і fail-closed відмовою на count-only observations, фіксуючи втрати agenda/firing/derivation інформації. Це корисний механічний протокол, але не доказ еквівалентності CLIPS і Datalog.

Чинний main не має lib/bridge/clips-to-datalog.lisp, а observer тест жив у старому crates/my-lisp. Тому стару гілку не треба зливати як активну семантику. Якщо потреба лишається, перенесення має бути перевірене проти чинних Lisp laws, актуального CLIPS/Datalog consumer та незалежного позитивного/негативного oracle. Координація — у вже наявному #718/#5041; нову гілку не створено.
