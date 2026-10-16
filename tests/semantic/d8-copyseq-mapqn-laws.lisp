; D8:01000010 COPY-SEQ proper-list lane; D8:01001010 MAPQN (CAR,CDR) over tails.
; Кожний нефоновий рядок = одна окрема нативна SENS програма з D1:1.
; Вісім незалежних перевірок включають позитив, перестановку і порожню межу.
(equal? (копіювати-послідовність (list (quote яблуко) (quote груша))) (list (quote яблуко) (quote груша)))
(null? (копіювати-послідовність (quote ())))
(not? (equal? (копіювати-послідовність (list (quote яблуко) (quote груша))) (list (quote груша) (quote яблуко))))
(equal? (копіювати-послідовність (list (list (quote яблуко)))) (list (list (quote яблуко))))
(equal? (голови-залишків (lambda (голова решта) (cons голова решта)) (list (quote яблуко) (quote груша))) (list (list (quote яблуко) (quote груша)) (list (quote груша))))
(not? (equal? (голови-залишків (lambda (голова решта) (cons голова решта)) (list (quote яблуко) (quote груша))) (list (list (quote груша) (quote яблуко)) (list (quote яблуко)))))
(null? (голови-залишків (lambda (голова решта) (cons голова решта)) (quote ())))
(equal? (голови-залишків (lambda (голова решта) (null? решта)) (list (quote яблуко) (quote груша))) (list (null? (list (quote груша))) (null? (quote ()))))
