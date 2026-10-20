; #217 — виконувані приклади чинної української операції «за-умовою».
;
; Контроль споживає результати, що належать домену. Він не вирішує, що довільні
; значення Lisp є істинними/хибними з їхньої форми.
;
; Exact-Q рішення — єдиний математичний бінарний вхід у цьому першому зрізі:
;   1/1 (канонічний запис 1) -> вибрати клаузу
;   0/1 (канонічний запис 0) -> перейти до наступної клаузи
;
; Інші вхідні значення не можна неявно вважати умовою.
; Імена expr, expected, error, active та case — поля формату свідчення.

((expr . "(за-умовою (1 7))")
 (expected . "7")
 (active . t)
 (case . exact-q-yes-selects))

((expr . "(за-умовою (0 7) (1 9))")
 (expected . "9")
 (active . t)
 (case . exact-q-no-continues))

((expr . "(за-умовою (1/2 7))")
 (error . "Type")
 (active . t)
 (case . ordinary-rational-is-not-decision))

((expr . "(за-умовою (2 7))")
 (error . "Type")
 (active . t)
 (case . ordinary-integer-is-not-decision))

((expr . "(за-умовою (() 7))")
 (error . "Type")
 (active . t)
 (case . empty-list-is-not-false))

((expr . "(за-умовою ((як-є radio) 7))")
 (error . "Type")
 (active . t)
 (case . symbol-is-not-condition))

((expr . "(за-умовою ((як-є (radio)) 7))")
 (error . "Type")
 (active . t)
 (case . list-is-not-condition))
