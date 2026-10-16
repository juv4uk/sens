; D6:110000 TAKE, D6:110001 DROP, D6:101100 CURRY — pure SENS laws.
; Очікується шість предикатів D1:1. Не оголошує прямої D6 callability opcode.
(list
  (equal? (взяти #d24:000000000000000000000010
                 (list (quote а) (quote б) (quote в)))
          (list (quote а) (quote б)))
  (equal? (взяти #d24:000000000000000000000000
                 (list (quote а)))
          (quote ()))
  (equal? (відкинути #d24:000000000000000000000001
                     (list (quote а) (quote б) (quote в)))
          (list (quote б) (quote в)))
  (equal? (відкинути #d24:000000000000000000000000
                     (list (quote а)))
          (list (quote а)))
  (equal? ((частково-застосувати cons (quote x)) (quote ()))
          (cons (quote x) (quote ())))
  (equal? (додати-1 #d24:000000000000000000000001)
          #d24:000000000000000000000010))
