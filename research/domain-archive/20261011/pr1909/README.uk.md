# Архів PR #1909 — replay PredicateBit source

**Статус: ARCHIVE-ONLY / НЕ ЗЛИВАТИ ВСЮ ГІЛКУ.**

PR #1909 має 20 змінених файлів, 1,329 додавань і 1,309 вилучень і базується на `replay/1807-predicate-runtime-20260930`, а не на поточному main. Він зачіпає Core/Core4/Macro, evaluator IO, source authority checkers, constitution, fixtures і benchmark harness. Це змішана семантична інтеграція, а не вузький сумісний PR.

Повний diff збережено в `predicatebit-current-main-review.patch`, а список усіх 20 paths/head/base/межі доказу — в `manifest.json`. Цей архів не стверджує, що зміни зайві; він означає, що їх треба брати по одній поведінковій одиниці з поточного main, не зливаючи застарілу ancestry.

Особливо перевірити вже активніший current-main contract для PredicateBit output та наявність `string_order_predicatebit.rs`; не дублювати identity/COND laws і не приймати старі `lib/core.lisp`/Core4 blobs wholesale. Усі джерела збережені в main; гілку не створювали.
