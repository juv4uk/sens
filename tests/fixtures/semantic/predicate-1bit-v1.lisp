; tests/fixtures/semantic/predicate-1bit-v1.lisp — #1709, закон #1699.
; Відповідь предиката = рівно один біт: 1 = ТАК, 0 = НІ.
; Ніякого четвертого типу: ні (), ні T/NIL, ні host Bool, ні 1^n/0^n,
; ні структурного запису. Якщо з'явиться третє представлення — це порушення
; цього закону, і таким рядом це видно.
;
; Predicate answer = exactly one bit: 1 = YES, 0 = NO. No fourth type: not
; (), not T/NIL, not a host Bool, not a 1^n/0^n run, not a structural record.
; A third presentation appearing anywhere below IS the violation this file
; exists to make visible.
;
; Джерела: #1699 (1 біт), #1704 (ATOM), #1705 (EQ), #1663 (спільна відповідь).
; Форми записані точними Function8/SpecialForm головами, без Symbol-авторитету.

((expect . expect-value)
 (expr . "(00100010 1 1)")
 (expected . (value (1)))
 (active . t)
 (name . "equal? 1 1 — точно один біт YES")
 (semantic-id . 00100010)
 (governs . "#1699")
 (note . "Відповідь предиката — один біт YES; не () і не T."))

((expect . expect-value)
 (expr . "(00100010 1 2)")
 (expected . (value (0)))
 (active . t)
 (name . "equal? 1 2 — точно один біт NO")
 (semantic-id . 00100010)
 (governs . "#1699")
 (note . "Відповідь предиката — один біт NO; не () і не T."))

((expect . expect-value)
 (expr . "(10110101 5)")
 (expected . (value (1)))
 (active . t)
 (name . "ATOM не-пара — один біт YES")
 (semantic-id . 10110101)
 (governs . "#1704")
 (note . "Будь-який не-структурний аргумент відповідає YES."))

((expect . expect-value)
 (expr . "(10110101 (00000001 (alpha beta)))")
 (expected . (value (0)))
 (active . t)
 (name . "ATOM пара — один біт NO")
 (semantic-id . 10110101)
 (governs . "#1704")
 (note . "Пара відповідає NO; третє представлення тут неможливе."))

; Цей ряд відкритий на головний закон, але ще не виконавний: поточний рантайм
; відповідає третім представленням (). #1704 вимагає () -> 1, #1713/#1714
; мають прибрати цю шкалу. Ряд лишається НЕ активним, доки закон не стане
; чинним на всіх профілях.
; This row states the central law but is not yet executable: the current
; runtime answers with a third presentation, (). #1704 requires () -> 1 and
; #1713/#1714 remove that scale. Stays inactive until the law holds.
((expect . expect-value)
 (expr . "(10110101 (00000001 ()))")
 (expected . (value (1)))
 (name . "ATOM пустого списку — один біт YES, а не третє представлення")
 (semantic-id . 10110101)
 (governs . "#1704 #1709")
 (note . "Поки неактивний: main відповідає (). Це і є четвертий тип, який #1699 забороняє."))
