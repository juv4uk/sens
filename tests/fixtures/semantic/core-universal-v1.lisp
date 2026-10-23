; tests/fixtures/semantic/core-universal-v1.lisp — #1709.
; Універсальний корпус семантичних очікувань для всіх профілів СЕНС:
; нативного обчислювача, Core1, Core2, Core3 та Core4.
; Якщо різні профілі повертають різні результати для одного закону,
; це семантична розбіжність, а не допустима властивість профілю.
; Rust переносить фактичний результат, але не встановлює очікувань
; і не має права змінювати їх залежно від профілю.
; Мовний вердикт залишається відповідальністю Lisp СЕНС.
;
; Виконувані вирази записані повною укр-проєкцією чинної драбини.
; Історичні SID8/Sens8 залишаються лише в історії Git, не у викликах.

((expect . expect-value)
 (expr . "(однакові? 1 1)")
 (expected . (value (1)))
 (active . t)
 (name . "universal: однакові? 1 1 -> 1 біт")
 (semantic-id . "D8:11110111")
 (governs . "#1699")
 (note . "Однакова відповідь у кожному профілі."))

((expect . expect-value)
 (expr . "(однакові? 1 2)")
 (expected . (value (0)))
 (active . t)
 (name . "universal: однакові? 1 2 -> 1 біт")
 (semantic-id . "D8:11110111")
 (governs . "#1699")
 (note . "Відсутність збігу теж має бути 0, а не ()."))

((expect . expect-value)
 (expr . "(атом? 5)")
 (expected . (value (1)))
 (active . t)
 (name . "universal: ATOM не-пара -> 1")
 (semantic-id . "D3:010")
 (governs . "#1704")
 (note . "Спільна істина для всіх профілів."))

((expect . expect-value)
 (expr . "(атом? (як-є (атом? решта)))")
 (expected . (value (0)))
 (active . t)
 (name . "universal: ATOM пара -> 0")
 (semantic-id . "D3:010")
 (governs . "#1704")
 (note . "Спільна істина для всіх профілів."))

((expect . expect-value)
 (expr . "(тотожне? (як-є атом?) (як-є атом?))")
 (expected . (value (1)))
 (active . t)
 (name . "universal: EQ той самий атом -> 1")
 (semantic-id . "D3:101")
 (governs . "#1705")
 (note . "Спільна істина для всіх профілів."))

((expect . expect-value)
 (expr . "(тотожне? (як-є атом?) (як-є решта))")
 (expected . (value (0)))
 (active . t)
 (name . "universal: EQ різні атоми -> 0")
 (semantic-id . "D3:101")
 (governs . "#1705")
 (note . "Спільна істина для всіх профілів."))

 ((expect . expect-rejected)
  (expr . "(тотожне? 1")
  (expected . (rejected "(тотожне? 1"))
  (active . t)
  (name . "universal: незакрита форма відхиляється, а не ремонтується")
  (semantic-id . "reader")
  (governs . "#1709")
  (note . "Корпус є Lisp-джерелом: пошкоджене джерело відхиляється читачем, а не мовчки виправляється."))
