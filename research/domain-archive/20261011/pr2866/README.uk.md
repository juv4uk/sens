# Архів PR #2866 — kernel ABI/domain identity boundary alternative

**Статус: ALREADY-IN-MAIN-NEWER.**

Повний diff збережений у `kernel-abi-domain-boundary-review.patch`. Поточний main вже має той самий принцип, але суворішу wrapper-схему:
- `LegacyAbiSemanticId`, а не загальний `SemanticId`;
- заборона імпорту language identity;
- тільки явна проєкція мова → legacy/kernel transport;
- актуальний workflow з concurrency, cancellation, ubuntu-24.04 і current-main witness.

Старий PR має менш точну назву `SemanticId` та менш суворий workflow. Його не можна зливати поверх main, бо це послаблює current ABI boundary. Архів зберігає історичну аргументацію, але не замінює чинний контракт. Нову гілку не створено.
