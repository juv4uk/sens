# Архів PR #2810 — рання версія runtime-peer tests

**Статус: ARCHIVE-ONLY / SUPERSEDED.**

Повний diff є в `runtime-peer-projection-early.patch`. Він містить ранній варіант тесту runtime peer-операторів, включно з перевірками наявності bare UK/SA/SYM values та presentation. Пізніший #2867 і поточний main прибрали застарілі очікування, що surface spellings мусять бути runtime значеннями до явного завантаження surface.

Поточний active file `crates/sens/tests/runtime_peer_operators.rs` (blob `96289f0d86cd0de50d56507c8b6a33ba7848b172`) зберігає registry parity/presentation, не старі bare-value assertions. Гілку збережено як provenance, не активний тест; жодної нової гілки не створено.
