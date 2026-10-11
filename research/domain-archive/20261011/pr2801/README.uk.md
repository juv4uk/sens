# Архів PR #2801 — explicit CoreD5 AST tag

**Статус: ALREADY-IN-MAIN-NEWER.**

У PR пропонувався окремий `ExprKind::CoreD5(CoreD5)` AST variant з FASL/wire tag. Поточний main має typed `CoreD5(Bit5)` carrier у `crates/sens/src/domain_words.rs`, але представлення AST/transport було узагальнене до `DomainIdentity` / `DomainCall` у `crates/sens/src/syntax.rs`. Окрема CoreD5-гілка AST дублювала б сучасну generic identity-модель та вимагала б другого набору wire tags.

Повний textual diff 4 файлів збережений у `core-d5-explicit-ast-review.patch`; маніфест фіксує origin і поточні main blobs. Це не означає втрату типізованого CoreD5 carrier: він лишається в main. Закриваємо цей старіший AST-варіант як superseded; нової гілки не створено.
