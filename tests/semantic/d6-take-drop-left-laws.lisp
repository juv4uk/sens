; D6:110000 TAKE та D6:110001 DROP: десять D1 законів лівого поділу.
(список
  (equal? (взяти #d24:000000000000000000000000 (list (quote а) (quote б))) (quote ()))
  (equal? (відкинути #d24:000000000000000000000000 (list (quote а) (quote б))) (list (quote а) (quote б)))
  (equal? (взяти #d24:000000000000000000000001 (list (quote а) (quote б))) (list (quote а)))
  (equal? (відкинути #d24:000000000000000000000001 (list (quote а) (quote б))) (list (quote б)))
  (equal? (взяти #d24:000000000000000000000010 (list (quote а) (quote б))) (list (quote а) (quote б)))
  (null? (відкинути #d24:000000000000000000000010 (list (quote а) (quote б))))
  (equal? (взяти #d24:000000000000000000000011 (list (quote а) (quote б))) (list (quote а) (quote б)))
  (null? (відкинути #d24:000000000000000000000011 (list (quote а) (quote б))))
  (null? (взяти #d24:000000000000000000000001 (quote ())))
  (null? (відкинути #d24:000000000000000000000001 (quote ()))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити порожній? null?)
