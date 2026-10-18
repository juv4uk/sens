; Чотири історичні епістемічні D10 функції, 12 незалежних законів D1:1.
; Точні координати: OBSERVATION 0010010011; CLAIM 0001110110;
; EVIDENCE 0010001111; INTENT 0010000101. Саме SENS виконує всі форми.
(equal? (створити-спостереження (quote телескоп) (quote зоря)) (список (quote observation) (список (quote source) (quote телескоп)) (список (quote statement) (quote зоря))))
(equal? (створити-твердження (quote зоря) (quote телескоп) (quote reviewed)) (список (quote claim) (список (quote statement) (quote зоря)) (список (quote source) (quote телескоп)) (список (quote review) (quote reviewed))))
(equal? (створити-доказ (quote посилання) (quote вимір) (quote supports) (quote digest)) (список (quote evidence) (список (quote claim-ref) (quote посилання)) (список (quote method) (quote вимір)) (список (quote outcome) (quote supports)) (список (quote source-ref) (quote digest))))
(equal? (створити-намір (quote ціль) (список (quote дозвіл)) (quote стоп) (quote результат)) (список (quote intent) (список (quote goal) (quote ціль)) (список (quote requires) (список (quote дозвіл))) (список (quote stop-on) (quote стоп)) (список (quote produces) (quote результат))))
(тотожне? (перше (створити-спостереження (quote а) (quote б))) (quote observation))
(тотожне? (перше (створити-твердження (quote а) (quote б) (quote reviewed))) (quote claim))
(тотожне? (перше (створити-доказ (quote а) (quote б) (quote supports) (quote г))) (quote evidence))
(тотожне? (перше (створити-намір (quote а) (quote б) (quote в) (quote г))) (quote intent))
(хибне? (equal? (створити-спостереження (quote а) (quote б)) (створити-спостереження (quote б) (quote а))))
(хибне? (equal? (створити-твердження (quote а) (quote б) (quote reviewed)) (створити-твердження (quote а) (quote б) (quote rejected))))
(хибне? (equal? (створити-доказ (quote а) (quote вимір) (quote supports) (quote г)) (створити-доказ (quote а) (quote вимір) (quote contradicts) (quote г))))
(хибне? (equal? (створити-намір (quote а) (quote б) (quote стоп) (quote г)) (створити-намір (quote а) (quote б) (quote тривати) (quote г))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
