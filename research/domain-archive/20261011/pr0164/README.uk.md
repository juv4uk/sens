# Архів PR #164 — RED-контракт адаптерів backend

**Статус: ARCHIVE-ONLY.** PR навмисно RED: його тест вимагає manifest, якого немає; старий тест використовує шлях `crates/my-lisp`. Це не завершена функціональність і не чинний SENS conformance.

Повні файли збережено під `source/` байт-у-байт зі старої гілки `feat/116-portable-witness-adapters`, head SHA `7f35d6a8d78d0ad6afe9385609998fab8039b02d`. Позитивний намір: native/meta/CML повинні споживати єдиний Lisp witness corpus, без host-authored expected/error truth. До активації потрібне окреме поточне рішення про те, чи є ці механізми актуальними в SENS і де лежить їхній сучасний adapter seam. Не копіювати старий RED-тест у поточний required CI як працюючий gate.

Нова гілка не створювалась; історичний PR буде закрито після збереження provenance.
