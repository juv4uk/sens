; My-Lisp task demonstration script
; Скрипт My-Lisp: демонстрація задач

; Demonstrate basic Lisp operations
; Демонстраціяbasic Lisp операцій

; 1. Arithmetic
; Арифметика
(додати 1 2 3 4 5)  ; => 15

; 2. cons cell
; cons-сельта
(визначити pair (сполучити 1 2))  ; Creates a pair (1 . 2)

; 3. car and cdr
; car та cdr
(перше pair)  ; => 1
(решта pair)  ; => 2

; 4. Simple function using lambda
; Проста функція використовуючи lambda
((функція (x) (помножити x x)) 5)  ; => 25

; 5. Task statistics summary
; Статистика задач

; From analysis: 457 total, 232 completed, 225 remaining
; З аналізу: 457 загальних, 232 виконаних, 225 залишених

(нехай ((total 457) (completed 232))
  (відняти total completed))

; 5. The CLI prints: 225 (last expression)
; CLI друкує: 225 (останній вираз)
