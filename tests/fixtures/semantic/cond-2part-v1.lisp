; tests/fixtures/semantic/cond-2part-v1.lisp — #1709, закон #1713.
; УCondition допускаються лише 2-частинні клаузи (test expression):
;   test = 1       -> select; результат = значення виразу
;   test = 0       -> skip; перейти до наступної клаузи
;   усі skip       -> вичерпання, структурне ()
;   інша форма     -> не допускається (negative fixture)
;
; Важлива різниця: () тут НЕ є відповіддю предиката. () тут — структурне
; значення вичерпання COND, яке існує і буде існувати. Заборонене
; представлення () стосується відповіді предиката, а не цього виразу.
;
; COND admits only 2-part clauses (test expression):
;   test = 1   -> select; result is the expression value
;   test = 0   -> skip; continue to the next clause
;   all skip   -> exhaustion, the structural value ()
;   other form -> not admissible (negative fixture)
;
; Note the boundary: () here is NOT a predicate answer. () here is the
; structural exhaustion value of COND and stays legal. The forbidden ()
; presentation is about predicate answers, not about this expression.

((expect . expect-value)
 (expr . "(00000111 ((00100010 1 1) 7))")
 (expected . (value 7))
 (active . t)
 (name . "COND: test 1 вибирає клаузу")
 (semantic-id . 00000111)
 (governs . "#1713")
 (note . "Точний біт 1 select -> значення виразу 7."))

((expect . expect-value)
 (expr . "(00000111 ((00100010 1 2) 7))")
 (expected . (value ()))
 (active . t)
 (name . "COND: test 0 пропускає, вичерпання дає структурне ()")
 (semantic-id . 00000111)
 (governs . "#1713")
 (note . "Точний біт 0 skip -> (), де () — вичерпання, а не відповідь предиката."))

((expect . expect-value)
 (expr . "(00000111 ((00100010 1 2) 7) ((00100010 1 1) 9))")
 (expected . (value 9))
 (active . t)
 (name . "COND: skip 0 продовжує до наступної клаузи з 1")
 (semantic-id . 00000111)
 (governs . "#1713")
 (note . "0 пропускається, наступний 1 вибирає 9 — не перший ненулльовий."))

; Negative fixture. Тричастинна клауза (query expected-result expression) —
; спадоковий migration-форма, який #1713/#1714 мають прибрати з читача.
; Ряд НЕ активний: поки що рантайм приймає її як query і повертає
; UnsatisfiedConditional замість відхилення читачем.
; Negative fixture. A 3-part clause is a legacy migration form that
; #1713/#1714 must remove from the reader. Inactive: the runtime still
; accepts it as a query and fails with UnsatisfiedConditional instead of
; being rejected by the reader.
((expect . expect-rejected)
 (expr . "(00000111 (0 7 8))")
 (expected . (rejected "(00000111 (0 7 8))"))
 (name . "COND: тричастинна клауза не допускається читачем")
 (semantic-id . 00000111)
 (governs . "#1713 #1714")
 (note . "Неактивний: main ще приймає 3-частинну форму. Порожній cond (InvalidForm) має нерatifікований закон — ряд свідомо не додано."))
