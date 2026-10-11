# Архів PR #1033 — явні entrypoint-и поза scripts/

**Статус: ARCHIVE-ONLY / CURRENT-MAIN CHECKER EXTENSION NEEDED.**

Обидва заявлені entrypoint-и й досі присутні в main: `crates/xtask/src/main.rs` (blob `7b05ea47e12d35e702bd33b1969b1767ce0ddab8`) та `githooks/pre-commit` (blob `13f2413b641abcea326ea8f22a8ec533c13a6634`). Однак чинний `knowledge/repo-tooling-inventory.lisp` уже виріс до значно більшої current-main версії, а `scripts/check-repo-tooling-inventory.lisp` перевіряє негайні `scripts/*` paths. Старий inventory із цієї гілки (14 KB) не може замінити current inventory (69 KB).

Тому оригінальні branch-head файли збережені повністю; наступне допустиме рішення — додати окрему обмежену scope-перевірку двох entrypoint-ів у чинному checker, після позитивних та негативних тестів. До такого перенесення цей PR не є активною перевіркою main. Нова гілка не створювалась.
