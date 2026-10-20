; #219 — явні результати уніфікації.
; Завершений запит уніфікації мусить зберігати розрізнення між порожньою
; успішною підстановкою і позитивно встановленою алгоритмічною відмовою.

((expr . "(unify-observe (quote radio) (quote radio) (quote ()))")
 (expected . "(unified ())")
 (active . t)
 (law . empty-substitution-is-success-data))

((expr . "(unify-observe (logic-var (quote x)) (quote alice) (quote ()))")
 (expected . "(unified ((x . alice)))")
 (active . t)
 (law . substitution-success-is-explicit))

((expr . "(unify-observe (quote radio) (quote antenna) (quote ()))")
 (expected . "(unification-failure radio antenna ())")
 (active . t)
 (law . established-failure-is-explicit))

((expr . "(unify-observe (logic-var (quote x)) (quote (f (var x))) (quote ()))")
 (expected . "(unification-failure (var x) (f (var x)) ())")
 (active . t)
 (law . occurs-check-failure-is-explicit))
