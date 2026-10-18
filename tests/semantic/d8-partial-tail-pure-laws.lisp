; D8: PARTIAL, structural TAILP та чисті list-head функції.
; Кожний нефоновий рядок — окрема фізична SENS-програма, очікується D1:1.
(equal? ((partial (lambda (a b) (cons a b)) (quote а)) (список (quote б))) (список (quote а) (quote б)))
(equal? ((застосувати-префікс (lambda (a b) (список a b)) (quote а)) (quote б)) (список (quote а) (quote б)))
(спільний-хвіст? (quote (б в)) (quote (а б в)))
(спільний-хвіст? (quote ()) (quote (а б)))
(хибне? (спільний-хвіст? (quote (б г)) (quote (а б в))))
(хибне? (спільний-хвіст? (quote (а)) (quote ())))
(equal? (додати-на-початок (quote а) (quote (б в))) (quote (а б в)))
(equal? (зняти-з-початку (quote (а б в))) (quote (б в)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
(визначити спільний-хвіст? tailp?)
