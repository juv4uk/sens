; My-Lisp task demonstration script
; Скрипт My-Lisp: демонстрація задач

; Demonstrate basic Lisp operations
; Демонстраціяbasic Lisp операцій

; 1. Arithmetic
; Арифметика
(00001100 1 2 3 4 5)  ; => 15

; 2. cons cell
; cons-сельта
(00001001 pair (00000100 1 2))  ; Creates a pair (1 . 2)

; 3. car and cdr
; car та cdr
(00000101 pair)  ; => 1
(00000110 pair)  ; => 2

; 4. Simple function using lambda
; Проста функція використовуючи lambda
((00001000 (x) (00001110 x x)) 5)  ; => 25

; 5. Task statistics summary
; Статистика задач

; From analysis: 457 total, 232 completed, 225 remaining
; З аналізу: 457 загальних, 232 виконаних, 225 залишених

(10011100 ((total 457) (completed 232))
  (00001101 total completed))

; 5. The CLI prints: 225 (last expression)
; CLI друкує: 225 (останній вираз)
