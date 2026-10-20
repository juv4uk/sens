; #217 — виконувані цілі для канонічного явного контролю.
;
; Контроль споживає результати, що належать домену. Він не вирішує, що довільні
; значення Lisp є істинними/хибними з їхньої форми.
;
; Exact-Q рішення — єдиний математичний бінарний вхід у цьому першому зрізі:
;   1/1 (канонічний запис 1) -> вибрати клаузу
;   0/1 (канонічний запис 0) -> перейти до наступної клаузи
;
; Усі інші рядки нижче мусять бути відкинуті при неявному вжитку як умова.

((expr . "(cond (1 7))")
 (expected . "7")
 (active . t)
 (case . exact-q-yes-selects))

((expr . "(cond (0 7) (1 9))")
 (expected . "9")
 (active . t)
 (case . exact-q-no-continues))

((expr . "(cond (1/2 7))")
 (error . "Type")
 (active . t)
 (case . ordinary-rational-is-not-decision))

((expr . "(cond (2 7))")
 (error . "Type")
 (active . t)
 (case . ordinary-integer-is-not-decision))

((expr . "(cond (() 7))")
 (error . "Type")
 (active . t)
 (case . empty-list-is-not-false))

((expr . "(cond ((quote radio) 7))")
 (error . "Type")
 (active . t)
 (case . symbol-is-not-condition))

((expr . "(cond ((quote (radio)) 7))")
 (error . "Type")
 (active . t)
 (case . list-is-not-condition))
