# Архів PR #2815 — explicit CoreD6 AST identity

**Статус: ALREADY-IN-MAIN-NEWER / HISTORICAL ALTERNATIVE.**

Повний diff п'яти файлів збережено в `core-d6-explicit-ast-review.patch`. Branch proposal додавав явний `ExprKind::CoreD6(CoreD6)` AST variant і відповідні identity/64-cell tests. Чинний main уже має типізований CoreD6(Bit6) carrier у `domain_words.rs`, але AST/transport використовує узагальнений `CoreDomainIdentity`/ `DomainIdentity`, що усуває потребу у власному варіанті AST для кожного домену.

Архів зберігає точну пропозицію й source-review, не вводячи дубльований AST tag або другу authority таблицю. Повний 64/64 witness має бути оцінений проти чинного generic AST у вже наявній D6 authority thread, не шляхом злиття старого snapshot. Нової гілки не створено.
