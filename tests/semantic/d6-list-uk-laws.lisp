; D6:000000/000001/101010/101011 — один native SENS-свідок.
; D1 1 для 7 позитивних та 2 негативних законів, D24 тільки явно кваліфікований.
(список
  (equal? (довжина (quote ())) #d24:000000000000000000000000)
  (equal? (довжина (list (quote а) (quote б))) #d24:000000000000000000000010)
  (equal? (довжина-до (list (quote а)) #d24:000000000000000000000001)
          #d24:000000000000000000000010)
  (equal? (відобразити-до (lambda (x) x)
                         (список (quote а) (quote б)) (quote ()))
          (список (quote а) (quote б)))
  (equal? (відобразити-до (lambda (x) x) (quote ()) (quote ()))
          (quote ()))
  (хибне? (equal? (відобразити-до (lambda (x) x)
                               (список (quote а) (quote б)) (quote ()))
                (список (quote б) (quote а))))
  (equal? (відсіяти-до (lambda (x) (тотожне? x (quote а)))
                       (список (quote б) (quote а) (quote б)) (quote ()))
          (список (quote а)))
  (equal? (відсіяти-до (lambda (x) (тотожне? x (quote а)))
                       (quote ()) (quote ()))
          (quote ()))
  (хибне? (equal? (відсіяти-до (lambda (x) (тотожне? x (quote а)))
                             (список (quote б) (quote а)) (quote ()))
                (список (quote б)))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити тотожне? eq?)
(визначити список list)
(визначити хибне? not?)
