; Чотири історичні епістемічні D10 функції, 12 незалежних законів D1:1.
; Точні координати: OBSERVATION 0010010011; CLAIM 0001110110;
; EVIDENCE 0010001111; INTENT 0010000101. Саме SENS виконує всі форми.
(equal? (створити-спостереження (quote телескоп) (quote зоря)) (list (quote observation) (list (quote source) (quote телескоп)) (list (quote statement) (quote зоря))))
(equal? (створити-твердження (quote зоря) (quote телескоп) (quote reviewed)) (list (quote claim) (list (quote statement) (quote зоря)) (list (quote source) (quote телескоп)) (list (quote review) (quote reviewed))))
(equal? (створити-доказ (quote посилання) (quote вимір) (quote supports) (quote digest)) (list (quote evidence) (list (quote claim-ref) (quote посилання)) (list (quote method) (quote вимір)) (list (quote outcome) (quote supports)) (list (quote source-ref) (quote digest))))
(equal? (створити-намір (quote ціль) (list (quote дозвіл)) (quote стоп) (quote результат)) (list (quote intent) (list (quote goal) (quote ціль)) (list (quote requires) (list (quote дозвіл))) (list (quote stop-on) (quote стоп)) (list (quote produces) (quote результат))))
(тотожне? (перше (створити-спостереження (quote а) (quote б))) (quote observation))
(тотожне? (перше (створити-твердження (quote а) (quote б) (quote reviewed))) (quote claim))
(тотожне? (перше (створити-доказ (quote а) (quote б) (quote supports) (quote г))) (quote evidence))
(тотожне? (перше (створити-намір (quote а) (quote б) (quote в) (quote г))) (quote intent))
(not? (equal? (створити-спостереження (quote а) (quote б)) (створити-спостереження (quote б) (quote а))))
(not? (equal? (створити-твердження (quote а) (quote б) (quote reviewed)) (створити-твердження (quote а) (quote б) (quote rejected))))
(not? (equal? (створити-доказ (quote а) (quote вимір) (quote supports) (quote г)) (створити-доказ (quote а) (quote вимір) (quote contradicts) (quote г))))
(not? (equal? (створити-намір (quote а) (quote б) (quote стоп) (quote г)) (створити-намір (quote а) (quote б) (quote тривати) (quote г))))
