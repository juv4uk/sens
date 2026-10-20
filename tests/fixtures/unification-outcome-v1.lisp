; #219 — сучасні українські запити до явних результатів уніфікації.
; Ключі звіту й англійські мітки результатів є незмінними даними протоколу.
; Завершений запит уніфікації мусить зберігати розрізнення між порожньою
; успішною підстановкою і позитивно встановленою алгоритмічною відмовою.

((expr . "(спостерігати-уніфікацію (як-є radio) (як-є radio) (як-є ()))")
 (expected . "(unified ())")
 (active . t)
 (law . empty-substitution-is-success-data))

((expr . "(спостерігати-уніфікацію (логічна-змінна (як-є x)) (як-є alice) (як-є ()))")
 (expected . "(unified ((x . alice)))")
 (active . t)
 (law . substitution-success-is-explicit))

((expr . "(спостерігати-уніфікацію (як-є radio) (як-є antenna) (як-є ()))")
 (expected . "(unification-failure radio antenna ())")
 (active . t)
 (law . established-failure-is-explicit))

((expr . "(спостерігати-уніфікацію (логічна-змінна (як-є x)) (як-є (f (var x))) (як-є ()))")
 (expected . "(unification-failure (var x) (f (var x)) ())")
 (active . t)
 (law . occurs-check-failure-is-explicit))
