(
  (name . "addition-is-commutative")
  (types . ("int" "int"))
  (expr . "(= (додати x y) (додати y x))")
)
(
  (name . "string-append-is-associative")
  (types . ("string" "string" "string"))
  (expr . "(однакові? (рядок-додати x (рядок-додати y z)) (рядок-додати (рядок-додати x y) z))")
)
(
  (name . "reverse-reverse-is-identity")
  (types . ("list"))
  (expr . "(однакові? (зворот (зворот x)) x)")
)
(
  (name . "persistent-map-insert-idempotency")
  (types . ("string-list" "string" "string"))
  (expr . "(нехай ((m (побудувати-мапу x мапа-порожній))) (однакові? (мапа-вставити y z (мапа-вставити y z мапа)) (мапа-вставити y z мапа)))")
)
(
  (name . "persistent-map-sorted-order")
  (types . ("string-list"))
  (expr . "(нехай ((m (побудувати-мапу x мапа-порожній))) (ключі-мапи-впорядковані? (мапа-список мапа)))")
)
(
  (name . "persistent-map-height-bound")
  (types . ("string-list"))
  (expr . "(нехай ((m (побудувати-мапу x мапа-порожній))) (нехай ((h (height-of мапа)) (n (довжина (мапа-список мапа)))) (не-менше? кількість (додати (число-фібоначчі (додати висота 2)) -1))))")
)
(
  (name . "world-monotonicity")
  (types . ("string-list" "string" "string"))
  (expr . "(нехай ((w (побудувати-світ x (порожній-світ)))) (= (додати 1 (довжина (світ-журнал світ))) (довжина (світ-журнал (світ-повідомити світ y z)))))")
)
(
  (name . "world-rollback-identity")
  (types . ("string-list" "string" "string"))
  (expr . "(нехай ((w (побудувати-світ x (порожній-світ)))) (однакові? (світ-батько (світ-повідомити світ y z)) світ))")
)
(
  (name . "knowledge-journal-append-only-monotonicity")
  (types . ("string-list" "string" "string"))
  (expr . "(нехай ((_1 (визначити *knowledge-journal* (як-є ()))) (_2 (повідомити-всі-події x)) (len-before (довжина *knowledge-journal*)) (_3 (визначити-модуль \"mod\" (список z)))) (= (додати 1 попередня-довжина) (довжина *knowledge-journal*)))")
)
(
  (name . "knowledge-journal-retract-inverse-of-tell")
  (types . ("string-list" "string"))
  (expr . "(нехай ((_1 (визначити *knowledge-journal* (як-є ()))) (_2 (повідомити-всі-події x)) (before (модуль-клаузи-зараз \"mod\")) (_3 (визначити-модуль \"mod\" (список y))) (_4 (відкликати-знання \"mod\" y))) (однакові? перед-дією (модуль-клаузи-зараз \"mod\")))")
)
