; D8: PARTIAL, structural TAILP та чисті list-head функції.
; Кожний нефоновий рядок — окрема фізична SENS-програма, очікується D1:1.
(equal? ((partial (lambda (a b) (cons a b)) (quote а)) (list (quote б))) (list (quote а) (quote б)))
(equal? ((застосувати-префікс (lambda (a b) (list a b)) (quote а)) (quote б)) (list (quote а) (quote б)))
(спільний-хвіст? (quote (б в)) (quote (а б в)))
(tailp? (quote ()) (quote (а б)))
(not? (спільний-хвіст? (quote (б г)) (quote (а б в))))
(not? (tailp? (quote (а)) (quote ())))
(equal? (додати-на-початок (quote а) (quote (б в))) (quote (а б в)))
(equal? (зняти-з-початку (quote (а б в))) (quote (б в)))
