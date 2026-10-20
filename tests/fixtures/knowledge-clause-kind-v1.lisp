; #218 — вид клаузи знань є явними даними домену.
; Виклики українською: є-факт? з ратифікованого Д9 та як-є з Д3.
; Позначки clause-kind, fact, rule та імена правил є незмінними даними.
; Історичні факти й змінні всередині цитованих клауз не перекладаємо.

((expr . "(є-факт? (як-є ((planet earth))))")
 (expected . "(clause-kind fact)")
 (active . t)
 (law . empty-body-is-fact))

((expr . "(є-факт? (як-є ((ancestor (var x) (var y)) (parent (var x) (var y)))))")
 (expected . "(clause-kind rule)")
 (active . t)
 (law . nonempty-body-is-rule))
